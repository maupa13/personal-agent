from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from db_compat import connect_app_db

PLAN_PRICES_RUB = {"LIGHT": 0, "MEDIUM": 500, "PRO": 1000}
PLAN_NAMES = {"LIGHT": "Лайт", "MEDIUM": "Медиум", "PRO": "Про"}
PLAN_SUPPORT = {"LIGHT": "community", "MEDIUM": "standard", "PRO": "priority"}
BILLING_CLASSES = {"LOCAL", "BYOK", "PLATFORM_REMOTE", "PRIVATE_REMOTE"}
SUBSCRIPTION_STATES = {"TRIAL", "ACTIVE", "PAST_DUE", "GRACE_PERIOD", "CANCEL_AT_PERIOD_END", "CANCELLED", "EXPIRED"}
PAYMENT_STATES = {"CREATED", "PENDING", "PAID", "FAILED", "CANCELLED", "REFUNDED", "PARTIALLY_REFUNDED"}
TOPUP_REQUEST_STATES = {"PENDING", "REVIEW_REQUIRED", "APPROVED", "REJECTED"}
THEME_CATALOG = {
    "ocean": {"name": "Голубая", "price_rub": 99},
    "forest": {"name": "Светло-зелёная", "price_rub": 99},
    "sunset": {"name": "Закат", "price_rub": 149},
    "sand": {"name": "Песок", "price_rub": 149},
    "coral": {"name": "Коралл", "price_rub": 149},
}


def now_ts() -> int:
    return int(time.time())


def month_window(ts: int | None = None) -> tuple[int, int]:
    """UTC calendar month; deterministic and good enough for the local foundation."""
    import datetime as _dt
    dt = _dt.datetime.fromtimestamp(ts or now_ts(), tz=_dt.timezone.utc)
    start = _dt.datetime(dt.year, dt.month, 1, tzinfo=_dt.timezone.utc)
    if dt.month == 12:
        end = _dt.datetime(dt.year + 1, 1, 1, tzinfo=_dt.timezone.utc)
    else:
        end = _dt.datetime(dt.year, dt.month + 1, 1, tzinfo=_dt.timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


@dataclass(frozen=True)
class InferenceUsage:
    input_tokens: int
    output_tokens: int
    exact: bool

    @property
    def total_tokens(self) -> int:
        return max(0, self.input_tokens) + max(0, self.output_tokens)


class BillingError(Exception):
    pass


class PaymentConfigurationError(BillingError):
    pass


class BillingService:
    def __init__(self, db_path: Path, secrets_dir: Path, *, test_mode: bool = False) -> None:
        self.db_path = Path(db_path)
        self.secrets_dir = Path(secrets_dir)
        self.test_mode = bool(test_mode)
        self.lock = threading.RLock()
        self.payment_api_base = os.getenv("PA_PAYMENT_API_BASE", "https://api.yookassa.ru/v3").rstrip("/")

    def db(self) -> Any:
        return connect_app_db(self.db_path)

    def init_schema(self) -> None:
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.secrets_dir, 0o700)
        except OSError:
            pass
        with self.lock, self.db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS plans (
                  id TEXT PRIMARY KEY,
                  display_name TEXT NOT NULL,
                  price_rub INTEGER NOT NULL,
                  support_level TEXT NOT NULL,
                  local_unlimited INTEGER NOT NULL DEFAULT 1,
                  remote_token_limit INTEGER NOT NULL DEFAULT 0,
                  remote_cost_limit_microrub INTEGER NOT NULL DEFAULT 0,
                  enabled INTEGER NOT NULL DEFAULT 1,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS subscriptions (
                  user_id TEXT PRIMARY KEY,
                  plan_id TEXT NOT NULL,
                  status TEXT NOT NULL,
                  period_start INTEGER NOT NULL,
                  period_end INTEGER NOT NULL,
                  auto_renew INTEGER NOT NULL DEFAULT 0,
                  payment_provider TEXT,
                  payment_method_id TEXT,
                  cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS usage_events (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  provider_id TEXT NOT NULL,
                  model_id TEXT NOT NULL,
                  billing_class TEXT NOT NULL,
                  source TEXT NOT NULL,
                  input_tokens INTEGER NOT NULL,
                  output_tokens INTEGER NOT NULL,
                  total_tokens INTEGER NOT NULL,
                  exact INTEGER NOT NULL,
                  estimated_cost_microrub INTEGER NOT NULL DEFAULT 0,
                  created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_usage_user_time ON usage_events(user_id,created_at);
                CREATE INDEX IF NOT EXISTS idx_usage_provider_time ON usage_events(provider_id,created_at);
                CREATE TABLE IF NOT EXISTS billing_preferences (
                  user_id TEXT PRIMARY KEY,
                  show_token_usage INTEGER NOT NULL DEFAULT 0,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS payments (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  plan_id TEXT NOT NULL,
                  amount_rub INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  provider TEXT NOT NULL,
                  provider_payment_id TEXT UNIQUE,
                  idempotency_key TEXT UNIQUE NOT NULL,
                  confirmation_url TEXT,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL,
                  raw_status TEXT
                );
                CREATE TABLE IF NOT EXISTS payment_events (
                  id TEXT PRIMARY KEY,
                  provider TEXT NOT NULL,
                  provider_event_key TEXT NOT NULL,
                  payload_hash TEXT NOT NULL,
                  processed_at INTEGER NOT NULL,
                  UNIQUE(provider,provider_event_key)
                );
                CREATE TABLE IF NOT EXISTS billing_settings (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS user_balances (
                  user_id TEXT PRIMARY KEY,
                  balance_microrub INTEGER NOT NULL DEFAULT 0,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS balance_ledger (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  delta_microrub INTEGER NOT NULL,
                  source TEXT NOT NULL,
                  source_ref TEXT,
                  note TEXT,
                  actor_user_id TEXT,
                  meta_json TEXT NOT NULL DEFAULT '{}',
                  created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_balance_ledger_user_time ON balance_ledger(user_id,created_at DESC);
                CREATE TABLE IF NOT EXISTS promo_codes (
                  id TEXT PRIMARY KEY,
                  code TEXT UNIQUE NOT NULL,
                  kind TEXT NOT NULL DEFAULT 'general',
                  amount_microrub INTEGER NOT NULL,
                  uses_total INTEGER NOT NULL,
                  uses_remaining INTEGER NOT NULL,
                  active INTEGER NOT NULL DEFAULT 1,
                  description TEXT NOT NULL DEFAULT '',
                  created_by_user_id TEXT,
                  expires_at INTEGER,
                  email_sent INTEGER NOT NULL DEFAULT 0,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS promo_redemptions (
                  id TEXT PRIMARY KEY,
                  promo_code_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  amount_microrub INTEGER NOT NULL,
                  redeemed_at INTEGER NOT NULL,
                  meta_json TEXT NOT NULL DEFAULT '{}',
                  UNIQUE(promo_code_id,user_id)
                );
                CREATE INDEX IF NOT EXISTS idx_promo_redemptions_user_time ON promo_redemptions(user_id,redeemed_at DESC);
                CREATE TABLE IF NOT EXISTS topup_requests (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  source TEXT NOT NULL,
                  amount_microrub INTEGER NOT NULL,
                  payment_reference TEXT,
                  note TEXT,
                  status TEXT NOT NULL,
                  requires_second_approval INTEGER NOT NULL DEFAULT 0,
                  reviewer_user_id TEXT,
                  second_reviewer_user_id TEXT,
                  reconciled_by_user_id TEXT,
                  reconciled_at INTEGER,
                  reconciliation_note TEXT,
                  review_note TEXT,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_topup_requests_status_time ON topup_requests(status,created_at DESC);
                CREATE TABLE IF NOT EXISTS user_theme_entitlements (
                  user_id TEXT NOT NULL,
                  theme_id TEXT NOT NULL,
                  source TEXT NOT NULL,
                  ledger_entry_id TEXT,
                  purchased_at INTEGER NOT NULL,
                  PRIMARY KEY(user_id, theme_id)
                );
                CREATE INDEX IF NOT EXISTS idx_user_theme_entitlements_user ON user_theme_entitlements(user_id, purchased_at DESC);
                """
            )
            ts = now_ts()
            for plan_id in ("LIGHT", "MEDIUM", "PRO"):
                # Safe-by-default: platform-funded remote AI is disabled until an admin sets a budget.
                conn.execute(
                    "INSERT INTO plans(id,display_name,price_rub,support_level,local_unlimited,remote_token_limit,remote_cost_limit_microrub,enabled,updated_at) "
                    "VALUES(?,?,?,?,TRUE,0,0,TRUE,?) ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name,price_rub=excluded.price_rub,support_level=excluded.support_level,local_unlimited=TRUE",
                    (plan_id, PLAN_NAMES[plan_id], PLAN_PRICES_RUB[plan_id], PLAN_SUPPORT[plan_id], ts),
                )
            conn.commit()

    @staticmethod
    def _rub_to_microrub(value: float | int) -> int:
        return int(round(float(value) * 1_000_000))

    @staticmethod
    def _microrub_to_rub(value: int | None) -> float:
        return round(int(value or 0) / 1_000_000, 6)

    @staticmethod
    def _clean_note(value: str, *, limit: int = 300) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())[:limit]

    @staticmethod
    def _clean_code(value: str) -> str:
        return re.sub(r"[^A-Z0-9-]", "", str(value or "").upper())[:40]

    def _setting(self, key: str, default: str = "") -> str:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT value FROM billing_settings WHERE key=?", (key,)).fetchone()
            return str(row["value"]) if row else default

    def _set_setting(self, key: str, value: str) -> None:
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO billing_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                (key, value, now_ts()),
            )
            conn.commit()

    def balance(self, user_id: str) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT balance_microrub,updated_at FROM user_balances WHERE user_id=?", (user_id,)).fetchone()
            sources = conn.execute(
                "SELECT source,COUNT(*) count,SUM(delta_microrub) net_microrub FROM balance_ledger WHERE user_id=? GROUP BY source ORDER BY ABS(SUM(delta_microrub)) DESC, source",
                (user_id,),
            ).fetchall()
        return {
            "user_id": user_id,
            "balance_rub": self._microrub_to_rub(row["balance_microrub"]) if row else 0.0,
            "updated_at": int(row["updated_at"]) if row else 0,
            "sources": [
                {"source": str(item["source"]), "count": int(item["count"] or 0), "net_rub": self._microrub_to_rub(item["net_microrub"])}
                for item in sources
            ],
        }

    def _write_balance_entry(
        self,
        conn: sqlite3.Connection,
        *,
        user_id: str,
        delta_microrub: int,
        source: str,
        source_ref: str = "",
        note: str = "",
        actor_user_id: str = "",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ts = now_ts()
        row = conn.execute("SELECT balance_microrub FROM user_balances WHERE user_id=?", (user_id,)).fetchone()
        current = int(row["balance_microrub"] or 0) if row else 0
        updated = current + int(delta_microrub)
        if updated < 0:
            raise BillingError("balance cannot become negative")
        ledger_id = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO balance_ledger(id,user_id,delta_microrub,source,source_ref,note,actor_user_id,meta_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                ledger_id,
                user_id,
                int(delta_microrub),
                str(source).strip().lower()[:40],
                str(source_ref or "").strip()[:160] or None,
                self._clean_note(note),
                str(actor_user_id or "").strip()[:64] or None,
                json.dumps(meta or {}, ensure_ascii=False),
                ts,
            ),
        )
        conn.execute(
            "INSERT INTO user_balances(user_id,balance_microrub,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET balance_microrub=excluded.balance_microrub,updated_at=excluded.updated_at",
            (user_id, updated, ts),
        )
        return {"user_id": user_id, "balance_rub": self._microrub_to_rub(updated), "updated_at": ts, "ledger_entry_id": ledger_id}

    def adjust_balance(self, *, user_id: str, delta_rub: float, reason: str, actor_user_id: str, source: str = "admin_manual") -> dict[str, Any]:
        delta_microrub = self._rub_to_microrub(delta_rub)
        if delta_microrub == 0:
            raise BillingError("balance change cannot be zero")
        with self.lock, self.db() as conn:
            result = self._write_balance_entry(
                conn,
                user_id=user_id,
                delta_microrub=delta_microrub,
                source=source,
                note=reason,
                actor_user_id=actor_user_id,
                meta={"kind": "admin_adjustment"},
            )
            conn.commit()
        return result

    def create_topup_request(self, *, user_id: str, amount_rub: float, payment_reference: str, note: str, source: str = "yoomoney") -> dict[str, Any]:
        amount_microrub = self._rub_to_microrub(amount_rub)
        if amount_microrub <= 0:
            raise BillingError("top-up amount must be positive")
        request_id = uuid.uuid4().hex
        ts = now_ts()
        clean_ref = self._clean_note(payment_reference, limit=160)
        clean_note = self._clean_note(note)
        requires_second_approval = amount_microrub >= self._rub_to_microrub(3000)
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO topup_requests(id,user_id,source,amount_microrub,payment_reference,note,status,requires_second_approval,created_at,updated_at) VALUES(?,?,?,?,?,?, 'PENDING', ?,?,?)",
                (request_id, user_id, str(source).strip().lower()[:40], amount_microrub, clean_ref or None, clean_note or None, int(requires_second_approval), ts, ts),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
        assert row is not None
        return self._topup_row(dict(row))

    def create_promo_code(
        self,
        *,
        amount_rub: float,
        uses_total: int,
        created_by_user_id: str,
        kind: str = "general",
        description: str = "",
        code: str = "",
        expires_at: int | None = None,
        send_to_email: str = "",
    ) -> dict[str, Any]:
        amount_microrub = self._rub_to_microrub(amount_rub)
        if amount_microrub <= 0:
            raise BillingError("promo amount must be positive")
        uses_total = int(uses_total)
        if uses_total < 1 or uses_total > 100000:
            raise BillingError("invalid promo uses_total")
        normalized_code = self._clean_code(code) or f"PA-{secrets.token_hex(3).upper()}"
        kind = re.sub(r"[^a-z0-9_-]", "", str(kind).strip().lower())[:32] or "general"
        ts = now_ts()
        with self.lock, self.db() as conn:
            try:
                conn.execute(
                    "INSERT INTO promo_codes(id,code,kind,amount_microrub,uses_total,uses_remaining,active,description,created_by_user_id,expires_at,email_sent,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        normalized_code,
                        kind,
                        amount_microrub,
                        uses_total,
                        uses_total,
                        1,
                        self._clean_note(description, limit=200),
                        created_by_user_id or None,
                        int(expires_at) if expires_at else None,
                        0,
                        ts,
                        ts,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise BillingError("promo code already exists") from exc
            conn.commit()
            row = conn.execute("SELECT * FROM promo_codes WHERE code=?", (normalized_code,)).fetchone()
        assert row is not None
        result = self._promo_row(dict(row))
        result["email_sent"] = False
        result["send_to_email"] = send_to_email
        return result

    def redeem_promo_code(self, *, user_id: str, code: str) -> dict[str, Any]:
        normalized_code = self._clean_code(code)
        if not normalized_code:
            raise BillingError("promo code is required")
        ts = now_ts()
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM promo_codes WHERE code=?", (normalized_code,)).fetchone()
            if not row:
                raise BillingError("promo code not found")
            promo = dict(row)
            if not bool(int(promo["active"])):
                raise BillingError("promo code is disabled")
            if int(promo["uses_remaining"] or 0) <= 0:
                raise BillingError("promo code is exhausted")
            if promo["expires_at"] is not None and int(promo["expires_at"]) <= ts:
                raise BillingError("promo code expired")
            duplicate = conn.execute("SELECT 1 FROM promo_redemptions WHERE promo_code_id=? AND user_id=?", (promo["id"], user_id)).fetchone()
            if duplicate:
                raise BillingError("promo code already redeemed")
            conn.execute(
                "INSERT INTO promo_redemptions(id,promo_code_id,user_id,amount_microrub,redeemed_at,meta_json) VALUES(?,?,?,?,?,?)",
                (uuid.uuid4().hex, promo["id"], user_id, int(promo["amount_microrub"]), ts, json.dumps({"code": normalized_code}, ensure_ascii=False)),
            )
            conn.execute(
                "UPDATE promo_codes SET uses_remaining=uses_remaining-1,updated_at=? WHERE id=? AND uses_remaining>0",
                (ts, promo["id"]),
            )
            balance = self._write_balance_entry(
                conn,
                user_id=user_id,
                delta_microrub=int(promo["amount_microrub"]),
                source="promo",
                source_ref=normalized_code,
                note=f"promo {normalized_code}",
                actor_user_id=str(promo.get("created_by_user_id") or ""),
                meta={"promo_code_id": promo["id"], "code": normalized_code, "kind": promo["kind"]},
            )
            conn.commit()
        return {"balance": balance, "code": normalized_code, "amount_rub": self._microrub_to_rub(promo["amount_microrub"])}

    @staticmethod
    def _topup_row(item: dict[str, Any]) -> dict[str, Any]:
        item["amount_rub"] = int(item.pop("amount_microrub", 0) or 0) / 1_000_000
        item["requires_second_approval"] = bool(int(item.get("requires_second_approval") or 0))
        return item

    @staticmethod
    def _promo_row(item: dict[str, Any]) -> dict[str, Any]:
        item["amount_rub"] = int(item.pop("amount_microrub", 0) or 0) / 1_000_000
        item["active"] = bool(int(item.get("active") or 0))
        return item

    def _topup_with_user(self, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        item = dict(row)
        item["amount_rub"] = self._microrub_to_rub(item.pop("amount_microrub", 0))
        item["requires_second_approval"] = bool(int(item.get("requires_second_approval") or 0))
        return item

    def reconcile_topup_request(self, *, request_id: str, reviewer_user_id: str, review_note: str = "") -> dict[str, Any]:
        ts = now_ts()
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
            if not row:
                raise BillingError("top-up request not found")
            item = dict(row)
            if item["status"] not in {"PENDING", "REVIEW_REQUIRED"}:
                raise BillingError("top-up request is already closed")
            requires_second = bool(int(item["requires_second_approval"] or 0))
            note = self._clean_note(review_note)
            if requires_second and item["status"] == "PENDING":
                conn.execute(
                    "UPDATE topup_requests SET status='REVIEW_REQUIRED',reviewer_user_id=?,review_note=?,updated_at=? WHERE id=?",
                    (reviewer_user_id, note or None, ts, request_id),
                )
                conn.commit()
                updated = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
                assert updated is not None
                return self._topup_row(dict(updated))
            if item.get("reviewer_user_id") and str(item["reviewer_user_id"]) == reviewer_user_id:
                raise BillingError("a different administrator must complete this review")
            self._write_balance_entry(
                conn,
                user_id=str(item["user_id"]),
                delta_microrub=int(item["amount_microrub"]),
                source="topup_request",
                source_ref=str(item.get("payment_reference") or request_id),
                note=note or str(item.get("note") or ""),
                actor_user_id=reviewer_user_id,
                meta={"topup_request_id": request_id, "source": item.get("source")},
            )
            conn.execute(
                "UPDATE topup_requests SET status='APPROVED',second_reviewer_user_id=COALESCE(second_reviewer_user_id, ?),reconciled_by_user_id=?,reconciled_at=?,reconciliation_note=?,review_note=COALESCE(review_note, ?),updated_at=? WHERE id=?",
                (reviewer_user_id if requires_second else None, reviewer_user_id, ts, note or None, note or None, ts, request_id),
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
        assert updated is not None
        return self._topup_row(dict(updated))

    def reject_topup_request(self, *, request_id: str, reviewer_user_id: str, review_note: str = "") -> dict[str, Any]:
        ts = now_ts()
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
            if not row:
                raise BillingError("top-up request not found")
            item = dict(row)
            if item["status"] not in {"PENDING", "REVIEW_REQUIRED"}:
                raise BillingError("top-up request is already closed")
            conn.execute(
                "UPDATE topup_requests SET status='REJECTED',reconciled_by_user_id=?,reconciled_at=?,review_note=?,updated_at=? WHERE id=?",
                (reviewer_user_id, ts, self._clean_note(review_note) or None, ts, request_id),
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
        assert updated is not None
        return self._topup_row(dict(updated))

    def user_billing_summary(self, user_id: str) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            payment = conn.execute(
                "SELECT COUNT(*) payments_total,SUM(CASE WHEN status='PAID' THEN 1 ELSE 0 END) payments_paid,SUM(CASE WHEN status='PAID' THEN amount_rub ELSE 0 END) payments_paid_rub,MAX(CASE WHEN status='PAID' THEN updated_at END) last_payment_at FROM payments WHERE user_id=?",
                (user_id,),
            ).fetchone()
            promo = conn.execute(
                "SELECT COUNT(*) promo_redemptions_total,SUM(amount_microrub) promo_redemptions_total_microrub,MAX(redeemed_at) last_promo_redeemed_at FROM promo_redemptions WHERE user_id=?",
                (user_id,),
            ).fetchone()
            topup = conn.execute(
                "SELECT COUNT(*) topup_requests_total,SUM(CASE WHEN status='APPROVED' THEN 1 ELSE 0 END) topup_requests_approved,MAX(created_at) last_topup_request_at FROM topup_requests WHERE user_id=?",
                (user_id,),
            ).fetchone()
            sources = conn.execute(
                "SELECT source,COUNT(*) count,SUM(delta_microrub) net_microrub FROM balance_ledger WHERE user_id=? GROUP BY source ORDER BY ABS(SUM(delta_microrub)) DESC, source LIMIT 6",
                (user_id,),
            ).fetchall()
        return {
            "payments_total": int(payment["payments_total"] or 0),
            "payments_paid": int(payment["payments_paid"] or 0),
            "payments_paid_rub": float(payment["payments_paid_rub"] or 0),
            "last_payment_at": int(payment["last_payment_at"] or 0) if payment["last_payment_at"] else None,
            "promo_redemptions_total": int(promo["promo_redemptions_total"] or 0),
            "promo_redemptions_rub": self._microrub_to_rub(promo["promo_redemptions_total_microrub"]),
            "last_promo_redeemed_at": int(promo["last_promo_redeemed_at"] or 0) if promo["last_promo_redeemed_at"] else None,
            "topup_requests_total": int(topup["topup_requests_total"] or 0),
            "topup_requests_approved": int(topup["topup_requests_approved"] or 0),
            "last_topup_request_at": int(topup["last_topup_request_at"] or 0) if topup["last_topup_request_at"] else None,
            "balance_sources": [
                {"source": str(item["source"]), "count": int(item["count"] or 0), "net_rub": self._microrub_to_rub(item["net_microrub"])}
                for item in sources
            ],
        }

    @staticmethod
    def _balance_from_connection(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
        row = conn.execute("SELECT balance_microrub,updated_at FROM user_balances WHERE user_id=?", (user_id,)).fetchone()
        value = int(row["balance_microrub"] or 0) if row else 0
        return {"user_id": user_id, "balance_rub": value / 1_000_000, "updated_at": int(row["updated_at"] or 0) if row else 0}

    def owned_themes(self, user_id: str) -> set[str]:
        with self.lock, self.db() as conn:
            rows = conn.execute("SELECT theme_id FROM user_theme_entitlements WHERE user_id=?", (user_id,)).fetchall()
        return {str(row["theme_id"]) for row in rows}

    def theme_catalog(self, user_id: str) -> list[dict[str, Any]]:
        owned = self.owned_themes(user_id)
        return [{"id": theme_id, **details, "owned": theme_id in owned} for theme_id, details in THEME_CATALOG.items()]

    def purchase_theme(self, *, user_id: str, theme_id: str) -> dict[str, Any]:
        theme_id = str(theme_id or "").strip().lower()
        item = THEME_CATALOG.get(theme_id)
        if not item:
            raise BillingError("unknown theme")
        price_microrub = self._rub_to_microrub(item["price_rub"])
        with self.lock, self.db() as conn:
            existing = conn.execute("SELECT theme_id FROM user_theme_entitlements WHERE user_id=? AND theme_id=?", (user_id, theme_id)).fetchone()
            if existing:
                return {"theme": theme_id, **item, "owned": True, "already_owned": True, "balance": self._balance_from_connection(conn, user_id)}
            balance = conn.execute("SELECT balance_microrub FROM user_balances WHERE user_id=?", (user_id,)).fetchone()
            current = int(balance["balance_microrub"] or 0) if balance else 0
            if current < price_microrub:
                raise BillingError("insufficient balance for theme")
            ledger = self._write_balance_entry(
                conn, user_id=user_id, delta_microrub=-price_microrub, source="theme_purchase",
                source_ref=theme_id, note=f"Покупка темы {theme_id}",
                meta={"kind": "theme_purchase", "theme_id": theme_id},
            )
            conn.execute(
                "INSERT INTO user_theme_entitlements(user_id,theme_id,source,ledger_entry_id,purchased_at) VALUES(?,?,?,?,?)",
                (user_id, theme_id, "balance", ledger["ledger_entry_id"], now_ts()),
            )
            conn.commit()
            return {"theme": theme_id, **item, "owned": True, "already_owned": False, "balance": self._balance_from_connection(conn, user_id)}

    def _payment_secret_path(self) -> Path:
        return self.secrets_dir / "payment-yookassa.secret"

    def _write_payment_secret(self, value: str) -> None:
        path = self._payment_secret_path()
        if not value:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            return
        tmp = path.with_suffix(".tmp")
        tmp.write_text(value, encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(path)

    def _read_payment_secret(self) -> str:
        try:
            return self._payment_secret_path().read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""

    def payment_config(self) -> dict[str, Any]:
        provider = self._setting("payment_provider", "disabled")
        shop_id = self._setting("yookassa_shop_id", "")
        public_base_url = self._setting("public_base_url", "")
        has_secret = bool(self._read_payment_secret())
        configured = provider == "yookassa" and bool(shop_id and public_base_url and has_secret)
        with self.lock, self.db() as conn:
            webhook_seen = bool(conn.execute("SELECT 1 FROM payment_events WHERE provider='yookassa' LIMIT 1").fetchone())
            paid_seen = bool(conn.execute("SELECT 1 FROM payments WHERE provider='yookassa' AND status='PAID' LIMIT 1").fetchone())
        webhook_path = "/api/billing/webhook/yookassa"
        return {
            "provider": provider,
            "shop_id": shop_id,
            "public_base_url": public_base_url,
            "has_secret": has_secret,
            "configured": configured,
            "webhook_path": webhook_path,
            "webhook_url": (public_base_url + webhook_path) if public_base_url else "",
            "setup": {
                "shop_id": bool(shop_id), "secret": has_secret,
                "public_https": bool(public_base_url.startswith("https://")),
                "webhook_seen": webhook_seen, "paid_payment_seen": paid_seen,
                "production_ready": bool(configured and webhook_seen and paid_seen),
            },
        }

    def configure_yookassa(self, *, shop_id: str, secret_key: str | None, public_base_url: str) -> dict[str, Any]:
        shop_id = str(shop_id).strip()
        public_base_url = str(public_base_url).strip().rstrip("/")
        if not shop_id or len(shop_id) > 80:
            raise BillingError("YooKassa shop_id is required")
        parsed = urllib.parse.urlparse(public_base_url)
        if parsed.scheme not in ({"http", "https"} if self.test_mode else {"https"}) or not parsed.netloc:
            raise BillingError("public base URL must be HTTPS")
        if parsed.username or parsed.password:
            raise BillingError("public base URL must not contain credentials")
        if secret_key is not None and secret_key != "":
            self._write_payment_secret(str(secret_key).strip())
        if not self._read_payment_secret():
            raise BillingError("YooKassa secret key is required")
        self._set_setting("payment_provider", "yookassa")
        self._set_setting("yookassa_shop_id", shop_id)
        self._set_setting("public_base_url", public_base_url)
        return self.payment_config()

    def disable_payment_provider(self) -> None:
        self._set_setting("payment_provider", "disabled")

    def plans(self) -> list[dict[str, Any]]:
        with self.lock, self.db() as conn:
            rows = conn.execute("SELECT * FROM plans ORDER BY price_rub,id").fetchall()
        return [self._plan_row(row) for row in rows]

    @staticmethod
    def _plan_row(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        get = row.__getitem__
        return {
            "id": str(get("id")),
            "display_name": str(get("display_name")),
            "price_rub": int(get("price_rub")),
            "support_level": str(get("support_level")),
            "local_unlimited": bool(int(get("local_unlimited"))),
            "remote_token_limit": int(get("remote_token_limit")),
            "remote_cost_limit_rub": int(get("remote_cost_limit_microrub")) / 1_000_000,
            "enabled": bool(int(get("enabled"))),
        }

    def update_plan_limits(self, plan_id: str, *, remote_token_limit: int, remote_cost_limit_rub: float) -> dict[str, Any]:
        plan_id = str(plan_id).upper()
        if plan_id not in PLAN_PRICES_RUB:
            raise BillingError("unknown plan")
        if remote_token_limit < 0 or remote_token_limit > 10_000_000_000:
            raise BillingError("invalid remote token limit")
        cost_microrub = int(round(float(remote_cost_limit_rub) * 1_000_000))
        if cost_microrub < 0 or cost_microrub > 10_000_000 * 1_000_000:
            raise BillingError("invalid remote cost limit")
        with self.lock, self.db() as conn:
            conn.execute("UPDATE plans SET remote_token_limit=?,remote_cost_limit_microrub=?,updated_at=? WHERE id=?", (remote_token_limit, cost_microrub, now_ts(), plan_id))
            conn.commit()
            row = conn.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
        assert row is not None
        return self._plan_row(row)

    def ensure_subscription(self, user_id: str, *, role: str = "USER") -> dict[str, Any]:
        user_id = str(user_id)
        if user_id == "local-owner" or str(role).upper() == "ADMIN":
            start, end = month_window()
            return {
                "user_id": user_id,
                "plan_id": "ADMIN",
                "status": "ACTIVE",
                "period_start": start,
                "period_end": end,
                "auto_renew": False,
                "payment_provider": None,
                "cancel_at_period_end": False,
                "billing_exempt": True,
            }
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM subscriptions WHERE user_id=?", (user_id,)).fetchone()
            if not row:
                start, end = month_window()
                conn.execute(
                    "INSERT INTO subscriptions(user_id,plan_id,status,period_start,period_end,auto_renew,payment_provider,payment_method_id,cancel_at_period_end,updated_at) VALUES(?,?, 'ACTIVE',?,?,0,NULL,NULL,0,?)",
                    (user_id, "LIGHT", start, end, now_ts()),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM subscriptions WHERE user_id=?", (user_id,)).fetchone()
        assert row is not None
        return {k: row[k] for k in row.keys()} | {"billing_exempt": False}

    def assign_plan(self, user_id: str, plan_id: str, *, auto_renew: bool = False, provider: str | None = None, payment_method_id: str | None = None) -> dict[str, Any]:
        plan_id = str(plan_id).upper()
        if plan_id not in PLAN_PRICES_RUB:
            raise BillingError("unknown plan")
        start = now_ts()
        end = start + 30 * 24 * 60 * 60
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO subscriptions(user_id,plan_id,status,period_start,period_end,auto_renew,payment_provider,payment_method_id,cancel_at_period_end,updated_at) "
                "VALUES(?,?, 'ACTIVE',?,?,?,?,?,0,?) ON CONFLICT(user_id) DO UPDATE SET plan_id=excluded.plan_id,status='ACTIVE',period_start=excluded.period_start,period_end=excluded.period_end,auto_renew=excluded.auto_renew,payment_provider=excluded.payment_provider,payment_method_id=COALESCE(excluded.payment_method_id,subscriptions.payment_method_id),cancel_at_period_end=0,updated_at=excluded.updated_at",
                (user_id, plan_id, start, end, int(bool(auto_renew)), provider, payment_method_id, now_ts()),
            )
            conn.commit()
        return self.ensure_subscription(user_id)

    def preference(self, user_id: str) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT show_token_usage FROM billing_preferences WHERE user_id=?", (user_id,)).fetchone()
        return {"show_token_usage": bool(int(row["show_token_usage"])) if row else False}

    def set_preference(self, user_id: str, *, show_token_usage: bool) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO billing_preferences(user_id,show_token_usage,updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET show_token_usage=excluded.show_token_usage,updated_at=excluded.updated_at",
                (user_id, int(bool(show_token_usage)), now_ts()),
            )
            conn.commit()
        return self.preference(user_id)

    def usage_summary(self, user_id: str, *, period_start: int | None = None, period_end: int | None = None) -> dict[str, Any]:
        start, end = (period_start, period_end) if period_start is not None and period_end is not None else month_window()
        with self.lock, self.db() as conn:
            rows = conn.execute(
                "SELECT billing_class,SUM(input_tokens) input_tokens,SUM(output_tokens) output_tokens,SUM(total_tokens) total_tokens,SUM(estimated_cost_microrub) cost FROM usage_events WHERE user_id=? AND created_at>=? AND created_at<? GROUP BY billing_class",
                (user_id, int(start), int(end)),
            ).fetchall()
        by_class: dict[str, Any] = {}
        total = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "estimated_cost_rub": 0.0}
        for row in rows:
            item = {
                "input_tokens": int(row["input_tokens"] or 0),
                "output_tokens": int(row["output_tokens"] or 0),
                "total_tokens": int(row["total_tokens"] or 0),
                "estimated_cost_rub": int(row["cost"] or 0) / 1_000_000,
            }
            by_class[str(row["billing_class"])] = item
            for key in ("input_tokens", "output_tokens", "total_tokens"):
                total[key] += int(item[key])
            total["estimated_cost_rub"] += float(item["estimated_cost_rub"])
        total["estimated_cost_rub"] = round(total["estimated_cost_rub"], 6)
        return {"period_start": int(start), "period_end": int(end), "by_class": by_class, "total": total}

    def snapshot(self, user: dict[str, Any]) -> dict[str, Any]:
        sub = self.ensure_subscription(str(user["id"]), role=str(user.get("role", "USER")))
        usage = self.usage_summary(str(user["id"]), period_start=int(sub["period_start"]), period_end=int(sub["period_end"]))
        pref = self.preference(str(user["id"]))
        balance = self.balance(str(user["id"]))
        summary = self.user_billing_summary(str(user["id"]))
        with self.lock, self.db() as conn:
            topup_rows = conn.execute("SELECT * FROM topup_requests WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (str(user["id"]),)).fetchall()
        if sub["plan_id"] == "ADMIN":
            plan = {
                "id": "ADMIN", "display_name": "Администратор", "price_rub": 0, "support_level": "owner",
                "local_unlimited": True, "remote_token_limit": None, "remote_cost_limit_rub": None, "enabled": True,
            }
        else:
            with self.lock, self.db() as conn:
                row = conn.execute("SELECT * FROM plans WHERE id=?", (sub["plan_id"],)).fetchone()
            if not row:
                raise BillingError("subscription plan missing")
            plan = self._plan_row(row)
        remote = usage["by_class"].get("PLATFORM_REMOTE", {"total_tokens": 0, "estimated_cost_rub": 0.0})
        token_limit = plan.get("remote_token_limit")
        cost_limit = plan.get("remote_cost_limit_rub")
        return {
            "plan": plan,
            "subscription": {
                "plan_id": sub.get("plan_id"), "status": sub.get("status"), "period_start": sub.get("period_start"), "period_end": sub.get("period_end"),
                "auto_renew": bool(sub.get("auto_renew")), "payment_provider": sub.get("payment_provider"),
                "cancel_at_period_end": bool(sub.get("cancel_at_period_end")), "billing_exempt": bool(sub.get("billing_exempt")),
            },
            "usage": usage,
            "balance": balance,
            "billing_summary": summary,
            "quota": {
                "platform_remote_tokens_used": int(remote.get("total_tokens", 0)),
                "platform_remote_tokens_limit": token_limit,
                "platform_remote_tokens_remaining": None if token_limit is None else max(0, int(token_limit) - int(remote.get("total_tokens", 0))),
                "platform_remote_cost_rub_used": float(remote.get("estimated_cost_rub", 0.0)),
                "platform_remote_cost_rub_limit": cost_limit,
                "platform_remote_cost_rub_remaining": None if cost_limit is None else max(0.0, round(float(cost_limit) - float(remote.get("estimated_cost_rub", 0.0)), 6)),
            },
            "preferences": pref,
            "payment": {"configured": self.payment_config()["configured"], "provider": self.payment_config()["provider"]},
            "topup_requests": [self._topup_row(dict(row)) for row in topup_rows],
            "themes": self.theme_catalog(str(user["id"])),
            "owned_themes": sorted(self.owned_themes(str(user["id"]))),
        }

    def route_allowed(self, user: dict[str, Any], provider: dict[str, Any]) -> tuple[bool, str | None]:
        billing_class = str(provider.get("billing_class") or "BYOK").upper()
        if billing_class not in BILLING_CLASSES:
            billing_class = "BYOK"
        if billing_class != "PLATFORM_REMOTE":
            return True, None
        snap = self.snapshot(user)
        if snap["subscription"].get("billing_exempt"):
            return True, None
        token_remaining = snap["quota"]["platform_remote_tokens_remaining"]
        cost_remaining = snap["quota"]["platform_remote_cost_rub_remaining"]
        if token_remaining is not None and token_remaining <= 0:
            return False, "remote_token_quota_exhausted"
        if cost_remaining is not None and cost_remaining <= 0:
            return False, "remote_cost_quota_exhausted"
        return True, None

    @staticmethod
    def estimate_usage(messages: list[dict[str, str]], output: str) -> InferenceUsage:
        # Fallback only. Provider-native counters remain authoritative when available.
        input_chars = sum(len(str(item.get("content", ""))) for item in messages)
        return InferenceUsage(max(1, (input_chars + 3) // 4), max(1, (len(output) + 3) // 4), False)

    @staticmethod
    def estimated_cost_microrub(provider: dict[str, Any], usage: InferenceUsage) -> int:
        input_per_m = float(provider.get("cost_input_per_million_rub") or 0.0)
        output_per_m = float(provider.get("cost_output_per_million_rub") or 0.0)
        rub = (usage.input_tokens / 1_000_000) * input_per_m + (usage.output_tokens / 1_000_000) * output_per_m
        return max(0, int(round(rub * 1_000_000)))

    def record_usage(self, *, user_id: str, provider: dict[str, Any], model_id: str, usage: InferenceUsage, source: str = "chat") -> dict[str, Any]:
        billing_class = str(provider.get("billing_class") or "BYOK").upper()
        if billing_class not in BILLING_CLASSES:
            billing_class = "BYOK"
        cost = self.estimated_cost_microrub(provider, usage)
        item = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "provider_id": str(provider.get("id") or "unknown"),
            "model_id": model_id,
            "billing_class": billing_class,
            "source": source,
            "input_tokens": max(0, int(usage.input_tokens)),
            "output_tokens": max(0, int(usage.output_tokens)),
            "total_tokens": max(0, int(usage.total_tokens)),
            "exact": int(bool(usage.exact)),
            "estimated_cost_microrub": cost,
            "created_at": now_ts(),
        }
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO usage_events(id,user_id,provider_id,model_id,billing_class,source,input_tokens,output_tokens,total_tokens,exact,estimated_cost_microrub,created_at) VALUES(:id,:user_id,:provider_id,:model_id,:billing_class,:source,:input_tokens,:output_tokens,:total_tokens,:exact,:estimated_cost_microrub,:created_at)",
                item,
            )
            conn.commit()
        return item | {"exact": bool(item["exact"]), "estimated_cost_rub": cost / 1_000_000}

    def _yookassa_headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        config = self.payment_config()
        secret = self._read_payment_secret()
        if not config["configured"] or not secret:
            raise PaymentConfigurationError("payment provider is not configured")
        credentials = base64.b64encode(f"{config['shop_id']}:{secret}".encode("utf-8")).decode("ascii")
        headers = {"Authorization": f"Basic {credentials}", "Accept": "application/json", "Content-Type": "application/json"}
        if idempotency_key:
            headers["Idempotence-Key"] = idempotency_key
        return headers

    def _payment_request(self, path: str, *, payload: dict[str, Any] | None = None, method: str | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.payment_api_base + path, data=data, method=method, headers=self._yookassa_headers(idempotency_key))
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise BillingError(f"payment API returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise BillingError("payment API unavailable") from exc
        obj = json.loads(raw or "{}")
        if not isinstance(obj, dict):
            raise BillingError("payment API returned invalid payload")
        return obj

    def create_checkout(self, user: dict[str, Any], plan_id: str) -> dict[str, Any]:
        plan_id = str(plan_id).upper()
        if plan_id == "LIGHT":
            current = self.ensure_subscription(str(user["id"]), role=str(user.get("role", "USER")))
            if current.get("plan_id") in {"MEDIUM", "PRO"} and int(current.get("period_end") or 0) > now_ts():
                self.cancel_subscription(str(user["id"]))
                return {"ok": True, "free": True, "plan_id": "LIGHT", "effective": "period_end"}
            self.assign_plan(str(user["id"]), "LIGHT")
            return {"ok": True, "free": True, "plan_id": "LIGHT", "effective": "immediate"}
        if plan_id not in {"MEDIUM", "PRO"}:
            raise BillingError("unknown paid plan")
        config = self.payment_config()
        if not config["configured"]:
            raise PaymentConfigurationError("payment provider is not configured")
        payment_id = uuid.uuid4().hex
        idem = str(uuid.uuid4())
        amount = PLAN_PRICES_RUB[plan_id]
        payload = {
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "capture": True,
            "confirmation": {"type": "redirect", "return_url": f"{config['public_base_url']}/account?payment=return"},
            "save_payment_method": True,
            "description": f"Personal Agent Rus — {PLAN_NAMES[plan_id]}, 1 месяц",
            "metadata": {"internal_payment_id": payment_id, "user_id": str(user["id"]), "plan_id": plan_id},
        }
        obj = self._payment_request("/payments", payload=payload, method="POST", idempotency_key=idem)
        provider_payment_id = str(obj.get("id") or "")
        if not provider_payment_id:
            raise BillingError("payment API did not return payment id")
        confirmation = obj.get("confirmation") if isinstance(obj.get("confirmation"), dict) else {}
        confirmation_url = str(confirmation.get("confirmation_url") or "")
        status = str(obj.get("status") or "pending")
        local_status = "PAID" if status == "succeeded" else "PENDING" if status in {"pending", "waiting_for_capture"} else "FAILED"
        ts = now_ts()
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO payments(id,user_id,plan_id,amount_rub,status,provider,provider_payment_id,idempotency_key,confirmation_url,created_at,updated_at,raw_status) VALUES(?,?,?,?,?,'yookassa',?,?,?,?,?,?)",
                (payment_id, str(user["id"]), plan_id, amount, local_status, provider_payment_id, idem, confirmation_url, ts, ts, status),
            )
            conn.commit()
        return {"ok": True, "payment_id": payment_id, "provider_payment_id": provider_payment_id, "status": local_status, "confirmation_url": confirmation_url}

    def payment_status(self, internal_payment_id: str, user_id: str) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM payments WHERE id=? AND user_id=?", (internal_payment_id, user_id)).fetchone()
        if not row:
            raise BillingError("payment not found")
        return {k: row[k] for k in row.keys() if k not in {"idempotency_key"}}

    def _provider_payment(self, provider_payment_id: str) -> dict[str, Any]:
        return self._payment_request("/payments/" + urllib.parse.quote(provider_payment_id, safe=""), method="GET")

    def process_yookassa_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.payment_config()["provider"] != "yookassa":
            raise PaymentConfigurationError("YooKassa is not enabled")
        if payload.get("type") != "notification" or not isinstance(payload.get("object"), dict):
            raise BillingError("invalid payment notification")
        event = str(payload.get("event") or "")
        notified = payload["object"]
        provider_payment_id = str(notified.get("id") or "")
        if not provider_payment_id:
            raise BillingError("payment id missing")
        # Do not trust notification body. Re-fetch the object from YooKassa and verify current status/metadata.
        verified = self._provider_payment(provider_payment_id)
        metadata = verified.get("metadata") if isinstance(verified.get("metadata"), dict) else {}
        internal_payment_id = str(metadata.get("internal_payment_id") or "")
        user_id = str(metadata.get("user_id") or "")
        plan_id = str(metadata.get("plan_id") or "").upper()
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM payments WHERE id=? AND provider_payment_id=?", (internal_payment_id, provider_payment_id)).fetchone()
        if not row or str(row["user_id"]) != user_id or str(row["plan_id"]) != plan_id:
            raise BillingError("payment metadata mismatch")
        expected_amount = int(row["amount_rub"])
        amount = verified.get("amount") if isinstance(verified.get("amount"), dict) else {}
        if str(amount.get("currency")) != "RUB" or abs(float(amount.get("value", -1)) - expected_amount) > 0.001:
            raise BillingError("payment amount mismatch")
        event_key = f"{event}:{provider_payment_id}:{verified.get('status')}"
        payload_hash = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        with self.lock, self.db() as conn:
            duplicate = conn.execute("SELECT 1 FROM payment_events WHERE provider='yookassa' AND provider_event_key=?", (event_key,)).fetchone()
            if duplicate:
                return {"ok": True, "duplicate": True}
            conn.execute("INSERT INTO payment_events(id,provider,provider_event_key,payload_hash,processed_at) VALUES(?, 'yookassa', ?, ?, ?)", (uuid.uuid4().hex, event_key, payload_hash, now_ts()))
            conn.commit()
        status = str(verified.get("status") or "")
        if status == "succeeded":
            payment_method = verified.get("payment_method") if isinstance(verified.get("payment_method"), dict) else {}
            method_id = str(payment_method.get("id") or "") if payment_method.get("saved") else None
            with self.lock, self.db() as conn:
                conn.execute("UPDATE payments SET status='PAID',raw_status=?,updated_at=? WHERE id=?", (status, now_ts(), internal_payment_id))
                conn.commit()
            self.assign_plan(user_id, plan_id, auto_renew=bool(method_id), provider="yookassa", payment_method_id=method_id)
            return {"ok": True, "status": "PAID", "plan_id": plan_id, "auto_renew": bool(method_id)}
        if status == "canceled":
            with self.lock, self.db() as conn:
                conn.execute("UPDATE payments SET status='FAILED',raw_status=?,updated_at=? WHERE id=?", (status, now_ts(), internal_payment_id))
                conn.commit()
            return {"ok": True, "status": "FAILED"}
        return {"ok": True, "status": "PENDING"}

    def cancel_subscription(self, user_id: str) -> dict[str, Any]:
        sub = self.ensure_subscription(user_id)
        if sub.get("plan_id") not in {"MEDIUM", "PRO"}:
            return sub
        with self.lock, self.db() as conn:
            conn.execute("UPDATE subscriptions SET status='CANCEL_AT_PERIOD_END',cancel_at_period_end=1,auto_renew=0,updated_at=? WHERE user_id=?", (now_ts(), user_id))
            conn.commit()
        return self.ensure_subscription(user_id)

    def renew_due(self, *, limit: int = 25) -> dict[str, Any]:
        """Charge due saved payment methods idempotently and expire non-renewing paid periods."""
        now = now_ts()
        expired = 0
        with self.lock, self.db() as conn:
            stale = conn.execute(
                "SELECT user_id FROM subscriptions WHERE plan_id IN ('MEDIUM','PRO') AND period_end<=? AND (auto_renew=0 OR cancel_at_period_end=1)",
                (now,),
            ).fetchall()
            for row in stale:
                start, finish = month_window(now)
                conn.execute("UPDATE subscriptions SET plan_id='LIGHT',status='ACTIVE',period_start=?,period_end=?,auto_renew=0,payment_provider=NULL,payment_method_id=NULL,cancel_at_period_end=0,updated_at=? WHERE user_id=?", (start, finish, now, row["user_id"]))
                expired += 1
            conn.commit()
            rows = conn.execute(
                "SELECT * FROM subscriptions WHERE status='ACTIVE' AND plan_id IN ('MEDIUM','PRO') AND auto_renew=1 AND cancel_at_period_end=0 AND period_end<=? AND payment_provider='yookassa' AND payment_method_id IS NOT NULL LIMIT ?",
                (now, max(1, min(int(limit), 100))),
            ).fetchall()
        results = []
        for row in rows:
            plan_id = str(row["plan_id"]); internal_payment_id = uuid.uuid4().hex
            idem = str(uuid.uuid5(uuid.NAMESPACE_URL, f"par-renew:{row['user_id']}:{row['period_end']}:{plan_id}"))
            payload = {
                "amount": {"value": f"{PLAN_PRICES_RUB[plan_id]:.2f}", "currency": "RUB"},
                "capture": True,
                "payment_method_id": str(row["payment_method_id"]),
                "description": f"Personal Agent Rus — продление {PLAN_NAMES[plan_id]}, 1 месяц",
                "metadata": {"internal_payment_id": internal_payment_id, "renewal": "1", "user_id": str(row["user_id"]), "plan_id": plan_id, "period_end": str(row["period_end"])},
            }
            try:
                obj = self._payment_request("/payments", payload=payload, method="POST", idempotency_key=idem)
                provider_payment_id = str(obj.get("id") or "")
                status = str(obj.get("status") or "pending")
                local_status = "PAID" if status == "succeeded" else "PENDING" if status in {"pending", "waiting_for_capture"} else "FAILED"
                with self.lock, self.db() as conn:
                    conn.execute("INSERT OR IGNORE INTO payments(id,user_id,plan_id,amount_rub,status,provider,provider_payment_id,idempotency_key,confirmation_url,created_at,updated_at,raw_status) VALUES(?,?,?,?,?,'yookassa',?,?,NULL,?,?,?)", (internal_payment_id, str(row["user_id"]), plan_id, PLAN_PRICES_RUB[plan_id], local_status, provider_payment_id, idem, now_ts(), now_ts(), status))
                    if local_status == "PAID":
                        next_start = int(row["period_end"]); next_end = next_start + 30 * 24 * 60 * 60
                        conn.execute("UPDATE subscriptions SET status='ACTIVE',period_start=?,period_end=?,updated_at=? WHERE user_id=?", (next_start, next_end, now_ts(), row["user_id"]))
                    elif local_status == "FAILED":
                        conn.execute("UPDATE subscriptions SET status='PAST_DUE',updated_at=? WHERE user_id=?", (now_ts(), row["user_id"]))
                    conn.commit()
                results.append({"user_id": row["user_id"], "plan_id": plan_id, "provider_payment_id": provider_payment_id, "status": local_status})
            except BillingError as exc:
                with self.lock, self.db() as conn:
                    conn.execute("UPDATE subscriptions SET status='PAST_DUE',updated_at=? WHERE user_id=?", (now_ts(), row["user_id"]))
                    conn.commit()
                results.append({"user_id": row["user_id"], "plan_id": plan_id, "error": str(exc)})
        return {"checked": len(rows), "expired_to_light": expired, "results": results}

    def admin_overview(self) -> dict[str, Any]:
        start, end = month_window()
        with self.lock, self.db() as conn:
            usage = conn.execute(
                "SELECT billing_class,provider_id,model_id,SUM(total_tokens) tokens,SUM(estimated_cost_microrub) cost,COUNT(*) events FROM usage_events WHERE created_at>=? AND created_at<? GROUP BY billing_class,provider_id,model_id ORDER BY tokens DESC",
                (start, end),
            ).fetchall()
            subscriptions = conn.execute("SELECT plan_id,status,COUNT(*) count FROM subscriptions GROUP BY plan_id,status ORDER BY plan_id,status").fetchall()
            payments = conn.execute("SELECT status,COUNT(*) count,SUM(amount_rub) amount_rub FROM payments GROUP BY status").fetchall()
            balances = conn.execute(
                "SELECT u.id AS user_id,u.email,u.display_name,u.role,u.status,COALESCE(b.balance_microrub,0) AS balance_microrub "
                "FROM users u LEFT JOIN user_balances b ON b.user_id=u.id ORDER BY COALESCE(b.balance_microrub,0) DESC,u.created_at DESC"
            ).fetchall()
            promo_codes = conn.execute(
                "SELECT p.*,COUNT(r.id) redemption_count,COUNT(DISTINCT r.user_id) unique_user_count,MAX(r.redeemed_at) last_redeemed_at "
                "FROM promo_codes p LEFT JOIN promo_redemptions r ON r.promo_code_id=p.id GROUP BY p.id ORDER BY p.created_at DESC LIMIT 100"
            ).fetchall()
            promo_redemptions = conn.execute(
                "SELECT r.id,r.user_id,r.amount_microrub,r.redeemed_at,p.code,p.kind,p.created_by_user_id,u.email,u.display_name,u.role "
                "FROM promo_redemptions r JOIN promo_codes p ON p.id=r.promo_code_id LEFT JOIN users u ON u.id=r.user_id "
                "ORDER BY r.redeemed_at DESC LIMIT 100"
            ).fetchall()
            topup_requests = conn.execute(
                "SELECT t.*,u.email,u.display_name,u.role,u.status AS user_status FROM topup_requests t "
                "LEFT JOIN users u ON u.id=t.user_id ORDER BY t.created_at DESC LIMIT 100"
            ).fetchall()
        return {
            "plans": self.plans(),
            "payment_config": self.payment_config(),
            "usage": [{"billing_class": r["billing_class"], "provider_id": r["provider_id"], "model_id": r["model_id"], "tokens": int(r["tokens"] or 0), "estimated_cost_rub": int(r["cost"] or 0) / 1_000_000, "events": int(r["events"])} for r in usage],
            "subscriptions": [{"plan_id": r["plan_id"], "status": r["status"], "count": int(r["count"])} for r in subscriptions],
            "payments": [{"status": r["status"], "count": int(r["count"]), "amount_rub": int(r["amount_rub"] or 0)} for r in payments],
            "balances": [{k: row[k] for k in row.keys() if k != "balance_microrub"} | {"balance_rub": self._microrub_to_rub(row["balance_microrub"])} for row in balances],
            "promo_codes": [
                self._promo_row(dict(row))
                | {
                    "redemption_count": int(row["redemption_count"] or 0),
                    "unique_user_count": int(row["unique_user_count"] or 0),
                    "last_redeemed_at": int(row["last_redeemed_at"] or 0) if row["last_redeemed_at"] else None,
                }
                for row in promo_codes
            ],
            "promo_redemptions": [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "display_name": row["display_name"],
                    "role": row["role"],
                    "code": row["code"],
                    "kind": row["kind"],
                    "created_by": row["created_by_user_id"],
                    "amount_rub": self._microrub_to_rub(row["amount_microrub"]),
                    "redeemed_at": int(row["redeemed_at"]),
                }
                for row in promo_redemptions
            ],
            "topup_requests": [self._topup_with_user(row) for row in topup_requests],
            "period_start": start,
            "period_end": end,
        }
