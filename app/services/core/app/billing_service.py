from __future__ import annotations

import base64
from email.message import EmailMessage
import hashlib
import hmac
import json
import os
import re
import sqlite3
import smtplib
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLAN_PRICES_RUB = {"LIGHT": 0, "MEDIUM": 500, "PRO": 1000}
PLAN_NAMES = {"LIGHT": "Лайт", "MEDIUM": "Медиум", "PRO": "Про"}
PLAN_SUPPORT = {"LIGHT": "community", "MEDIUM": "standard", "PRO": "priority"}
BILLING_CLASSES = {"LOCAL", "BYOK", "PLATFORM_REMOTE", "PRIVATE_REMOTE"}
SUBSCRIPTION_STATES = {"TRIAL", "ACTIVE", "PAST_DUE", "GRACE_PERIOD", "CANCEL_AT_PERIOD_END", "CANCELLED", "EXPIRED"}
PAYMENT_STATES = {"CREATED", "PENDING", "PAID", "FAILED", "CANCELLED", "REFUNDED", "PARTIALLY_REFUNDED"}
THEME_CATALOG: tuple[dict[str, Any], ...] = (
    {"id": "system", "display_name": "Как в системе", "price_rub": 0, "free": True, "accent": "#8db8ff"},
    {"id": "dark", "display_name": "Тёмная", "price_rub": 0, "free": True, "accent": "#f3f4f6"},
    {"id": "light", "display_name": "Светлая", "price_rub": 0, "free": True, "accent": "#17191f"},
    {"id": "ocean", "display_name": "Голубая", "price_rub": 49, "free": False, "accent": "#52a8ff"},
    {"id": "forest", "display_name": "Светло-зелёная", "price_rub": 49, "free": False, "accent": "#63d29f"},
    {"id": "sunset", "display_name": "Закат", "price_rub": 59, "free": False, "accent": "#ff9d66"},
    {"id": "sand", "display_name": "Песок", "price_rub": 39, "free": False, "accent": "#e7c78c"},
    {"id": "coral", "display_name": "Коралл", "price_rub": 59, "free": False, "accent": "#ff7e9b"},
)
THEME_IDS = {str(item["id"]) for item in THEME_CATALOG}
FREE_THEME_IDS = {str(item["id"]) for item in THEME_CATALOG if bool(item.get("free"))}


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
        self.topup_second_approval_rub = float(os.getenv("PA_TOPUP_SECOND_APPROVAL_RUB", "5000"))
        self.payment_api_base = os.getenv("PA_PAYMENT_API_BASE", "https://api.yookassa.ru/v3").rstrip("/")
        self.smtp_host = os.getenv("PA_SMTP_HOST", "").strip()
        self.smtp_port = int(os.getenv("PA_SMTP_PORT", "587"))
        self.smtp_user = os.getenv("PA_SMTP_USER", "").strip()
        self.smtp_password = os.getenv("PA_SMTP_PASSWORD", "").strip()
        self.smtp_from = os.getenv("PA_SMTP_FROM", self.smtp_user or "").strip()
        self.smtp_use_tls = os.getenv("PA_SMTP_USE_TLS", "1").strip().lower() in {"1", "true", "yes", "on"}

    def db(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

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
                CREATE TABLE IF NOT EXISTS billing_balances (
                  user_id TEXT PRIMARY KEY,
                  balance_microrub INTEGER NOT NULL DEFAULT 0,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS balance_events (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  actor_user_id TEXT,
                  source TEXT NOT NULL,
                  delta_microrub INTEGER NOT NULL,
                  reason TEXT NOT NULL,
                  reference TEXT,
                  created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_balance_events_user_time ON balance_events(user_id,created_at);
                CREATE TABLE IF NOT EXISTS promo_codes (
                  code TEXT PRIMARY KEY,
                  kind TEXT NOT NULL DEFAULT 'general',
                  amount_microrub INTEGER NOT NULL,
                  uses_total INTEGER NOT NULL DEFAULT 1,
                  uses_remaining INTEGER NOT NULL DEFAULT 1,
                  active INTEGER NOT NULL DEFAULT 1,
                  created_by TEXT,
                  description TEXT,
                  expires_at INTEGER,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS promo_redemptions (
                  id TEXT PRIMARY KEY,
                  code TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  redeemed_at INTEGER NOT NULL,
                  amount_microrub INTEGER NOT NULL,
                  UNIQUE(code,user_id)
                );
                CREATE TABLE IF NOT EXISTS topup_requests (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  source TEXT NOT NULL,
                  amount_microrub INTEGER NOT NULL,
                  note TEXT,
                  payment_reference TEXT NOT NULL DEFAULT '',
                  status TEXT NOT NULL,
                  reviewer_user_id TEXT,
                  second_reviewer_user_id TEXT,
                  reconciled_by_user_id TEXT,
                  reconciled_at INTEGER,
                  reconciliation_note TEXT,
                  review_note TEXT,
                  created_at INTEGER NOT NULL,
                  reviewed_at INTEGER,
                  second_reviewed_at INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_topup_requests_user_time ON topup_requests(user_id,created_at);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_topup_requests_payment_reference_unique ON topup_requests(payment_reference) WHERE payment_reference <> '';
                CREATE TABLE IF NOT EXISTS theme_unlocks (
                  user_id TEXT NOT NULL,
                  theme_id TEXT NOT NULL,
                  price_microrub INTEGER NOT NULL,
                  actor_user_id TEXT,
                  purchased_at INTEGER NOT NULL,
                  PRIMARY KEY(user_id, theme_id)
                );
                CREATE INDEX IF NOT EXISTS idx_theme_unlocks_theme_time ON theme_unlocks(theme_id, purchased_at DESC);
                CREATE TABLE IF NOT EXISTS theme_purchases (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  theme_id TEXT NOT NULL,
                  price_microrub INTEGER NOT NULL,
                  actor_user_id TEXT,
                  created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_theme_purchases_user_time ON theme_purchases(user_id, created_at DESC);
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
                """
            )
            ts = now_ts()
            for plan_id in ("LIGHT", "MEDIUM", "PRO"):
                # Safe-by-default: platform-funded remote AI is disabled until an admin sets a budget.
                conn.execute(
                    "INSERT INTO plans(id,display_name,price_rub,support_level,local_unlimited,remote_token_limit,remote_cost_limit_microrub,enabled,updated_at) "
                    "VALUES(?,?,?,?,1,0,0,1,?) ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name,price_rub=excluded.price_rub,support_level=excluded.support_level,local_unlimited=1",
                    (plan_id, PLAN_NAMES[plan_id], PLAN_PRICES_RUB[plan_id], PLAN_SUPPORT[plan_id], ts),
                )
            promo_cols = {str(row[1]) for row in conn.execute("PRAGMA table_info(promo_codes)").fetchall()}
            if "kind" not in promo_cols:
                conn.execute("ALTER TABLE promo_codes ADD COLUMN kind TEXT NOT NULL DEFAULT 'general'")
            topup_cols = {str(row[1]) for row in conn.execute("PRAGMA table_info(topup_requests)").fetchall()}
            if "payment_reference" not in topup_cols:
                conn.execute("ALTER TABLE topup_requests ADD COLUMN payment_reference TEXT NOT NULL DEFAULT ''")
            if "second_reviewer_user_id" not in topup_cols:
                conn.execute("ALTER TABLE topup_requests ADD COLUMN second_reviewer_user_id TEXT")
            if "reconciled_by_user_id" not in topup_cols:
                conn.execute("ALTER TABLE topup_requests ADD COLUMN reconciled_by_user_id TEXT")
            if "reconciled_at" not in topup_cols:
                conn.execute("ALTER TABLE topup_requests ADD COLUMN reconciled_at INTEGER")
            if "reconciliation_note" not in topup_cols:
                conn.execute("ALTER TABLE topup_requests ADD COLUMN reconciliation_note TEXT")
            if "review_note" not in topup_cols:
                conn.execute("ALTER TABLE topup_requests ADD COLUMN review_note TEXT")
            if "second_reviewed_at" not in topup_cols:
                conn.execute("ALTER TABLE topup_requests ADD COLUMN second_reviewed_at INTEGER")
            conn.commit()

    @staticmethod
    def _rub_to_microrub(value: float | int | str) -> int:
        try:
            return int(round(float(value) * 1_000_000))
        except (TypeError, ValueError) as exc:
            raise BillingError("invalid ruble amount") from exc

    @staticmethod
    def _normalize_promo_code(code: str) -> str:
        normalized = re.sub(r"[^A-Z0-9-]", "", str(code).strip().upper())
        if not normalized:
            raise BillingError("promo code is required")
        if len(normalized) > 40:
            raise BillingError("promo code is too long")
        return normalized

    def theme_catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "id": str(item["id"]),
                "display_name": str(item["display_name"]),
                "price_rub": int(item["price_rub"]),
                "free": bool(item["free"]),
                "accent": str(item["accent"]),
            }
            for item in THEME_CATALOG
        ]

    def owned_theme_ids(self, user_id: str) -> list[str]:
        with self.lock, self.db() as conn:
            rows = conn.execute("SELECT theme_id FROM theme_unlocks WHERE user_id=?", (str(user_id),)).fetchall()
        owned = {str(row["theme_id"]) for row in rows}
        return sorted(owned | FREE_THEME_IDS)

    def owns_theme(self, user_id: str, theme_id: str) -> bool:
        theme_id = str(theme_id).strip().lower()
        if theme_id in FREE_THEME_IDS:
            return True
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT 1 FROM theme_unlocks WHERE user_id=? AND theme_id=?", (str(user_id), theme_id)).fetchone()
        return bool(row)

    def purchase_theme(self, user_id: str, theme_id: str, *, actor_user_id: str | None = None) -> dict[str, Any]:
        theme_id = str(theme_id).strip().lower()
        theme = next((item for item in THEME_CATALOG if str(item["id"]) == theme_id), None)
        if not theme:
            raise BillingError("unknown theme")
        if theme_id in FREE_THEME_IDS:
            return {
                "theme": {k: theme[k] for k in ("id", "display_name", "price_rub", "free", "accent")},
                "owned": True,
                "purchase": None,
                "balance": self.balance(str(user_id)),
                "owned_theme_ids": self.owned_theme_ids(str(user_id)),
            }
        price_microrub = int(round(float(theme["price_rub"]) * 1_000_000))
        ts = now_ts()
        with self.lock, self.db() as conn:
            existing = conn.execute("SELECT 1 FROM theme_unlocks WHERE user_id=? AND theme_id=?", (str(user_id), theme_id)).fetchone()
            if existing:
                return {
                    "theme": {k: theme[k] for k in ("id", "display_name", "price_rub", "free", "accent")},
                    "owned": True,
                    "purchase": None,
                    "balance": self.balance(str(user_id)),
                    "owned_theme_ids": self.owned_theme_ids(str(user_id)),
                }
            balance = self._set_balance(
                conn,
                user_id=str(user_id),
                delta_microrub=-price_microrub,
                actor_user_id=actor_user_id,
                source="theme_purchase",
                reason=f"purchase theme {theme_id}",
                reference=theme_id,
            )
            conn.execute(
                "INSERT INTO theme_unlocks(user_id,theme_id,price_microrub,actor_user_id,purchased_at) VALUES(?,?,?,?,?)",
                (str(user_id), theme_id, price_microrub, actor_user_id, ts),
            )
            purchase_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO theme_purchases(id,user_id,theme_id,price_microrub,actor_user_id,created_at) VALUES(?,?,?,?,?,?)",
                (purchase_id, str(user_id), theme_id, price_microrub, actor_user_id, ts),
            )
            conn.commit()
        return {
            "theme": {k: theme[k] for k in ("id", "display_name", "price_rub", "free", "accent")},
            "owned": True,
            "purchase": {
                "id": purchase_id,
                "user_id": str(user_id),
                "theme_id": theme_id,
                "price_rub": round(price_microrub / 1_000_000, 6),
                "actor_user_id": actor_user_id,
                "created_at": ts,
            },
            "balance": balance,
            "owned_theme_ids": self.owned_theme_ids(str(user_id)),
        }

    def _ensure_balance_row(self, conn: sqlite3.Connection, user_id: str) -> None:
        conn.execute(
            "INSERT OR IGNORE INTO billing_balances(user_id,balance_microrub,updated_at) VALUES(?,?,?)",
            (user_id, 0, now_ts()),
        )

    def balance(self, user_id: str) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT balance_microrub FROM billing_balances WHERE user_id=?", (user_id,)).fetchone()
        balance_microrub = int(row["balance_microrub"]) if row else 0
        return {
            "user_id": user_id,
            "balance_microrub": balance_microrub,
            "balance_rub": round(balance_microrub / 1_000_000, 6),
        }

    def _set_balance(self, conn: sqlite3.Connection, *, user_id: str, delta_microrub: int, actor_user_id: str | None, source: str, reason: str, reference: str | None = None) -> dict[str, Any]:
        if delta_microrub == 0:
            raise BillingError("balance delta must be non-zero")
        self._ensure_balance_row(conn, user_id)
        row = conn.execute("SELECT balance_microrub FROM billing_balances WHERE user_id=?", (user_id,)).fetchone()
        current = int(row["balance_microrub"]) if row else 0
        updated = current + int(delta_microrub)
        if updated < 0:
            raise BillingError("insufficient balance")
        conn.execute("UPDATE billing_balances SET balance_microrub=?,updated_at=? WHERE user_id=?", (updated, now_ts(), user_id))
        conn.execute(
            "INSERT INTO balance_events(id,user_id,actor_user_id,source,delta_microrub,reason,reference,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (uuid.uuid4().hex, user_id, actor_user_id, source, int(delta_microrub), reason[:240], reference, now_ts()),
        )
        return {"user_id": user_id, "balance_microrub": updated, "balance_rub": round(updated / 1_000_000, 6)}

    def adjust_balance(self, user_id: str, *, delta_rub: float | int | str, actor_user_id: str | None = None, source: str = "admin", reason: str = "", reference: str | None = None) -> dict[str, Any]:
        delta_microrub = self._rub_to_microrub(delta_rub)
        reason = reason.strip() or ("balance adjustment" if delta_microrub > 0 else "balance charge")
        with self.lock, self.db() as conn:
            result = self._set_balance(conn, user_id=str(user_id), delta_microrub=delta_microrub, actor_user_id=actor_user_id, source=source, reason=reason, reference=reference)
            conn.commit()
        return result

    def charge_balance(self, user_id: str, *, amount_microrub: int, actor_user_id: str | None = None, source: str = "usage", reason: str = "", reference: str | None = None) -> dict[str, Any]:
        reason = reason.strip() or "balance charge"
        with self.lock, self.db() as conn:
            result = self._set_balance(conn, user_id=str(user_id), delta_microrub=-abs(int(amount_microrub)), actor_user_id=actor_user_id, source=source, reason=reason, reference=reference)
            conn.commit()
        return result

    def refund_balance(self, user_id: str, *, amount_microrub: int, actor_user_id: str | None = None, source: str = "refund", reason: str = "", reference: str | None = None) -> dict[str, Any]:
        reason = reason.strip() or "balance refund"
        with self.lock, self.db() as conn:
            result = self._set_balance(conn, user_id=str(user_id), delta_microrub=abs(int(amount_microrub)), actor_user_id=actor_user_id, source=source, reason=reason, reference=reference)
            conn.commit()
        return result

    def create_promo_code(
        self,
        *,
        amount_rub: float | int | str,
        uses_total: int = 1,
        code: str | None = None,
        kind: str = "general",
        description: str = "",
        expires_at: int | None = None,
        created_by: str | None = None,
        send_to_email: str | None = None,
        send_to_name: str | None = None,
        send_subject: str | None = None,
        send_message: str | None = None,
    ) -> dict[str, Any]:
        amount_microrub = self._rub_to_microrub(amount_rub)
        if amount_microrub <= 0:
            raise BillingError("promo amount must be positive")
        uses_total = int(uses_total)
        if uses_total < 1 or uses_total > 1000:
            raise BillingError("uses_total must be between 1 and 1000")
        kind = str(kind).strip().lower() or "general"
        if kind not in {"general", "starter"}:
            raise BillingError("unsupported promo kind")
        promo_code = self._normalize_promo_code(code or uuid.uuid4().hex[:12].upper())
        description = str(description).strip()[:240]
        if expires_at is not None:
            expires_at = int(expires_at)
            if expires_at <= now_ts():
                raise BillingError("promo code expiry must be in the future")
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO promo_codes(code,kind,amount_microrub,uses_total,uses_remaining,active,created_by,description,expires_at,created_at,updated_at) VALUES(?,?,?,?,?,1,?,?,?,?,?)",
                (promo_code, kind, amount_microrub, uses_total, uses_total, created_by, description, expires_at, now_ts(), now_ts()),
            )
            conn.commit()
        promo = self.get_promo_code(promo_code)
        email_sent = False
        if send_to_email:
            email_subject = str(send_subject or "Ваш промокод Personal Agent").strip()
            recipient_name = str(send_to_name or "").strip()
            lines = [
                f"Промокод: {promo_code}",
                f"Номинал: {promo['amount_rub']:.2f} ₽",
                f"Использований: {uses_total}",
            ]
            if description:
                lines.append(f"Комментарий: {description}")
            if send_message:
                lines.append("")
                lines.append(str(send_message).strip())
            body = "\n".join(lines)
            email_sent = self.send_email(
                to_email=send_to_email,
                subject=email_subject,
                body=body,
                from_name=recipient_name or "Personal Agent",
            )
        return promo | {"email_sent": email_sent, "email_to": send_to_email if email_sent else None}

    def get_promo_code(self, code: str) -> dict[str, Any] | None:
        promo_code = self._normalize_promo_code(code)
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM promo_codes WHERE code=?", (promo_code,)).fetchone()
        if not row:
            return None
        return {
            "code": str(row["code"]),
            "kind": str(row["kind"] or "general"),
            "amount_rub": round(int(row["amount_microrub"]) / 1_000_000, 6),
            "uses_total": int(row["uses_total"]),
            "uses_remaining": int(row["uses_remaining"]),
            "active": bool(int(row["active"])),
            "created_by": row["created_by"],
            "description": row["description"],
            "expires_at": row["expires_at"],
            "created_at": int(row["created_at"]),
            "updated_at": int(row["updated_at"]),
        }

    def list_promo_codes(self, *, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self.lock, self.db() as conn:
            rows = conn.execute("SELECT code FROM promo_codes ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [item for item in (self.get_promo_code(str(row["code"])) for row in rows) if item]

    def redeem_promo_code(self, user_id: str, code: str) -> dict[str, Any]:
        promo_code = self._normalize_promo_code(code)
        ts = now_ts()
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM promo_codes WHERE code=?", (promo_code,)).fetchone()
            if not row or not int(row["active"]):
                raise BillingError("promo code not found")
            expires_at = row["expires_at"]
            if expires_at is not None and int(expires_at) <= ts:
                raise BillingError("promo code expired")
            if int(row["uses_remaining"]) <= 0:
                raise BillingError("promo code exhausted")
            already = conn.execute("SELECT 1 FROM promo_redemptions WHERE code=? AND user_id=?", (promo_code, str(user_id))).fetchone()
            if already:
                raise BillingError("promo code already redeemed")
            amount_microrub = int(row["amount_microrub"])
            conn.execute(
                "UPDATE promo_codes SET uses_remaining=uses_remaining-1,updated_at=? WHERE code=? AND uses_remaining>0",
                (ts, promo_code),
            )
            if conn.execute("SELECT changes()").fetchone()[0] == 0:
                raise BillingError("promo code exhausted")
            self._ensure_balance_row(conn, str(user_id))
            result = self._set_balance(
                conn,
                user_id=str(user_id),
                delta_microrub=amount_microrub,
                actor_user_id=str(user_id),
                source="promo",
                reason=f"redeem promo {promo_code}",
                reference=promo_code,
            )
            conn.execute(
                "INSERT INTO promo_redemptions(id,code,user_id,redeemed_at,amount_microrub) VALUES(?,?,?,?,?)",
                (uuid.uuid4().hex, promo_code, str(user_id), ts, amount_microrub),
            )
            conn.commit()
        return {"promo_code": promo_code, "amount_rub": round(amount_microrub / 1_000_000, 6), "balance": result}

    def create_topup_request(self, user_id: str, *, amount_rub: float | int | str, source: str = "yoomoney", note: str = "", payment_reference: str = "") -> dict[str, Any]:
        amount_microrub = self._rub_to_microrub(amount_rub)
        if amount_microrub <= 0:
            raise BillingError("top-up amount must be positive")
        source = str(source).strip().lower() or "yoomoney"
        note = str(note).strip()[:500]
        payment_reference = str(payment_reference).strip()
        if not payment_reference:
            raise BillingError("payment reference is required")
        if len(payment_reference) > 120:
            raise BillingError("payment reference is too long")
        request_id = uuid.uuid4().hex
        ts = now_ts()
        with self.lock, self.db() as conn:
            duplicate = conn.execute("SELECT 1 FROM topup_requests WHERE payment_reference=? LIMIT 1", (payment_reference,)).fetchone()
            if duplicate:
                raise BillingError("payment reference already used")
            conn.execute(
                "INSERT INTO topup_requests(id,user_id,source,amount_microrub,note,payment_reference,status,created_at) VALUES(?,?,?,?,?,?,'PENDING',?)",
                (request_id, str(user_id), source, amount_microrub, note, payment_reference, ts),
            )
            conn.commit()
        return self.get_topup_request(request_id)

    def get_topup_request(self, request_id: str) -> dict[str, Any] | None:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
        if not row:
            return None
        return {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "source": str(row["source"]),
            "amount_rub": round(int(row["amount_microrub"]) / 1_000_000, 6),
            "note": row["note"],
            "payment_reference": str(row["payment_reference"] or ""),
            "status": str(row["status"]),
            "reviewer_user_id": row["reviewer_user_id"],
            "second_reviewer_user_id": row["second_reviewer_user_id"],
            "reconciled_by_user_id": row["reconciled_by_user_id"],
            "reconciled_at": row["reconciled_at"],
            "reconciliation_note": row["reconciliation_note"],
            "review_note": row["review_note"],
            "created_at": int(row["created_at"]),
            "reviewed_at": row["reviewed_at"],
            "second_reviewed_at": row["second_reviewed_at"],
            "requires_second_approval": bool(int(row["amount_microrub"]) >= int(round(self.topup_second_approval_rub * 1_000_000))),
        }

    def list_topup_requests(self, *, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self.lock, self.db() as conn:
            rows = conn.execute("SELECT id FROM topup_requests ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [item for item in (self.get_topup_request(str(row["id"])) for row in rows) if item]

    @staticmethod
    def _chunked(values: list[str], size: int = 200) -> list[list[str]]:
        size = max(1, int(size))
        return [values[index:index + size] for index in range(0, len(values), size)]

    def user_billing_summaries(self, user_ids: list[str]) -> dict[str, dict[str, Any]]:
        ids = [str(user_id) for user_id in user_ids if str(user_id).strip()]
        if not ids:
            return {}
        summaries: dict[str, dict[str, Any]] = {}
        for user_id in ids:
            summaries[user_id] = {
                "payments_total": 0,
                "payments_paid": 0,
                "payments_failed": 0,
                "payments_pending": 0,
                "payments_paid_rub": 0.0,
                "last_payment_at": None,
                "last_paid_at": None,
                "promo_redemptions_total": 0,
                "promo_redemptions_rub": 0.0,
                "last_promo_redeemed_at": None,
                "topup_requests_total": 0,
                "topup_requests_pending": 0,
                "topup_requests_approved": 0,
                "topup_requests_review_required": 0,
                "topup_requests_rejected": 0,
                "last_topup_request_at": None,
                "balance_events_total": 0,
                "balance_events_net_rub": 0.0,
                "last_balance_event_at": None,
                "balance_sources": [],
            }
        for chunk in self._chunked(ids, 200):
            placeholders = ",".join("?" for _ in chunk)
            with self.lock, self.db() as conn:
                payment_rows = conn.execute(
                    f"""
                    SELECT user_id,
                           COUNT(*) total_count,
                           SUM(CASE WHEN status='PAID' THEN 1 ELSE 0 END) paid_count,
                           SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) failed_count,
                           SUM(CASE WHEN status='PENDING' THEN 1 ELSE 0 END) pending_count,
                           SUM(CASE WHEN status='PAID' THEN amount_rub ELSE 0 END) paid_amount_rub,
                           MAX(created_at) last_payment_at,
                           MAX(CASE WHEN status='PAID' THEN updated_at ELSE NULL END) last_paid_at
                    FROM payments
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id
                    """,
                    chunk,
                ).fetchall()
                promo_rows = conn.execute(
                    f"""
                    SELECT user_id,
                           COUNT(*) total_count,
                           SUM(amount_microrub) amount_microrub,
                           MAX(redeemed_at) last_redeemed_at
                    FROM promo_redemptions
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id
                    """,
                    chunk,
                ).fetchall()
                topup_rows = conn.execute(
                    f"""
                    SELECT user_id,
                           COUNT(*) total_count,
                           SUM(CASE WHEN status='PENDING' THEN 1 ELSE 0 END) pending_count,
                           SUM(CASE WHEN status='APPROVED' THEN 1 ELSE 0 END) approved_count,
                           SUM(CASE WHEN status='REVIEW_REQUIRED' THEN 1 ELSE 0 END) review_required_count,
                           SUM(CASE WHEN status='REJECTED' THEN 1 ELSE 0 END) rejected_count,
                           MAX(created_at) last_topup_request_at
                    FROM topup_requests
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id
                    """,
                    chunk,
                ).fetchall()
                balance_rows = conn.execute(
                    f"""
                    SELECT user_id,
                           COUNT(*) total_count,
                           SUM(delta_microrub) net_microrub,
                           MAX(created_at) last_balance_event_at
                    FROM balance_events
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id
                    """,
                    chunk,
                ).fetchall()
                source_rows = conn.execute(
                    f"""
                    SELECT user_id,source,COUNT(*) event_count,SUM(delta_microrub) net_microrub,MAX(created_at) last_event_at
                    FROM balance_events
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id,source
                    ORDER BY user_id, event_count DESC, last_event_at DESC
                    """,
                    chunk,
                ).fetchall()
            for row in payment_rows:
                item = summaries[str(row["user_id"])]
                item["payments_total"] = int(row["total_count"] or 0)
                item["payments_paid"] = int(row["paid_count"] or 0)
                item["payments_failed"] = int(row["failed_count"] or 0)
                item["payments_pending"] = int(row["pending_count"] or 0)
                item["payments_paid_rub"] = round(float(row["paid_amount_rub"] or 0), 6)
                item["last_payment_at"] = int(row["last_payment_at"]) if row["last_payment_at"] is not None else None
                item["last_paid_at"] = int(row["last_paid_at"]) if row["last_paid_at"] is not None else None
            for row in promo_rows:
                item = summaries[str(row["user_id"])]
                item["promo_redemptions_total"] = int(row["total_count"] or 0)
                item["promo_redemptions_rub"] = round(int(row["amount_microrub"] or 0) / 1_000_000, 6)
                item["last_promo_redeemed_at"] = int(row["last_redeemed_at"]) if row["last_redeemed_at"] is not None else None
            for row in topup_rows:
                item = summaries[str(row["user_id"])]
                item["topup_requests_total"] = int(row["total_count"] or 0)
                item["topup_requests_pending"] = int(row["pending_count"] or 0)
                item["topup_requests_approved"] = int(row["approved_count"] or 0)
                item["topup_requests_review_required"] = int(row["review_required_count"] or 0)
                item["topup_requests_rejected"] = int(row["rejected_count"] or 0)
                item["last_topup_request_at"] = int(row["last_topup_request_at"]) if row["last_topup_request_at"] is not None else None
            for row in balance_rows:
                item = summaries[str(row["user_id"])]
                item["balance_events_total"] = int(row["total_count"] or 0)
                item["balance_events_net_rub"] = round(int(row["net_microrub"] or 0) / 1_000_000, 6)
                item["last_balance_event_at"] = int(row["last_balance_event_at"]) if row["last_balance_event_at"] is not None else None
            for row in source_rows:
                item = summaries[str(row["user_id"])]
                item["balance_sources"].append(
                    {
                        "source": row["source"],
                        "count": int(row["event_count"] or 0),
                        "net_rub": round(int(row["net_microrub"] or 0) / 1_000_000, 6),
                        "last_event_at": int(row["last_event_at"]) if row["last_event_at"] is not None else None,
                    }
                )
        return summaries

    def approve_topup_request(self, request_id: str, *, reviewer_user_id: str) -> dict[str, Any]:
        return self.reconcile_topup_request(request_id, reviewer_user_id=reviewer_user_id)

    def reconcile_topup_request(self, request_id: str, *, reviewer_user_id: str, review_note: str = "") -> dict[str, Any]:
        review_note = str(review_note).strip()[:240]
        if not review_note:
            raise BillingError("review note is required")
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
            if not row:
                raise BillingError("top-up request not found")
            status = str(row["status"])
            if status not in {"PENDING", "REVIEW_REQUIRED"}:
                raise BillingError("top-up request already reviewed")
            amount_microrub = int(row["amount_microrub"])
            threshold_microrub = int(round(self.topup_second_approval_rub * 1_000_000))
            review_required = amount_microrub >= threshold_microrub
            if status == "PENDING" and review_required:
                conn.execute(
                    "UPDATE topup_requests SET status='REVIEW_REQUIRED',reviewer_user_id=?,reviewed_at=?,review_note=?,reconciled_by_user_id=?,reconciled_at=?,reconciliation_note=? WHERE id=?",
                    (str(reviewer_user_id), now_ts(), review_note, str(reviewer_user_id), now_ts(), review_note, request_id),
                )
                conn.commit()
                return {"request": self.get_topup_request(request_id), "balance": self.balance(str(row["user_id"])), "requires_second_approval": True}
            if status == "REVIEW_REQUIRED":
                first_reviewer = str(row["reviewer_user_id"] or "")
                if first_reviewer and first_reviewer == str(reviewer_user_id):
                    raise BillingError("second approval must be performed by another admin")
            result = self._set_balance(
                conn,
                user_id=str(row["user_id"]),
                delta_microrub=amount_microrub,
                actor_user_id=str(reviewer_user_id),
                source=str(row["source"]),
                reason=f"approved top-up request {request_id}",
                reference=request_id,
            )
            if status == "REVIEW_REQUIRED":
                conn.execute(
                    "UPDATE topup_requests SET status='APPROVED',second_reviewer_user_id=?,second_reviewed_at=?,reconciled_by_user_id=?,reconciled_at=?,reconciliation_note=? WHERE id=?",
                    (str(reviewer_user_id), now_ts(), str(reviewer_user_id), now_ts(), review_note, request_id),
                )
            else:
                conn.execute(
                    "UPDATE topup_requests SET status='APPROVED',reviewer_user_id=?,reviewed_at=?,reconciled_by_user_id=?,reconciled_at=?,reconciliation_note=? WHERE id=?",
                    (str(reviewer_user_id), now_ts(), str(reviewer_user_id), now_ts(), review_note, request_id),
                )
            conn.commit()
        return {"request": self.get_topup_request(request_id), "balance": result, "requires_second_approval": False}

    def reject_topup_request(self, request_id: str, *, reviewer_user_id: str, review_note: str = "") -> dict[str, Any]:
        review_note = str(review_note).strip()[:240]
        if not review_note:
            raise BillingError("review note is required")
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM topup_requests WHERE id=?", (request_id,)).fetchone()
            if not row:
                raise BillingError("top-up request not found")
            if str(row["status"]) not in {"PENDING", "REVIEW_REQUIRED"}:
                raise BillingError("top-up request already reviewed")
            conn.execute(
                "UPDATE topup_requests SET status='REJECTED',reviewer_user_id=COALESCE(reviewer_user_id,?),review_note=?,reviewed_at=? WHERE id=?",
                (str(reviewer_user_id), review_note, now_ts(), request_id),
            )
            conn.commit()
        return {"request": self.get_topup_request(request_id)}

    def estimate_remote_usage(self, messages: list[dict[str, str]], spec: dict[str, Any]) -> InferenceUsage:
        input_chars = sum(len(str(item.get("content", ""))) for item in messages)
        input_tokens = max(1, (input_chars + 2) // 3)
        output_tokens = max(1, int(spec.get("num_predict") or 32))
        return InferenceUsage(input_tokens, output_tokens, False)

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

    def _email_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)

    def send_email(self, *, to_email: str, subject: str, body: str, from_name: str = "Personal Agent") -> bool:
        to_email = str(to_email).strip()
        subject = str(subject).strip()
        body = str(body)
        if not to_email or not subject or not body or not self._email_configured():
            return False
        message = EmailMessage()
        message["From"] = f"{from_name} <{self.smtp_from}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as client:
            if self.smtp_use_tls:
                client.starttls()
            if self.smtp_user and self.smtp_password:
                client.login(self.smtp_user, self.smtp_password)
            client.send_message(message)
        return True

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
            "themes": {
                "catalog": self.theme_catalog(),
                "owned_theme_ids": self.owned_theme_ids(str(user["id"])),
                "active_theme_id": str(pref.get("theme") or "system"),
            },
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
        }

    def route_allowed(self, user: dict[str, Any], provider: dict[str, Any], *, messages: list[dict[str, str]] | None = None, spec: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        billing_class = str(provider.get("billing_class") or "BYOK").upper()
        if billing_class not in BILLING_CLASSES:
            billing_class = "BYOK"
        if billing_class != "PLATFORM_REMOTE":
            return True, None
        snap = self.snapshot(user)
        estimated_cost = self.estimated_cost_microrub(provider, self.estimate_remote_usage(messages or [], spec or {}))
        balance_microrub = int((snap.get("balance") or {}).get("balance_microrub") or 0)
        if balance_microrub < estimated_cost:
            return False, "remote_balance_exhausted"
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
        if billing_class == "PLATFORM_REMOTE" and cost > 0:
            self.charge_balance(user_id, amount_microrub=cost, source="usage", reason=f"{source} remote usage", reference=item["id"])
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
            payment_rows = conn.execute(
                "SELECT user_id,COUNT(*) total_count,SUM(CASE WHEN status='PAID' THEN 1 ELSE 0 END) paid_count,"
                "SUM(CASE WHEN status='PAID' THEN amount_rub ELSE 0 END) paid_amount_rub,"
                "MAX(created_at) last_payment_at,MAX(CASE WHEN status='PAID' THEN updated_at ELSE NULL END) last_paid_at "
                "FROM payments GROUP BY user_id"
            ).fetchall()
            balances = conn.execute(
                "SELECT b.user_id,b.balance_microrub,u.email,u.display_name,u.role,u.status FROM billing_balances b LEFT JOIN users u ON u.id=b.user_id ORDER BY b.balance_microrub DESC, b.updated_at DESC LIMIT 100"
            ).fetchall()
            promo_codes = conn.execute("SELECT code,kind,amount_microrub,uses_total,uses_remaining,active,created_by,description,expires_at,created_at,updated_at FROM promo_codes ORDER BY updated_at DESC LIMIT 100").fetchall()
            promo_stats = conn.execute(
                "SELECT code,COUNT(*) redemption_count,COUNT(DISTINCT user_id) unique_user_count,SUM(amount_microrub) amount_microrub,MAX(redeemed_at) last_redeemed_at "
                "FROM promo_redemptions GROUP BY code"
            ).fetchall()
            promo_redemptions = conn.execute(
                "SELECT r.code,r.user_id,r.redeemed_at,r.amount_microrub,u.email,u.display_name,u.role,p.kind,p.created_by "
                "FROM promo_redemptions r "
                "LEFT JOIN users u ON u.id=r.user_id "
                "LEFT JOIN promo_codes p ON p.code=r.code "
                "ORDER BY r.redeemed_at DESC LIMIT 200"
            ).fetchall()
            topup_requests = conn.execute(
                "SELECT r.id,r.user_id,r.source,r.amount_microrub,r.note,r.payment_reference,r.status,r.reviewer_user_id,r.second_reviewer_user_id,r.reconciled_by_user_id,r.reconciled_at,r.reconciliation_note,r.review_note,r.created_at,r.reviewed_at,r.second_reviewed_at,u.email,u.display_name,u.role FROM topup_requests r LEFT JOIN users u ON u.id=r.user_id ORDER BY r.created_at DESC LIMIT 100"
            ).fetchall()
            theme_purchases = conn.execute(
                "SELECT p.id,p.user_id,p.theme_id,p.price_microrub,p.actor_user_id,p.created_at,u.email,u.display_name,u.role,a.email AS actor_email,a.display_name AS actor_display_name "
                "FROM theme_purchases p "
                "LEFT JOIN users u ON u.id=p.user_id "
                "LEFT JOIN users a ON a.id=p.actor_user_id "
                "ORDER BY p.created_at DESC LIMIT 100"
            ).fetchall()
        payment_by_user = {
            str(row["user_id"]): {
                "payments_total": int(row["total_count"] or 0),
                "payments_paid": int(row["paid_count"] or 0),
                "payments_paid_rub": round(float(row["paid_amount_rub"] or 0), 6),
                "last_payment_at": int(row["last_payment_at"]) if row["last_payment_at"] is not None else None,
                "last_paid_at": int(row["last_paid_at"]) if row["last_paid_at"] is not None else None,
            }
            for row in payment_rows
        }
        promo_stats_by_code = {
            str(row["code"]): {
                "redemption_count": int(row["redemption_count"] or 0),
                "unique_user_count": int(row["unique_user_count"] or 0),
                "amount_rub": round(int(row["amount_microrub"] or 0) / 1_000_000, 6),
                "last_redeemed_at": int(row["last_redeemed_at"]) if row["last_redeemed_at"] is not None else None,
            }
            for row in promo_stats
        }
        return {
            "plans": self.plans(),
            "payment_config": self.payment_config(),
            "usage": [{"billing_class": r["billing_class"], "provider_id": r["provider_id"], "model_id": r["model_id"], "tokens": int(r["tokens"] or 0), "estimated_cost_rub": int(r["cost"] or 0) / 1_000_000, "events": int(r["events"])} for r in usage],
            "subscriptions": [{"plan_id": r["plan_id"], "status": r["status"], "count": int(r["count"])} for r in subscriptions],
            "payments": [{"status": r["status"], "count": int(r["count"]), "amount_rub": int(r["amount_rub"] or 0)} for r in payments],
            "balances": [
                {
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "display_name": row["display_name"],
                    "role": row["role"],
                    "status": row["status"],
                    "balance_microrub": int(row["balance_microrub"] or 0),
                    "balance_rub": round(int(row["balance_microrub"] or 0) / 1_000_000, 6),
                }
                for row in balances
            ],
            "promo_codes": [
                {
                    "code": row["code"],
                    "kind": row["kind"],
                    "amount_rub": round(int(row["amount_microrub"] or 0) / 1_000_000, 6),
                    "uses_total": int(row["uses_total"] or 0),
                    "uses_remaining": int(row["uses_remaining"] or 0),
                    "active": bool(int(row["active"] or 0)),
                    "created_by": row["created_by"],
                    "description": row["description"],
                    "expires_at": row["expires_at"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "redemption_count": promo_stats_by_code.get(str(row["code"]), {}).get("redemption_count", 0),
                    "unique_user_count": promo_stats_by_code.get(str(row["code"]), {}).get("unique_user_count", 0),
                    "last_redeemed_at": promo_stats_by_code.get(str(row["code"]), {}).get("last_redeemed_at"),
                }
                for row in promo_codes
            ],
            "promo_redemptions": [
                {
                    "code": row["code"],
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "display_name": row["display_name"],
                    "role": row["role"],
                    "kind": row["kind"],
                    "created_by": row["created_by"],
                    "redeemed_at": row["redeemed_at"],
                    "amount_rub": round(int(row["amount_microrub"] or 0) / 1_000_000, 6),
                }
                for row in promo_redemptions
            ],
            "topup_requests": [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "display_name": row["display_name"],
                    "role": row["role"],
                    "source": row["source"],
                    "amount_rub": round(int(row["amount_microrub"] or 0) / 1_000_000, 6),
                    "note": row["note"],
                    "payment_reference": row["payment_reference"],
                    "status": row["status"],
                    "reviewer_user_id": row["reviewer_user_id"],
                    "second_reviewer_user_id": row["second_reviewer_user_id"],
                    "reconciled_by_user_id": row["reconciled_by_user_id"],
                    "reconciled_at": row["reconciled_at"],
                    "reconciliation_note": row["reconciliation_note"],
                    "review_note": row["review_note"],
                    "created_at": row["created_at"],
                    "reviewed_at": row["reviewed_at"],
                    "second_reviewed_at": row["second_reviewed_at"],
                }
                for row in topup_requests
            ],
            "theme_purchases": [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "display_name": row["display_name"],
                    "role": row["role"],
                    "theme_id": row["theme_id"],
                    "price_rub": round(int(row["price_microrub"] or 0) / 1_000_000, 6),
                    "actor_user_id": row["actor_user_id"],
                    "actor_email": row["actor_email"],
                    "actor_display_name": row["actor_display_name"],
                    "created_at": row["created_at"],
                }
                for row in theme_purchases
            ],
            "payment_by_user": payment_by_user,
            "period_start": start,
            "period_end": end,
        }
