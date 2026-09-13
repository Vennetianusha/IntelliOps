import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("intelliops.ai")


def analyze_issue(title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes an engineering issue title and description, returning structured AI metadata:
    - category (bug, feature, incident, task, tech_debt)
    - priority (low, medium, high, critical)
    - assigned_team (backend, frontend, devops, platform, data)
    - keywords (List[str])
    - suggested_action (str)

    If GEMINI_API_KEY is configured, queries Google Gemini API.
    If the API call fails or no key is configured, falls back to a heuristic rule engine.
    """
    desc = description or ""
    combined_text = f"Title: {title}\nDescription: {desc}".strip()

    # Attempt AI API analysis if API key is provided
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())

            prompt = f"""
You are an expert AI Engineering Operations Lead. Analyze the technical issue below and return ONLY a valid JSON object.

ISSUE:
{combined_text}

JSON SCHEMA REQUIRED:
{{
  "category": "bug" | "feature" | "incident" | "task" | "tech_debt",
  "priority": "low" | "medium" | "high" | "critical",
  "assigned_team": "backend" | "frontend" | "devops" | "platform" | "data",
  "keywords": ["list", "of", "relevant", "technical", "terms"],
  "suggested_action": "Clear actionable step to investigate or resolve this issue"
}}
"""
            response = client.models.generate_content(
                model=settings.AI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            if response and response.text:
                data = json.loads(response.text)
                return _validate_and_normalize_ai_response(data, title, desc)

        except Exception as e:
            logger.warning(f"AI Provider API call failed: {str(e)}. Falling back to heuristic engine.")

    # Heuristic Rule Engine Fallback
    return _fallback_heuristic_analysis(title, desc)


def _validate_and_normalize_ai_response(data: Dict[str, Any], title: str, desc: str) -> Dict[str, Any]:
    """
    Validates and normalizes fields returned by the AI provider.
    """
    valid_categories = {"bug", "feature", "incident", "task", "tech_debt"}
    valid_priorities = {"low", "medium", "high", "critical"}
    valid_teams = {"backend", "frontend", "devops", "platform", "data"}

    cat = str(data.get("category", "")).lower()
    pri = str(data.get("priority", "")).lower()
    team = str(data.get("assigned_team", "")).lower()
    keywords = data.get("keywords", [])
    action = str(data.get("suggested_action", "")).strip()

    fallback = _fallback_heuristic_analysis(title, desc)

    return {
        "category": cat if cat in valid_categories else fallback["category"],
        "priority": pri if pri in valid_priorities else fallback["priority"],
        "assigned_team": team if team in valid_teams else fallback["assigned_team"],
        "keywords": [str(k).lower() for k in keywords[:6]] if isinstance(keywords, list) and keywords else fallback["keywords"],
        "suggested_action": action if action else fallback["suggested_action"],
    }


def _fallback_heuristic_analysis(title: str, desc: str) -> Dict[str, Any]:
    """
    Rule-based technical issue analyzer that generates structured suggestions
    when external AI APIs are offline or unconfigured.
    """
    text = f"{title} {desc}".lower()

    # Category Detection
    if any(k in text for k in ["outage", "down", "production", "crash", "incident", "spike", "500"]):
        category = "incident"
    elif any(k in text for k in ["bug", "error", "fail", "exception", "broken", "fix", "defect"]):
        category = "bug"
    elif any(k in text for k in ["add", "build", "create", "support", "feature", "new", "ui", "button", "export", "csv"]):
        category = "feature"
    elif any(k in text for k in ["refactor", "cleanup", "debt", "deprecated", "legacy"]):
        category = "tech_debt"
    else:
        category = "task"


    # Priority Detection
    if any(k in text for k in ["outage", "down", "security", "data loss", "critical"]):
        priority = "critical"
    elif any(k in text for k in ["high", "timeout", "spike", "blocker", "slow", "urgent"]):
        priority = "high"
    elif any(k in text for k in ["low", "minor", "cosmetic", "typo"]):
        priority = "low"
    else:
        priority = "medium"

    # Team Detection
    if any(k in text for k in ["react", "css", "component", "frontend", "vite", "ui", "html"]):
        assigned_team = "frontend"
    elif any(k in text for k in ["docker", "deploy", "kubernetes", "ci", "devops", "cloud", "aws", "pipeline"]):
        assigned_team = "devops"
    elif any(k in text for k in ["auth", "gateway", "infrastructure", "platform", "redis"]):
        assigned_team = "platform"
    elif any(k in text for k in ["data", "etl", "warehouse", "spark", "query"]):
        assigned_team = "data"
    else:
        assigned_team = "backend"

    # Keyword Extraction
    extracted = set(re.findall(r"\b[a-z]{4,15}\b", text))
    stopwords = {"this", "that", "with", "from", "have", "been", "will", "would", "could", "should", "there", "their", "issue"}
    tech_keywords = [w for w in extracted if w not in stopwords][:5]

    # Actionable Suggestion
    if category == "incident":
        suggested_action = "Identify root cause in server/error logs, check recent deployments, and page relevant on-call engineers."
    elif category == "bug":
        suggested_action = "Reproduce bug in dev environment, inspect stack trace, and write targeted unit test fix."
    elif category == "feature":
        suggested_action = "Review feature requirements, design component architecture, and break into sub-tasks."
    elif category == "tech_debt":
        suggested_action = "Audit affected codebase area, plan refactoring steps, and verify test coverage before modification."
    else:
        suggested_action = "Review task scope, assign lead engineer, and schedule for current sprint iteration."

    return {
        "category": category,
        "priority": priority,
        "assigned_team": assigned_team,
        "keywords": tech_keywords,
        "suggested_action": suggested_action,
    }
