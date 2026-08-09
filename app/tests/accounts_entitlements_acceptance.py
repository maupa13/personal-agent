from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE_APP = ROOT / "services" / "core" / "app"
sys.path.insert(0, str(CORE_APP))

from entitlement_service import EntitlementService  # noqa: E402
from server_database import validate_server_database_config  # noqa: E402


def check(value: bool, test_id: str, message: str) -> None:
    if not value:
        raise AssertionError(f"{test_id}: {message}")
    print(f"[PASS] {test_id} - {message}")


def main() -> int:
    tmp_root = ROOT / "release-evidence" / "_tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp = tmp_root / "accounts-entitlements"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        db = tmp / "alpha2.db"
        ent = EntitlementService(db)
        ent.init_schema()
        light = ent.for_plan("LIGHT")
        medium = ent.for_plan("MEDIUM")
        pro = ent.for_plan("PRO")
        check(light["chat"]["enabled"] and light["web"]["enabled"], "PLAN-001", "Light keeps useful chat/web baseline")
        check(not light["code"]["enabled"] and not light["mode_smart"]["enabled"], "PLAN-003", "Light does not expose paid smart/code capabilities")
        check(medium["code"]["enabled"] and medium["research"]["enabled"], "PLAN-001-MEDIUM", "Medium enables research/code")
        check(pro["deep_research"]["enabled"] and pro["priority_queue"]["enabled"], "PLAN-001-PRO", "Pro carries advanced entitlements")
        ent.update("LIGHT", "code", enabled=True)
        check(ent.for_plan("LIGHT")["code"]["enabled"], "PLAN-ADMIN-001", "Admin entitlement override persists in DB")
        reopened = EntitlementService(db); reopened.init_schema()
        check(reopened.for_plan("LIGHT")["code"]["enabled"], "PLAN-PERSIST-001", "Entitlement override survives process recreation")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    old = os.environ.get("PA_DATABASE_URL")
    try:
        os.environ["PA_DATABASE_URL"] = "postgresql://user:secret@db.internal:5432/personal_agent"
        target = validate_server_database_config()
        check(target["kind"] == "postgresql" and target["host"] == "db.internal" and "secret" not in json.dumps(target), "PG-FOUNDATION-001", "PostgreSQL config is recognized without leaking credentials")
    finally:
        if old is None: os.environ.pop("PA_DATABASE_URL", None)
        else: os.environ["PA_DATABASE_URL"] = old

    compose = (ROOT / "deploy/server/compose.postgres-foundation.yaml").read_text(encoding="utf-8")
    migration = (ROOT / "migrations/postgres/0001_productization_foundation.sql").read_text(encoding="utf-8")
    check("postgres:18.4-bookworm" in compose and "par-server-postgres" in compose, "PG-FOUNDATION-002", "Server foundation pins PostgreSQL major/minor profile and named volume")
    check(all(token in migration for token in ("CREATE TABLE IF NOT EXISTS users", "CREATE TABLE IF NOT EXISTS conversations", "CREATE TABLE IF NOT EXISTS plan_entitlements", "idx_conversations_user_updated")), "PG-FOUNDATION-003", "PostgreSQL migration contains identity, conversation and entitlement indexes")

    main_py = (CORE_APP / "main.py").read_text(encoding="utf-8")
    ui_js = (CORE_APP / "static/app.js").read_text(encoding="utf-8")
    auth_js = (CORE_APP / "static/auth.js").read_text(encoding="utf-8")
    admin_js = (CORE_APP / "static/admin.js").read_text(encoding="utf-8")
    lan_ps = (ROOT / "scripts/lan.ps1").read_text(encoding="utf-8")
    check("require_entitlement(user, \"research\")" in main_py and "ENTITLEMENTS.mode_allowed" in main_py, "PLAN-001-BACKEND", "Backend enforces capability and mode entitlements")
    check("mode_${mode.id}" in ui_js and "entitlementEnabled" in ui_js, "PLAN-002", "USER mode selector derives from effective entitlements")
    check("/api/auth/sessions" in auth_js and "revoke-all" in auth_js, "AUTH-005", "Account UI manages device sessions")
    check("remember_me" in main_py and "auth_login_attempts" in main_py and "argon2" in main_py, "AUTH-006", "Auth includes remember-me, persisted throttling and Argon2 migration")
    check("/api/admin/auth/registration-policy" in admin_js and "revoke-sessions" in admin_js, "ADMIN-002", "Admin UI controls registration and sessions")
    check("PA_LAN_PUBLIC_URL" in lan_ps and "PA_LAN_ENABLED" in lan_ps, "LAN-001", "LAN lifecycle persists product-visible state")
    check("/api/admin/lan/qr.svg" in main_py and "lanQr" in admin_js, "LAN-002", "Admin exposes LAN address and QR contract")

    print("PAR_V080_ALPHA2_ACCOUNTS_ENTITLEMENTS_ACCEPTANCE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
