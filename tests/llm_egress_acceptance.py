import io
import os
from pathlib import Path
import socket
import sys
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'services' / 'core' / 'app'))
from llm_egress import LlmEgress
import urllib3


class EgressTests(unittest.TestCase):
    def test_disabled_does_not_intercept_existing_clients(self):
        e = LlmEgress()
        self.assertFalse(e.handles('https://api.openai.com/v1/models'))

    def test_selective_exact_hostname_with_ipv6_and_internal_bypass(self):
        e = LlmEgress('http://127.0.0.1:18981')
        for host in ('api.openai.com', 'generativelanguage.googleapis.com', 'api.deepseek.com'):
            self.assertTrue(e.handles(f'https://{host}/models'))
        for url in ('http://ollama:11434', 'https://example.com', 'https://api.openai.com.evil.test', 'http://[::1]', 'https://172.30.0.10'):
            self.assertFalse(e.handles(url))

    def test_invalid_configuration_fails_at_startup(self):
        for url in ('socks5://localhost:1080', 'http://user:password@localhost:80',
                    'http://localhost', 'http://localhost:80/path', 'http://localhost:99999'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                LlmEgress(url)

    def test_no_direct_fallback_even_with_environment_no_proxy(self):
        # Bind but do not listen, retaining the port so it cannot be reused by another service.
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            e = LlmEgress(f'http://127.0.0.1:{sock.getsockname()[1]}')
            with patch.dict(os.environ, {'NO_PROXY': '*', 'HTTPS_PROXY': 'http://invalid:1'}):
                started = time.monotonic()
                with self.assertRaises(urllib.error.URLError):
                    e.open(urllib.request.Request('https://api.openai.com/v1/models'), 120)
                self.assertLess(time.monotonic() - started, 7)

    def test_pool_reused_timeouts_tls_and_redirects(self):
        e = LlmEgress('http://127.0.0.1:18981')
        pool = e.pool
        self.assertEqual(pool.connection_pool_kw['cert_reqs'], 'CERT_REQUIRED')
        with patch.object(pool, 'request') as request:
            request.return_value = urllib3.HTTPResponse(body=io.BytesIO(b'ok'), status=200, preload_content=False)
            e.open(urllib.request.Request('https://api.openai.com/v1/models'), 300)
            kwargs = request.call_args.kwargs
            self.assertEqual(kwargs['timeout'].connect_timeout, 5)
            self.assertEqual(kwargs['timeout'].read_timeout, 120)
            self.assertFalse(kwargs['redirect'])
            self.assertFalse(kwargs['retries'])
            self.assertIs(e.pool, pool)

    def test_http_errors_preserve_body_without_direct_redirect(self):
        e = LlmEgress('http://127.0.0.1:18981')
        for code in (302, 401, 403, 429, 503):
            response = urllib3.HTTPResponse(body=io.BytesIO(b'provider error'), status=code, preload_content=False)
            with patch.object(e.pool, 'request', return_value=response) as request:
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    e.open(urllib.request.Request('https://api.openai.com/v1/models'), 12)
                self.assertEqual(ctx.exception.code, code)
                self.assertEqual(ctx.exception.read(), b'provider error')
                ctx.exception.close()
                request.assert_called_once()

    def test_selected_hosts_cannot_downgrade_tls(self):
        e = LlmEgress('http://127.0.0.1:18981')
        with self.assertRaises(urllib.error.URLError):
            e.open(urllib.request.Request('http://api.openai.com/v1/models'), 5)


if __name__ == '__main__':
    unittest.main()
