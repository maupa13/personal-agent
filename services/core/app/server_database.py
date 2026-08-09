from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


class ServerDatabaseError(Exception):
    pass


@dataclass(frozen=True)
class DatabaseTarget:
    kind: str
    dsn: str
    host: str = ""
    port: int = 0
    database: str = ""


def resolve_database_target() -> DatabaseTarget:
    """Resolve server DB configuration without opening a connection.

    Local profile remains SQLite. Server/VPS profile uses PostgreSQL when PA_DATABASE_URL is set.
    Secrets are never returned by this object.
    """
    raw = os.getenv("PA_DATABASE_URL", "").strip()
    if not raw:
        return DatabaseTarget(kind="sqlite", dsn="")
    parsed = urlparse(raw)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ServerDatabaseError("PA_DATABASE_URL must use postgresql://")
    if not parsed.hostname or not parsed.path.strip("/"):
        raise ServerDatabaseError("PA_DATABASE_URL requires host and database")
    return DatabaseTarget(
        kind="postgresql",
        dsn="configured",
        host=parsed.hostname,
        port=int(parsed.port or 5432),
        database=parsed.path.strip("/")[:128],
    )


def postgres_driver_available() -> bool:
    try:
        import psycopg  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def validate_server_database_config() -> dict[str, Any]:
    target = resolve_database_target()
    if target.kind == "sqlite":
        return {"kind": "sqlite", "configured": False, "driver_available": False}
    return {
        "kind": target.kind,
        "configured": True,
        "driver_available": postgres_driver_available(),
        "host": target.host,
        "port": target.port,
        "database": target.database,
    }
