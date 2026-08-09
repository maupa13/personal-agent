from __future__ import annotations

import os
import re
import sqlite3
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


def database_url() -> str:
    return os.getenv("PA_DATABASE_URL", "").strip()


def using_postgres() -> bool:
    raw = database_url()
    return raw.startswith(("postgresql://", "postgres://"))


def integrity_error_types() -> tuple[type[BaseException], ...]:
    types: list[type[BaseException]] = [sqlite3.IntegrityError]
    try:
        import psycopg
        types.append(psycopg.IntegrityError)
    except Exception:
        pass
    return tuple(types)


class DbRow(Mapping[str, Any]):
    def __init__(self, columns: list[str], values: tuple[Any, ...]):
        self._columns = columns
        self._values = values
        self._by_name = {name: values[index] for index, name in enumerate(columns)}

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(key, int):
            return self._values[key]
        return self._by_name[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._columns)

    def __len__(self) -> int:
        return len(self._columns)

    def keys(self) -> list[str]:  # sqlite3.Row compatibility
        return list(self._columns)


def _sqlite_connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def connect_app_db(db_path: Path) -> Any:
    if not using_postgres():
        return _sqlite_connect(Path(db_path))
    try:
        import psycopg
    except Exception as exc:  # pragma: no cover - depends on deployment image
        raise RuntimeError("PA_DATABASE_URL is set, but psycopg is not installed") from exc
    return PostgresConnection(psycopg.connect(database_url()))


def table_columns(conn: Any, table: str) -> set[str]:
    safe = re.sub(r"[^A-Za-z0-9_]", "", str(table))
    if not safe:
        return set()
    if isinstance(conn, PostgresConnection):
        return {
            str(row["column_name"])
            for row in conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=?",
                (safe,),
            ).fetchall()
        }
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({safe})")}


def list_tables(conn: Any) -> list[str]:
    if isinstance(conn, PostgresConnection):
        return [
            str(row["name"])
            for row in conn.execute(
                "SELECT table_name AS name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"
            ).fetchall()
        ]
    return [str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]


class PostgresCursor:
    def __init__(self, cursor: Any):
        self._cursor = cursor
        self._columns: list[str] = []
        self._prefetched: list[DbRow] = []
        self.lastrowid: int | None = None

    @property
    def rowcount(self) -> int:
        return int(self._cursor.rowcount)

    def execute(self, sql: str, params: Any = None) -> "PostgresCursor":
        translated = translate_sql(sql)
        fetch_last_id = self._should_return_last_id(translated)
        if fetch_last_id:
            translated = translated.rstrip().rstrip(";") + " RETURNING id"
        self._cursor.execute(translated, tuple(params or ()))
        self._columns = [item.name for item in (self._cursor.description or [])]
        if fetch_last_id:
            row = self._cursor.fetchone()
            if row:
                self.lastrowid = int(row[0])
            self._prefetched = []
            self._columns = []
        return self

    @staticmethod
    def _should_return_last_id(sql: str) -> bool:
        clean = sql.strip().lower()
        return clean.startswith("insert into task_events(") and " returning " not in clean

    def fetchone(self) -> DbRow | None:
        if self._prefetched:
            return self._prefetched.pop(0)
        row = self._cursor.fetchone()
        return DbRow(self._columns, tuple(row)) if row is not None else None

    def fetchall(self) -> list[DbRow]:
        rows = self._prefetched
        self._prefetched = []
        rows.extend(DbRow(self._columns, tuple(row)) for row in self._cursor.fetchall())
        return rows

    def __iter__(self) -> Iterator[DbRow]:
        while True:
            row = self.fetchone()
            if row is None:
                break
            yield row


class PostgresConnection:
    def __init__(self, conn: Any):
        self._conn = conn

    def cursor(self) -> PostgresCursor:
        return PostgresCursor(self._conn.cursor())

    def execute(self, sql: str, params: Any = None) -> PostgresCursor:
        cur = self.cursor()
        return cur.execute(sql, params)

    def executescript(self, script: str) -> None:
        for statement in split_sql_script(script):
            self.execute(statement)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "PostgresConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def split_sql_script(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    for ch in script:
        current.append(ch)
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
        elif ch in {"'", '"'}:
            quote = ch
        elif ch == ";":
            statement = "".join(current).strip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def translate_sql(sql: str) -> str:
    stripped = sql.strip()
    pragma = re.fullmatch(r"PRAGMA\s+table_info\(([^)]+)\)", stripped, flags=re.I)
    if pragma:
        table = re.sub(r"[^A-Za-z0-9_]", "", pragma.group(1))
        return (
            "SELECT ordinal_position - 1 AS cid, column_name AS name, data_type AS type, "
            "CASE WHEN is_nullable='NO' THEN 1 ELSE 0 END AS notnull, column_default AS dflt_value, 0 AS pk "
            "FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position"
        ) % ("%s",) if table == "%s" else (
            "SELECT ordinal_position - 1 AS cid, column_name AS name, data_type AS type, "
            "CASE WHEN is_nullable='NO' THEN 1 ELSE 0 END AS notnull, column_default AS dflt_value, 0 AS pk "
            f"FROM information_schema.columns WHERE table_schema='public' AND table_name='{table}' ORDER BY ordinal_position"
        )
    out = stripped
    out = re.sub(r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", "BIGSERIAL PRIMARY KEY", out, flags=re.I)
    out = re.sub(r"\s+COLLATE\s+NOCASE\b", "", out, flags=re.I)
    out = re.sub(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", out, flags=re.I)
    if re.match(r"\s*INSERT\s+INTO\b", out, flags=re.I) and " OR IGNORE " in stripped.upper() and " ON CONFLICT " not in out.upper():
        out = out.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    out = replace_qmark_params(out)
    return out


def replace_qmark_params(sql: str) -> str:
    result: list[str] = []
    quote = ""
    escaped = False
    for ch in sql:
        if quote:
            result.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in {"'", '"'}:
            quote = ch
            result.append(ch)
        elif ch == "?":
            result.append("%s")
        else:
            result.append(ch)
    return "".join(result)
