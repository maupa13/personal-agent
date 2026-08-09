from __future__ import annotations

import io
import json
import os
import pathlib
import shutil
import sys
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "core" / "app"))
from orchestrator_service import TaskStore
from deployment_service import (
    bootstrap_runtime,
    deploy,
    host_key_sha256,
    preflight,
    public_hot_verify,
    resolve_remote_root,
    rollback,
    server_bundle,
    add_core_to_bundle,
)


class FakeSession:
    def __init__(self, memory=2048):
        self.commands = []
        self.uploads = {}
        self.memory = memory

    def run(self, command, timeout=120):
        self.commands.append(command)
        if "uname -srm" in command:
            return 0, "Linux 6.8 x86_64\n", ""
        if "docker --version" in command:
            return 0, "Docker version 29.6.2\n", ""
        if "docker compose version" in command:
            return 0, "Docker Compose version v5.3.1\n", ""
        if "MemTotal" in command:
            return 0, str(self.memory) + "\n", ""
        if "df -Pk" in command:
            return 0, str(20 * 1024 * 1024) + "\n", ""
        if "id -un" in command:
            return 0, "deploy\n", ""
        if "$(id -u)" in command:
            return 0, "1000\n/home/deploy\n", ""
        return 0, "ok\n", ""

    def put_bytes(self, path, data):
        self.uploads[path] = data

    def close(self):
        pass


def main() -> int:
    tmp = ROOT / "release-evidence" / "_tmp" / "par-task-store"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        store = TaskStore(tmp / "state.db")
        store.init_schema()
        task = store.create(
            "u1",
            "research_report",
            "Test",
            {"question": "q", "formats": ["md"]},
            [{"capability": "web.research", "title": "web"}, {"capability": "artifact.verify", "title": "verify"}],
        )
        assert task["status"] == "CREATED" and len(task["steps"]) == 2
        store.set_task(task["id"], status="RUNNING", phase="web", progress=20, started=True)
        store.set_step(task["id"], 0, status="STARTED")
        store.set_step(task["id"], 0, status="VERIFIED", output={"sources": 2})
        store.event(task["id"], "u1", "task.progress", "RUNNING", "web", 20, "Ищу")
        events = store.events("u1", task["id"])
        assert [e["id"] for e in events] == sorted(e["id"] for e in events) and len(events) >= 2
        assert task["id"] in store.recoverable()
        assert store.request_cancel("u2", task["id"]) is False
        assert store.request_cancel("u1", task["id"]) is True and store.cancelled(task["id"]) is True
        assert store.get("u2", task["id"]) is None

        bundle = server_bundle("0.8.0-alpha.7", "server-lite", "agent.example.test", "ADMIN_TOKEN_TEST")
        full = add_core_to_bundle(bundle, ROOT / "services" / "core")
        with tarfile.open(fileobj=io.BytesIO(full), mode="r:gz") as tf:
            names = set(tf.getnames())
            assert {"docker-compose-main.yaml", ".env.server", "Caddyfile", "core/app/main.py", "core/Dockerfile"} <= names
            compose = tf.extractfile("docker-compose-main.yaml").read().decode()
            env = tf.extractfile(".env.server").read().decode()
            caddy = tf.extractfile("Caddyfile").read().decode()
            assert "caddy:2.11.2" in compose and "ollama:" not in compose and "code-worker:" not in compose and "browser:" not in compose
            assert "agent.example.test" in caddy and "reverse_proxy core:8080" in caddy
            assert "ADMIN_TOKEN_TEST" in env

        session = FakeSession(memory=2048)
        pf = preflight(session)
        assert pf["ok"] is True and pf["recommended_profile"] == "server-lite" and pf["memory_mb"] == 2048
        session2 = FakeSession(memory=8192)
        assert preflight(session2)["recommended_profile"] == "server-standard"
        assert resolve_remote_root(session) == "/home/deploy/.local/share/personal-agent"

        class RootBootstrapSession(FakeSession):
            def run(self, command, timeout=120):
                self.commands.append(command)
                if command == "id -u":
                    return 0, "0\n", ""
                if "cat /etc/os-release" in command:
                    return 0, "ID=ubuntu\nID_LIKE=debian\n", ""
                return 0, "ok\n", ""

        bootstrap_session = RootBootstrapSession()
        bootstrap = bootstrap_runtime(bootstrap_session)
        assert bootstrap["ok"] and bootstrap["docker"] and bootstrap["compose"]
        bootstrap_commands = "\n".join(bootstrap_session.commands)
        assert "apt-get install" in bootstrap_commands and "curl" not in bootstrap_commands and "get.docker.com" not in bootstrap_commands

        result = deploy(session, full, "0.8.0-alpha.7")
        assert result["hot_verify"] == "PASS" and len(session.uploads) == 1
        joined = "\n".join(session.commands)
        assert "ln -sfn" in joined and " current" in joined and "previous" in joined and "docker compose" in joined and "/api/health" in joined
        for forbidden in ("down -v", "volume prune", "system prune"):
            assert forbidden not in joined.lower()
        rb = rollback(session)
        assert rb["status"] == "ROLLED_BACK"
        joined = "\n".join(session.commands)
        assert "readlink -f previous" in joined

        fp = host_key_sha256(b"test-host-key")
        assert fp.startswith("SHA256:") and len(fp) > 20

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps({"product": "Personal Agent Rus", "version": "0.8.0-alpha.7"}).encode()

        verify = public_hot_verify("agent.example.test", "0.8.0-alpha.7", timeout_seconds=5, opener=lambda *_a, **_k: FakeResponse())
        assert verify["ok"] and verify["https"] and verify["url"] == "https://agent.example.test/api/system"

        import importlib
        import types

        os.environ.setdefault("PA_DB", str(tmp / "main.db"))
        os.environ.setdefault("PA_WORKSPACE_ROOT", str(tmp / "workspaces"))
        os.environ.setdefault("PA_SECRETS_DIR", str(tmp / "secrets"))
        os.environ.setdefault("PA_LOG_DIR", str(tmp / "logs"))
        os.environ.setdefault("PA_TEST_MODE", "1")

        def install_stub(name, **attrs):
            module = types.ModuleType(name)
            for key, value in attrs.items():
                setattr(module, key, value)
            sys.modules.setdefault(name, module)

        install_stub("docx", Document=type("Document", (), {}))
        install_stub("openpyxl", Workbook=type("Workbook", (), {}), load_workbook=lambda *args, **kwargs: object())
        install_stub("pptx", Presentation=type("Presentation", (), {}))
        install_stub("pypdf", PdfReader=type("PdfReader", (), {}))
        install_stub("reportlab")
        install_stub("reportlab.lib")
        install_stub("reportlab.lib.pagesizes", A4=(210, 297))
        install_stub("reportlab.lib.styles", ParagraphStyle=type("ParagraphStyle", (), {}), getSampleStyleSheet=lambda: {})
        install_stub("reportlab.lib.units", mm=1)
        install_stub("reportlab.pdfbase")
        install_stub("reportlab.pdfbase.pdfmetrics", registerFont=lambda *args, **kwargs: None)
        install_stub("reportlab.pdfbase.ttfonts", TTFont=type("TTFont", (), {}))
        install_stub("reportlab.platypus", Paragraph=type("Paragraph", (), {}), SimpleDocTemplate=type("SimpleDocTemplate", (), {}), Spacer=type("Spacer", (), {}))
        core_main = importlib.import_module("main")
        original = (core_main.get_provider, core_main.read_provider_secret, core_main.routing, core_main.public_admin_json)
        calls = []
        try:
            core_main.get_provider = lambda _pid: {"id": "provider-remote", "name": "Remote API", "type": "openai_compatible", "base_url": "https://api.example.test/v1", "billing_class": "BYOK", "cost_input_per_million_rub": 0, "cost_output_per_million_rub": 0}
            core_main.read_provider_secret = lambda _p: "TOP-SECRET"
            core_main.routing = lambda: {"auto": {"provider_id": "provider-remote", "model_id": "model-a"}, "fast": {"provider_id": "provider-remote", "model_id": "model-a"}, "smart": {"provider_id": "provider-remote", "model_id": "model-a"}}

            def fake_admin(domain, token, path, method="GET", body=None, timeout=20):
                calls.append((domain, token, path, method, body))
                if path == "/api/admin/providers":
                    return 201, {"ok": True}
                if path == "/api/admin/inventory":
                    return 200, {"models": [{"provider_id": "provider-remote", "model_id": "model-a"}]}
                if path == "/api/admin/routing":
                    return 200, {"ok": True}
                return 404, {}

            core_main.public_admin_json = fake_admin
            seeded = core_main.seed_remote_provider_to_vps("agent.example.test", "SERVER-ADMIN", "provider-remote")
            assert seeded["ok"] and seeded["model_count"] == 1 and seeded["secret_transferred"] is True
            assert calls[0][4]["api_key"] == "TOP-SECRET" and "TOP-SECRET" not in json.dumps(seeded)
            assert calls[-1][2] == "/api/admin/routing"
        finally:
            core_main.get_provider, core_main.read_provider_secret, core_main.routing, core_main.public_admin_json = original

        main_src = (ROOT / "services" / "core" / "app" / "main.py").read_text(encoding="utf-8")
        schema = main_src[main_src.index("CREATE TABLE IF NOT EXISTS deployment_targets"): main_src.index(");", main_src.index("CREATE TABLE IF NOT EXISTS deployment_targets"))]
        for forbidden in ("password", "private_key", "passphrase", "secret"):
            assert forbidden not in schema.lower()

        lan = (ROOT / "scripts" / "lan.ps1").read_text(encoding="utf-8")
        assert "PA_BIND_IP" in lan and "New-NetFirewallRule" in lan and "-Profile Private" in lan
        for forbidden in ("down -v", "volume prune", "system prune"):
            assert forbidden not in lan.lower()

        print("PAR_V080_ORCHESTRATOR_DEPLOYMENT_ACCEPTANCE PASS: task-store events cancel isolation recovery server-lite bundle preflight staged-deploy internal/public-hot-verify rollback host-key no-secret-persistence LAN-contract")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
