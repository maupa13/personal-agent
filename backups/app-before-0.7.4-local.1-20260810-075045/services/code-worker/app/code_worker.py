from __future__ import annotations

import json
import os
import re
import resource
import shutil
import signal
import socketserver
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

SOCKET_PATH = Path(os.getenv('PA_CODE_SOCKET', '/ipc/code-worker.sock'))
WORK_ROOT = Path(os.getenv('PA_CODE_WORK_ROOT', '/work'))
RUNNER_UID = int(os.getenv('PA_CODE_RUNNER_UID', '10002'))
RUNNER_GID = int(os.getenv('PA_CODE_RUNNER_GID', '10002'))
MAX_SOURCE_BYTES = int(os.getenv('PA_CODE_MAX_SOURCE_BYTES', str(256 * 1024)))
MAX_OUTPUT_BYTES = int(os.getenv('PA_CODE_MAX_OUTPUT_BYTES', str(1024 * 1024)))
MAX_TIMEOUT_SECONDS = int(os.getenv('PA_CODE_MAX_TIMEOUT_SECONDS', '30'))
MAX_FILE_BYTES = int(os.getenv('PA_CODE_MAX_FILE_BYTES', str(8 * 1024 * 1024)))

LANGUAGES = {
    'python': {'display': 'Python', 'version_cmd': ['python3', '--version']},
    'java': {'display': 'Java 21', 'version_cmd': ['java', '-version']},
    'powershell': {'display': 'PowerShell', 'version_cmd': ['pwsh', '-Version']},
}

JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.RLock()
PROCESSES: dict[str, subprocess.Popen] = {}
PRLIMIT_BIN = shutil.which('prlimit') or '/usr/bin/prlimit'
SETPRIV_BIN = shutil.which('setpriv') or '/usr/bin/setpriv'
CANCEL_EVENTS: dict[str, threading.Event] = {}


def now_ms() -> int:
    return int(time.time() * 1000)


def safe_job(job: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in job.items() if k not in {'work_dir'}}


def update_job(job_id: str, **values: Any) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job:
            job.update(values)
            job['updated_at'] = now_ms()


def sandbox_command(command: list[str], timeout_seconds: int) -> list[str]:
    if not Path(PRLIMIT_BIN).exists() or not Path(SETPRIV_BIN).exists():
        raise RuntimeError("sandbox requires util-linux prlimit/setpriv")
    address_space = 1536 * 1024 * 1024
    return [
        PRLIMIT_BIN,
        '--core=0:0',
        f'--cpu={max(1, timeout_seconds)}:{max(1, timeout_seconds + 1)}',
        f'--fsize={MAX_FILE_BYTES}:{MAX_FILE_BYTES}',
        '--nofile=64:64',
        '--nproc=64:64',
        f'--as={address_space}:{address_space}',
        '--',
        SETPRIV_BIN,
        f'--reuid={RUNNER_UID}',
        f'--regid={RUNNER_GID}',
        '--clear-groups',
        '--',
        *command,
    ]


def read_limited(path: Path) -> tuple[str, bool]:
    if not path.exists():
        return '', False
    raw = path.read_bytes()
    truncated = len(raw) > MAX_OUTPUT_BYTES
    return raw[:MAX_OUTPUT_BYTES].decode('utf-8', errors='replace'), truncated


def terminate_process(job_id: str) -> None:
    with JOBS_LOCK:
        proc = PROCESSES.get(job_id)
    if not proc or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 1.5
    while time.monotonic() < deadline and proc.poll() is None:
        time.sleep(0.05)
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_command(job_id: str, command: list[str], cwd: Path, timeout_seconds: int, phase: str) -> dict[str, Any]:
    stdout_path = cwd / f'{phase}.stdout'
    stderr_path = cwd / f'{phase}.stderr'
    env = {
        'PATH': os.getenv('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
        'HOME': str(cwd / 'home'),
        'TMPDIR': str(cwd / 'tmp'),
        'LANG': 'C.UTF-8',
        'LC_ALL': 'C.UTF-8',
        'PYTHONDONTWRITEBYTECODE': '1',
        'POWERSHELL_TELEMETRY_OPTOUT': '1',
        'DOTNET_CLI_TELEMETRY_OPTOUT': '1',
    }
    (cwd / 'home').mkdir(exist_ok=True)
    (cwd / 'tmp').mkdir(exist_ok=True)
    for p in (cwd / 'home', cwd / 'tmp'):
        os.chown(p, RUNNER_UID, RUNNER_GID)
        os.chmod(p, 0o700)
    started = time.monotonic()
    with stdout_path.open('wb') as out, stderr_path.open('wb') as err:
        proc = subprocess.Popen(
            sandbox_command(command, timeout_seconds),
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=err,
            env=env,
            start_new_session=True,
        )
        with JOBS_LOCK:
            PROCESSES[job_id] = proc
        deadline = time.monotonic() + timeout_seconds
        timed_out = False
        cancelled = False
        while proc.poll() is None:
            if CANCEL_EVENTS[job_id].is_set():
                cancelled = True
                terminate_process(job_id)
                break
            if time.monotonic() >= deadline:
                timed_out = True
                terminate_process(job_id)
                break
            time.sleep(0.05)
        try:
            return_code = proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            terminate_process(job_id)
            return_code = proc.wait(timeout=2)
    if return_code == -getattr(signal, 'SIGXCPU', 24):
        timed_out = True
    with JOBS_LOCK:
        PROCESSES.pop(job_id, None)
    stdout, out_truncated = read_limited(stdout_path)
    stderr, err_truncated = read_limited(stderr_path)
    return {
        'command': command,
        'exit_code': int(return_code),
        'duration_ms': int((time.monotonic() - started) * 1000),
        'stdout': stdout,
        'stderr': stderr,
        'output_truncated': bool(out_truncated or err_truncated),
        'timed_out': timed_out,
        'cancelled': cancelled,
    }


def java_class_name(code: str) -> str:
    match = re.search(r'\bpublic\s+(?:final\s+)?class\s+([A-Za-z_$][A-Za-z0-9_$]*)', code)
    if not match:
        match = re.search(r'\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)', code)
    return match.group(1) if match else 'Main'


def execute_job(job_id: str, language: str, code: str, timeout_seconds: int) -> None:
    work_dir = WORK_ROOT / job_id
    try:
        work_dir.mkdir(parents=True, exist_ok=False)
        os.chown(work_dir, RUNNER_UID, RUNNER_GID)
        os.chmod(work_dir, 0o700)
        update_job(job_id, status='RUNNING', started_at=now_ms(), progress=10)
        if language == 'python':
            source = work_dir / 'main.py'
            source.write_text(code, encoding='utf-8')
            os.chown(source, RUNNER_UID, RUNNER_GID)
            result = run_command(job_id, ['python3', '-I', '-B', 'main.py'], work_dir, timeout_seconds, 'run')
            compile_result = None
        elif language == 'powershell':
            source = work_dir / 'main.ps1'
            source.write_text(code, encoding='utf-8')
            os.chown(source, RUNNER_UID, RUNNER_GID)
            result = run_command(job_id, ['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', 'main.ps1'], work_dir, timeout_seconds, 'run')
            compile_result = None
        elif language == 'java':
            class_name = java_class_name(code)
            source = work_dir / f'{class_name}.java'
            source.write_text(code, encoding='utf-8')
            os.chown(source, RUNNER_UID, RUNNER_GID)
            update_job(job_id, progress=30)
            compile_result = run_command(job_id, ['javac', '-J-Xmx256m', '-J-XX:CompressedClassSpaceSize=64m', '-J-XX:MaxMetaspaceSize=128m', '-J-Djava.io.tmpdir=tmp', '-encoding', 'UTF-8', source.name], work_dir, timeout_seconds, 'compile')
            if compile_result['cancelled']:
                update_job(job_id, status='CANCELLED', progress=100, compile=compile_result, finished_at=now_ms(), error='cancelled')
                return
            if compile_result['timed_out']:
                update_job(job_id, status='FAILED', progress=100, compile=compile_result, finished_at=now_ms(), error='compile timeout')
                return
            if compile_result['exit_code'] != 0:
                update_job(job_id, status='FAILED', progress=100, compile=compile_result, finished_at=now_ms(), error='compile failed')
                return
            update_job(job_id, progress=60)
            result = run_command(job_id, ['java', '-Xms16m', '-Xmx256m', '-XX:CompressedClassSpaceSize=64m', '-XX:MaxMetaspaceSize=128m', '-Djava.io.tmpdir=tmp', '-Dfile.encoding=UTF-8', class_name], work_dir, timeout_seconds, 'run')
        else:
            raise ValueError('unsupported language')
        if result['cancelled']:
            status, error = 'CANCELLED', 'cancelled'
        elif result['timed_out']:
            status, error = 'FAILED', 'execution timeout'
        elif result['exit_code'] == 0:
            status, error = 'COMPLETED', None
        else:
            status, error = 'FAILED', 'process exited with non-zero status'
        update_job(job_id, status=status, progress=100, compile=compile_result, result=result, finished_at=now_ms(), error=error)
    except Exception as exc:
        update_job(job_id, status='FAILED', progress=100, finished_at=now_ms(), error=f'{type(exc).__name__}: {exc}')
    finally:
        with JOBS_LOCK:
            PROCESSES.pop(job_id, None)


def runtime_inventory() -> dict[str, Any]:
    inventory = []
    for language, spec in LANGUAGES.items():
        command = spec['version_cmd']
        try:
            completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
            version = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else 'available'
            available = completed.returncode == 0
        except Exception:
            version, available = '', False
        inventory.append({'id': language, 'label': spec['display'], 'available': available, 'version': version})
    return {'ready': all(item['available'] for item in inventory), 'languages': inventory, 'network': 'disabled'}


class Handler(BaseHTTPRequestHandler):
    server_version = 'PersonalAgentCodeWorker/0.7.3'

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self) -> dict[str, Any]:
        length = int(self.headers.get('Content-Length', '0') or '0')
        if length < 0 or length > MAX_SOURCE_BYTES + 64 * 1024:
            raise ValueError('request too large')
        raw = self.rfile.read(length)
        return json.loads(raw.decode('utf-8') or '{}')

    def do_GET(self) -> None:
        path = self.path.split('?', 1)[0]
        if path == '/health':
            self.send_json(200, runtime_inventory())
            return
        if path.startswith('/jobs/'):
            job_id = path.rsplit('/', 1)[-1]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
            if not job:
                self.send_json(404, {'error': 'job not found'})
            else:
                self.send_json(200, safe_job(job))
            return
        self.send_json(404, {'error': 'not found'})

    def do_POST(self) -> None:
        path = self.path.split('?', 1)[0]
        if path == '/jobs':
            try:
                body = self.body()
                language = str(body.get('language', '')).strip().lower()
                code = str(body.get('code', ''))
                timeout_seconds = int(body.get('timeout_seconds', 10))
                if language not in LANGUAGES:
                    self.send_json(400, {'error': 'unsupported language'})
                    return
                if not code.strip():
                    self.send_json(400, {'error': 'code is required'})
                    return
                if len(code.encode('utf-8')) > MAX_SOURCE_BYTES:
                    self.send_json(413, {'error': 'source is too large'})
                    return
                timeout_seconds = max(1, min(timeout_seconds, MAX_TIMEOUT_SECONDS))
                job_id = uuid.uuid4().hex
                ts = now_ms()
                job = {'id': job_id, 'language': language, 'status': 'QUEUED', 'progress': 0, 'created_at': ts, 'updated_at': ts, 'timeout_seconds': timeout_seconds, 'error': None}
                with JOBS_LOCK:
                    JOBS[job_id] = job
                    CANCEL_EVENTS[job_id] = threading.Event()
                thread = threading.Thread(target=execute_job, args=(job_id, language, code, timeout_seconds), daemon=True)
                thread.start()
                self.send_json(202, safe_job(job))
            except Exception as exc:
                self.send_json(400, {'error': f'{type(exc).__name__}: {exc}'})
            return
        if path.startswith('/jobs/') and path.endswith('/cancel'):
            job_id = path.split('/')[-2]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                event = CANCEL_EVENTS.get(job_id)
            if not job or not event:
                self.send_json(404, {'error': 'job not found'})
                return
            if job['status'] in {'COMPLETED', 'FAILED', 'CANCELLED'}:
                self.send_json(200, safe_job(job))
                return
            event.set()
            terminate_process(job_id)
            update_job(job_id, status='CANCELLED', progress=100, finished_at=now_ms(), error='cancelled')
            with JOBS_LOCK:
                job = JOBS[job_id]
            self.send_json(200, safe_job(job))
            return
        self.send_json(404, {'error': 'not found'})


class ThreadingUnixHTTPServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> int:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    # Runner must be able to traverse the root but may only enter its own 0700 job directory.
    try:
        os.chmod(WORK_ROOT, 0o711)
    except OSError:
        pass
    SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SOCKET_PATH.exists() or SOCKET_PATH.is_socket():
        SOCKET_PATH.unlink()
    server = ThreadingUnixHTTPServer(str(SOCKET_PATH), Handler)
    os.chmod(SOCKET_PATH, 0o600)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        try:
            SOCKET_PATH.unlink()
        except FileNotFoundError:
            pass
        shutil.rmtree(WORK_ROOT, ignore_errors=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
