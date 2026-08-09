from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from db_compat import connect_app_db

TERMINAL_STATES = {"COMPLETED", "PARTIAL", "BLOCKED", "FAILED", "CANCELLED"}
ACTIVE_STATES = {"CREATED", "PLANNING", "QUEUED", "RUNNING", "RETRYING", "VERIFYING", "WAITING_PERMISSION", "WAITING_USER"}


def now_ts() -> int:
    return int(time.time())


class TaskError(ValueError):
    pass


class TaskStore:
    """Durable task/step/event store. Execution stays in Core so tool calls keep existing policy boundaries."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.lock = threading.RLock()

    def _db(self) -> Any:
        return connect_app_db(self.db_path)

    def init_schema(self) -> None:
        with self.lock, self._db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  task_type TEXT NOT NULL,
                  status TEXT NOT NULL,
                  phase TEXT NOT NULL DEFAULT '',
                  progress INTEGER NOT NULL DEFAULT 0,
                  title TEXT NOT NULL,
                  input_json TEXT NOT NULL,
                  result_json TEXT,
                  error TEXT,
                  cancel_requested INTEGER NOT NULL DEFAULT 0,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL,
                  started_at INTEGER,
                  finished_at INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_user_updated ON tasks(user_id,updated_at DESC);
                CREATE TABLE IF NOT EXISTS task_steps (
                  id TEXT PRIMARY KEY,
                  task_id TEXT NOT NULL,
                  step_index INTEGER NOT NULL,
                  capability TEXT NOT NULL,
                  title TEXT NOT NULL,
                  status TEXT NOT NULL,
                  input_json TEXT NOT NULL,
                  output_json TEXT,
                  error TEXT,
                  started_at INTEGER,
                  finished_at INTEGER,
                  UNIQUE(task_id,step_index),
                  FOREIGN KEY(task_id) REFERENCES tasks(id)
                );
                CREATE INDEX IF NOT EXISTS idx_task_steps_task ON task_steps(task_id,step_index);
                CREATE TABLE IF NOT EXISTS task_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  status TEXT NOT NULL,
                  phase TEXT NOT NULL,
                  progress INTEGER NOT NULL,
                  message TEXT NOT NULL,
                  data_json TEXT,
                  created_at INTEGER NOT NULL,
                  FOREIGN KEY(task_id) REFERENCES tasks(id)
                );
                CREATE INDEX IF NOT EXISTS idx_task_events_task ON task_events(task_id,id);
                """
            )
            conn.commit()

    def create(self, user_id: str, task_type: str, title: str, input_data: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
        task_id = uuid.uuid4().hex
        ts = now_ts()
        with self.lock, self._db() as conn:
            conn.execute(
                "INSERT INTO tasks(id,user_id,task_type,status,phase,progress,title,input_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (task_id, user_id, task_type, "CREATED", "created", 0, title[:180], json.dumps(input_data, ensure_ascii=False), ts, ts),
            )
            for index, step in enumerate(steps):
                conn.execute(
                    "INSERT INTO task_steps(id,task_id,step_index,capability,title,status,input_json) VALUES(?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, task_id, index, str(step["capability"]), str(step["title"])[:180], "NOT_STARTED", json.dumps(step.get("input") or {}, ensure_ascii=False)),
                )
            conn.commit()
        self.event(task_id, user_id, "task.created", "CREATED", "created", 0, "Задача создана")
        return self.get(user_id, task_id) or {}

    def get(self, user_id: str, task_id: str) -> dict[str, Any] | None:
        with self.lock, self._db() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=? AND user_id=?", (task_id, user_id)).fetchone()
            if not row:
                return None
            steps = [dict(item) for item in conn.execute("SELECT * FROM task_steps WHERE task_id=? ORDER BY step_index", (task_id,))]
        return self._serialize(dict(row), steps)

    def get_internal(self, task_id: str) -> dict[str, Any] | None:
        with self.lock, self._db() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                return None
            steps = [dict(item) for item in conn.execute("SELECT * FROM task_steps WHERE task_id=? ORDER BY step_index", (task_id,))]
        return self._serialize(dict(row), steps)

    def list(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(100, int(limit)))
        with self.lock, self._db() as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY updated_at DESC LIMIT ?", (user_id, limit))]
        return [self._serialize(row, []) for row in rows]

    @staticmethod
    def _serialize(row: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
        out = {k: row[k] for k in row if k not in {"input_json", "result_json", "cancel_requested"}}
        out["input"] = json.loads(row.get("input_json") or "{}")
        out["result"] = json.loads(row.get("result_json") or "null")
        out["cancel_requested"] = bool(row.get("cancel_requested"))
        serialized_steps = []
        for step in steps:
            serialized_steps.append({
                "id": step["id"], "index": step["step_index"], "capability": step["capability"], "title": step["title"],
                "status": step["status"], "input": json.loads(step.get("input_json") or "{}"),
                "output": json.loads(step.get("output_json") or "null"), "error": step.get("error"),
                "started_at": step.get("started_at"), "finished_at": step.get("finished_at"),
            })
        out["steps"] = serialized_steps
        return out

    def set_task(self, task_id: str, *, status: str | None = None, phase: str | None = None, progress: int | None = None,
                 result: Any = None, error: str | None = None, started: bool = False, finished: bool = False) -> None:
        fields: list[str] = ["updated_at=?"]
        values: list[Any] = [now_ts()]
        if status is not None:
            fields.append("status=?"); values.append(status)
        if phase is not None:
            fields.append("phase=?"); values.append(phase)
        if progress is not None:
            fields.append("progress=?"); values.append(max(0, min(100, int(progress))))
        if result is not None:
            fields.append("result_json=?"); values.append(json.dumps(result, ensure_ascii=False))
        if error is not None:
            fields.append("error=?"); values.append(error[:4000])
        if started:
            fields.append("started_at=COALESCE(started_at,?)"); values.append(now_ts())
        if finished:
            fields.append("finished_at=?"); values.append(now_ts())
        values.append(task_id)
        with self.lock, self._db() as conn:
            conn.execute(f"UPDATE tasks SET {','.join(fields)} WHERE id=?", values)
            conn.commit()

    def set_step(self, task_id: str, step_index: int, *, status: str, output: Any = None, error: str | None = None) -> None:
        started_at = now_ts() if status in {"STARTED", "RUNNING"} else None
        finished_at = now_ts() if status in {"COMMITTED", "VERIFIED", "FAILED", "CANCELLED"} else None
        with self.lock, self._db() as conn:
            row = conn.execute("SELECT started_at FROM task_steps WHERE task_id=? AND step_index=?", (task_id, step_index)).fetchone()
            if not row:
                raise TaskError("task step not found")
            conn.execute(
                "UPDATE task_steps SET status=?,output_json=COALESCE(?,output_json),error=?,started_at=COALESCE(started_at,?),finished_at=COALESCE(?,finished_at) WHERE task_id=? AND step_index=?",
                (status, json.dumps(output, ensure_ascii=False) if output is not None else None, error, started_at, finished_at, task_id, step_index),
            )
            conn.commit()

    def request_cancel(self, user_id: str, task_id: str) -> bool:
        with self.lock, self._db() as conn:
            cur = conn.execute("UPDATE tasks SET cancel_requested=1,updated_at=? WHERE id=? AND user_id=? AND status NOT IN ('COMPLETED','PARTIAL','BLOCKED','FAILED','CANCELLED')", (now_ts(), task_id, user_id))
            conn.commit()
            return cur.rowcount > 0

    def cancelled(self, task_id: str) -> bool:
        with self.lock, self._db() as conn:
            row = conn.execute("SELECT cancel_requested,status FROM tasks WHERE id=?", (task_id,)).fetchone()
            return bool(row and (row["cancel_requested"] or row["status"] == "CANCELLED"))

    def event(self, task_id: str, user_id: str, event_type: str, status: str, phase: str, progress: int, message: str, data: Any = None) -> int:
        with self.lock, self._db() as conn:
            cur = conn.execute(
                "INSERT INTO task_events(task_id,user_id,event_type,status,phase,progress,message,data_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (task_id, user_id, event_type, status, phase, max(0, min(100, int(progress))), message[:1000], json.dumps(data, ensure_ascii=False) if data is not None else None, now_ts()),
            )
            conn.commit()
            return int(cur.lastrowid)

    def events(self, user_id: str, task_id: str, after_id: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        with self.lock, self._db() as conn:
            rows = conn.execute(
                "SELECT id,event_type,status,phase,progress,message,data_json,created_at FROM task_events WHERE task_id=? AND user_id=? AND id>? ORDER BY id LIMIT ?",
                (task_id, user_id, max(0, int(after_id)), max(1, min(500, int(limit)))),
            )
            return [{**{k: row[k] for k in row.keys() if k != "data_json"}, "data": json.loads(row["data_json"] or "null")} for row in rows]

    def recoverable(self) -> list[str]:
        with self.lock, self._db() as conn:
            rows = conn.execute("SELECT id FROM tasks WHERE status IN ('CREATED','PLANNING','QUEUED','RUNNING','RETRYING','VERIFYING') AND cancel_requested=0 ORDER BY created_at").fetchall()
            return [str(row["id"]) for row in rows]


class TaskRuntime:
    def __init__(self, store: TaskStore, runner: Callable[[str], None]):
        self.store = store
        self.runner = runner
        self.lock = threading.RLock()
        self.threads: dict[str, threading.Thread] = {}

    def start(self, task_id: str) -> None:
        with self.lock:
            existing = self.threads.get(task_id)
            if existing and existing.is_alive():
                return
            thread = threading.Thread(target=self._run, args=(task_id,), name=f"par-task-{task_id[:8]}", daemon=True)
            self.threads[task_id] = thread
            thread.start()

    def _run(self, task_id: str) -> None:
        try:
            self.runner(task_id)
        finally:
            with self.lock:
                self.threads.pop(task_id, None)

    def resume_recoverable(self) -> None:
        for task_id in self.store.recoverable():
            self.start(task_id)
