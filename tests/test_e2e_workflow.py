"""End-to-end workflow test for Tax God Super Agent Co-Pilot (live server)."""

import time
import sys
import requests

BASE = "http://127.0.0.1:8000"
EMAIL = f"e2e-{int(time.time())}@test.taxgod.dev"
PASSWORD = "TestPass123!"
failures: list[str] = []
token: str = ""
user_id: str = ""
business_id: str = ""
client_id: str = ""
invoice_id: str = ""
account_id_1: str = ""
account_id_2: str = ""


def step(name: str, method: str, path: str, expected: int, json_body=None, params=None):
    """Execute a step, print status, return response json or None."""
    global failures
    url = f"{BASE}{path}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.request(method, url, json=json_body, params=params, headers=headers, timeout=15)
        if r.status_code == expected:
            print(f"  ✅ {name} [{r.status_code}]")
            return r.json() if r.content else {}
        else:
            detail = r.text[:200]
            print(f"  ❌ {name} — expected {expected}, got {r.status_code}: {detail}")
            failures.append(f"{name}: expected {expected}, got {r.status_code}")
            return r.json() if r.content and r.headers.get("content-type", "").startswith("application/json") else None
    except Exception as e:
        print(f"  ❌ {name} — exception: {e}")
        failures.append(f"{name}: {e}")
        return None


def main():
    global token, user_id, business_id, client_id, invoice_id, account_id_1, account_id_2

    print(f"\n{'='*60}")
    print("  Tax God E2E Workflow Test")
    print(f"  Server: {BASE}")
    print(f"  User:   {EMAIL}")
    print(f"{'='*60}\n")

    # 1. Register
    print("[1] Register new user")
    data = step("Register", "POST", "/api/v1/auth/register", 201,
                json_body={"email": EMAIL, "password": PASSWORD, "full_name": "E2E Test User"})
    if data:
        user_id = data.get("id", "")

    # 2. Login
    print("[2] Login")
    data = step("Login", "POST", "/api/v1/auth/login", 200,
                json_body={"email": EMAIL, "password": PASSWORD})
    if data:
        token = data.get("access_token", "")

    if not token:
        print("\n⛔ Cannot continue without auth token. Aborting.")
        sys.exit(1)

    # 3. Create business
    print("[3] Create business")
    data = step("Create business", "POST", "/api/v1/businesses", 201,
                json_body={"name": "E2E Test Corp", "business_type": "llc", "ein": "12-3456789"})
    if data:
        business_id = data.get("id", "")

    # 4. Create client
    print("[4] Create client")
    data = step("Create client", "POST", "/api/v1/clients", 201,
                json_body={"name": "Acme Inc", "email": "acme@example.com", "company": "Acme Corp"})
    if data:
        client_id = data.get("id", "")

    # 5. Create invoice
    print("[5] Create invoice")
    data = step("Create invoice", "POST", "/api/v1/invoices", 201,
                json_body={
                    "client_id": client_id,
                    "invoice_number": f"INV-E2E-{int(time.time())}",
                    "amount": 5000.00,
                    "status": "sent",
                    "due_date": "2026-07-01T00:00:00Z",
                })
    if data:
        invoice_id = data.get("id", "")

    # 6. Create expense
    print("[6] Create expense")
    step("Create expense", "POST", "/api/v1/expenses", 201,
         json_body={
             "date": "2026-06-01T00:00:00Z",
             "vendor": "Office Depot",
             "amount": 250.00,
             "category": "office",
             "tax_deductible": True,
         })

    # 7. Quarterly estimate
    print("[7] Check quarterly estimate")
    data = step("Quarterly estimate", "GET", "/api/v1/estimates/quarterly", 200)
    if data:
        print(f"       → income={data.get('income')}, expenses={data.get('expenses')}")

    # 8. Trial balance
    print("[8] Check trial balance")
    data = step("Trial balance", "GET", "/api/v1/ledger/trial-balance", 200)
    if data:
        print(f"       → balanced={data.get('balanced')}, accounts={len(data.get('accounts', []))}")

    # 9. Create chart accounts + journal entry
    print("[9] Create chart accounts + journal entry")
    data = step("Create asset account", "POST", "/api/v1/ledger/accounts", 201,
                json_body={"code": "1000", "name": "Cash", "account_type": "asset"})
    if data:
        account_id_1 = data.get("id", "")

    data = step("Create revenue account", "POST", "/api/v1/ledger/accounts", 201,
                json_body={"code": "4000", "name": "Service Revenue", "account_type": "revenue"})
    if data:
        account_id_2 = data.get("id", "")

    if account_id_1 and account_id_2:
        step("Create journal entry", "POST", "/api/v1/ledger/journal", 201,
             json_body={
                 "date": "2026-06-05T00:00:00Z",
                 "description": "E2E test revenue",
                 "lines": [
                     {"account_id": account_id_1, "debit": 1000.0, "credit": 0.0},
                     {"account_id": account_id_2, "debit": 0.0, "credit": 1000.0},
                 ],
             })
    else:
        print("  ⚠️  Skipping journal entry (missing account IDs)")
        failures.append("Journal entry: skipped due to missing accounts")

    # 10. Generate document
    print("[10] Generate document")
    step("Generate client_welcome doc", "POST", "/api/v1/documents/generate", 200,
         json_body={"doc_type": "client_welcome", "client_id": client_id})

    # 11. Tax planning projection
    print("[11] Tax planning projection")
    data = step("Tax projection", "GET", "/api/v1/tax-planning/projection", 200)
    if data:
        print(f"       → ytd_income={data.get('ytd_income')}, ytd_expenses={data.get('ytd_expenses')}")

    # 12. Summary
    print(f"\n{'='*60}")
    if not failures:
        print("  🎉 ALL STEPS PASSED")
    else:
        print(f"  ⚠️  {len(failures)} FAILURE(S):")
        for f in failures:
            print(f"     • {f}")
    print(f"{'='*60}\n")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
