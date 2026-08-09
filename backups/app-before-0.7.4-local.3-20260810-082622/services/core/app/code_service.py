from __future__ import annotations

import http.client
import json
import socket
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

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 15) -> dict[str, Any]:
        raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers = {'Accept': 'application/json'}
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

    def health(self, timeout: float = 1.0) -> dict[str, Any]:
        return self._request('GET', '/health', timeout=timeout)

    def create_job(self, language: str, code: str, timeout_seconds: int) -> dict[str, Any]:
        return self._request('POST', '/jobs', {'language': language, 'code': code, 'timeout_seconds': timeout_seconds}, timeout=10)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._request('GET', f'/jobs/{job_id}', timeout=5)

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        return self._request('POST', f'/jobs/{job_id}/cancel', {}, timeout=5)
