"""Seed the database with well-known test credentials and sample companies.

- Runs on every container start.
- If SEED_RESET=1 is set in the environment (testing mode), existing rows are
  wiped first so every test run begins from a clean, predictable state.
- In normal mode (no SEED_RESET) rows are only inserted if they do not already
  exist, so re-starting the container is safe.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from repo root: `python scripts/seed_test_data.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cdm_reflex_portal.database import Company, SessionLocal, User, hash_password, init_db

# ── Initialise schema ─────────────────────────────────────────────────────────
init_db()

RESET = os.environ.get("SEED_RESET", "0") == "1"

# ── Test accounts ─────────────────────────────────────────────────────────────
# Testers log in with these credentials.  Passwords are intentionally simple
# for testing but still pass the minimum-6-character validation.
TEST_USERS = [
    {"username": "admin",  "password": "Admin@123",  "role": "ADMIN"},
    {"username": "editor", "password": "Editor@123", "role": "EDITOR"},
    {"username": "viewer", "password": "Viewer@123", "role": "VIEWER"},
]

# ── Sample companies ──────────────────────────────────────────────────────────
TEST_COMPANIES = [
    {
        "cin": "U74999MH2021PTC111001",
        "name": "Acme Solutions Pvt. Ltd.",
        "company_class": "PRIVATE",
        "company_type": "Company limited by Shares",
        "sub_category": "Non-government company",
        "date_of_incorporation": "15/01/2021",
        "email": "contact@acme.example.com",
        "address": "101 MG Road, Pune, Maharashtra 411001",
    },
    {
        "cin": "L65910KA2020PLC222002",
        "name": "Zenith Finance Ltd.",
        "company_class": "PUBLIC",
        "company_type": "Company limited by Shares",
        "sub_category": "Non-government company",
        "date_of_incorporation": "01/06/2020",
        "email": "info@zenith.example.com",
        "address": "55 Brigade Road, Bengaluru, Karnataka 560001",
    },
    {
        "cin": "U72900DL2019OPC333003",
        "name": "Delta Tech OPC Pvt. Ltd.",
        "company_class": "PRIVATE",
        "company_type": "Company limited by Shares",
        "sub_category": "Non-government company",
        "date_of_incorporation": "20/03/2019",
        "email": "",
        "address": "Plot 7, Sector 18, Noida, Uttar Pradesh 201301",
    },
]

with SessionLocal() as session:
    if RESET:
        print("[seed] SEED_RESET=1 — wiping existing rows...")
        session.query(Company).delete()
        session.query(User).delete()
        session.commit()

    for u in TEST_USERS:
        if not session.query(User).filter(User.username == u["username"]).first():
            session.add(
                User(
                    username=u["username"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                )
            )
            print(f"  [seed] Created user    : {u['username']} / {u['password']}  ({u['role']})")
        else:
            print(f"  [seed] User exists     : {u['username']}")

    for c in TEST_COMPANIES:
        if not session.query(Company).filter(Company.cin == c["cin"]).first():
            session.add(
                Company(
                    cin=c["cin"],
                    name=c["name"],
                    company_class=c["company_class"],
                    company_type=c["company_type"],
                    sub_category=c["sub_category"],
                    date_of_incorporation=c.get("date_of_incorporation") or None,
                    email=c.get("email") or None,
                    address=c.get("address") or None,
                )
            )
            print(f"  [seed] Created company : {c['name']}")
        else:
            print(f"  [seed] Company exists  : {c['name']}")

    session.commit()

print("[seed] Done.")
