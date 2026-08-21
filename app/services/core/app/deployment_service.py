from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shlex
import socket
import tarfile
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

try:
    import paramiko
except Exception:  # pragma: no cover - surfaced as capability unavailable
    paramiko = None


class DeploymentError(RuntimeError):
    pass


@dataclass
class SSHCredentials:
    host: str
    port: int
    username: str
    password: str = ""
    private_key: str = ""
    private_key_passphrase: str = ""
    expected_host_key_sha256: str = ""


class SSHSession(Protocol):
    def run(self, command: str, timeout: int = 120) -> tuple[int, str, str]: ...
    def put_bytes(self, remote_path: str, data: bytes) -> None: ...
    def close(self) -> None: ...


class ParamikoSession:
    def __init__(self, creds: SSHCredentials, timeout: int = 15):
        if paramiko is None:
            raise DeploymentError("SSH deployment support is unavailable: paramiko is not installed")
        self.creds = creds
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())
        host_key = self._fetch_host_key(creds.host, creds.port, timeout)
        fingerprint = host_key_sha256(host_key.asbytes())
        if not creds.expected_host_key_sha256:
            raise DeploymentError(f"SSH host key is not trusted yet. Fingerprint: {fingerprint}")
        if fingerprint != creds.expected_host_key_sha256:
            raise DeploymentError(f"SSH host key mismatch. Expected {creds.expected_host_key_sha256}, observed {fingerprint}")
        host_keys = self.client.get_host_keys()
        host_keys.add(creds.host, host_key.get_name(), host_key)
        pkey = None
        if creds.private_key:
            pkey = self._load_private_key(creds.private_key, creds.private_key_passphrase)
        self.client.connect(
            hostname=creds.host, port=creds.port, username=creds.username,
            password=creds.password or None, pkey=pkey,
            timeout=timeout, banner_timeout=timeout, auth_timeout=timeout,
            allow_agent=False, look_for_keys=False,
        )

    @staticmethod
    def _fetch_host_key(host: str, port: int, timeout: int):
        sock = socket.create_connection((host, port), timeout=timeout)
        transport = paramiko.Transport(sock)
        try:
            transport.start_client(timeout=timeout)
            return transport.get_remote_server_key()
        finally:
            transport.close()
            sock.close()

    @staticmethod
    def _load_private_key(raw: str, passphrase: str):
        errors = []
        for klass in (paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey):
            try:
                return klass.from_private_key(io.StringIO(raw), password=passphrase or None)
            except Exception as exc:
                errors.append(type(exc).__name__)
        raise DeploymentError("Unsupported or invalid private SSH key")

    def run(self, command: str, timeout: int = 120) -> tuple[int, str, str]:
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout, get_pty=False)
        try:
            stdin.close()
        except Exception:
            pass
        code = stdout.channel.recv_exit_status()
        return code, stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")

    def put_bytes(self, remote_path: str, data: bytes) -> None:
        sftp = self.client.open_sftp()
        try:
            with sftp.file(remote_path, "wb") as handle:
                handle.write(data)
        finally:
            sftp.close()

    def close(self) -> None:
        self.client.close()


def host_key_sha256(raw_key: bytes) -> str:
    digest = hashlib.sha256(raw_key).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def _server_env_line(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        if default is None:
            return None
        value = default
    return f"{name}={value}"


def fetch_host_fingerprint(host: str, port: int = 22, timeout: int = 10) -> dict[str, str]:
    if paramiko is None:
        raise DeploymentError("SSH deployment support is unavailable: paramiko is not installed")
    sock = socket.create_connection((host, int(port)), timeout=timeout)
    transport = paramiko.Transport(sock)
    try:
        transport.start_client(timeout=timeout)
        key = transport.get_remote_server_key()
        return {"type": key.get_name(), "sha256": host_key_sha256(key.asbytes())}
    finally:
        transport.close(); sock.close()


def server_bundle(version: str, profile: str, domain: str, admin_token: str, registration_policy: str = "open") -> bytes:
    """Create a self-contained server deployment bundle. No credentials are included except the target server admin token."""
    if profile not in {"server-lite", "server-standard"}:
        raise DeploymentError("unsupported server profile")
    domain = domain.strip().lower()
    if not domain or any(ch.isspace() for ch in domain) or "/" in domain:
        raise DeploymentError("valid server domain is required")
    caddy = f"""{domain} {{\n    encode zstd gzip\n    reverse_proxy core:8080\n}}\n"""
    env_lines = [
        _server_env_line("PA_PRODUCT_FAMILY", "Personal Agent"),
        _server_env_line("PA_PRODUCT_NAME", "Personal Agent Rus"),
        _server_env_line("PA_EDITION", "rus"),
        _server_env_line("PA_LOCALE", "ru-RU"),
        f"PA_VERSION={version}",
        "PA_RUNTIME_PROFILE=server",
        "PA_AUTH_MODE=accounts",
        "PA_SECURE_COOKIES=1",
        _server_env_line("PA_PUBLIC_URL", f"https://{domain}"),
        _server_env_line("PA_SITE_TITLE", "Personal Agent Rus"),
        _server_env_line("PA_SITE_DESCRIPTION", "AI-помощник для чата, файлов, веб-поиска, кода, задач, монетизации и администрирования."),
        _server_env_line("PA_SITE_KEYWORDS", "AI помощник, личный ассистент, чат, файлы, веб-поиск, код, задачи, VPS, биллинг, SEO"),
        _server_env_line("PA_GOOGLE_SITE_VERIFICATION"),
        _server_env_line("PA_YANDEX_VERIFICATION"),
        _server_env_line("PA_HEAD_SNIPPETS"),
        _server_env_line("PA_BODY_SNIPPETS"),
        _server_env_line("PA_CSP_EXTRA"),
        f"PA_REGISTRATION_POLICY={registration_policy}",
        f"PA_ADMIN_TOKEN={admin_token}",
        _server_env_line("PA_HOST", "0.0.0.0"),
        _server_env_line("PA_PORT", "8080"),
        _server_env_line("PA_DB", "/data/personal-agent-rus.db"),
        _server_env_line("PA_WORKSPACE_ROOT", "/data/workspaces"),
        _server_env_line("PA_SECRETS_DIR", "/data/secrets"),
        _server_env_line("PA_SESSION_TTL_SECONDS", str(30 * 24 * 60 * 60)),
        _server_env_line("PA_SESSION_SHORT_TTL_SECONDS", str(24 * 60 * 60)),
        _server_env_line("PA_LOGIN_WINDOW_SECONDS", "900"),
        _server_env_line("PA_LOGIN_MAX_FAILURES", "8"),
        _server_env_line("PA_LAN_ENABLED", "0"),
        _server_env_line("PA_LAN_PUBLIC_URL"),
        _server_env_line("PA_BOOTSTRAP_MODEL"),
        _server_env_line("PA_OLLAMA_URL", ""),
        _server_env_line("PA_SEARXNG_URL", ""),
        _server_env_line("PA_BROWSER_URL", ""),
        _server_env_line("PA_CODE_SOCKET"),
        _server_env_line("PA_UI_PORT", "8080"),
        _server_env_line("PA_WEB_MAX_BYTES", str(3 * 1024 * 1024)),
        _server_env_line("PA_WEB_MAX_SOURCES", "8"),
        _server_env_line("PA_LIST_RESULT_MINIMUM", "7"),
        _server_env_line("PA_FILE_MAX_BYTES", str(20 * 1024 * 1024)),
        _server_env_line("PA_CODE_MAX_TIMEOUT_SECONDS", "30"),
        _server_env_line("PA_USER_TOUR_VERSION", "1"),
        _server_env_line("PA_ADMIN_TOUR_VERSION", "1"),
        _server_env_line("PA_TEST_MODE", "0"),
        _server_env_line("PA_DEBUG_DIAGNOSTICS", "0"),
        _server_env_line("PA_PAYMENT_API_BASE", "https://api.yookassa.ru/v3"),
        _server_env_line("PA_TOPUP_SECOND_APPROVAL_RUB", "5000"),
        _server_env_line("PA_SMTP_HOST"),
        _server_env_line("PA_SMTP_PORT", "587"),
        _server_env_line("PA_SMTP_USER"),
        _server_env_line("PA_SMTP_PASSWORD"),
        _server_env_line("PA_SMTP_FROM"),
        _server_env_line("PA_SMTP_USE_TLS", "1"),
        _server_env_line("PA_OBS_DISK_FREE_THRESHOLD", "0.10"),
        _server_env_line("PA_OBS_MEMORY_FREE_THRESHOLD", "0.10"),
        _server_env_line("PA_VPN_ROUTING_ENABLED"),
        _server_env_line("PA_VPN_ROUTING_MODE", "wireguard"),
        _server_env_line("PA_VPN_PREFERENCE_ID"),
        _server_env_line("PA_VPN_VPS1_NAME", "VPS1"),
        _server_env_line("PA_VPN_VPS1_INTERFACE", "wg0"),
        _server_env_line("PA_VPN_VPS1_ADDRESS", "10.10.0.2/24"),
        _server_env_line("PA_VPN_VPS1_SUBNET", "10.10.0.0/24"),
        _server_env_line("PA_VPN_VPS1_AUTOSTART", "1"),
        _server_env_line("PA_VPN_VPS2_NAME", "VPS2"),
        _server_env_line("PA_VPN_VPS2_HOST"),
        _server_env_line("PA_VPN_VPS2_ADDRESS", "10.10.0.1/24"),
        _server_env_line("PA_VPN_ENDPOINT_PORT", "51820"),
        _server_env_line("PA_VPN_NAT_INTERFACE", "eth0"),
        _server_env_line("PA_VPN_IP_FORWARD", "1"),
        _server_env_line("PA_VPN_UPSTREAM_NAME", "OpenAPI"),
        _server_env_line("PA_VPN_UPSTREAM_HOST", "api.example.com"),
        _server_env_line("PA_VPN_UPSTREAM_IP"),
        _server_env_line("PA_VPN_ALLOWED_IPS"),
        _server_env_line("PA_VPN_NOTES"),
    ]
    env = "\n".join(line for line in env_lines if line is not None) + "\n"
    compose = f"""name: personal-agent-rus-server\nservices:\n  core:\n    build:\n      context: ./core\n    image: personal-agent-core:{version}-server\n    restart: unless-stopped\n    env_file: .env.server
    volumes:\n      - par-server-data:/data\n    expose:\n      - \"8080\"\n    healthcheck:\n      test: [\"CMD\", \"python\", \"-c\", \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=3)\"]\n      interval: 10s\n      timeout: 5s\n      retries: 30\n      start_period: 10s\n  caddy:\n    image: caddy:2.11.2\n    restart: unless-stopped\n    ports:\n      - \"80:80\"\n      - \"443:443\"\n      - \"443:443/udp\"\n    volumes:\n      - ./Caddyfile:/etc/caddy/Caddyfile:ro\n      - par-server-caddy-data:/data\n      - par-server-caddy-config:/config\n    depends_on:\n      core:\n        condition: service_healthy\nvolumes:\n  par-server-data:\n  par-server-caddy-data:\n  par-server-caddy-config:\n"""
    readme = f"Personal Agent Rus {version}\nProfile: {profile}\nDomain: {domain}\nGenerated by Deployment Manager.\n"
    payloads = {"docker-compose-main.yaml": compose.encode(), ".env.server": env.encode(), "Caddyfile": caddy.encode(), "README.txt": readme.encode()}
    # Core runtime source is copied from the installed package at deploy time by caller using add_core_to_bundle.
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in payloads.items():
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o600 if name == ".env.server" else 0o644; info.mtime = int(time.time())
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def add_core_to_bundle(bundle: bytes, core_root: Path) -> bytes:
    """Repack generated server bundle with the exact Core source used by this release."""
    src = Path(core_root)
    if not (src / "Dockerfile").is_file() or not (src / "app" / "main.py").is_file():
        raise DeploymentError("core source is unavailable for deployment bundle")
    source_files: dict[str, tuple[bytes, int]] = {}
    for path in src.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = "core/" + path.relative_to(src).as_posix()
        source_files[rel] = (path.read_bytes(), 0o755 if path.name.endswith(".sh") else 0o644)
    original: dict[str, tuple[bytes, int]] = {}
    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as tf:
        for member in tf.getmembers():
            if member.isfile():
                original[member.name] = (tf.extractfile(member).read(), member.mode)
    original.update(source_files)
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tf:
        for name in sorted(original):
            data, mode = original[name]
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = mode; info.mtime = int(time.time())
            tf.addfile(info, io.BytesIO(data))
    return out.getvalue()


def preflight(session: SSHSession) -> dict[str, Any]:
    commands = {
        "os": "uname -srm",
        "docker": "docker --version",
        "compose": "docker compose version",
        "memory_mb": "awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo",
        "disk_kb": "df -Pk / | awk 'NR==2 {print $4}'",
        "user": "id -un",
    }
    result: dict[str, Any] = {"ok": True, "checks": {}}
    for name, command in commands.items():
        code, stdout, stderr = session.run(command, timeout=20)
        result["checks"][name] = {"ok": code == 0, "value": stdout.strip()[:500], "error": stderr.strip()[:500]}
        if name in {"docker", "compose"} and code != 0:
            result["ok"] = False
    try:
        result["memory_mb"] = int(result["checks"]["memory_mb"]["value"] or 0)
        result["disk_free_mb"] = int(result["checks"]["disk_kb"]["value"] or 0) // 1024
    except Exception:
        result["ok"] = False
    result["recommended_profile"] = "server-lite" if result.get("memory_mb", 0) < 4096 else "server-standard"
    return result



def resolve_remote_root(session: SSHSession) -> str:
    code, out, err = session.run('printf "%s\n%s\n" "$(id -u)" "$HOME"', timeout=20)
    if code != 0:
        raise DeploymentError(err or out or "cannot resolve remote home")
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if len(lines) < 2 or not lines[0].isdigit() or not lines[1].startswith('/'):
        raise DeploymentError("invalid remote identity/home")
    return "/opt/personal-agent" if int(lines[0]) == 0 else lines[1].rstrip('/') + "/.local/share/personal-agent"

def deploy(session: SSHSession, bundle: bytes, version: str, *, remote_root: str = "/opt/personal-agent") -> dict[str, Any]:
    if not version or not all(ch.isalnum() or ch in ".-_" for ch in version):
        raise DeploymentError("invalid release version")
    release_dir = f"{remote_root}/releases/{version}-{int(time.time())}"
    archive = f"/tmp/personal-agent-{uuid.uuid4().hex}.tar.gz"
    commands = [
        f"mkdir -p {shlex.quote(remote_root + '/releases')}",
        f"mkdir -p {shlex.quote(release_dir)}",
    ]
    for cmd in commands:
        code, out, err = session.run(cmd, timeout=30)
        if code != 0:
            raise DeploymentError(err or out or "remote directory preparation failed")
    session.put_bytes(archive, bundle)
    code, out, err = session.run(f"tar -xzf {shlex.quote(archive)} -C {shlex.quote(release_dir)} && rm -f {shlex.quote(archive)}", timeout=60)
    if code != 0:
        raise DeploymentError(err or out or "release extraction failed")
    # Keep a previous pointer before switching the active release.
    switch = (
        f"set -eu; cd {shlex.quote(remote_root)}; "
        "if [ -L current ]; then old=$(readlink -f current || true); [ -n \"$old\" ] && ln -sfn \"$old\" previous || true; fi; "
        f"ln -sfn {shlex.quote(release_dir)} current; cd current; "
        "docker compose --env-file .env.server -f docker-compose-main.yaml up -d --build"
    )
    code, out, err = session.run(switch, timeout=900)
    if code != 0:
        raise DeploymentError((err or out or "remote compose deployment failed")[-4000:])
    verify_cmd = (
        f"cd {shlex.quote(remote_root)}/current && "
        "for i in $(seq 1 60); do "
        "if docker compose --env-file .env.server -f docker-compose-main.yaml exec -T core python -c \"import urllib.request,json; x=json.load(urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=3)); assert x.get('ready')\" >/dev/null 2>&1; then exit 0; fi; sleep 2; done; exit 1"
    )
    code, out, err = session.run(verify_cmd, timeout=180)
    if code != 0:
        raise DeploymentError("remote hot verification failed")
    return {"ok": True, "release_dir": release_dir, "version": version, "hot_verify": "PASS"}


def rollback(session: SSHSession, *, remote_root: str = "/opt/personal-agent") -> dict[str, Any]:
    cmd = (
        f"set -eu; cd {shlex.quote(remote_root)}; test -L previous; target=$(readlink -f previous); test -d \"$target\"; "
        "current_old=$(readlink -f current || true); ln -sfn \"$target\" current; "
        "[ -n \"$current_old\" ] && ln -sfn \"$current_old\" previous || true; "
        "cd current; docker compose --env-file .env.server -f docker-compose-main.yaml up -d --build"
    )
    code, out, err = session.run(cmd, timeout=900)
    if code != 0:
        raise DeploymentError((err or out or "rollback failed")[-4000:])
    return {"ok": True, "status": "ROLLED_BACK"}


def apply_vpn_plan(session: SSHSession, plan: dict[str, Any], *, role: str = "vps1") -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise DeploymentError("vpn plan must be an object")
    role = "vps2" if str(role).strip().lower() in {"vps2", "server", "upstream"} else "vps1"
    config_key = "server_config" if role == "vps2" else "client_config"
    commands_key = "server_commands" if role == "vps2" else "client_commands"
    config = str(plan.get(config_key) or "").strip()
    if not config:
        raise DeploymentError(f"vpn plan {config_key} is missing")
    commands = plan.get(commands_key)
    if commands_key == "server_commands" and (not isinstance(commands, list) or not commands):
        raise DeploymentError("vpn plan server commands are missing")
    verification = plan.get("verification") if isinstance(plan.get("verification"), dict) else {}
    interface = str(verification.get("vps2_interface") if role == "vps2" else verification.get("vps1_interface") or "wg0").strip() or "wg0"
    mode = str(verification.get("mode") or "wireguard").strip().lower()
    service_name = "wg-quick@" + interface
    remote_tmp = f"/tmp/personal-agent-vpn-{role}-{uuid.uuid4().hex}.conf"
    remote_target = f"/etc/wireguard/{interface}.conf"
    session.put_bytes(remote_tmp, config.encode("utf-8"))
    commands = [
        "sudo mkdir -p /etc/wireguard",
        f"sudo install -D -m 600 {shlex.quote(remote_tmp)} {shlex.quote(remote_target)}",
        f"sudo rm -f {shlex.quote(remote_tmp)}",
    ]
    for command in commands:
        code, out, err = session.run(command, timeout=60)
        if code != 0:
            raise DeploymentError((err or out or "vpn config install failed")[-4000:])
    executed: list[str] = []
    if role == "vps2":
        if not isinstance(commands, list) or not commands:
            raise DeploymentError("vpn plan server commands are missing")
        for command in commands:
            cmd = str(command).strip()
            if not cmd:
                continue
            code, out, err = session.run(cmd, timeout=120)
            executed.append(cmd)
            if code != 0:
                raise DeploymentError((err or out or f"vpn command failed: {cmd}")[-4000:])
    restart_cmds = [f"sudo systemctl enable {service_name}", f"sudo systemctl restart {service_name}"]
    for command in restart_cmds:
        code, out, err = session.run(command, timeout=120)
        if code != 0:
            raise DeploymentError((err or out or "vpn service restart failed")[-4000:])
    return {
        "ok": True,
        "service_name": service_name,
        "remote_target": remote_target,
        "role": role,
        "mode": mode,
        "executed_commands": executed,
        "verification": verification,
    }


def public_hot_verify(domain: str, expected_version: str, *, timeout_seconds: int = 120, opener=None) -> dict[str, Any]:
    """Verify the exact public HTTPS release after Caddy/DNS/TLS are active."""
    import urllib.request
    domain = domain.strip().lower()
    if not domain or '/' in domain or any(ch.isspace() for ch in domain):
        raise DeploymentError("valid public domain is required")
    open_fn = opener or urllib.request.urlopen
    url = f"https://{domain}/api/system"
    deadline = time.monotonic() + max(5, int(timeout_seconds))
    delay = 1.0
    last_error = ""
    attempts = 0
    while time.monotonic() < deadline:
        attempts += 1
        try:
            with open_fn(url, timeout=min(10, max(2, int(deadline - time.monotonic())))) as response:
                status = int(getattr(response, "status", 200))
                if status != 200:
                    raise DeploymentError(f"public HTTP status {status}")
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("product") != "Personal Agent Rus":
                raise DeploymentError("public endpoint returned another product")
            if str(payload.get("version")) != str(expected_version):
                raise DeploymentError(f"public version mismatch: expected {expected_version}, got {payload.get('version')}")
            return {"ok": True, "url": url, "version": expected_version, "attempts": attempts, "https": True}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(delay, max(0.1, remaining)))
            delay = min(5.0, delay * 1.5)
    raise DeploymentError(f"public HTTPS hot verification failed for {url}: {last_error or 'timeout'}")


def bootstrap_runtime(session: SSHSession) -> dict[str, Any]:
    """Install Docker from distribution packages on supported Debian/Ubuntu VPS. Requires root SSH."""
    code, out, err = session.run("id -u", timeout=20)
    if code != 0 or out.strip() != "0":
        raise DeploymentError("Automatic VPS bootstrap requires root SSH. Use a prepared deploy user with Docker for normal deploys.")
    code, os_release, err = session.run("cat /etc/os-release", timeout=20)
    if code != 0:
        raise DeploymentError(err or "cannot detect VPS distribution")
    meta: dict[str, str] = {}
    for line in os_release.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            meta[key.strip()] = value.strip().strip('"')
    distro = (meta.get("ID") or "").lower()
    like = (meta.get("ID_LIKE") or "").lower()
    if distro not in {"debian", "ubuntu"} and not any(x in like.split() for x in {"debian", "ubuntu"}):
        raise DeploymentError(f"Automatic bootstrap currently supports Debian/Ubuntu family, got {distro or 'unknown'}")
    commands = [
        "export DEBIAN_FRONTEND=noninteractive; apt-get update",
        "export DEBIAN_FRONTEND=noninteractive; "
        "if apt-cache show docker-compose-v2 >/dev/null 2>&1; then apt-get install -y ca-certificates docker.io docker-compose-v2; "
        "elif apt-cache show docker-compose-plugin >/dev/null 2>&1; then apt-get install -y ca-certificates docker.io docker-compose-plugin; "
        "else apt-get install -y ca-certificates docker.io docker-compose; fi",
        "systemctl enable --now docker || service docker start",
        "docker --version && docker compose version",
    ]
    logs: list[dict[str, Any]] = []
    for command in commands:
        code, stdout, stderr = session.run(command, timeout=900)
        logs.append({"command": command.split(";")[-1].strip()[:100], "ok": code == 0, "stdout": stdout[-1000:], "stderr": stderr[-1000:]})
        if code != 0:
            raise DeploymentError((stderr or stdout or "VPS runtime bootstrap failed")[-3000:])
    return {"ok": True, "distribution": distro or "debian-compatible", "docker": True, "compose": True, "steps": logs}
