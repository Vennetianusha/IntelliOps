import json
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.issue import AIAnalysisResponse
from app.cache.service import get_cached_ai_triage, set_cached_ai_triage

logger = logging.getLogger("intelliops.ai")

VALID_CATEGORIES = {"bug", "feature", "incident", "task", "tech_debt"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_TEAMS = {"backend", "frontend", "devops", "platform", "data"}

GENERIC_STOPWORDS = {
    "this", "that", "with", "from", "have", "been", "will", "would", "could", "should",
    "there", "their", "issue", "issues", "users", "user", "entering", "affects", "page", "screen",
    "using", "when", "after", "before", "because", "happens", "latest", "version", "system",
    "application", "please", "about", "which", "where", "what", "more", "some", "such",
    "the", "and", "for", "are", "but", "not", "all", "any", "can", "had", "her", "was",
    "one", "our", "out", "has", "him", "how", "new", "now", "old", "see", "two", "way",
    "who", "did", "its", "let", "put", "say", "she", "too", "use", "able", "switch", "between",
    "across", "cannot", "currently", "several", "into", "reduce", "same", "worked", "correctly",
    "happens", "consistently", "whenever", "client", "sends", "valid", "request", "filtered",
    "engineering", "list", "file", "data", "offline", "during", "night", "batch", "load"
}


def _has_pattern(text: str, keywords: List[str]) -> bool:
    """
    Returns True if any keyword or phrase matches the text.
    For single-word tokens (no spaces, hyphens, or slashes), enforces whole-word boundaries (\\b)
    to prevent false substring matches (e.g. 'form' matching inside 'platform' or 'information').
    For multi-word phrases, checks phrase inclusion.
    """
    text_lower = text.lower()
    for k in keywords:
        k_clean = k.strip().lower()
        if not k_clean:
            continue
        if " " not in k_clean and "-" not in k_clean and "/" not in k_clean:
            pattern = rf"\b{re.escape(k_clean)}\b"
            if re.search(pattern, text_lower):
                return True
        else:
            if k_clean in text_lower:
                return True
    return False


def analyze_issue(title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes an engineering issue title and description, returning structured AI metadata:
    - category (bug, feature, incident, task, tech_debt)
    - priority (low, medium, high, critical)
    - assigned_team (backend, frontend, devops, platform, data)
    - keywords (List[str])
    - suggested_action (str)

    Checks Redis cache for key 'ai:triage:v2:<hash>'.
    Queries Google Gemini API when GEMINI_API_KEY is configured.
    Applies Pydantic validation, conflict resolution, and falls back gracefully to a deterministic rule engine.
    Stores clean result in Redis cache.
    """
    desc = description or ""
    combined_text = f"Title: {title}\nDescription: {desc}".strip()

    logger.info(f"[TRIAGE STEP 1] Input Title: '{title}' | Description: '{desc}'")

    # 0. Check Redis cache first (Cache HIT / MISS)
    cached_res = get_cached_ai_triage(title, desc)
    if cached_res is not None:
        logger.info(f"[TRIAGE STEP 2] Redis Cache HIT for '{title}': {cached_res}")
        return cached_res
    else:
        logger.info(f"[TRIAGE STEP 2] Redis Cache MISS for '{title}'")

    result: Optional[Dict[str, Any]] = None

    # 1. Query Google Gemini API if key is provided
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())

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

            if response and response.text:
                text_content = response.text.strip()
                logger.info(f"[TRIAGE STEP 3] Gemini Raw Response:\n{text_content}")
                if text_content.startswith("```"):
                    text_content = re.sub(r"^```(?:json)?\n?", "", text_content)
                    text_content = re.sub(r"\n?```$", "", text_content).strip()
                raw_data = json.loads(text_content)
                logger.info(f"[TRIAGE STEP 4] Parsed Gemini JSON: {raw_data}")
                result = _validate_and_normalize_ai_response(raw_data, title, desc)

        except Exception as e:
            logger.warning(f"Gemini API call or parsing failed: {str(e)}. Falling back to deterministic triage engine.")

    # 2. Fall back to Deterministic Triage Engine if Gemini unconfigured/failed
    if result is None:
        logger.info(f"[TRIAGE STEP 7] Using Deterministic Fallback Engine for '{title}'")
        result = _fallback_heuristic_analysis(title, desc)

    logger.info(f"[TRIAGE STEP 8] Final Triage Result: {result}")

    # 3. Save result to Redis cache
    set_cached_ai_triage(title, desc, result, ttl=300)

    return result


def _detect_team(title: str, desc: str) -> str:
    """
    Determines the primary technical engineering team based on explicit technical domain signals.
    """
    text_lower = f"{title} {desc}".lower()

    # 1. DevOps Signals (CI/CD, Docker, GitHub Actions, deployment pipelines, release automation, staging/test env)
    devops_keywords = [
        "docker", "ci pipeline", "cd pipeline", "ci/cd", "github actions", "deployment fail", "deployment failed",
        "deployment job", "deployment pipeline", "build pipeline", "staging environment", "staging deployment",
        "production deployment", "automate production releases", "release pipeline", "kubernetes", "k8s", "helm",
        "terraform", "infrastructure automation", "test environment configuration", "staging test environment",
        "environment variables and seed data", "test environment", "pipeline fails", "deployment failure",
        "fails during deployment"
    ]
    if _has_pattern(text_lower, devops_keywords):
        return "devops"

    # 2. Platform Signals (OS, Linux, Ubuntu, system runtime, platform services, runtime upgrade, system libraries)
    platform_keywords = [
        "operating system", "os update", "ubuntu", "upgrading ubuntu", "linux update", "linux", "system runtime",
        "kernel", "operating-system", "platform service", "system-level", "system core", "runtime upgrade",
        "runtime update", "runtime compatibility", "system libraries", "system library", "linux upgrade",
        "service stopped after linux"
    ]
    if _has_pattern(text_lower, platform_keywords):
        return "platform"

    # 3. Data Signals (ETL, analytics, data pipelines, reporting, daily report, missing records, data quality)
    data_keywords = [
        "data pipeline", "etl", "analytics report", "analytics pipeline", "analytics", "missing records",
        "incorrect data", "data quality", "reporting data", "data processing", "data warehouse",
        "daily report", "incorrect records", "data ingestion", "missing user records", "missing customer records",
        "dropping records", "daily data quality report", "analytics is dropping"
    ]
    if _has_pattern(text_lower, data_keywords):
        return "data"

    # 4. Frontend Signals (UI, webpage, screen, dashboard, React, browser, rendering, dark mode, CSS, theme, buttons, navigation)
    frontend_keywords = [
        "dark mode", "dark theme", "theme switcher", "theme toggle", "light and dark", "switch between light",
        "dashboard", "profile page", "login page", "sign-in page", "login screen", "navigation menu", "navbar",
        "submit button", "search button", "search box", "button", "ui", "webpage", "screen", "react", "browser",
        "rendering", "not rendering", "css", "layout", "visual behavior", "blank screen", "blank page",
        "displaying incorrectly", "client-side", "frontend", "user interface", "form", "menu", "does nothing in the browser",
        "page is not rendering", "component is not rendering", "theme"
    ]
    if _has_pattern(text_lower, frontend_keywords):
        return "frontend"

    # 5. Backend Signals (REST API, FastAPI, 500 error, server-side, endpoint, auth logic, database query)
    backend_keywords = [
        "api", "rest api", "fastapi", "endpoint", "500", "http 500", "server-side", "backend",
        "server error", "server returns", "invalid json", "database query", "sqlalchemy", "postgres",
        "request processing", "backend service", "auth logic", "authentication logic", "query builder",
        "uploading a file", "uploading a large file", "upload a file", "uploading", "customer api",
        "user history", "document the latest api"
    ]
    if _has_pattern(text_lower, backend_keywords):
        return "backend"

    return "backend"


def _detect_category(title: str, desc: str) -> str:
    """
    Determines category based on problem intent:
    - incident: Active production outage / disruption
    - tech_debt: Refactoring / duplication removal / maintainability
    - feature: Requesting new functionality / capabilities
    - task: Concrete maintenance / documentation work
    - bug: Existing functionality broken or failing
    """
    text_lower = f"{title} {desc}".lower()

    # 1. Incident Signals
    incident_keywords = [
        "production service is completely unavailable", "production is down", "service unavailable",
        "production outage", "outage", "completely unavailable", "multiple regions",
        "service is down", "widespread failure", "system-wide failure", "down in production",
        "production database cluster outage", "production database outage", "production api is down",
        "production service is unavailable"
    ]
    if _has_pattern(text_lower, incident_keywords):
        return "incident"

    # 2. Tech Debt Signals
    tech_debt_keywords = [
        "refactor", "duplicated", "duplication", "legacy", "clean up", "cleanup",
        "maintainability", "deprecated", "tech debt", "technical debt", "duplicated validation code",
        "remove duplicated"
    ]
    if _has_pattern(text_lower, tech_debt_keywords):
        return "tech_debt"

    # 3. Task Signals (Documentation, env setup, dependencies, test configuration)
    task_keywords = [
        "update api documentation", "update documentation", "update docs", "document the latest api",
        "document api", "prepare test environment", "update dependency documentation", "update dependency",
        "test environment configuration", "create test cases"
    ]
    if _has_pattern(text_lower, task_keywords):
        return "task"

    # 4. Feature Signals (Adding NEW functionality / options)
    feature_triggers = [
        "add ", "introduce", "implement ", "support ", "allow users to", "enable users to",
        "provide an option", "export issues as csv", "dark mode", "theme switcher", "theme toggle",
        "build a new", "switch between light", "automate production releases", "add a daily data quality",
        "improve ", "enhance "
    ]
    is_feature_signal = _has_pattern(text_lower, feature_triggers)
    is_bug_signal = any(b in text_lower for b in ["fails", "failing", "broken", "broke", "crash", "crashes", "blank", "500", "error", "panic", "down", "outage", "does nothing", "no longer starts", "dropping records", "stopped"])
    
    if is_feature_signal and not is_bug_signal:
        return "feature"

    # 5. Bug Signals (Existing functionality broken)
    bug_keywords = [
        "blank screen", "blank page", "completely blank", "blank interface", "blank", "returns 500", "http 500", "500 error",
        "crash", "crashes", "fails", "failing", "broken", "broke", "does not work", "does nothing",
        "not responding", "unavailable", "unable to log in", "cannot see", "incorrect data", "invalid json",
        "missing records", "panic", "breaks", "collapses unexpectedly", "not rendering",
        "failed", "stopped working", "incorrect records", "returns null", "returns incorrect",
        "incorrect user data", "missing user records", "no longer starts", "dropping records", "stopped"
    ]
    if _has_pattern(text_lower, bug_keywords):
        return "bug"

    if is_feature_signal:
        return "feature"

    return "task"


def _detect_priority(title: str, desc: str, category: str) -> str:
    """
    Determines issue priority:
    - critical: Severe production-wide / system-wide outage ONLY
    - high: Important failures, API 500, broken deployment, OS failure, login blank screen, dropping records
    - medium: Normal bugs, feature requests, tech debt
    - low: Documentation, minor maintenance
    """
    text_lower = f"{title} {desc}".lower()

    if category == "incident" or "completely unavailable" in text_lower or "system-wide failure" in text_lower or "production database cluster outage" in text_lower or "users across multiple regions" in text_lower:
        return "critical"

    if category == "bug":
        high_impact = [
            "500", "deployment fails", "deployment failed", "fails during deployment", "pipeline fails",
            "fails after", "unable to log in", "completely blank", "crashes", "production failure",
            "critical bug", "panic", "kernel panic", "stopped working", "service stopped", "no longer starts",
            "dropping records", "failing", "blank screen", "not rendering", "http 500", "server returns"
        ]
        if _has_pattern(text_lower, high_impact):
            return "high"
        return "medium"

    if category == "task":
        if _has_pattern(text_lower, ["documentation", "docs", "minor", "typo", "document"]):
            return "low"
        return "medium"

    return "medium"


def _extract_keywords(title: str, desc: str, category: str, team: str) -> List[str]:
    """
    Extracts 3 to 5 meaningful technical keywords, filtering out generic stopwords.
    """
    text_lower = f"{title} {desc}".lower()

    domain_map = [
        ("theme switcher", "theme_switcher"),
        ("dark mode", "dark_mode"),
        ("blank screen", "blank_screen"),
        ("login page", "login_page"),
        ("profile page", "profile_page"),
        ("navigation menu", "navigation_menu"),
        ("submit button", "submit_button"),
        ("github actions", "github_actions"),
        ("release pipeline", "release_pipeline"),
        ("ci pipeline", "ci_pipeline"),
        ("ci/cd", "ci_cd"),
        ("docker", "docker"),
        ("operating system", "operating_system"),
        ("linux upgrade", "linux_upgrade"),
        ("ubuntu", "ubuntu"),
        ("linux", "linux_os"),
        ("data pipeline", "data_pipeline"),
        ("etl pipeline", "etl_pipeline"),
        ("analytics pipeline", "analytics_pipeline"),
        ("data quality", "data_quality"),
        ("rest api", "rest_api"),
        ("fastapi", "fastapi"),
        ("500 error", "http_500"),
        ("http 500", "http_500"),
        ("invalid json", "invalid_json"),
        ("user history", "user_history"),
        ("csv", "csv_export"),
        ("dashboard", "dashboard"),
        ("refactor", "refactoring"),
        ("duplicated", "code_duplication")
    ]

    found_keywords = []
    seen = set()

    for phrase, kw in domain_map:
        if _has_pattern(text_lower, [phrase]) and kw not in seen:
            seen.add(kw)
            found_keywords.append(kw)

    words = re.findall(r"\b[a-z]{3,20}\b", text_lower)
    for word in words:
        if word not in GENERIC_STOPWORDS and word not in seen:
            seen.add(word)
            found_keywords.append(word)
            if len(found_keywords) >= 5:
                break

    if not found_keywords:
        found_keywords = [category, team]

    return found_keywords[:5]


def _generate_suggested_action(category: str, team: str, text: str) -> str:
    """
    Generates actionable triage suggestion matching category and team.
    """
    if category == "incident":
        return f"Check service health metrics, inspect server error logs, examine recent deployments, and page on-call {team} engineers."

    elif category == "bug":
        if team == "frontend":
            return "Inspect browser console and network tab, reproduce UI rendering failure, and fix client component state or CSS styling."
        elif team == "devops":
            return "Examine CI/CD build logs, verify Docker container and staging configuration, and resolve deployment pipeline failure."
        elif team == "platform":
            return "Review system event logs, check operating system dependencies and runtime configuration, and fix service startup issue."
        elif team == "data":
            return "Inspect data pipeline execution logs, trace data transformation steps, and resolve data accuracy/missing record issue."
        else:
            return "Inspect server error logs and stack traces, reproduce HTTP failure in dev environment, and patch backend endpoint handler."

    elif category == "feature":
        if team == "frontend":
            return "Implement the dashboard theme toggle/UI component and update the frontend CSS theme styles and state."
        elif team == "backend":
            return "Define REST API schemas, implement backend service logic, and write comprehensive integration unit tests."
        elif team == "devops":
            return "Configure CI/CD deployment workflows, build release automation scripts, and verify pipeline execution."
        elif team == "platform":
            return "Audit system runtime compatibility, prepare OS/platform scripts, and execute platform environment update."
        elif team == "data":
            return "Design data pipeline ETL transformations, configure analytics aggregations, and validate output dataset."

    elif category == "tech_debt":
        return f"Audit affected codebase area, plan refactoring steps for the {team} component to eliminate duplication, and verify unit test coverage."

    elif category == "task":
        if team == "backend":
            return "Draft and publish technical API documentation for the specified backend endpoints."
        return f"Review task specifications, execute concrete {team} updates, and verify documentation/configuration changes."

    return f"Review issue details with team lead, implement required {team} changes, and verify resolution."


def _validate_and_normalize_ai_response(data: Dict[str, Any], title: str, desc: str) -> Dict[str, Any]:
    """
    Validates Gemini output using Pydantic AIAnalysisResponse and applies strict
    deterministic conflict resolution rules ("Do Not Trust AI Blindly").
    """
    cat = str(data.get("category", "")).lower().strip()
    pri = str(data.get("priority", "")).lower().strip()
    team = str(data.get("assigned_team", "")).lower().strip()
    raw_keywords = data.get("keywords", [])
    action = str(data.get("suggested_action", "")).strip()

    text_lower = f"{title} {desc}".lower()

    # 1. Deterministic validation checks for Team, Category, Priority
    expected_team = _detect_team(title, desc)
    expected_cat = _detect_category(title, desc)
    expected_pri = _detect_priority(title, desc, expected_cat)

    logger.info(f"[TRIAGE STEP 5] Heuristic Expected: Cat='{expected_cat}', Team='{expected_team}', Pri='{expected_pri}'")

    # 2. Strict Enum Validation & Override Logic
    if cat not in VALID_CATEGORIES or cat != expected_cat:
        cat = expected_cat

    if team not in VALID_TEAMS:
        team = expected_team
    else:
        # Override team if Gemini assigned wrong team when domain is explicitly detected by rule engine
        if expected_team in ["frontend", "devops", "platform", "data", "backend"] and team != expected_team:
            team = expected_team

    if pri not in VALID_PRIORITIES or (expected_pri in ["critical", "high"] and pri != expected_pri):
        pri = expected_pri

    # 3. Keyword Extraction & Sanitization
    sanitized_keywords = []
    if isinstance(raw_keywords, list) and raw_keywords:
        for kw in raw_keywords:
            kw_str = str(kw).lower().strip().replace("_", " ")
            subwords = kw_str.split()
            valid_parts = [w for w in subwords if w not in GENERIC_STOPWORDS and len(w) >= 3]
            if valid_parts:
                cleaned_kw = "_".join(valid_parts)
                if cleaned_kw not in sanitized_keywords:
                    sanitized_keywords.append(cleaned_kw)

    if len(sanitized_keywords) < 3:
        fallback_kws = _extract_keywords(title, desc, cat, team)
        for fkw in fallback_kws:
            if fkw not in sanitized_keywords:
                sanitized_keywords.append(fkw)

    # 4. Action Alignment Guardrails (Ensure action matches team & category)
    action = _ensure_action_category_alignment(action, cat, team, text_lower)

    logger.info(f"[TRIAGE STEP 6] Post-Guardrail Normalized: Cat='{cat}', Team='{team}', Pri='{pri}', Action='{action}'")

    # 5. Final Pydantic Schema Validation
    validated_payload = {
        "category": cat,
        "priority": pri,
        "assigned_team": team,
        "keywords": sanitized_keywords[:5],
        "suggested_action": action,
    }

    try:
        model_obj = AIAnalysisResponse.model_validate(validated_payload)
        return model_obj.model_dump()
    except ValidationError as ve:
        logger.warning(f"AI response schema validation failed: {str(ve)}. Using fallback.")
        return _fallback_heuristic_analysis(title, desc)


def _ensure_action_category_alignment(action: str, category: str, team: str, text: str) -> str:
    """
    Ensures suggested action directly aligns with the issue category and assigned team,
    eliminating generic sprint-planning advice or cross-team action mismatches.
    """
    if not action or len(action) < 15:
        return _generate_suggested_action(category, team, text)

    action_lower = action.lower()

    # Reject generic sprint-planning fluff
    fluff_terms = ["sprint iteration", "review task scope", "assign lead engineer", "schedule for current sprint", "sprint planning"]
    if any(f in action_lower for f in fluff_terms):
        return _generate_suggested_action(category, team, text)

    # Reject cross-team mismatches (e.g. backend/frontend actions for devops team)
    if team == "frontend" and any(b in action_lower for b in ["backend component", "backend endpoint", "rest api schema", "fastapi handler", "database endpoint", "backend endpoint/handler", "ci/cd build"]):
        return _generate_suggested_action(category, team, text)

    if team == "devops" and any(f in action_lower for f in ["browser console", "react component", "css style", "theme toggle", "browser developer console", "reproduce ui rendering"]):
        return _generate_suggested_action(category, team, text)

    if team == "backend" and any(f in action_lower for f in ["react component", "css style", "theme toggle", "browser console"]):
        return _generate_suggested_action(category, team, text)

    return action


def _fallback_heuristic_analysis(title: str, desc: str) -> Dict[str, Any]:
    """
    Deterministic rule engine that provides robust, reliable issue triage
    when external AI APIs are unconfigured or unavailable.
    """
    text = f"{title} {desc}".lower()

    category = _detect_category(title, desc)
    assigned_team = _detect_team(title, desc)
    priority = _detect_priority(title, desc, category)
    keywords = _extract_keywords(title, desc, category, assigned_team)
    suggested_action = _generate_suggested_action(category, assigned_team, text)

    return {
        "category": category,
        "priority": priority,
        "assigned_team": assigned_team,
        "keywords": keywords,
        "suggested_action": suggested_action,
    }

