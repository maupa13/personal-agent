from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class ConversationError(Exception):
    pass


class ConversationStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._lock = threading.RLock()

    def _db(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    def init_schema(self) -> None:
        with self._lock, self._db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS folders (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  name TEXT NOT NULL,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_folders_user_updated
                  ON folders(user_id, updated_at DESC);

                CREATE TABLE IF NOT EXISTS conversations (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  folder_id TEXT,
                  title TEXT NOT NULL,
                  custom_title INTEGER NOT NULL DEFAULT 0,
                  pinned_at INTEGER,
                  archived_at INTEGER,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
                  ON conversations(user_id, archived_at, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_conversations_folder
                  ON conversations(user_id, folder_id, updated_at DESC);

                CREATE TABLE IF NOT EXISTS messages (
                  id TEXT PRIMARY KEY,
                  conversation_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  kind TEXT NOT NULL DEFAULT 'message',
                  sources_json TEXT NOT NULL DEFAULT '[]',
                  attachments_json TEXT NOT NULL DEFAULT '[]',
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL,
                  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                );
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
                  ON messages(user_id, conversation_id, created_at ASC);

                CREATE TABLE IF NOT EXISTS user_onboarding (
                  user_id TEXT NOT NULL,
                  tour_id TEXT NOT NULL,
                  tour_version INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  current_step INTEGER NOT NULL DEFAULT 0,
                  completed_at INTEGER,
                  updated_at INTEGER NOT NULL,
                  PRIMARY KEY(user_id, tour_id)
                );
                """
            )
            conn.commit()

    @staticmethod
    def _clean_title(value: str) -> str:
        clean = " ".join(str(value or "").split()).strip()[:100]
        return clean or "Новый чат"

    @staticmethod
    def title_from_text(text: str) -> str:
        clean = " ".join(str(text or "").split()).strip()
        if not clean:
            return "Новый чат"
        return clean[:56] + ("…" if len(clean) > 56 else "")

    def _owned_conversation(self, conn: sqlite3.Connection, user_id: str, conversation_id: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id=? AND user_id=?",
            (conversation_id, user_id),
        ).fetchone()
        if not row:
            raise ConversationError("conversation not found")
        return row

    def create(self, user_id: str, *, title: str = "Новый чат", folder_id: str | None = None) -> dict[str, Any]:
        ts = self._now_ms()
        cid = uuid.uuid4().hex
        with self._lock, self._db() as conn:
            if folder_id:
                folder = conn.execute("SELECT id FROM folders WHERE id=? AND user_id=?", (folder_id, user_id)).fetchone()
                if not folder:
                    raise ConversationError("folder not found")
            conn.execute(
                "INSERT INTO conversations(id,user_id,folder_id,title,custom_title,created_at,updated_at) VALUES(?,?,?,?,0,?,?)",
                (cid, user_id, folder_id, self._clean_title(title), ts, ts),
            )
            conn.commit()
        return self.get(user_id, cid)

    def list(self, user_id: str, *, query: str = "", include_archived: bool = False, limit: int = 200) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        params: list[Any] = [user_id]
        where = ["c.user_id=?"]
        if not include_archived:
            where.append("c.archived_at IS NULL")
        q = " ".join(str(query or "").split()).strip()
        if q:
            like = f"%{q}%"
            where.append("(c.title LIKE ? OR EXISTS (SELECT 1 FROM messages m WHERE m.conversation_id=c.id AND m.user_id=c.user_id AND m.content LIKE ?))")
            params.extend([like, like])
        params.append(limit)
        sql = f"""
            SELECT c.id,c.folder_id,c.title,c.custom_title,c.pinned_at,c.archived_at,c.created_at,c.updated_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id=c.id AND m.user_id=c.user_id) AS message_count,
                   (SELECT substr(m.content,1,180) FROM messages m WHERE m.conversation_id=c.id AND m.user_id=c.user_id ORDER BY m.created_at DESC LIMIT 1) AS preview
            FROM conversations c
            WHERE {' AND '.join(where)}
            ORDER BY (c.pinned_at IS NOT NULL) DESC,c.pinned_at DESC,c.updated_at DESC
            LIMIT ?
        """
        with self._lock, self._db() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def export_all(self, user_id: str, *, limit: int = 500) -> dict[str, Any]:
        limit = max(1, min(int(limit), 500))
        with self._lock, self._db() as conn:
            conversations = [dict(row) for row in conn.execute(
                "SELECT * FROM conversations WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()]
            ids = [item["id"] for item in conversations]
            messages_by_conversation: dict[str, list[dict[str, Any]]] = {cid: [] for cid in ids}
            if ids:
                placeholders = ",".join("?" for _ in ids)
                rows = conn.execute(
                    f"SELECT id,conversation_id,role,content,kind,sources_json,attachments_json,created_at,updated_at FROM messages WHERE user_id=? AND conversation_id IN ({placeholders}) ORDER BY created_at ASC,id ASC",
                    [user_id, *ids],
                ).fetchall()
                for row in rows:
                    item = dict(row)
                    cid = item.pop("conversation_id")
                    try:
                        item["sources"] = json.loads(item.pop("sources_json") or "[]")
                    except Exception:
                        item["sources"] = []
                    try:
                        item["attachments"] = json.loads(item.pop("attachments_json") or "[]")
                    except Exception:
                        item["attachments"] = []
                    messages_by_conversation.setdefault(cid, []).append(item)
            for conversation in conversations:
                conversation["messages"] = messages_by_conversation.get(conversation["id"], [])
            folders = [dict(row) for row in conn.execute(
                "SELECT id,name,created_at,updated_at FROM folders WHERE user_id=? ORDER BY name COLLATE NOCASE",
                (user_id,),
            ).fetchall()]
        return {"schema_version": 1, "folders": folders, "conversations": conversations}

    def get(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        with self._lock, self._db() as conn:
            row = self._owned_conversation(conn, user_id, conversation_id)
            messages = []
            for m in conn.execute(
                "SELECT id,role,content,kind,sources_json,attachments_json,created_at,updated_at FROM messages WHERE conversation_id=? AND user_id=? ORDER BY created_at ASC,id ASC",
                (conversation_id, user_id),
            ):
                item = dict(m)
                try:
                    item["sources"] = json.loads(item.pop("sources_json") or "[]")
                except Exception:
                    item["sources"] = []
                try:
                    item["attachments"] = json.loads(item.pop("attachments_json") or "[]")
                except Exception:
                    item["attachments"] = []
                messages.append(item)
            result = dict(row)
            result["messages"] = messages
            return result

    def add_message(
        self,
        user_id: str,
        conversation_id: str,
        *,
        role: str,
        content: str,
        kind: str = "message",
        sources: list[dict[str, Any]] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        role = str(role).lower().strip()
        if role not in {"user", "assistant"}:
            raise ConversationError("invalid message role")
        content = str(content or "")[:100_000]
        if not content.strip() and not attachments:
            raise ConversationError("message content is empty")
        ts = self._now_ms()
        mid = message_id or uuid.uuid4().hex
        sources = list(sources or [])[:20]
        attachments = list(attachments or [])[:20]
        with self._lock, self._db() as conn:
            conversation = self._owned_conversation(conn, user_id, conversation_id)
            conn.execute(
                "INSERT INTO messages(id,conversation_id,user_id,role,content,kind,sources_json,attachments_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (mid, conversation_id, user_id, role, content, str(kind or "message")[:40], json.dumps(sources, ensure_ascii=False), json.dumps(attachments, ensure_ascii=False), ts, ts),
            )
            if role == "user" and not int(conversation["custom_title"] or 0) and conversation["title"] == "Новый чат":
                conn.execute("UPDATE conversations SET title=?,updated_at=? WHERE id=? AND user_id=?", (self.title_from_text(content), ts, conversation_id, user_id))
            else:
                conn.execute("UPDATE conversations SET updated_at=? WHERE id=? AND user_id=?", (ts, conversation_id, user_id))
            conn.commit()
        return {"id": mid, "role": role, "content": content, "kind": kind, "sources": sources, "attachments": attachments, "created_at": ts, "updated_at": ts}

    def rename(self, user_id: str, conversation_id: str, title: str) -> dict[str, Any]:
        ts = self._now_ms()
        with self._lock, self._db() as conn:
            self._owned_conversation(conn, user_id, conversation_id)
            conn.execute("UPDATE conversations SET title=?,custom_title=1,updated_at=? WHERE id=? AND user_id=?", (self._clean_title(title), ts, conversation_id, user_id))
            conn.commit()
        return self.get(user_id, conversation_id)

    def clear(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        ts = self._now_ms()
        with self._lock, self._db() as conn:
            self._owned_conversation(conn, user_id, conversation_id)
            conn.execute("DELETE FROM messages WHERE conversation_id=? AND user_id=?", (conversation_id, user_id))
            conn.execute("UPDATE conversations SET title='Новый чат',custom_title=0,updated_at=? WHERE id=? AND user_id=?", (ts, conversation_id, user_id))
            conn.commit()
        return self.get(user_id, conversation_id)

    def delete(self, user_id: str, conversation_id: str) -> None:
        with self._lock, self._db() as conn:
            self._owned_conversation(conn, user_id, conversation_id)
            conn.execute("DELETE FROM messages WHERE conversation_id=? AND user_id=?", (conversation_id, user_id))
            conn.execute("DELETE FROM conversations WHERE id=? AND user_id=?", (conversation_id, user_id))
            conn.commit()

    def move(self, user_id: str, conversation_id: str, folder_id: str | None) -> dict[str, Any]:
        ts = self._now_ms()
        with self._lock, self._db() as conn:
            self._owned_conversation(conn, user_id, conversation_id)
            if folder_id:
                folder = conn.execute("SELECT id FROM folders WHERE id=? AND user_id=?", (folder_id, user_id)).fetchone()
                if not folder:
                    raise ConversationError("folder not found")
            conn.execute("UPDATE conversations SET folder_id=?,updated_at=? WHERE id=? AND user_id=?", (folder_id, ts, conversation_id, user_id))
            conn.commit()
        return self.get(user_id, conversation_id)

    def set_pinned(self, user_id: str, conversation_id: str, pinned: bool) -> dict[str, Any]:
        ts = self._now_ms()
        with self._lock, self._db() as conn:
            self._owned_conversation(conn, user_id, conversation_id)
            conn.execute("UPDATE conversations SET pinned_at=? WHERE id=? AND user_id=?", (ts if pinned else None, conversation_id, user_id))
            conn.commit()
        return self.get(user_id, conversation_id)

    def set_archived(self, user_id: str, conversation_id: str, archived: bool) -> dict[str, Any]:
        ts = self._now_ms()
        with self._lock, self._db() as conn:
            self._owned_conversation(conn, user_id, conversation_id)
            conn.execute(
                "UPDATE conversations SET archived_at=?,pinned_at=CASE WHEN ? THEN NULL ELSE pinned_at END,updated_at=? WHERE id=? AND user_id=?",
                (ts if archived else None, 1 if archived else 0, ts, conversation_id, user_id),
            )
            conn.commit()
        return self.get(user_id, conversation_id)

    def folders(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock, self._db() as conn:
            rows = conn.execute(
                "SELECT f.id,f.name,f.created_at,f.updated_at,(SELECT COUNT(*) FROM conversations c WHERE c.user_id=f.user_id AND c.folder_id=f.id AND c.archived_at IS NULL) AS conversation_count FROM folders f WHERE f.user_id=? ORDER BY f.name COLLATE NOCASE",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def create_folder(self, user_id: str, name: str) -> dict[str, Any]:
        clean = self._clean_title(name)
        ts = self._now_ms()
        fid = uuid.uuid4().hex
        with self._lock, self._db() as conn:
            conn.execute("INSERT INTO folders(id,user_id,name,created_at,updated_at) VALUES(?,?,?,?,?)", (fid, user_id, clean, ts, ts))
            conn.commit()
        return {"id": fid, "name": clean, "created_at": ts, "updated_at": ts, "conversation_count": 0}

    def rename_folder(self, user_id: str, folder_id: str, name: str) -> dict[str, Any]:
        clean = self._clean_title(name)
        ts = self._now_ms()
        with self._lock, self._db() as conn:
            row = conn.execute("SELECT id FROM folders WHERE id=? AND user_id=?", (folder_id, user_id)).fetchone()
            if not row:
                raise ConversationError("folder not found")
            conn.execute("UPDATE folders SET name=?,updated_at=? WHERE id=? AND user_id=?", (clean, ts, folder_id, user_id))
            conn.commit()
        return next(folder for folder in self.folders(user_id) if folder["id"] == folder_id)

    def delete_folder(self, user_id: str, folder_id: str) -> None:
        with self._lock, self._db() as conn:
            row = conn.execute("SELECT id FROM folders WHERE id=? AND user_id=?", (folder_id, user_id)).fetchone()
            if not row:
                raise ConversationError("folder not found")
            conn.execute("UPDATE conversations SET folder_id=NULL WHERE user_id=? AND folder_id=?", (user_id, folder_id))
            conn.execute("DELETE FROM folders WHERE id=? AND user_id=?", (folder_id, user_id))
            conn.commit()

    def import_legacy(self, user_id: str, conversations: list[dict[str, Any]]) -> dict[str, int]:
        imported = 0
        skipped = 0
        if not isinstance(conversations, list):
            raise ConversationError("conversations array required")
        with self._lock, self._db() as conn:
            existing = int(conn.execute("SELECT COUNT(*) FROM conversations WHERE user_id=?", (user_id,)).fetchone()[0])
        if existing:
            return {"imported": 0, "skipped": len(conversations)}
        for raw in conversations[:100]:
            try:
                conv = self.create(user_id, title=self._clean_title(raw.get("title", "Новый чат")))
                for msg in list(raw.get("messages") or [])[-200:]:
                    role = "assistant" if msg.get("role") == "assistant" else "user"
                    self.add_message(user_id, conv["id"], role=role, content=str(msg.get("content", "")), kind=str(msg.get("kind", "message")), sources=list(msg.get("sources") or []), attachments=list(msg.get("attachments") or []))
                imported += 1
            except Exception:
                skipped += 1
        return {"imported": imported, "skipped": skipped}

    def onboarding_get(self, user_id: str, tour_id: str, tour_version: int) -> dict[str, Any]:
        with self._lock, self._db() as conn:
            row = conn.execute("SELECT * FROM user_onboarding WHERE user_id=? AND tour_id=?", (user_id, tour_id)).fetchone()
        if not row:
            return {"tour_id": tour_id, "tour_version": tour_version, "status": "not_started", "current_step": 0, "completed_at": None}
        result = dict(row)
        if int(result.get("tour_version") or 0) < int(tour_version) and result.get("status") == "completed":
            result["status"] = "update_available"
            result["current_step"] = 0
        return result

    def onboarding_set(self, user_id: str, tour_id: str, tour_version: int, status: str, current_step: int = 0) -> dict[str, Any]:
        if status not in {"in_progress", "completed", "skipped"}:
            raise ConversationError("invalid onboarding status")
        ts = self._now_ms()
        completed_at = ts if status in {"completed", "skipped"} else None
        with self._lock, self._db() as conn:
            conn.execute(
                "INSERT INTO user_onboarding(user_id,tour_id,tour_version,status,current_step,completed_at,updated_at) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(user_id,tour_id) DO UPDATE SET tour_version=excluded.tour_version,status=excluded.status,current_step=excluded.current_step,completed_at=excluded.completed_at,updated_at=excluded.updated_at",
                (user_id, tour_id, int(tour_version), status, max(0, int(current_step)), completed_at, ts),
            )
            conn.commit()
        return self.onboarding_get(user_id, tour_id, tour_version)
