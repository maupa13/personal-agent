from __future__ import annotations

import http.client
import json
import socket
from urllib.parse import urlparse
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


class TCPHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, timeout: float = 15):
        super().__init__(host, port=port, timeout=timeout)


class CodeWorkerClient:
    def __init__(self, socket_path: str):
        self.socket_path = str(socket_path)
        self._tcp_target: tuple[str, int] | None = None
        if self.socket_path.startswith('tcp://'):
            parsed = urlparse(self.socket_path)
            host = parsed.hostname or '127.0.0.1'
            port = int(parsed.port or 0)
            if not port:
                raise ValueError('invalid tcp code worker socket')
            self._tcp_target = (host, port)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 15, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
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
        conn: http.client.HTTPConnection
        if self._tcp_target is not None:
            conn = TCPHTTPConnection(self._tcp_target[0], self._tcp_target[1], timeout=timeout)
        else:
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

    def health(self, timeout: float = 1.0, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('GET', '/health', timeout=timeout, trace_headers=trace_headers)

    def create_job(self, language: str, code: str, timeout_seconds: int, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('POST', '/jobs', {'language': language, 'code': code, 'timeout_seconds': timeout_seconds}, timeout=10, trace_headers=trace_headers)

    def get_job(self, job_id: str, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('GET', f'/jobs/{job_id}', timeout=5, trace_headers=trace_headers)

    def cancel_job(self, job_id: str, trace_headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request('POST', f'/jobs/{job_id}/cancel', {}, timeout=5, trace_headers=trace_headers)
