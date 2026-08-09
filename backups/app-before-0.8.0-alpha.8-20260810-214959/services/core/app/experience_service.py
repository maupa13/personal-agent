from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class ExperienceError(Exception):
    pass


DEFAULT_PREFERENCES: dict[str, Any] = {
    "ui_language": "ru",
    "response_language": "auto",
    "theme": "system",
    "execution_policy": "auto",
    "tone": "normal",
    "ui_scale": "normal",
}

UI_LANGUAGES = {"ru", "en"}
RESPONSE_LANGUAGES = {"auto", "ru", "en"}
THEMES = {"system", "dark", "light"}
EXECUTION_POLICIES = {"auto", "local_only", "prefer_local", "remote_allowed", "remote_only"}
TONES = {"normal", "friendly", "ironic", "meme", "serious", "expert", "brief", "detailed"}
UI_SCALES = {"compact", "normal", "large"}
FEEDBACK_CATEGORIES = {"idea", "bug", "quality", "ux", "other"}


class ExperienceService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.lock = threading.RLock()

    def _db(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.lock, self._db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS user_experience_preferences (
                  user_id TEXT PRIMARY KEY,
                  ui_language TEXT NOT NULL DEFAULT 'ru',
                  response_language TEXT NOT NULL DEFAULT 'auto',
                  theme TEXT NOT NULL DEFAULT 'system',
                  execution_policy TEXT NOT NULL DEFAULT 'auto',
                  tone TEXT NOT NULL DEFAULT 'normal',
                  ui_scale TEXT NOT NULL DEFAULT 'normal',
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS feedback (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  category TEXT NOT NULL,
                  rating INTEGER,
                  message TEXT NOT NULL,
                  page TEXT NOT NULL DEFAULT '',
                  status TEXT NOT NULL DEFAULT 'new',
                  created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status,created_at DESC);
                CREATE TABLE IF NOT EXISTS conversation_shares (
                  id TEXT PRIMARY KEY,
                  share_token_hash TEXT UNIQUE NOT NULL,
                  user_id TEXT NOT NULL,
                  conversation_id TEXT NOT NULL,
                  title TEXT NOT NULL,
                  content_md TEXT NOT NULL,
                  created_at INTEGER NOT NULL,
                  expires_at INTEGER NOT NULL,
                  revoked_at INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_shares_user_created ON conversation_shares(user_id,created_at DESC);
                """
            )
            columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(user_experience_preferences)").fetchall()}
            if "ui_scale" not in columns:
                conn.execute("ALTER TABLE user_experience_preferences ADD COLUMN ui_scale TEXT NOT NULL DEFAULT 'normal'")
            conn.commit()

    @staticmethod
    def _validate(raw: dict[str, Any]) -> dict[str, Any]:
        value = dict(DEFAULT_PREFERENCES)
        value.update({k: raw[k] for k in DEFAULT_PREFERENCES if k in raw})
        value["ui_language"] = str(value["ui_language"]).strip().lower()
        value["response_language"] = str(value["response_language"]).strip().lower()
        value["theme"] = str(value["theme"]).strip().lower()
        value["execution_policy"] = str(value["execution_policy"]).strip().lower()
        value["tone"] = str(value["tone"]).strip().lower()
        value["ui_scale"] = str(value["ui_scale"]).strip().lower()
        if value["ui_language"] not in UI_LANGUAGES:
            raise ExperienceError("unsupported UI language")
        if value["response_language"] not in RESPONSE_LANGUAGES:
            raise ExperienceError("unsupported response language")
        if value["theme"] not in THEMES:
            raise ExperienceError("unsupported theme")
        if value["execution_policy"] not in EXECUTION_POLICIES:
            raise ExperienceError("unsupported execution policy")
        if value["tone"] not in TONES:
            raise ExperienceError("unsupported tone")
        if value["ui_scale"] not in UI_SCALES:
            raise ExperienceError("unsupported UI scale")
        return value

    def preferences(self, user_id: str) -> dict[str, Any]:
        with self.lock, self._db() as conn:
            row = conn.execute(
                "SELECT ui_language,response_language,theme,execution_policy,tone,ui_scale,updated_at FROM user_experience_preferences WHERE user_id=?",
                (user_id,),
            ).fetchone()
        return self._validate(dict(row) if row else DEFAULT_PREFERENCES) | {"updated_at": int(row["updated_at"]) if row else 0}

    def set_preferences(self, user_id: str, body: dict[str, Any]) -> dict[str, Any]:
        current = self.preferences(user_id)
        cleaned = self._validate(current | {k: body[k] for k in DEFAULT_PREFERENCES if k in body})
        ts = int(time.time())
        with self.lock, self._db() as conn:
            conn.execute(
                "INSERT INTO user_experience_preferences(user_id,ui_language,response_language,theme,execution_policy,tone,ui_scale,updated_at) VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET ui_language=excluded.ui_language,response_language=excluded.response_language,theme=excluded.theme,execution_policy=excluded.execution_policy,tone=excluded.tone,ui_scale=excluded.ui_scale,updated_at=excluded.updated_at",
                (user_id, cleaned["ui_language"], cleaned["response_language"], cleaned["theme"], cleaned["execution_policy"], cleaned["tone"], cleaned["ui_scale"], ts),
            )
            conn.commit()
        return cleaned | {"updated_at": ts}

    def add_feedback(self, user_id: str, body: dict[str, Any]) -> dict[str, Any]:
        category = str(body.get("category") or "other").strip().lower()
        if category not in FEEDBACK_CATEGORIES:
            raise ExperienceError("unsupported feedback category")
        message = " ".join(str(body.get("message") or "").split()).strip()
        if not 3 <= len(message) <= 4000:
            raise ExperienceError("feedback message must contain 3-4000 characters")
        rating_raw = body.get("rating")
        rating = None if rating_raw in (None, "") else int(rating_raw)
        if rating is not None and rating not in {1, 2, 3, 4, 5}:
            raise ExperienceError("feedback rating must be 1-5")
        page = str(body.get("page") or "").strip()[:300]
        item = {"id": secrets.token_hex(16), "user_id": user_id, "category": category, "rating": rating, "message": message, "page": page, "status": "new", "created_at": int(time.time())}
        with self.lock, self._db() as conn:
            conn.execute(
                "INSERT INTO feedback(id,user_id,category,rating,message,page,status,created_at) VALUES(:id,:user_id,:category,:rating,:message,:page,:status,:created_at)",
                item,
            )
            conn.commit()
        return {k: item[k] for k in ("id", "category", "rating", "status", "created_at")}

    def feedback_list(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self.lock, self._db() as conn:
            rows = conn.execute(
                "SELECT id,user_id,category,rating,message,page,status,created_at FROM feedback ORDER BY created_at DESC LIMIT ?",
                (max(1, min(int(limit), 500)),),
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_share(self, user_id: str, conversation_id: str, title: str, content_md: str, *, ttl_seconds: int = 7 * 24 * 60 * 60) -> dict[str, Any]:
        content_md = str(content_md or "")
        if not content_md.strip() or len(content_md.encode("utf-8")) > 2 * 1024 * 1024:
            raise ExperienceError("conversation share is empty or too large")
        ttl_seconds = max(600, min(int(ttl_seconds), 30 * 24 * 60 * 60))
        token = secrets.token_urlsafe(24)
        item_id = secrets.token_hex(16)
        ts = int(time.time())
        expires = ts + ttl_seconds
        with self.lock, self._db() as conn:
            conn.execute(
                "INSERT INTO conversation_shares(id,share_token_hash,user_id,conversation_id,title,content_md,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                (item_id, self._token_hash(token), user_id, conversation_id, str(title or "Диалог")[:120], content_md, ts, expires),
            )
            conn.commit()
        return {"id": item_id, "token": token, "title": str(title or "Диалог")[:120], "created_at": ts, "expires_at": expires}

    def get_share(self, token: str) -> dict[str, Any] | None:
        if not token or len(token) > 256:
            return None
        now = int(time.time())
        with self.lock, self._db() as conn:
            row = conn.execute(
                "SELECT id,title,content_md,created_at,expires_at,revoked_at FROM conversation_shares WHERE share_token_hash=?",
                (self._token_hash(token),),
            ).fetchone()
        if not row or row["revoked_at"] is not None or int(row["expires_at"]) <= now:
            return None
        return dict(row)

    def revoke_share(self, user_id: str, share_id: str) -> bool:
        with self.lock, self._db() as conn:
            cur = conn.execute(
                "UPDATE conversation_shares SET revoked_at=? WHERE id=? AND user_id=? AND revoked_at IS NULL",
                (int(time.time()), share_id, user_id),
            )
            conn.commit()
            return cur.rowcount > 0
