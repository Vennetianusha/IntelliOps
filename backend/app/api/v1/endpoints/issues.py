from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.models.issue import Issue
from app.schemas.issue import (
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    AIAnalysisRequest,
    AIAnalysisResponse,
)
from app.cache.service import (
    get_cached_issues_list,
    set_cached_issues_list,
    get_cached_issue_detail,
    set_cached_issue_detail,
    invalidate_issue_caches,
)
from app.services.ai_service import analyze_issue

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze an issue with AI",
    description="Analyzes an issue title and description to predict category, priority, team, keywords, and suggested actions.",
)
def analyze_issue_endpoint(payload: AIAnalysisRequest):
    """
    Standalone AI analysis endpoint for issue triage preview.
    Uses AI provider or heuristic fallback if AI is unavailable.
    """
    analysis = analyze_issue(payload.title, payload.description)
    return analysis


@router.post(
    "",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new issue",
    description="Creates a new engineering issue. Enriches missing or default fields with AI issue analysis.",
)
def create_issue(
    issue_in: IssueCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new issue in PostgreSQL, auto-enriching metadata with AI analysis,
    and invalidating Redis list caches.
    """
    try:
        # Run AI analysis to enrich category, priority, and assigned_team if omitted or default
        ai_data = analyze_issue(issue_in.title, issue_in.description)

        category = issue_in.category if issue_in.category else ai_data["category"]
        priority = issue_in.priority if issue_in.priority else ai_data["priority"]
        assigned_team = issue_in.assigned_team if issue_in.assigned_team else ai_data["assigned_team"]

        issue = Issue(
            title=issue_in.title,
            description=issue_in.description,
            category=category,
            priority=priority,
            status=issue_in.status or "open",
            assigned_team=assigned_team,
        )
        db.add(issue)
        db.commit()
        db.refresh(issue)

        # Cache Invalidation: Purge stale list queries
        invalidate_issue_caches()

        return issue
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating issue: {str(e)}",
        )


@router.get(
    "",
    response_model=List[IssueResponse],
    status_code=status.HTTP_200_OK,
    summary="List issues",
    description="Retrieve all engineering issues with Cache-Aside pattern (Redis -> PostgreSQL fallback).",
)
def list_issues(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[str] = Query(None, alias="priority", description="Filter by priority"),
    db: Session = Depends(get_db),
):
    """
    Cache-Aside GET list endpoint.
    """
    # 1. Cache-Aside Check
    cached = get_cached_issues_list(status_filter, priority_filter)
    if cached is not None:
        return cached

    # 2. Database query on cache miss
    try:
        query = db.query(Issue)
        if status_filter:
            query = query.filter(Issue.status == status_filter)
        if priority_filter:
            query = query.filter(Issue.priority == priority_filter)

        issues = query.order_by(Issue.created_at.desc()).all()

        # 3. Populate Redis cache
        serialized = [IssueResponse.model_validate(item).model_dump(mode="json") for item in issues]
        set_cached_issues_list(status_filter, priority_filter, serialized)

        return serialized
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching issues: {str(e)}",
        )


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
    status_code=status.HTTP_200_OK,
    summary="Get issue by ID",
    description="Retrieve issue details with Cache-Aside pattern.",
)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
):
    """
    Cache-Aside GET detail endpoint.
    """
    # 1. Cache-Aside Check
    cached = get_cached_issue_detail(issue_id)
    if cached is not None:
        return cached

    # 2. Database query on cache miss
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {issue_id} not found.",
            )

        # 3. Populate Redis cache
        serialized = IssueResponse.model_validate(issue).model_dump(mode="json")
        set_cached_issue_detail(issue_id, serialized)

        return serialized
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while reading issue: {str(e)}",
        )


@router.put(
    "/{issue_id}",
    response_model=IssueResponse,
    status_code=status.HTTP_200_OK,
    summary="Update issue by ID",
    description="Update issue fields and invalidate associated Redis cache entries.",
)
def update_issue(
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an issue and purge associated list and detail cache keys.
    """
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {issue_id} not found.",
            )

        update_data = issue_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)

        db.commit()
        db.refresh(issue)

        # Cache Invalidation
        invalidate_issue_caches(issue_id=issue_id)

        return issue
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while updating issue: {str(e)}",
        )


@router.delete(
    "/{issue_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete issue by ID",
    description="Delete an issue and purge associated Redis cache entries.",
)
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an issue and purge cache entries.
    """
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {issue_id} not found.",
            )

        db.delete(issue)
        db.commit()

        # Cache Invalidation
        invalidate_issue_caches(issue_id=issue_id)

        return {"message": f"Issue {issue_id} deleted successfully", "id": issue_id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while deleting issue: {str(e)}",
        )
