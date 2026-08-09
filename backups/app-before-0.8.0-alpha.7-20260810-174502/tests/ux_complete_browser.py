from __future__ import annotations

import importlib.util
import pathlib
import re

from playwright.sync_api import expect, sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("browser_fixtures", ROOT / "tests/browser_journeys.py")
fixtures = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(fixtures)


def check(condition: bool, test_id: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{test_id}: {message}")
    print(f"[PASS] {test_id} - {message}")


def main() -> int:
    executable = fixtures.chromium_path()
    if not executable:
        raise SystemExit("No Chromium/Chrome executable found; set PA_TEST_CHROMIUM")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=executable, args=["--no-sandbox"])

        page = browser.new_page(viewport={"width": 1440, "height": 900})
        fixtures.load_user(page)
        expect(page.locator("#brandName")).to_have_text("Родной Агент")
        check(page.title() == "Родной Агент", "BRAND-A5-BROWSER-RU", "RU shell uses Родной Агент")

        # Keyboard resize and collapse must work without a mouse.
        resizer = page.locator("#sidebarResizer")
        before = int(resizer.get_attribute("aria-valuenow") or "282")
        resizer.focus(); page.keyboard.press("ArrowRight")
        after = int(resizer.get_attribute("aria-valuenow") or "0")
        check(after > before, "A11Y-A5-BROWSER-RESIZE", "sidebar resizer responds to keyboard")
        page.keyboard.press("Control+b")
        expect(page.locator("#sidebar")).to_have_class(re.compile("collapsed"))
        check(page.locator("#folders").is_hidden() and page.locator("#conversations").is_hidden(), "UX-A5-BROWSER-COLLAPSE", "collapsed rail does not compress project/chat rows")
        page.keyboard.press("Control+b")

        # Switch the complete user experience to English + light + local-only + meme tone.
        page.locator("#settingsEntry").click()
        page.locator("#uiLanguage").select_option("en")
        page.locator("#responseLanguage").select_option("en")
        page.locator("#themeSelect").select_option("light")
        page.locator("#executionPolicy").select_option("local_only")
        page.locator("#tonePreset").select_option("meme")
        page.locator("#saveExperiencePreferences").click()
        expect(page.locator("#experienceState")).to_contain_text("Saved")
        expect(page.locator("#brandName")).to_have_text("Personal Agent")
        expect(page.locator("#newChat")).to_contain_text("New chat")
        check(page.title() == "Personal Agent", "I18N-A5-BROWSER-SHELL", "EN switch updates shell title and brand")
        check(page.evaluate("document.documentElement.dataset.theme") == "light", "THEME-A5-BROWSER", "light theme applies immediately")
        check(page.evaluate("window.__backend.experiencePreferences.execution_policy") == "local_only", "EXEC-A5-BROWSER", "local-only selection persists through backend preference flow")
        check(page.locator("#feedbackMessage").get_attribute("placeholder") == "What should be improved?", "I18N-A5-BROWSER-FEEDBACK", "feedback placeholder follows UI language")
        check(page.locator("#sidebarResizer").get_attribute("aria-label") == "Resize sidebar", "A11Y-A5-BROWSER-I18N", "sidebar accessibility label follows UI language")

        # Full USER tour must be localized, not only its first step.
        page.locator("#closeSettings").click()
        page.locator("#brandHelp").click(); page.locator("#restartTour").click(); expect(page.locator("#tourProgress")).to_contain_text("1 of")
        for idx in range(9):
            title = page.locator("#tourTitle").inner_text()
            body = page.locator("#tourText").inner_text()
            check(not re.search(r"[А-Яа-яЁё]", title + body), f"I18N-A5-TOUR-{idx+1:02d}", f"USER tour step {idx+1} is English")
            if idx < 8:
                page.locator("#tourNext").click()
        page.locator("#tourNext").click()
        expect(page.locator("#tourLayer")).to_be_hidden()

        # State matrix is visible, accessible, and recoverable through Retry.
        page.evaluate("showRuntimeState('offline', tr('runtimeOfflineTitle'), tr('runtimeOfflineDetail'))")
        expect(page.locator("#runtimeStateBanner")).to_be_visible()
        expect(page.locator("#runtimeStateTitle")).to_contain_text("Connection")
        expect(page.locator("#runtimeRetry")).to_have_text("Retry")
        check(page.locator("#runtimeStateBanner").get_attribute("aria-live") == "polite", "UX-009-BROWSER-STATE", "offline state is accessible and offers Retry")

        # Wide fields: the actual textarea/editor should use most of their content panel width.
        page.locator("#settingsEntry").click(); page.locator('[data-settings-tab="web"]').click()
        web = page.locator("#webExcludedDomains").bounding_box(); panel = page.locator(".settings-content").bounding_box()
        check(bool(web and panel and web["width"] >= panel["width"] * 0.75), "UX-A5-BROWSER-WEB-FORM", "Web domain textarea uses the content width")
        page.locator('[data-settings-tab="code"]').click()
        editor = page.locator("#codeEditor").bounding_box(); panel = page.locator(".settings-content").bounding_box()
        check(bool(editor and panel and editor["width"] >= panel["width"] * 0.75), "UX-A5-BROWSER-CODE-FORM", "code editor uses the content width")
        page.close()

        # Account page gets real EN dynamic billing copy, not only an English header.
        account = browser.new_page(viewport={"width": 1100, "height": 800})
        account.set_content(fixtures.ACCOUNT)
        fixtures.install_storage(account, "localStorage", {"par-ui-language": "en", "par-theme-preference": "light"})
        account.add_style_tag(content=fixtures.CSS); account.add_script_tag(content=fixtures.BACKEND_STUB); account.add_script_tag(content=fixtures.AUTH_JS)
        expect(account.locator("#billingAccount")).to_be_visible()
        expect(account.locator("#currentPlan")).to_have_text("Light")
        check("Local:" in account.locator("#usageSummary").inner_text(), "I18N-A5-BROWSER-ACCOUNT", "account billing details are localized to English")
        account.close()

        # Admin has independent EN/theme UX and keeps the real model/routing surface.
        admin = browser.new_page(viewport={"width": 1280, "height": 900})
        fixtures.load_admin(admin)
        expect(admin.locator("#admin")).to_be_visible()
        admin.locator("#adminLocaleToggle").click()
        expect(admin.locator("#adminBrandName")).to_have_text("Personal Agent")
        expect(admin.get_by_role("button", name="Models", exact=True)).to_be_visible()
        expect(admin.get_by_role("button", name="Routing", exact=True)).to_be_visible()
        overview_copy = admin.locator('[data-panel="overview"]').inner_text()
        check(not re.search(r"[А-Яа-яЁё]", overview_copy), "ADMIN-A5-BROWSER-DYNAMIC-I18N", "Admin overview dynamic product copy is localized to English")
        admin.get_by_role("button", name="Routing", exact=True).click()
        expect(admin.locator('select[data-mode="smart"]')).to_be_visible()
        before_theme=admin.evaluate("document.documentElement.dataset.theme")
        admin.locator("#adminThemeToggle").click()
        after_theme=admin.evaluate("document.documentElement.dataset.theme")
        check(after_theme in {"light","dark"} and after_theme!=before_theme, "ADMIN-A5-BROWSER-THEME", "Admin theme toggle applies")
        check(admin.title() == "Administration — Personal Agent", "ADMIN-A5-BROWSER-I18N", "Admin title is localized")
        admin.close()
        browser.close()

    print("PAR_V080_ALPHA5_UX_COMPLETE_BROWSER PASS")
    return 0


def page_is_theme(page, expected: str) -> bool:
    return page.evaluate("document.documentElement.dataset.theme") == expected


if __name__ == "__main__":
    raise SystemExit(main())
