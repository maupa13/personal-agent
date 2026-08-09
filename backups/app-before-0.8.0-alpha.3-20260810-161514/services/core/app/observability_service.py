from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any


class StructuredLogger:
    _SENSITIVE_KEYS = {"password", "token", "token_hash", "api_key", "secret", "authorization", "cookie", "content"}

    @classmethod
    def _sensitive_key(cls, key: Any) -> bool:
        normalized = str(key).strip().lower().replace("-", "_")
        return normalized in cls._SENSITIVE_KEYS or normalized.endswith("_secret") or normalized.endswith("_token") or normalized.endswith("_password") or normalized.endswith("_api_key")

    def __init__(self, root: Path, *, service: str, version: str, max_bytes: int = 20 * 1024 * 1024, backups: int = 10):
        self.root = Path(root)
        self.service = service
        self.version = version
        self.max_bytes = max(1024 * 1024, int(max_bytes))
        self.backups = max(1, int(backups))
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / f"{service}.jsonl"

    def _rotate(self) -> None:
        try:
            if not self.path.exists() or self.path.stat().st_size < self.max_bytes:
                return
            oldest = self.root / f"{self.service}.jsonl.{self.backups}"
            oldest.unlink(missing_ok=True)
            for i in range(self.backups - 1, 0, -1):
                src = self.root / f"{self.service}.jsonl.{i}"
                dst = self.root / f"{self.service}.jsonl.{i+1}"
                if src.exists():
                    src.replace(dst)
            self.path.replace(self.root / f"{self.service}.jsonl.1")
        except OSError:
            pass

    @staticmethod
    def _safe(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            return value[:2000]
        if isinstance(value, dict):
            return {str(k): "[REDACTED]" if StructuredLogger._sensitive_key(k) else StructuredLogger._safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [StructuredLogger._safe(v) for v in value[:50]]
        return str(value)[:1000]

    def event(self, event: str, *, level: str = "INFO", **fields: Any) -> None:
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "epoch_ms": int(time.time() * 1000),
            "level": str(level).upper(),
            "service": self.service,
            "version": self.version,
            "event": str(event)[:120],
        }
        for key, value in fields.items():
            record[str(key)] = "[REDACTED]" if self._sensitive_key(key) else self._safe(value)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            self._rotate()
            try:
                with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write(line)
            except OSError:
                pass
        print(line.rstrip(), flush=True)

    def tail(self, limit: int = 200) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 5000))
        try:
            lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
        except OSError:
            return []
        result: list[dict[str, Any]] = []
        for line in lines:
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    result.append(value)
            except Exception:
                continue
        return result

    def query(self, *, limit: int = 200, level: str = "", event: str = "", request_id: str = "", correlation_id: str = "") -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 1000))
        filters = {
            "level": str(level or "").strip().upper(),
            "event": str(event or "").strip().lower(),
            "request_id": str(request_id or "").strip(),
            "correlation_id": str(correlation_id or "").strip(),
        }
        scan = self.tail(min(5000, max(1000, limit * 10)))
        result: list[dict[str, Any]] = []
        for record in reversed(scan):
            if filters["level"] and str(record.get("level", "")).upper() != filters["level"]:
                continue
            if filters["event"] and filters["event"] not in str(record.get("event", "")).lower():
                continue
            if filters["request_id"] and str(record.get("request_id", "")) != filters["request_id"]:
                continue
            if filters["correlation_id"] and str(record.get("correlation_id", "")) != filters["correlation_id"]:
                continue
            result.append(record)
            if len(result) >= limit:
                break
        result.reverse()
        return result
