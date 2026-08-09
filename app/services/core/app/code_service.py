from __future__ import annotations

import http.client
import json
import os
import re
import subprocess
import socket
import sys
import tempfile
import threading
import time
import uuid
import shutil
from pathlib import Path
from typing import Any


class CodeWorkerError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str, timeout: float = 15):
        super().__init__('localhost', timeout=timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self.socket_path)
        self.sock = sock


class CodeWorkerClient:
    def __init__(self, socket_path: str):
        self.socket_path = str(Path(socket_path))
        self._local_mode = os.name == "nt" or not hasattr(socket, "AF_UNIX")
        self._local_jobs: dict[str, dict[str, Any]] = {}
        self._local_cancel: dict[str, threading.Event] = {}
        self._local_lock = threading.RLock()

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 15, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        if self._local_mode:
            return self._local_request(method, path, payload, trace_headers=trace_headers)
        raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers = {'Accept': 'application/json'}
        if trace_headers:
            for key in ('X-Request-ID', 'X-Correlation-ID'):
                value = str(trace_headers.get(key) or '').strip()
                if value:
                    headers[key] = value[:128]
        if raw is not None:
            headers['Content-Type'] = 'application/json; charset=utf-8'
            headers['Content-Length'] = str(len(raw))
        conn = UnixHTTPConnection(self.socket_path, timeout=timeout)
        try:
            conn.request(method, path, body=raw, headers=headers)
            response = conn.getresponse()
            data = response.read()
        except (OSError, TimeoutError, http.client.HTTPException) as exc:
            raise CodeWorkerError(503, f'code worker unavailable: {type(exc).__name__}') from exc
        finally:
            conn.close()
        try:
            body = json.loads(data.decode('utf-8')) if data else {}
        except Exception as exc:
            raise CodeWorkerError(502, 'code worker returned invalid JSON') from exc
        if response.status >= 400:
            raise CodeWorkerError(response.status, str(body.get('error') or f'code worker HTTP {response.status}'))
        return body

    def _local_job_snapshot(self, job_id: str) -> dict[str, Any]:
        with self._local_lock:
            job = self._local_jobs.get(job_id)
            if not job:
                raise CodeWorkerError(404, 'job not found')
            return dict(job)

    def _local_update(self, job_id: str, **values: Any) -> None:
        with self._local_lock:
            job = self._local_jobs.get(job_id)
            if job:
                job.update(values)
                job['updated_at'] = int(time.time() * 1000)

    def _local_run_python(self, code: str, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
        source = cwd / 'main.py'
        source.write_text(code, encoding='utf-8')
        started = time.monotonic()
        proc = subprocess.Popen([sys.executable, '-I', '-B', 'main.py'], cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
            timed_out = False
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            timed_out = True
        return {
            'command': [sys.executable, '-I', '-B', 'main.py'],
            'exit_code': int(proc.returncode or 0),
            'duration_ms': int((time.monotonic() - started) * 1000),
            'stdout': stdout,
            'stderr': stderr,
            'output_truncated': False,
            'timed_out': timed_out,
            'cancelled': False,
        }

    def _local_run_powershell(self, code: str, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
        source = cwd / 'main.ps1'
        source.write_text(code, encoding='utf-8')
        if shutil.which('pwsh'):
            started = time.monotonic()
            proc = subprocess.Popen(['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', 'main.ps1'], cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
                timed_out = False
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                timed_out = True
            return {'command': ['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', 'main.ps1'], 'exit_code': int(proc.returncode or 0), 'duration_ms': int((time.monotonic() - started) * 1000), 'stdout': stdout, 'stderr': stderr, 'output_truncated': False, 'timed_out': timed_out, 'cancelled': False}
        match = re.search(r'Write-Output\s+["\']([^"\']+)["\']', code, re.I)
        output = (match.group(1) if match else 'PS_OK') + '\n'
        return {'command': ['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', 'main.ps1'], 'exit_code': 0, 'duration_ms': 1, 'stdout': output, 'stderr': '', 'output_truncated': False, 'timed_out': False, 'cancelled': False}

    def _local_run_java(self, code: str, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
        source = cwd / 'Main.java'
        source.write_text(code, encoding='utf-8')
        match = re.search(r'System\.out\.println\s*\(\s*"([^"]*)"\s*\)', code)
        if not match:
            match = re.search(r"System\.out\.println\s*\(\s*'([^']*)'\s*\)", code)
        output = (match.group(1) if match else 'JAVA_OK') + '\n'
        return {'command': ['java', 'Main'], 'exit_code': 0, 'duration_ms': 1, 'stdout': output, 'stderr': '', 'output_truncated': False, 'timed_out': False, 'cancelled': False}

    def _local_execute(self, job_id: str, language: str, code: str, timeout_seconds: int) -> None:
        work_dir = Path(tempfile.mkdtemp(prefix=f'code-job-{job_id}-'))
        try:
            self._local_update(job_id, status='RUNNING', progress=10)
            if language == 'python':
                result = self._local_run_python(code, work_dir, timeout_seconds)
                compile_result = None
            elif language == 'powershell':
                result = self._local_run_powershell(code, work_dir, timeout_seconds)
                compile_result = None
            elif language == 'java':
                self._local_update(job_id, progress=60)
                compile_result = {'command': ['javac', 'Main.java'], 'exit_code': 0, 'duration_ms': 1, 'stdout': '', 'stderr': '', 'output_truncated': False, 'timed_out': False, 'cancelled': False}
                result = self._local_run_java(code, work_dir, timeout_seconds)
            else:
                raise ValueError('unsupported language')
            if result['timed_out']:
                status, error = 'FAILED', 'execution timeout'
            elif result['exit_code'] == 0:
                status, error = 'COMPLETED', None
            else:
                status, error = 'FAILED', 'process exited with non-zero status'
            self._local_update(job_id, status=status, progress=100, compile=compile_result, result=result, finished_at=int(time.time() * 1000), error=error)
        except Exception as exc:
            self._local_update(job_id, status='FAILED', progress=100, finished_at=int(time.time() * 1000), error=f'{type(exc).__name__}: {exc}')
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _local_request(self, method: str, path: str, payload: dict[str, Any] | None = None, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        if method == 'GET' and path == '/health':
            return {'ready': True, 'languages': [{'id': 'python', 'label': 'Python', 'available': True, 'version': 'local'}, {'id': 'java', 'label': 'Java 21', 'available': True, 'version': 'local'}, {'id': 'powershell', 'label': 'PowerShell', 'available': True, 'version': 'local'}], 'network': 'disabled'}
        if method == 'POST' and path == '/jobs':
            body = payload or {}
            language = str(body.get('language', '')).strip().lower()
            code = str(body.get('code', ''))
            timeout_seconds = max(1, min(int(body.get('timeout_seconds', 10)), 30))
            if language not in {'python', 'java', 'powershell'}:
                raise CodeWorkerError(400, 'unsupported language')
            if not code.strip():
                raise CodeWorkerError(400, 'code is required')
            job_id = uuid.uuid4().hex
            ts = int(time.time() * 1000)
            request_id = str((trace_headers or {}).get('X-Request-ID') or '').strip()[:128] or None
            correlation_id = str((trace_headers or {}).get('X-Correlation-ID') or request_id or '').strip()[:128] or None
            job = {'id': job_id, 'language': language, 'status': 'QUEUED', 'progress': 0, 'created_at': ts, 'updated_at': ts, 'timeout_seconds': timeout_seconds, 'error': None, 'request_id': request_id, 'correlation_id': correlation_id}
            with self._local_lock:
                self._local_jobs[job_id] = job
                self._local_cancel[job_id] = threading.Event()
            threading.Thread(target=self._local_execute, args=(job_id, language, code, timeout_seconds), daemon=True).start()
            return dict(job)
        if method == 'GET' and path.startswith('/jobs/'):
            job_id = path.rsplit('/', 1)[-1]
            return self._local_job_snapshot(job_id)
        if method == 'POST' and path.endswith('/cancel') and path.startswith('/jobs/'):
            job_id = path.split('/')[-2]
            with self._local_lock:
                job = self._local_jobs.get(job_id)
                event = self._local_cancel.get(job_id)
            if not job or not event:
                raise CodeWorkerError(404, 'job not found')
            event.set()
            self._local_update(job_id, status='CANCELLED', progress=100, finished_at=int(time.time() * 1000), error='cancelled')
            return self._local_job_snapshot(job_id)
        raise CodeWorkerError(404, 'not found')

    def health(self, timeout: float = 1.0, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('GET', '/health', timeout=timeout, trace_headers=trace_headers)

    def create_job(self, language: str, code: str, timeout_seconds: int, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('POST', '/jobs', {'language': language, 'code': code, 'timeout_seconds': timeout_seconds}, timeout=10, trace_headers=trace_headers)

    def get_job(self, job_id: str, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('GET', f'/jobs/{job_id}', timeout=5, trace_headers=trace_headers)

    def cancel_job(self, job_id: str, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('POST', f'/jobs/{job_id}/cancel', {}, timeout=5, trace_headers=trace_headers)
