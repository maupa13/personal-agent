# Security

External web/file/tool content is untrusted data, never instruction authority. Web requests enforce SSRF policy: only public http(s), no embedded credentials, loopback/private/link-local/metadata/internal runtime targets blocked, redirects revalidated. Browser worker receives no Docker socket/provider secrets.

USER/ADMIN boundaries remain strict. Future file/code workers must use isolated workspaces and bounded sandboxes.

## v0.7 public server session hardening

When `PA_RUNTIME_PROFILE=server`, `PA_SECURE_COOKIES` defaults to enabled and generated server bundles force it on. Account session cookies are `HttpOnly`, `SameSite=Lax` and `Secure`. State-changing USER requests in `PA_AUTH_MODE=accounts` require `X-CSRF-Token`; the token is derived per session using HMAC and is returned only through authenticated same-origin auth state. Missing/incorrect CSRF fails with HTTP 403. Admin API continues to require its explicit Bearer token and does not reuse USER cookie authority.

VPS SSH credentials are operation-scoped only. Persisted deployment target rows contain host metadata and the expected SSH host-key SHA256 fingerprint, never password/private-key/passphrase. Public deploy success additionally requires trusted HTTPS exact-version verification.
