from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IssueBase(BaseModel):
    """Base Pydantic schema containing shared fields for Issue entities."""
    title: str = Field(..., min_length=1, max_length=255, description="Short summary of the issue")
    description: Optional[str] = Field(None, description="Detailed technical issue description")
    category: str = Field("bug", min_length=1, max_length=50, description="Category e.g. bug, feature, incident, task")
    priority: str = Field("medium", max_length=50, description="Priority e.g. low, medium, high, critical")
    status: str = Field("open", max_length=50, description="Status e.g. open, in_progress, resolved, closed")
    assigned_team: Optional[str] = Field(None, max_length=100, description="Assigned engineering team")


class IssueCreate(IssueBase):
    """Schema for validating issue creation POST requests."""
    category: Optional[str] = Field("bug", max_length=50)
    priority: Optional[str] = Field("medium", max_length=50)
    status: Optional[str] = Field("open", max_length=50)


class IssueUpdate(BaseModel):
    """Schema for validating issue update PUT requests (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    priority: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    assigned_team: Optional[str] = Field(None, max_length=100)


class IssueResponse(IssueBase):
    """Schema for serializing Issue objects into JSON responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAnalysisRequest(BaseModel):
    """Schema for AI issue analysis requests."""
    title: str = Field(..., min_length=1, max_length=255, description="Issue title to analyze")
    description: Optional[str] = Field(None, description="Issue description to analyze")


class AIAnalysisResponse(BaseModel):
    """Schema for structured AI analysis results."""
    category: str
    priority: str
    assigned_team: str
    keywords: List[str]
    suggested_action: str
