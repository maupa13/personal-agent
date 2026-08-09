from __future__ import annotations

import json
import os
import pathlib
import socket
import subprocess
import tempfile
import shutil
import os
import time
from contextlib import contextmanager
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / 'release-evidence' / '_tmp' / 'productization'
TMP_ROOT.mkdir(parents=True, exist_ok=True)
@contextmanager
def repo_tmp(prefix: str):
    td = TMP_ROOT / f"{prefix}-{os.getpid()}-{int(time.time() * 1000)}"
    td.mkdir(parents=True, exist_ok=True)
    try:
        yield td
    finally:
        shutil.rmtree(td, ignore_errors=True)

CORE_APP = ROOT / "services" / "core" / "app"

import sys
sys.path.insert(0, str(CORE_APP))

from conversation_service import ConversationError, ConversationStore  # noqa: E402
from observability_service import StructuredLogger  # noqa: E402


def check(condition: bool, test_id: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{test_id}: {message}")
    print(f"[PASS] {test_id} - {message}")


def expect_owned_failure(callable_obj, test_id: str) -> None:
    try:
        callable_obj()
    except ConversationError:
        print(f"[PASS] {test_id} - ownership boundary rejected cross-user access")
        return
    raise AssertionError(f"{test_id}: cross-user access was not rejected")


def main() -> int:
    with repo_tmp("productization") as tmp:
        root = pathlib.Path(tmp)
        db = root / "data" / "personal-agent.db"
        store = ConversationStore(db)
        store.init_schema()

        user_a = "user-a"
        user_b = "user-b"

        folder = store.create_folder(user_a, "Работа")
        folder = store.rename_folder(user_a, folder["id"], "Проект Alpha")
        check(folder["name"] == "Проект Alpha", "UX-004", "project/folder create and rename work")

        conversation = store.create(user_a, folder_id=folder["id"])
        cid = conversation["id"]
        store.add_message(user_a, cid, role="user", content="План миграции PostgreSQL")
        store.add_message(user_a, cid, role="assistant", content="Подготовлен проверяемый план")
        loaded = store.get(user_a, cid)
        check(len(loaded["messages"]) == 2 and loaded["folder_id"] == folder["id"], "CONV-005", "folder membership and messages persist")
        check(loaded["title"].startswith("План миграции"), "UX-005", "conversation receives a useful server-side title")
        moved = store.move(user_a, cid, None)
        check(moved["folder_id"] is None, "UX-004-MOVE", "conversation can move out of a project")
        store.move(user_a, cid, folder["id"])
        pinned = store.set_pinned(user_a, cid, True)
        check(bool(pinned["pinned_at"]), "UX-005-PIN", "conversation pin is persisted")
        archived = store.set_archived(user_a, cid, True)
        check(bool(archived["archived_at"]) and archived["pinned_at"] is None, "UX-005-ARCHIVE", "archiving removes pin and persists archive state")
        check(not any(item["id"] == cid for item in store.list(user_a)), "UX-005-ARCHIVE-HIDDEN", "archived conversation is excluded from normal history")
        check(any(item["id"] == cid for item in store.list(user_a, include_archived=True)), "UX-005-ARCHIVE-LIST", "archived conversation remains recoverable")
        store.set_archived(user_a, cid, False)

        hits = store.list(user_a, query="PostgreSQL")
        check(any(item["id"] == cid for item in hits), "UX-006", "server search finds message content")
        exported = store.export_all(user_a)
        check(exported["schema_version"] == 1 and exported["conversations"][0]["messages"], "CONV-007", "all-chat export is server-side and includes complete messages")

        # Re-open the same physical database to prove process-independent persistence.
        reopened = ConversationStore(db)
        reopened.init_schema()
        check(reopened.get(user_a, cid)["messages"][-1]["content"] == "Подготовлен проверяемый план", "CONV-002", "conversation survives store/process recreation")

        expect_owned_failure(lambda: reopened.get(user_b, cid), "CONV-004")
        expect_owned_failure(lambda: reopened.move(user_b, cid, None), "CONV-004-MOVE")
        expect_owned_failure(lambda: reopened.delete(user_b, cid), "CONV-004-DELETE")
        reopened.delete_folder(user_a, folder["id"])
        check(reopened.get(user_a, cid)["folder_id"] is None and not reopened.folders(user_a), "UX-004-DELETE", "deleting a project preserves its conversations")

        # Legacy browser state may be imported once, but the server becomes authoritative afterwards.
        legacy_user = "legacy-user"
        legacy = [{"title": "Старый диалог", "messages": [{"role": "user", "content": "старое сообщение"}, {"role": "assistant", "content": "старый ответ"}]}]
        result = reopened.import_legacy(legacy_user, legacy)
        second = reopened.import_legacy(legacy_user, legacy)
        check(result == {"imported": 1, "skipped": 0} and second["imported"] == 0, "CONV-001", "legacy browser history imports once into server storage")

        initial = reopened.onboarding_get(user_a, "user", 1)
        check(initial["status"] == "not_started", "ONB-001", "first user has not-started tour state")
        reopened.onboarding_set(user_a, "user", 1, "in_progress", 3)
        progress = reopened.onboarding_get(user_a, "user", 1)
        check(progress["status"] == "in_progress" and progress["current_step"] == 3, "ONB-004", "tour progress persists server-side")
        reopened.onboarding_set(user_a, "user", 1, "completed", 8)
        upgraded = reopened.onboarding_get(user_a, "user", 2)
        check(upgraded["status"] == "update_available" and upgraded["current_step"] == 0, "ONB-005", "new tour version can expose only new onboarding")
        reopened.onboarding_set(user_b, "user", 1, "skipped", 0)
        check(reopened.onboarding_get(user_b, "user", 1)["status"] == "skipped", "ONB-002", "tour can be skipped")

        log_dir = root / "logs"
        logger = StructuredLogger(log_dir, service="core", version="0.8.0-alpha.7", max_bytes=1024 * 1024, backups=2)
        logger.event("auth.test", user_id=user_a, password="never-log-me", authorization="Bearer secret", context={"api_key": "secret-key", "safe": "ok"})
        record = logger.tail(1)[0]
        check(record["password"] == "[REDACTED]" and record["authorization"] == "[REDACTED]" and record["context"]["api_key"] == "[REDACTED]", "OBS-003", "structured logger redacts secrets recursively")
        check(record["user_id"] == user_a and record["event"] == "auth.test", "OBS-001", "structured event retains correlation-friendly fields")
        logger.event("trace.test", level="ERROR", request_id="req-filter", correlation_id="corr-filter")
        filtered = logger.query(limit=10, level="ERROR", request_id="req-filter")
        check(len(filtered) == 1 and filtered[0]["correlation_id"] == "corr-filter", "OBS-001-FILTER", "structured logs support deterministic request/level filtering")

        # Rotation contract: pre-fill beyond configured threshold, then emit one event.
        logger.path.write_text("x" * (1024 * 1024 + 32), encoding="utf-8")
        logger.event("rotation.test", request_id="req-1")
        check((log_dir / "core.jsonl.1").exists() and logger.path.exists(), "OBS-004", "structured logs rotate instead of growing without bound")

    user_js = (ROOT / "services/core/app/static/app.js").read_text(encoding="utf-8")
    index = (ROOT / "services/core/app/static/index.html").read_text(encoding="utf-8")
    admin = (ROOT / "services/core/app/static/admin.html").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "services/core/app/static/manifest.webmanifest").read_text(encoding="utf-8"))

    check("localStorage.setItem(STORAGE_KEY" not in user_js and "/api/conversations" in user_js, "CONV-003-CONTRACT", "browser cannot use localStorage as canonical conversation store")
    check(all(token in index for token in ("sidebarResizer", "collapseSidebar", "newFolder", "brandHelp", "tourLayer", "modeButton")), "UX-001", "resizable/collapsible shell and guided USER tour controls ship together")
    check("key.toLowerCase()==='b'" in user_js and "key.toLowerCase()==='n'" in user_js and "key.toLowerCase()==='k'" in user_js, "UX-003", "Ctrl+B/Ctrl+N/Ctrl+K contracts are implemented")
    check("adminEntry" in index and 'id="adminEntry"' in index, "UX-007", "Admin navigation has a role-controlled UI target")
    check(all(token in admin for token in ("Логи и аудит", "Диагностика", "adminTourButton", "adminTourLayer")), "ONB-101", "Admin Console ships a separate guided tour and diagnostics surfaces")
    check(manifest.get("name") == "Родной Агент" and manifest.get("short_name") == "Родной Агент", "UX-010", "browser application identity manifest is localized and complete")
    check((ROOT / "services/core/app/static/favicon.svg").exists(), "UX-010-FAVICON", "browser favicon ships with product identity")

    # OBS-002 component proof: the real Browser worker preserves trace identity at its HTTP boundary.
    sock = socket.socket(); sock.bind(("127.0.0.1", 0)); browser_port = sock.getsockname()[1]; sock.close()
    browser_env = os.environ.copy(); browser_env.update({"PYTHONDONTWRITEBYTECODE":"1", "PA_BROWSER_HOST":"127.0.0.1", "PA_BROWSER_PORT":str(browser_port)})
    browser_proc = subprocess.Popen([sys.executable, str(ROOT / "services/browser/app/browser_worker.py")], env=browser_env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        trace_headers = {"X-Request-ID":"req-browser-component", "X-Correlation-ID":"corr-browser-component"}
        response = None
        for _ in range(80):
            try:
                request = urllib.request.Request(f"http://127.0.0.1:{browser_port}/health", headers=trace_headers)
                response = urllib.request.urlopen(request, timeout=1)
                break
            except Exception:
                time.sleep(0.05)
        check(response is not None, "OBS-002-BROWSER-READY", "real Browser worker starts for trace component test")
        response_headers = {k.lower(): v for k, v in response.headers.items()}
        response.read(); response.close()
        check(response_headers.get("x-request-id") == "req-browser-component" and response_headers.get("x-correlation-id") == "corr-browser-component", "OBS-002-BROWSER", "Browser worker preserves request/correlation IDs")
    finally:
        browser_proc.terminate()
        try: browser_proc.wait(timeout=5)
        except subprocess.TimeoutExpired: browser_proc.kill(); browser_proc.wait(timeout=5)

    print("PAR_V080_PRODUCTIZATION_ACCEPTANCE PASS: conversations folders search persistence isolation onboarding logs correlation shell admin-tour browser-identity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
