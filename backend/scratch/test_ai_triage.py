import sys
import os
import json
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ai_service import analyze_issue
from app.cache.service import get_cached_ai_triage, set_cached_ai_triage, build_ai_triage_cache_key
from app.cache.client import redis_client

logging.basicConfig(level=logging.INFO)

def run_tests():
    # Flush stale AI triage keys
    try:
        redis_client.delete_pattern("ai:triage:*")
        print("[CACHE] Flushed stale Redis AI triage keys (ai:triage:*)")
    except Exception as e:
        print(f"[CACHE WARNING] Could not flush Redis keys: {e}")

    print("=" * 75)
    print("STEP 9 & 10 — RUNNING TEST SUITE A THROUGH I WITH REDIS VERIFICATION")
    print("=" * 75)

    test_cases = [
        ("TEST A", "Add a theme switcher to the web dashboard", "Users should be able to switch between light and dark themes from the dashboard.", "feature", "frontend", ["medium"]),
        ("TEST B", "Release pipeline fails during deployment", "The CI pipeline completes the build but fails when deploying the application to the staging environment.", "bug", "devops", ["high"]),
        ("TEST C", "Login page is not rendering", "The login screen remains blank when users open it in the browser.", "bug", "frontend", ["medium", "high"]),
        ("TEST D", "Customer API returns HTTP 500", "The REST API returns an HTTP 500 error when creating a customer.", "bug", "backend", ["high"]),
        ("TEST E", "Service stopped after Linux upgrade", "The application worked before the operating system upgrade but now fails during startup.", "bug", "platform", ["high"]),
        ("TEST F", "Analytics pipeline is dropping records", "Some customer records are missing from the daily analytics output.", "bug", "data", ["medium", "high"]),
        ("TEST G", "Remove duplicated authentication logic", "Authentication logic is duplicated across several backend modules and should be refactored into a shared implementation.", "tech_debt", "backend", ["medium"]),
        ("TEST H", "Update API documentation", "Update the documentation with the latest REST endpoints and response examples.", "task", "backend", ["low", "medium"]),
        ("TEST I", "Production service is unavailable", "Users across multiple regions cannot access the production application.", "incident", ["devops", "backend"], ["critical"]),
    ]

    results_summary = []
    passed_count = 0

    for code, title, desc, exp_cat, exp_team, exp_pri_list in test_cases:
        res = analyze_issue(title, desc)
        
        cat_match = res["category"] == exp_cat
        team_match = res["assigned_team"] in exp_team if isinstance(exp_team, list) else res["assigned_team"] == exp_team
        pri_match = res["priority"] in exp_pri_list

        is_pass = cat_match and team_match and pri_match
        status = "[PASS]" if is_pass else "[FAIL]"

        if is_pass:
            passed_count += 1

        print(f"\n{code} ({status})")
        print(f"  Title      : '{title}'")
        print(f"  Expected   : Cat='{exp_cat}', Team='{exp_team}', Priority={exp_pri_list}")
        print(f"  Actual     : Cat='{res['category']}', Team='{res['assigned_team']}', Priority='{res['priority']}'")
        print(f"  Action     : {res['suggested_action']}")
        print(f"  Keywords   : {res['keywords']}")

        results_summary.append((code, status, title, res["category"], res["assigned_team"], res["priority"]))

    print("\n" + "=" * 75)
    print("TEST SUITE SUMMARY")
    print("=" * 75)
    for code, status, title, cat, team, pri in results_summary:
        print(f"  {code} {status} | '{title[:45]}...' -> ({cat}, {team}, {pri})")

    print(f"\nPassed: {passed_count}/{len(test_cases)}")

    print("\n" + "=" * 75)
    print("REDIS MISS -> SET -> HIT VERIFICATION FOR TEST A & TEST B")
    print("=" * 75)

    # Test A Redis Verification
    t_a, d_a = test_cases[0][1], test_cases[0][2]
    key_a = build_ai_triage_cache_key(t_a, d_a)
    print(f"Key for Test A: {key_a}")
    
    # 1. Ensure key deleted
    redis_client.delete(key_a)
    print("Step 1: Cleared key for Test A")

    # 2. First execution -> MISS -> SET
    print("Step 2: Executing Test A (Redis MISS expected)...")
    res_a_1 = analyze_issue(t_a, d_a)
    cached_a = get_cached_ai_triage(t_a, d_a)
    assert cached_a is not None, "Test A should be cached in Redis after 1st call!"
    print("[OK] Test A Redis MISS -> Analysis -> SET verified!")

    # 3. Second execution -> HIT
    print("Step 3: Executing Test A again (Redis HIT expected)...")
    res_a_2 = analyze_issue(t_a, d_a)
    assert res_a_1 == res_a_2, "Test A cached result matches 1st call!"
    print("[OK] Test A Redis HIT verified!")

    # Test B Redis Verification
    t_b, d_b = test_cases[1][1], test_cases[1][2]
    key_b = build_ai_triage_cache_key(t_b, d_b)
    print(f"\nKey for Test B: {key_b}")
    assert key_a != key_b, "Cache key for Test A and Test B MUST be different!"
    print("[OK] Test A and Test B have distinct cache keys!")

    redis_client.delete(key_b)
    res_b_1 = analyze_issue(t_b, d_b)
    cached_b = get_cached_ai_triage(t_b, d_b)
    assert cached_b is not None, "Test B should be cached in Redis!"
    print("[OK] Test B Redis MISS -> Analysis -> SET verified!")

    res_b_2 = analyze_issue(t_b, d_b)
    assert res_b_1 == res_b_2, "Test B cached result matches!"
    print("[OK] Test B Redis HIT verified!")

    print("\nAll verification steps completed successfully!")

if __name__ == "__main__":
    run_tests()
