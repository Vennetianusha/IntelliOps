import requests
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.cache.client import redis_client

url = "http://localhost:8000/api/v1/issues/analyze"

try:
    redis_client.delete_pattern("ai:triage:*")
    print("[CACHE] Flushed Redis AI triage cache keys")
except Exception as e:
    print(f"[CACHE] Flush skipped: {e}")

test_cases = [
    ("TEST 1", "Add dark mode to the dashboard", "", "feature", "frontend", ["medium"]),
    ("TEST 2", "Login page is completely blank", "Users cannot see the login interface after opening the application in the browser.", "bug", "frontend", ["medium", "high"]),
    ("TEST 3", "Release pipeline fails during deployment", "The CI pipeline completes the build but fails when deploying the application to staging.", "bug", "devops", ["high"]),
    ("TEST 4", "Customer API returns HTTP 500", "The REST API returns an HTTP 500 error when creating a customer.", "bug", "backend", ["high"]),
]

print("=" * 75)
print("VERIFYING ALL 4 MANDATORY TESTS VIA LIVE HTTP API (port 8000)")
print("=" * 75)

for code, title, desc, exp_cat, exp_team, exp_pri_list in test_cases:
    payload = {"title": title, "description": desc}
    
    # 1. First HTTP call
    res1 = requests.post(url, json=payload).json()
    
    # 2. Second HTTP call (Redis HIT)
    res2 = requests.post(url, json=payload).json()

    cat_ok = res1.get("category") == exp_cat
    team_ok = res1.get("assigned_team") == exp_team
    pri_ok = res1.get("priority") in exp_pri_list
    hit_ok = res1 == res2

    status = "[PASS]" if (cat_ok and team_ok and pri_ok and hit_ok) else "[FAIL]"

    print(f"\n{code} ({status})")
    print(f"  Title           : '{title}'")
    print(f"  Description     : '{desc}'")
    print(f"  Expected        : Cat='{exp_cat}', Team='{exp_team}', Priority={exp_pri_list}")
    print(f"  HTTP Response 1 : Cat='{res1.get('category')}', Team='{res1.get('assigned_team')}', Priority='{res1.get('priority')}'")
    print(f"  Suggested Action: {res1.get('suggested_action')}")
    print(f"  Redis HIT Match : {hit_ok}")

print("\n" + "=" * 75)
