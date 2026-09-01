from __future__ import annotations

import json
import os
import pathlib
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = ROOT / "services" / "core" / "app" / "main.py"


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def req(url: str, *, method: str = "GET", body: dict | None = None, token: str | None = None, expect: int | None = None, timeout: int = 10):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        status = int(exc.code)
    payload = json.loads(raw or "{}")
    if expect is not None and status != expect:
        raise AssertionError(f"{url}: expected {expect}, got {status}: {payload}")
    return status, payload


def wait_ready(base: str, *, seconds: int = 15) -> None:
    end = time.time() + seconds
    last = None
    while time.time() < end:
        try:
            last = req(base + "/api/health", expect=None, timeout=1)
            if last[0] == 200 and last[1].get("ready") is True:
                return
        except Exception as exc:
            last = repr(exc)
        time.sleep(0.1)
    raise AssertionError(f"server did not become ready: {last}")


def start_core(env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, str(CORE)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


class ExternalState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.last = {"path": "", "saw_proxy": False, "authorization": ""}

    def record(self, handler: BaseHTTPRequestHandler) -> None:
        with self.lock:
            self.last = {
                "path": handler.path,
                "saw_proxy": str(handler.headers.get("X-Proxy-Hop") or "") == "1",
                "authorization": str(handler.headers.get("Authorization") or ""),
            }

    def snapshot(self) -> dict[str, object]:
        with self.lock:
            return dict(self.last)


class ExternalHandler(BaseHTTPRequestHandler):
    state: ExternalState

    def log_message(self, *args):
        pass

    def sendj(self, status: int, obj: dict[str, object]) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self) -> dict[str, object]:
        size = int(self.headers.get("Content-Length") or "0")
        return json.loads(self.rfile.read(size) or b"{}")

    def do_GET(self) -> None:
        if self.path == "/test/last":
            self.sendj(200, self.state.snapshot())
            return
        self.state.record(self)
        if self.path == "/v1/models":
            self.sendj(200, {"object": "list", "data": [{"id": "proxy-model", "object": "model"}]})
            return
        self.sendj(404, {"ok": False})

    def do_POST(self) -> None:
        self.state.record(self)
        if self.path == "/v1/responses":
            self.body()
            self.sendj(
                200,
                {
                    "id": "resp_proxy",
                    "object": "response",
                    "output_text": "PROXY_OK",
                    "usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10},
                },
            )
            return
        self.sendj(404, {"ok": False})


class ProxyState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.hits = 0
        self.last_url = ""

    def record(self, url: str) -> None:
        with self.lock:
            self.hits += 1
            self.last_url = url

    def snapshot(self) -> dict[str, object]:
        with self.lock:
            return {"hits": self.hits, "last_url": self.last_url}


class ProxyHandler(BaseHTTPRequestHandler):
    state: ProxyState
    upstream_port: int

    def log_message(self, *args):
        pass

    def _forward(self) -> None:
        target_url = self.path
        if not target_url.startswith("http://"):
            self.send_error(502, "proxy expected absolute-form URL")
            return
        self.state.record(target_url)
        size = int(self.headers.get("Content-Length") or "0")
        data = self.rfile.read(size) if size else None
        parsed = urllib.parse.urlparse(target_url)
        forward_url = target_url
        if parsed.hostname == "external.test":
            forward_url = urllib.parse.urlunparse(
                parsed._replace(netloc=f"127.0.0.1:{self.upstream_port}")
            )
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"proxy-connection", "host", "connection"}
        }
        headers["X-Proxy-Hop"] = "1"
        forwarded = urllib.request.Request(forward_url, data=data, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(forwarded, timeout=10) as upstream:
                body = upstream.read()
                self.send_response(int(upstream.status))
                for key, value in upstream.headers.items():
                    if key.lower() in {"connection", "transfer-encoding"}:
                        continue
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            self.send_response(int(exc.code))
            for key, value in exc.headers.items():
                if key.lower() in {"connection", "transfer-encoding"}:
                    continue
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

    def do_GET(self) -> None:
        self._forward()

    def do_POST(self) -> None:
        self._forward()


def serve(server: ThreadingHTTPServer) -> threading.Thread:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def main() -> int:
    admin_token = "proxy-admin-token"
    core_port = free_port()
    ollama_port = free_port()
    web_port = free_port()
    ext_port = free_port()
    proxy_port = free_port()

    external_state = ExternalState()
    ExternalHandler.state = external_state
    ext_server = ThreadingHTTPServer(("127.0.0.1", ext_port), ExternalHandler)
    serve(ext_server)

    proxy_state = ProxyState()
    ProxyHandler.state = proxy_state
    ProxyHandler.upstream_port = ext_port
    proxy_server = ThreadingHTTPServer(("127.0.0.1", proxy_port), ProxyHandler)
    serve(proxy_server)

    fake_ollama = subprocess.Popen([sys.executable, str(ROOT / "tests" / "fake_ollama.py"), str(ollama_port)])
    fake_web = subprocess.Popen([sys.executable, str(ROOT / "tests" / "fake_web.py"), str(web_port)])

    tmp_path = ROOT / "_tmp_proxy_acceptance" / f"run-{os.getpid()}-{int(time.time() * 1000)}"
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "secrets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "workspaces").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    try:
        env = os.environ.copy()
        env.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PA_RUNTIME_PROFILE": "server",
                "PA_HOST": "127.0.0.1",
                "PA_PORT": str(core_port),
                "PA_ADMIN_TOKEN": admin_token,
                "PA_DB": str(tmp_path / "personal-agent-rus.db"),
                "PA_SECRETS_DIR": str(tmp_path / "secrets"),
                "PA_WORKSPACE_ROOT": str(tmp_path / "workspaces"),
                "PA_LOG_DIR": str(tmp_path / "logs"),
                "PA_TEST_MODE": "1",
                "PA_OLLAMA_URL": f"http://127.0.0.1:{ollama_port}",
                "PA_SEARXNG_URL": f"http://127.0.0.1:{web_port}",
                "PA_BROWSER_URL": f"http://127.0.0.1:{web_port}",
                "PA_CODE_SOCKET": "",
                "PA_OPENAI_API_KEY": "",
            }
        )
        core = start_core(env)
        base = f"http://127.0.0.1:{core_port}"
        try:
            wait_ready(base)
            assert proxy_state.snapshot()["hits"] == 0

            _, search = req(base + "/api/web/search", method="POST", body={"query": "proxy bypass internal", "limit": 2}, expect=200)
            assert len(search["results"]) >= 1
            assert proxy_state.snapshot()["hits"] == 0

            _, configured = req(
                base + "/api/admin/egress-proxy",
                method="POST",
                token=admin_token,
                body={
                    "enabled": True,
                    "label": "Proxy test",
                    "http_proxy_url": f"http://127.0.0.1:{proxy_port}",
                    "https_proxy_url": f"http://127.0.0.1:{proxy_port}",
                    "username": "proxy-user",
                    "password": "proxy-pass",
                    "no_proxy": ["127.0.0.1", "localhost", "::1", "ollama", "searxng", "browser", "core", "smtp", "caddy"],
                },
                expect=200,
            )
            assert configured["egress_proxy"]["enabled"] is True
            assert configured["egress_proxy"]["has_secret"] is True

            _, observability = req(base + "/api/admin/observability", token=admin_token, expect=200)
            components = observability["observability"]["components"]
            assert components["egress_proxy_enabled"] is True
            assert components["egress_proxy_schemes"] == ["http", "https"]

            _, proxy_test = req(
                base + "/api/admin/egress-proxy/test",
                method="POST",
                token=admin_token,
                body={"url": f"http://external.test:{ext_port}/v1/models"},
                expect=200,
            )
            assert proxy_test["result"]["http_status"] == 200
            assert int(proxy_state.snapshot()["hits"]) >= 1

            _, created = req(
                base + "/api/admin/providers",
                method="POST",
                token=admin_token,
                body={
                    "name": "Proxy test provider",
                    "type": "openai_responses",
                    "base_url": f"http://external.test:{ext_port}/v1",
                    "api_key": "proxy-secret",
                    "billing_class": "PLATFORM_REMOTE",
                },
                expect=201,
            )
            provider_id = created["provider"]["id"]
            assert created["provider"]["model_count"] == 1
            assert int(proxy_state.snapshot()["hits"]) >= 1
            ext_last = req(f"http://127.0.0.1:{ext_port}/test/last", expect=200)[1]
            assert ext_last["path"] == "/v1/models"
            assert ext_last["saw_proxy"] is True
            assert ext_last["authorization"].startswith("Bearer ")

            _, cleared = req(
                base + "/api/admin/egress-proxy/secret/clear",
                method="POST",
                token=admin_token,
                body={},
                expect=200,
            )
            assert cleared["egress_proxy"]["has_secret"] is False

        finally:
            core.terminate()
            fake_web.terminate()
            fake_ollama.terminate()
            ext_server.shutdown()
            proxy_server.shutdown()
            core.wait(timeout=10)
            fake_web.wait(timeout=10)
            fake_ollama.wait(timeout=10)
    except Exception:
        if core and core.stdout:
            try:
                print(core.stdout.read())
            except Exception:
                pass
        raise
    print("EGRESS_PROXY_ACCEPTANCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
