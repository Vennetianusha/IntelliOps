import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.services.ai_service import analyze_issue, _validate_and_normalize_ai_response, _fallback_heuristic_analysis, _detect_team, _detect_category, _detect_priority
from app.cache.service import get_cached_ai_triage, build_ai_triage_cache_key

title = "Add dark mode to the dashboard"
desc = ""

print("=" * 70)
print("TRACE FOR: Title='Add dark mode to the dashboard', Desc=''")
print("=" * 70)

# 1. Check Redis cache
cache_key = build_ai_triage_cache_key(title, desc)
cached_val = get_cached_ai_triage(title, desc)
print(f"\n1. REDIS CACHE (Key: {cache_key}):")
print("   Value:", cached_val)

# 2. Heuristic Detection
print("\n2. HEURISTIC ENGINE DETECTIONS:")
print("   Expected Team    :", _detect_team(title, desc))
print("   Expected Category:", _detect_category(title, desc))
print("   Expected Priority:", _detect_priority(title, desc, _detect_category(title, desc)))

# 3. Gemini API direct call
print("\n3. GEMINI API CALL:")
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())
        combined_text = f"Title: {title}\nDescription: {desc}".strip()
        
        prompt = f"""
You are an expert AI Engineering Operations Lead. Analyze the technical issue below and return ONLY a valid JSON object.

ISSUE TO TRIAGE:
{combined_text}

CLASSIFICATION RULES:

1. CATEGORY (Must be one of: "bug", "feature", "incident", "task", "tech_debt"):
- "incident": Active operational or production outage / disruption (e.g. production service down, service completely unavailable, widespread outage).
- "tech_debt": Primary purpose is refactoring, code cleanup, removing duplication, legacy code removal, maintainability.
- "feature": Requesting NEW functionality, UI enhancements, or capabilities that do NOT exist (e.g. add dark mode, add theme switcher, introduce CSV export, implement endpoint, automate release pipeline).
- "task": Concrete maintenance or documentation item that is NOT a broken existing feature and NOT a new product feature (e.g., update API documentation, prepare test environment, update dependencies).
- "bug": Existing functionality is broken, failing, crashing, blank screen, 500 error, behaving incorrectly.

2. ASSIGNED TEAM (Must be one of: "frontend", "backend", "devops", "platform", "data"):
CRITICAL RULE: assigned_team MUST represent the primary engineering team responsible for implementing or fixing the issue, NOT a team that might support it indirectly. DO NOT default to "backend".
If description is empty, analyze the title alone!

- "frontend": Client-side UI, React, web page, screen, dashboard, buttons, forms, CSS layout, theme switcher, dark mode, browser rendering, visual behavior, client state.
  Examples:
  * "Add dark mode to dashboard" -> frontend
  * "Add a theme switcher to the web dashboard" -> frontend
  * "Dashboard button does not work" -> frontend
  * "Login page is blank" -> frontend
  * "React component is not rendering" -> frontend
  * "CSS layout is broken" -> frontend

- "backend": Server-side APIs, REST endpoints, FastAPI, business logic, server database queries, server-side authentication, HTTP 500 server errors.
  Examples:
  * "REST API returns 500" -> backend
  * "FastAPI endpoint crashes" -> backend
  * "Implement an endpoint to retrieve user history" -> backend
  * "Document the latest API endpoints" -> backend

- "devops": Deployment pipelines, CI/CD, GitHub Actions, Docker containers, release engineering, staging/production deployment automation.
  Examples:
  * "Release pipeline fails during deployment" -> devops
  * "CI pipeline deployment fails" -> devops
  * "Docker deployment fails" -> devops
  * "Automate production releases" -> devops

- "platform": Operating system, Linux core, system runtime upgrades, OS-level libraries, platform infrastructure core.
  Examples:
  * "Application fails after Linux update" -> platform
  * "Service fails after runtime upgrade" -> platform
  * "Service stopped after Linux upgrade" -> platform

- "data": Data pipelines, ETL jobs, analytics processing, data warehouse ingestion, reporting data, missing records.
  Examples:
  * "ETL pipeline produces incorrect records" -> data
  * "Analytics pipeline is dropping records" -> data
  * "Daily report is missing customer records" -> data

3. PRIORITY (Must be one of: "low", "medium", "high", "critical"):
- "critical": Severe production-wide or system-wide outage ONLY.
- "high": Significant failures, important functionality blocked (HTTP 500 errors, deployment failure, CI pipeline failure, OS update service failure, login blank screen, analytics dropping records).
- "medium": Standard bugs, standard feature requests, refactoring / tech debt.
- "low": Documentation updates, minor maintenance, low-impact work.

4. KEYWORDS:
- 3 to 5 meaningful technical terms (e.g., ["dark_mode", "dashboard", "frontend"]). DO NOT copy random filler words.

5. SUGGESTED ACTION:
Must directly match assigned_team and category:
- FRONTEND: Focus on frontend component, theme toggle, React state, CSS, or browser UI work. NEVER mention backend components or API endpoints for frontend issues!
- BACKEND: Focus on REST API endpoints, server logic, database handlers, or HTTP status codes.
- DEVOPS: Focus on CI/CD pipelines, Docker images, GitHub Actions, or deployment scripts.
- PLATFORM: Focus on OS dependencies, system runtime logs, kernel updates, or platform configuration.
- DATA: Focus on ETL data pipelines, analytics data validation, or database transformation steps.

JSON OUTPUT SCHEMA:
{{
  "category": "bug" | "feature" | "incident" | "task" | "tech_debt",
  "priority": "low" | "medium" | "high" | "critical",
  "assigned_team": "frontend" | "backend" | "devops" | "platform" | "data",
  "keywords": ["tech1", "tech2", "tech3"],
  "suggested_action": "Clear actionable triage recommendation matching assigned_team"
}}
"""
        response = client.models.generate_content(
            model=settings.AI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        print("   Raw Gemini Response Text:")
        print(response.text)
        
        parsed = json.loads(response.text)
        print("\n4. PARSED GEMINI JSON:")
        print(json.dumps(parsed, indent=2))
        
        validated = _validate_and_normalize_ai_response(parsed, title, desc)
        print("\n5. AFTER VALIDATION & GUARDRAILS:")
        print(json.dumps(validated, indent=2))
        
    except Exception as e:
        print("   Gemini API call failed:", e)
else:
    print("   GEMINI_API_KEY not set.")

# 6. Fallback engine result
print("\n6. DETERMINISTIC FALLBACK RESULT:")
print(json.dumps(_fallback_heuristic_analysis(title, desc), indent=2))

# 7. Final analyze_issue call
print("\n7. FINAL analyze_issue() RETURN:")
print(json.dumps(analyze_issue(title, desc), indent=2))
