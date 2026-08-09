from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from db_compat import connect_app_db


DEFAULT_ENTITLEMENTS: dict[str, dict[str, tuple[bool, int | None]]] = {
    "LIGHT": {
        "chat": (True, None),
        "mode_auto": (True, None),
        "mode_fast": (True, None),
        "mode_smart": (False, None),
        "web": (True, None),
        "research": (False, None),
        "deep_research": (False, None),
        "files_read": (True, None),
        "files_create": (False, None),
        "code": (False, None),
        "long_tasks": (False, None),
        "remote_ai": (False, None),
        "priority_queue": (False, None),
        "advanced_exports": (False, None),
        "automation": (False, None),
        "media": (False, None),
        "max_concurrent_tasks": (True, 1),
        "storage_quota_mb": (True, 512),
        "max_file_size_mb": (True, 20),
    },
    "MEDIUM": {
        "chat": (True, None),
        "mode_auto": (True, None),
        "mode_fast": (True, None),
        "mode_smart": (True, None),
        "web": (True, None),
        "research": (True, None),
        "deep_research": (False, None),
        "files_read": (True, None),
        "files_create": (True, None),
        "code": (True, None),
        "long_tasks": (True, None),
        "remote_ai": (True, None),
        "priority_queue": (False, None),
        "advanced_exports": (True, None),
        "automation": (False, None),
        "media": (False, None),
        "max_concurrent_tasks": (True, 3),
        "storage_quota_mb": (True, 2048),
        "max_file_size_mb": (True, 50),
    },
    "PRO": {
        "chat": (True, None),
        "mode_auto": (True, None),
        "mode_fast": (True, None),
        "mode_smart": (True, None),
        "web": (True, None),
        "research": (True, None),
        "deep_research": (True, None),
        "files_read": (True, None),
        "files_create": (True, None),
        "code": (True, None),
        "long_tasks": (True, None),
        "remote_ai": (True, None),
        "priority_queue": (True, None),
        "advanced_exports": (True, None),
        "automation": (False, None),
        "media": (False, None),
        "max_concurrent_tasks": (True, 6),
        "storage_quota_mb": (True, 8192),
        "max_file_size_mb": (True, 100),
    },
}

MODE_FEATURE = {"auto": "mode_auto", "fast": "mode_fast", "smart": "mode_smart"}


class EntitlementError(Exception):
    pass


class EntitlementService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.lock = threading.RLock()

    def db(self) -> Any:
        return connect_app_db(self.db_path)

    def init_schema(self) -> None:
        with self.lock, self.db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS plan_entitlements (
                  plan_id TEXT NOT NULL,
                  feature_key TEXT NOT NULL,
                  enabled INTEGER NOT NULL DEFAULT 0,
                  limit_value INTEGER,
                  updated_at INTEGER NOT NULL,
                  PRIMARY KEY(plan_id, feature_key)
                );
                CREATE INDEX IF NOT EXISTS idx_plan_entitlements_plan ON plan_entitlements(plan_id);
                """
            )
            ts = int(time.time())
            for plan_id, features in DEFAULT_ENTITLEMENTS.items():
                for key, (enabled, limit_value) in features.items():
                    conn.execute(
                        "INSERT OR IGNORE INTO plan_entitlements(plan_id,feature_key,enabled,limit_value,updated_at) VALUES(?,?,?,?,?)",
                        (plan_id, key, int(enabled), limit_value, ts),
                    )
            conn.commit()

    def for_plan(self, plan_id: str) -> dict[str, Any]:
        plan_id = str(plan_id).upper()
        with self.lock, self.db() as conn:
            rows = conn.execute(
                "SELECT feature_key,enabled,limit_value FROM plan_entitlements WHERE plan_id=? ORDER BY feature_key",
                (plan_id,),
            ).fetchall()
        return {
            str(row["feature_key"]): {
                "enabled": bool(int(row["enabled"])),
                "limit": None if row["limit_value"] is None else int(row["limit_value"]),
            }
            for row in rows
        }

    def effective(self, *, plan_id: str, privileged: bool = False, personal: bool = False) -> dict[str, Any]:
        if privileged or personal:
            keys = sorted({key for plan in DEFAULT_ENTITLEMENTS.values() for key in plan})
            result = {key: {"enabled": True, "limit": None} for key in keys}
            result["max_concurrent_tasks"]["limit"] = 20
            result["storage_quota_mb"]["limit"] = None
            result["max_file_size_mb"]["limit"] = None
            return result
        return self.for_plan(plan_id)

    def update(self, plan_id: str, feature_key: str, *, enabled: bool, limit_value: int | None = None) -> dict[str, Any]:
        plan_id = str(plan_id).upper()
        feature_key = str(feature_key).strip().lower()
        if plan_id not in DEFAULT_ENTITLEMENTS:
            raise EntitlementError("unknown plan")
        allowed = {key for features in DEFAULT_ENTITLEMENTS.values() for key in features}
        if feature_key not in allowed:
            raise EntitlementError("unknown entitlement")
        if limit_value is not None and (int(limit_value) < 0 or int(limit_value) > 10_000_000_000):
            raise EntitlementError("invalid entitlement limit")
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO plan_entitlements(plan_id,feature_key,enabled,limit_value,updated_at) VALUES(?,?,?,?,?) "
                "ON CONFLICT(plan_id,feature_key) DO UPDATE SET enabled=excluded.enabled,limit_value=excluded.limit_value,updated_at=excluded.updated_at",
                (plan_id, feature_key, int(bool(enabled)), limit_value, int(time.time())),
            )
            conn.commit()
        return {"plan_id": plan_id, "feature_key": feature_key, "enabled": bool(enabled), "limit": limit_value}

    @staticmethod
    def allowed(entitlements: dict[str, Any], feature_key: str) -> bool:
        item = entitlements.get(feature_key) or {}
        return bool(item.get("enabled"))

    @staticmethod
    def mode_allowed(entitlements: dict[str, Any], mode: str) -> bool:
        feature = MODE_FEATURE.get(str(mode).lower())
        return bool(feature and EntitlementService.allowed(entitlements, feature))
