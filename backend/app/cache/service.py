from typing import Any, List, Optional
from app.cache.client import redis_client


def build_list_cache_key(status: Optional[str] = None, priority: Optional[str] = None) -> str:
    """
    Constructs deterministic Redis cache key for issue list query combinations.
    Example: 'issues:list:status=open:priority=high'
    """
    s_part = f"status={status}" if status else "status=all"
    p_part = f"priority={priority}" if priority else "priority=all"
    return f"issues:list:{s_part}:{p_part}"


def build_detail_cache_key(issue_id: int) -> str:
    """
    Constructs Redis cache key for single issue detail lookup.
    Example: 'issues:detail:1'
    """
    return f"issues:detail:{issue_id}"


def get_cached_issues_list(status: Optional[str] = None, priority: Optional[str] = None) -> Optional[List[Any]]:
    """
    Attempts to read cached issues list from Redis.
    """
    key = build_list_cache_key(status, priority)
    return redis_client.get(key)


def set_cached_issues_list(status: Optional[str], priority: Optional[str], data: List[Any], ttl: Optional[int] = None):
    """
    Caches issues list JSON data in Redis.
    """
    key = build_list_cache_key(status, priority)
    redis_client.set(key, data, ttl=ttl)


def get_cached_issue_detail(issue_id: int) -> Optional[Any]:
    """
    Attempts to read cached issue detail from Redis.
    """
    key = build_detail_cache_key(issue_id)
    return redis_client.get(key)


def set_cached_issue_detail(issue_id: int, data: Any, ttl: Optional[int] = None):
    """
    Caches single issue detail JSON data in Redis.
    """
    key = build_detail_cache_key(issue_id)
    redis_client.set(key, data, ttl=ttl)


import hashlib


def build_ai_triage_cache_key(title: str, description: Optional[str] = None) -> str:
    """
    Constructs deterministic Redis cache key for AI issue triage analysis.
    Uses versioned namespace 'ai:triage:v3:<sha256>' to invalidate all legacy AI cache entries.
    """
    normalized = f"{(title or '').strip().lower()}:{(description or '').strip().lower()}"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"ai:triage:v3:{digest}"


def get_cached_ai_triage(title: str, description: Optional[str] = None) -> Optional[Any]:
    """
    Attempts to read cached AI triage analysis from Redis.
    """
    key = build_ai_triage_cache_key(title, description)
    return redis_client.get(key)


def set_cached_ai_triage(title: str, description: Optional[str], data: Any, ttl: Optional[int] = 300):
    """
    Caches AI triage analysis JSON data in Redis with default 300s TTL.
    """
    if not data or not isinstance(data, dict):
        return
    key = build_ai_triage_cache_key(title, description)
    redis_client.set(key, data, ttl=ttl)


def invalidate_issue_caches(issue_id: Optional[int] = None):
    """
    Invalidates issue caches on mutation (Create/Update/Delete).
    Always flushes list caches ('issues:list:*').
    If issue_id is provided, also invalidates 'issues:detail:<issue_id>'.
    """
    # Flushes all cached lists
    redis_client.delete_pattern("issues:list:*")

    # Flushes specific detail cache if issue_id specified
    if issue_id is not None:
        key = build_detail_cache_key(issue_id)
        redis_client.delete(key)

