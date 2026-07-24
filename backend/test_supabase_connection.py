"""
STEP 6 — Standalone Supabase connection test
Run from project root: .venv/Scripts/python backend/test_supabase_connection.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# ── 1. Load .env ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

url = os.getenv("SUPABASE_URL", "").strip()
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

# ── 2. Print diagnostics (never print full key) ────────────────────────────────
print(f"SUPABASE_URL       : {url or 'MISSING'}")
print(f"SERVICE_ROLE_KEY   : {'KEY LOADED — first 6 chars: ' + key[:6] if key else 'KEY MISSING'}")

if not url or not key:
    print("\n--- DIAGNOSIS: .env is missing or variables are empty.")
    print("    Fix: ensure backend/.env exists with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    raise SystemExit(1)

# ── 3. Create client ──────────────────────────────────────────────────────────
try:
    client = create_client(url, key)
    print("\n[OK]  Supabase client created successfully.")
except Exception as exc:
    print(f"\n[FAIL]  Supabase client creation FAILED: {exc}")
    raise SystemExit(1)

# ── 4. Test insert ────────────────────────────────────────────────────────────
TEST_RECORD = {
    "customer_name": "TEST_USER",
    "phone": "0000000000",
    "service_type": "agriculture",
    "customize_details": {
        "machineName": "Test Tractor",
        "weight": "500kg",
        "color": "Red",
        "comment": "Test insert",
        "customerName": "TEST_USER",
        "phone": "0000000000"
    },
    "status": "pending",
}

print("\nAttempting test insert into 'orders' table...")
try:
    response = client.table("orders").insert(TEST_RECORD).execute()
    rows = response.data or []
    if rows:
        print(f"\n[OK]  INSERT SUCCEEDED! Row returned:\n{json.dumps(rows[0], indent=2, default=str)}")
        # Clean up the test row
        inserted_id = rows[0].get("id")
        if inserted_id:
            client.table("orders").delete().eq("id", inserted_id).execute()
            print(f"\n[OK]  Test row (id={inserted_id}) deleted from Supabase.")
    else:
        print("\n[WARN]  Insert executed but no row returned — check RLS policies.")
except Exception as exc:
    print(f"\n[FAIL]  INSERT FAILED: {type(exc).__name__}: {exc}")
    raise SystemExit(1)
