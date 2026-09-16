"""Selective, pooled HTTP CONNECT transport for rodnoi-agent's urllib callers.

Uses urllib3 (not a custom proxy). No environment proxy or direct fallback.
"""
import os
import urllib.error
from urllib.parse import urlsplit

DEFAULT_HOSTS = ('api.openai.com', 'generativelanguage.googleapis.com', 'api.deepseek.com')


class LlmEgress:
    def __init__(self, proxy_url='', hosts=DEFAULT_HOSTS):
        self.hosts = frozenset(h.lower() for h in hosts)
        self.pool = None
        if not proxy_url:
            return
        parsed = urlsplit(proxy_url)
        if (parsed.scheme != 'http' or not parsed.hostname or not parsed.port
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')):
            raise ValueError('PA_LLM_EGRESS_PROXY_URL must be an HTTP CONNECT endpoint without credentials/path')
        if not self.hosts or any(not h or '/' in h or ':' in h or '*' in h for h in self.hosts):
            raise ValueError('PA_LLM_EGRESS_HOSTS must contain exact DNS hostnames')
        import urllib3
        self.pool = urllib3.ProxyManager(proxy_url, num_pools=8, maxsize=16, block=True,
                                         cert_reqs='CERT_REQUIRED', retries=False)

    def handles(self, url):
        return self.pool is not None and (urlsplit(url).hostname or '').lower() in self.hosts

    def open(self, req, timeout):
        import urllib3
        parsed = urlsplit(req.full_url)
        if parsed.scheme != 'https' or parsed.username or parsed.password:
            raise urllib.error.URLError('LLM egress requires HTTPS without URL credentials')
        if self.pool is None:
            raise urllib.error.URLError('LLM egress is disabled')
        headers = dict(req.header_items())
        headers.pop('Connection', None)
        try:
            response = self.pool.request(req.get_method(), req.full_url, body=req.data,
                                         headers=headers, preload_content=False,
                                         redirect=False, retries=False, pool_timeout=5,
                                         timeout=urllib3.Timeout(connect=5, read=min(float(timeout), 120)))
        except urllib3.exceptions.HTTPError as exc:
            # Do not include URL, headers, provider secrets or raw exception text.
            raise urllib.error.URLError(f'LLM egress unavailable ({type(exc).__name__})') from None
        if response.status >= 300:
            # Provider redirects are intentionally not followed, including to direct hosts.
            raise urllib.error.HTTPError(req.full_url, response.status, 'Provider HTTP error',
                                         response.headers, response)
        return response


TRANSPORT = LlmEgress(os.getenv('PA_LLM_EGRESS_PROXY_URL', '').strip(),
                      tuple(h.strip() for h in os.getenv('PA_LLM_EGRESS_HOSTS', ','.join(DEFAULT_HOSTS)).split(',') if h.strip()))
