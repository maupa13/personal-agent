from __future__ import annotations

import json
import os
import pathlib
import time
import traceback
from playwright.sync_api import Browser, BrowserContext, Locator, Page, sync_playwright

BASE = os.getenv("PA_BASE_URL", "http://host.docker.internal:3100").rstrip("/")
TOKEN = os.getenv("PA_ADMIN_TOKEN", "")
BOOTSTRAP_MODEL = os.getenv("PA_BOOTSTRAP_MODEL", "qwen3:0.6b")
ARTIFACT_DIR = pathlib.Path(os.getenv("PA_ARTIFACT_DIR", "/tmp/par-acceptance-artifacts"))
DETERMINISTIC_BACKEND = os.getenv("PA_DETERMINISTIC_BACKEND", "0") == "1"
USER_XSS = '<img src=x onerror=window.__parUserXss=1>'
ASSISTANT_XSS = '<img src=x onerror=window.__parXss=1>'
ADMIN_XSS = '<img src=x onerror=window.__parXssAdmin=1>'


def wait_ready(page: Page) -> None:
    deadline = time.monotonic() + 120
    last = None
    while time.monotonic() < deadline:
        try:
            response = page.request.get(BASE + "/api/health", timeout=3000)
            body = response.json()
            last = (response.status, body)
            if response.status == 200 and body.get("ready") is True:
                return
        except Exception as exc:
            last = repr(exc)
        time.sleep(0.25)
    raise AssertionError(f"Personal Agent Rus did not become ready: {last}")


def wait_count(locator: Locator, expected: int, timeout_ms: int = 15000) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    last = None
    while time.monotonic() < deadline:
        try:
            last = locator.count()
            if last == expected:
                return
        except Exception as exc:
            last = repr(exc)
        time.sleep(0.1)
    raise AssertionError(f"Expected locator count {expected}, got {last}")


def wait_new_item(locator: Locator, previous_count: int, timeout_ms: int = 180000) -> None:
    locator.nth(previous_count).wait_for(state="visible", timeout=timeout_ms)
    count = locator.count()
    if count <= previous_count:
        raise AssertionError(f"Expected a new item after index {previous_count - 1}, got {count}")


def wait_text(locator: Locator, needle: str | None = None, *, nonempty: bool = False, timeout_ms: int = 15000) -> str:
    deadline = time.monotonic() + timeout_ms / 1000
    last = ""
    while time.monotonic() < deadline:
        try:
            last = (locator.text_content() or "").strip()
            if needle is not None and needle in last:
                return last
            if nonempty and last:
                return last
        except Exception:
            pass
        time.sleep(0.1)
    expectation = f"containing {needle!r}" if needle is not None else "non-empty"
    raise AssertionError(f"Expected text {expectation}; last value was {last!r}")


def new_page(browser: Browser, name: str, viewport: dict[str, int]) -> tuple[BrowserContext, Page, dict[str, list[str]]]:
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    events: dict[str, list[str]] = {"console": [], "page_errors": [], "network_errors": []}
    page.on("console", lambda msg: events["console"].append(f"{msg.type}: {msg.text}"))
    page.on("pageerror", lambda exc: events["page_errors"].append(str(exc)))
    page.on("requestfailed", lambda req: events["network_errors"].append(f"{req.method} {req.url}: {req.failure}"))
    return context, page, events


def attach_diagnostics(page: Page, events: dict[str, list[str]], name: str, extra: dict | None = None) -> None:
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(ARTIFACT_DIR / f"{name}.png"), full_page=True)
        (ARTIFACT_DIR / f"{name}.html").write_text(page.content(), encoding="utf-8")
        (ARTIFACT_DIR / f"{name}-console.log").write_text("\n".join(events["console"]), encoding="utf-8")
        (ARTIFACT_DIR / f"{name}-page-errors.log").write_text("\n".join(events["page_errors"]), encoding="utf-8")
        (ARTIFACT_DIR / f"{name}-network-errors.log").write_text("\n".join(events["network_errors"]), encoding="utf-8")
        ctx = {
            "name": name,
            "base_url": BASE,
            "url": page.url,
            "title": page.title() if page.url else "",
            "timestamp": int(time.time()),
            "deterministic_backend": DETERMINISTIC_BACKEND,
            "extra": extra or {},
        }
        (ARTIFACT_DIR / f"{name}-test-context.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def assert_no_browser_errors(events: dict[str, list[str]], phase: str) -> None:
    errors = events["page_errors"] + [x for x in events["console"] if x.lower().startswith("error:")]
    if errors:
        raise AssertionError(f"Browser errors during {phase}: {errors}")


def user_journey(browser: Browser) -> None:
    context, page, events = new_page(browser, "desktop-user", {"width": 1440, "height": 900})
    try:
        wait_ready(page)
        response = page.goto(BASE + "/", wait_until="domcontentloaded")
        assert response is not None and response.ok, f"USER page load failed: {response.status if response else 'no response'}"
        csp = response.headers.get("content-security-policy", "")
        cache_control = response.headers.get("cache-control", "")
        assert "script-src 'self'" in csp and "unsafe-eval" not in csp, f"Unexpected CSP: {csp}"
        assert "no-store" in cache_control, f"USER UI may be stale after update: Cache-Control={cache_control!r}"
        assert page.title() == "Personal Agent Rus"
        body = page.locator("body").inner_text().lower()
        for secret in ("qwen", "ollama", "model_id", "par-rus-ollama"):
            assert secret not in body, f"USER leaked {secret}"
        wait_count(page.locator(".mode"), 3)
        assert page.locator('a[href="/admin"]').count() >= 1
        assert page.locator('#sidebar').is_visible() and page.locator('#newChat').is_visible() and page.locator('.composer').is_visible()
        assert page.locator('#chatSearch').is_visible() and page.locator('#settingsEntry').is_visible()
        assert page.locator('#clearAllShortcut').is_visible() and page.locator('#chatMenuButton').is_visible()

        for label in ("Авто", "Быстро", "Умно"):
            page.get_by_role("button", name=label, exact=False).click()
            page.locator("#input").fill(f"Ответь одним словом: тест режима {label}")
            assistant = page.locator(".msg.assistant")
            before = assistant.count()
            page.locator("#send").click()
            wait_new_item(assistant, before, timeout_ms=180000)
            assert assistant.last.inner_text().strip()

        # Rus edition must not fall back to an English greeting/default on a short neutral Russian reply.
        assistant = page.locator(".msg.assistant")
        before = assistant.count()
        page.locator("#input").fill("ок")
        page.locator("#send").click()
        wait_new_item(assistant, before, timeout_ms=180000)
        short_reply = assistant.last.inner_text().strip()
        assert any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in short_reply), f"Rus short reply is not Russian: {short_reply!r}"

        # Web is a real capability in v0.3.0. The deterministic fixture exercises the
        # complete UI -> Core -> search/fetch -> evidence -> model path without external internet.
        # The real-runtime suite validates UI readiness; live DTF is a separate WEB-ACCEPTANCE canary
        # so an external outage never makes the general browser suite flaky.
        system = page.request.get(BASE + "/api/system", timeout=5000).json()
        assert system.get("capabilities", {}).get("web", {}).get("status") == "ready"
        assert system.get("capabilities", {}).get("research", {}).get("status") == "ready"
        if DETERMINISTIC_BACKEND:
            assistant_web = page.locator(".msg.assistant")
            before_web = assistant_web.count()
            page.locator('#input').fill('Выдай новости с https://dtf.ru/')
            page.locator('#send').click()
            wait_new_item(assistant_web, before_web, timeout_ms=30000)
            assert page.locator('.message-sources .source-card').count() >= 1, "Web response has no source evidence"
            assert 'веб-доступ' not in assistant_web.last.inner_text().lower()

        # Real-model live acceptance must never depend on a stochastic model echoing an exact payload.
        # USER-origin hostile HTML is always deterministic and must remain text under the production UI/CSP.
        assistant = page.locator(".msg.assistant")
        users = page.locator(".msg.user")
        before_assistant = assistant.count()
        before_user = users.count()
        probe = "PAR_XSS" if DETERMINISTIC_BACKEND else USER_XSS
        page.locator("#input").fill(probe)
        page.locator("#send").click()
        wait_new_item(users, before_user, timeout_ms=15000)
        wait_new_item(assistant, before_assistant, timeout_ms=180000)

        if DETERMINISTIC_BACKEND:
            assert ASSISTANT_XSS in assistant.last.inner_text(), "Controlled backend did not return the assistant XSS fixture"
            assert page.evaluate("window.__parXss") is None
        else:
            assert USER_XSS in users.last.inner_text(), "Hostile USER payload was not rendered as literal text"
            assert page.evaluate("window.__parUserXss") is None
        assert page.locator("#chat img").count() == 0, "Hostile chat content created executable image DOM"

        # Product Shell controls are functional in the real HTTP/CSP path, not merely present in static HTML.
        page.locator("#chatMenuButton").click()
        page.locator('#chatMenu [data-action="rename"]').click()
        page.locator("#actionInput").fill("Acceptance chat")
        page.locator("#actionConfirm").click()
        assert page.locator("#conversationTitle").inner_text() == "Acceptance chat"
        page.locator("#chatSearch").fill("Acceptance")
        assert page.locator(".conversation-item").count() == 1
        page.locator("#chatSearch").fill("")
        page.locator("#settingsEntry").click()
        page.locator("#settingsBackdrop").wait_for(state="visible", timeout=5000)
        page.get_by_role("button", name="Данные", exact=True).click()
        assert page.locator("#clearCurrentChat").is_visible() and page.locator("#clearAllChats").is_visible()
        page.locator("#closeSettings").click()

        assert page.evaluate("localStorage.getItem('par-mode')") == "smart"
        saved = page.evaluate("localStorage.getItem('par-chat')")
        assert saved and "тест режима" in saved

        page.reload(wait_until="domcontentloaded")
        wait_count(page.locator(".mode"), 3)
        assert page.locator(".mode.active").inner_text().startswith("Умно")
        assert "тест режима" in page.locator("#chat").inner_text()
        assert_no_browser_errors(events, "USER journey")
    except Exception:
        attach_diagnostics(page, events, "desktop-user-failure", {"phase": "user"})
        raise
    finally:
        context.close()


def mobile_journey(browser: Browser) -> None:
    context, page, events = new_page(browser, "mobile-user", {"width": 390, "height": 844})
    try:
        response = page.goto(BASE + "/", wait_until="domcontentloaded")
        assert response is not None and response.ok
        wait_count(page.locator(".mode"), 3)
        assert page.locator("#input").is_visible() and page.locator("#send").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2")
        page.locator("#openSidebar").click()
        page.wait_for_timeout(260)
        box = page.locator("#sidebar").bounding_box()
        assert box and box["x"] >= -1, f"Mobile sidebar stayed off-screen: {box}"
        assert page.locator('a[href="/admin"]').count() >= 1
        page.locator("#closeSidebar").click()
        assistant = page.locator(".msg.assistant")
        before = assistant.count()
        page.locator("#input").fill("Коротко ответь: мобильный тест")
        page.locator("#send").click()
        wait_new_item(assistant, before, timeout_ms=180000)
        assert assistant.last.inner_text().strip()
        assert_no_browser_errors(events, "mobile journey")
    except Exception:
        attach_diagnostics(page, events, "mobile-user-failure", {"phase": "mobile"})
        raise
    finally:
        context.close()


def admin_journey(browser: Browser) -> None:
    if not TOKEN:
        raise AssertionError("PA_ADMIN_TOKEN not supplied to live browser acceptance")
    context, page, events = new_page(browser, "admin", {"width": 1280, "height": 900})
    try:
        response = page.goto(BASE + "/admin", wait_until="domcontentloaded")
        assert response is not None and response.ok
        assert "no-store" in response.headers.get("cache-control", ""), "ADMIN UI may be stale after update"
        page.locator("#token").fill("definitely-wrong-token")
        page.locator("#loginBtn").click()
        wait_text(page.locator("#loginError"), nonempty=True)

        page.locator("#token").fill(TOKEN)
        page.locator("#loginBtn").click()
        page.locator("#admin").wait_for(state="visible", timeout=15000)
        page.get_by_role("button", name="Маршрутизация").click()

        models = page.locator("#models .model-item")
        if models.count() < 1:
            raise AssertionError("Admin UI returned no installed models")
        assert page.locator("#models img").count() == 0, "Model names must not create executable HTML"
        if DETERMINISTIC_BACKEND:
            assert ADMIN_XSS in page.locator("#models").inner_text(), "Controlled backend did not expose the admin XSS fixture as data"
            assert page.evaluate("window.__parXssAdmin") is None

        selects = page.locator("select[data-mode]")
        wait_count(selects, 3)
        original = {mode: page.locator(f'select[data-mode="{mode}"]').input_value() for mode in ("auto", "fast", "smart")}
        option_values = page.locator('select[data-mode="smart"] option').evaluate_all("els => els.map(e => e.value)")
        target = next((value for value in option_values if value != original["smart"]), original["smart"])
        assert target

        page.locator('select[data-mode="smart"]').select_option(target)
        page.locator("#saveRoutes").click()
        wait_text(page.locator("#saveState"), "Сохранено")

        # Pull an already-cached bootstrap model. On the reference host this should be fast,
        # exercises the async job UI, and avoids forcing another large model download.
        page.get_by_role("button", name="Модели").click()
        page.locator("#pullModel").fill(BOOTSTRAP_MODEL)
        page.locator("#pullBtn").click()
        state = wait_text(page.locator("#pullState"), "completed", timeout_ms=120000)
        assert "100%" in state

        # Session-scoped admin login and the saved routing must survive page reload.
        page.reload(wait_until="domcontentloaded")
        page.locator("#admin").wait_for(state="visible", timeout=15000)
        page.get_by_role("button", name="Маршрутизация").click()
        assert page.locator('select[data-mode="smart"]').input_value() == target

        # Acceptance must restore the pre-test routing so a test never mutates the owner's configuration.
        for mode, value in original.items():
            page.locator(f'select[data-mode="{mode}"]').select_option(value)
        page.locator("#saveRoutes").click()
        wait_text(page.locator("#saveState"), "Сохранено")
        page.reload(wait_until="domcontentloaded")
        page.locator("#admin").wait_for(state="visible", timeout=15000)
        page.get_by_role("button", name="Маршрутизация").click()
        for mode, value in original.items():
            assert page.locator(f'select[data-mode="{mode}"]').input_value() == value

        assert_no_browser_errors(events, "ADMIN journey")
    except Exception:
        attach_diagnostics(page, events, "admin-failure", {"phase": "admin"})
        raise
    finally:
        context.close()


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        chromium_override = os.getenv("PA_TEST_CHROMIUM")
        launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
        if chromium_override:
            launch_kwargs["executable_path"] = chromium_override
        browser = p.chromium.launch(**launch_kwargs)
        try:
            user_journey(browser)
            mobile_journey(browser)
            admin_journey(browser)
        except Exception:
            traceback.print_exc()
            print(f"PAR_LIVE_BROWSER_ACCEPTANCE artifacts: {ARTIFACT_DIR}")
            return 1
        finally:
            browser.close()
    mode = "deterministic-security-backend" if DETERMINISTIC_BACKEND else "real-runtime"
    print(f"PAR_LIVE_BROWSER_ACCEPTANCE PASS: {mode} strict-csp cache-version product-shell history-search-settings desktop modes rus-language chat web-ready web-evidence xss persistence mobile-chat admin-routing model-pull cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
