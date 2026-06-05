"""
Tax God - Live Tier Testing Script
Tests all 4 user profiles against the running server at http://127.0.0.1:8000
"""

import requests

BASE = "http://127.0.0.1:8000/api/v1"

USERS = [
    {"email": "admin-test@taxgod.dev", "label": "ADMIN (pro/active)", "role": "admin",
     "chat_expected": 200, "admin_expected": 200},
    {"email": "pro-user@taxgod.dev", "label": "PRO (client/pro/active)", "role": "client",
     "chat_expected": 200, "admin_expected": 403},
    {"email": "trial-user@taxgod.dev", "label": "TRIAL (client/free_trial/trialing)", "role": "client",
     "chat_expected": 200, "admin_expected": 403},
    {"email": "expired-user@taxgod.dev", "label": "EXPIRED (client/free_trial/expired)", "role": "client",
     "chat_expected": 402, "admin_expected": 403},
]
PASSWORD = "TestPass123!"


def run_tests():
    results = {}
    for user in USERS:
        email = user["email"]
        label = user["label"]
        tests = []
        token = None
        original_name = None

        # 1. Login
        r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": PASSWORD})
        if r.status_code == 200 and "access_token" in r.json():
            token = r.json()["access_token"]
            tests.append(("POST /auth/login", "PASS", r.status_code))
        else:
            tests.append(("POST /auth/login", "FAIL", r.status_code))
            results[label] = tests
            continue

        headers = {"Authorization": f"Bearer {token}"}

        # 2. GET /auth/me
        r = requests.get(f"{BASE}/auth/me", headers=headers)
        if r.status_code == 200:
            data = r.json()
            role_ok = data.get("role") == user["role"]
            tests.append(("GET /auth/me", "PASS" if role_ok else f"FAIL(role={data.get('role')})", r.status_code))
            original_name = data.get("full_name")
        else:
            tests.append(("GET /auth/me", "FAIL", r.status_code))

        # 3. GET /clients
        r = requests.get(f"{BASE}/clients", headers=headers)
        tests.append(("GET /clients", "PASS" if r.status_code == 200 else "FAIL", r.status_code))

        # 4. POST /clients
        r = requests.post(f"{BASE}/clients", headers=headers,
                          json={"name": "Test Client from Tier Script", "email": "test@example.com"})
        tests.append(("POST /clients", "PASS" if r.status_code == 201 else "FAIL", r.status_code))

        # 5. GET /businesses
        r = requests.get(f"{BASE}/businesses", headers=headers)
        tests.append(("GET /businesses", "PASS" if r.status_code == 200 else "FAIL", r.status_code))

        # 6. GET /invoices
        r = requests.get(f"{BASE}/invoices", headers=headers)
        tests.append(("GET /invoices", "PASS" if r.status_code == 200 else "FAIL", r.status_code))

        # 7. GET /expenses
        r = requests.get(f"{BASE}/expenses", headers=headers)
        tests.append(("GET /expenses", "PASS" if r.status_code == 200 else "FAIL", r.status_code))

        # 8. POST /chat/query
        r = requests.post(f"{BASE}/chat/query", headers=headers, json={"query": "What is IRC 199A?"})
        expected = user["chat_expected"]
        if r.status_code == expected:
            tests.append(("POST /chat/query", "PASS", r.status_code))
        else:
            tests.append(("POST /chat/query", f"FAIL(expected {expected})", r.status_code))

        # 9. GET /analytics/governance/circuit-breaker
        r = requests.get(f"{BASE}/analytics/governance/circuit-breaker", headers=headers)
        expected = user["admin_expected"]
        if r.status_code == expected:
            tests.append(("GET /analytics/governance/circuit-breaker", "PASS", r.status_code))
        else:
            tests.append(("GET /analytics/governance/circuit-breaker", f"FAIL(expected {expected})", r.status_code))

        # 10. PATCH /profile
        r = requests.patch(f"{BASE}/profile", headers=headers, json={"full_name": "Updated Name"})
        if r.status_code == 200 and r.json().get("full_name") == "Updated Name":
            tests.append(("PATCH /profile (update)", "PASS", r.status_code))
        else:
            tests.append(("PATCH /profile (update)", "FAIL", r.status_code))

        # 11. Revert name
        r = requests.patch(f"{BASE}/profile", headers=headers, json={"full_name": original_name or ""})
        if r.status_code == 200:
            tests.append(("PATCH /profile (revert)", "PASS", r.status_code))
        else:
            tests.append(("PATCH /profile (revert)", "FAIL", r.status_code))

        results[label] = tests

    # Print report
    print("\n" + "=" * 70)
    print("TAX GOD - LIVE TIER TEST REPORT")
    print("=" * 70)
    total_pass = 0
    total_fail = 0
    for label, tests in results.items():
        print(f"\n{'─' * 70}")
        print(f"  {label}")
        print(f"{'─' * 70}")
        for name, status, code in tests:
            icon = "✅" if status == "PASS" else "❌"
            print(f"  {icon} {name:<45} {status:<20} [{code}]")
            if status == "PASS":
                total_pass += 1
            else:
                total_fail += 1

    print(f"\n{'=' * 70}")
    print(f"  TOTAL: {total_pass} PASSED, {total_fail} FAILED")
    print(f"{'=' * 70}\n")
    return total_fail == 0


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
