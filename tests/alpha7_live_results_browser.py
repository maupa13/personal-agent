from __future__ import annotations

import importlib.util
import pathlib

from playwright.sync_api import expect, sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("browser_fixtures", ROOT / "tests/browser_journeys.py")
fixtures = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(fixtures)


def check(condition: bool, test_id: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{test_id}: {message}")
    print(f"[PASS] {test_id} - {message}", flush=True)


def main() -> int:
    executable = fixtures.chromium_path()
    if not executable:
        raise SystemExit("No Chromium/Chrome executable found; set PA_TEST_CHROMIUM")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=executable, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        fixtures.load_user(page)

        # Add the current news scenario to the deterministic fixture and rerender.
        page.evaluate("""
          window.__backend.scenarios.push({
            id:'news',title:'Разобраться в новостях',description:'Собрать свежие источники и объяснить, что произошло',
            category:'life',icon:'◉',required_capabilities:['web'],example_prompt:'Собери свежие новости по интересующей меня теме и объясни главное.',
            max_clarification_rounds:1,clarification_options:['Главное','Технологии','Игры','Россия','Мир','Бизнес','Наука','Спорт','Другое']
          });
          state.scenarios=JSON.parse(JSON.stringify(window.__backend.scenarios)); renderAll();
        """)
        news = page.locator('.scenario-card[data-scenario="news"]')
        expect(news).to_be_visible()

        # A scenario and a quick action must never look selected at the same time.
        page.locator('.starter-card[data-intent="research"]').click()
        expect(page.locator('.starter-card.active')).to_have_count(1)
        expect(page.locator('.scenario-card.active')).to_have_count(0)
        news.click()
        expect(page.locator('.scenario-card.active')).to_have_count(1)
        expect(page.locator('.starter-card.active')).to_have_count(0)
        page.locator('.starter-card[data-preset="explain"]').click()
        expect(page.locator('.starter-card.active')).to_have_count(1)
        expect(page.locator('.scenario-card.active')).to_have_count(0)
        check(True, "UX-SELECT-A7-BROWSER", "scenario and quick-action selected states are mutually exclusive")

        # UI scale changes the actual rendered density and persists through the preference flow.
        normal_h = page.locator('.starter-card').first.bounding_box()["height"]
        page.locator('#settingsEntry').click()
        page.locator('#uiScale').select_option('compact')
        page.locator('#saveExperiencePreferences').click()
        expect(page.locator('#experienceState')).to_contain_text('Сохран')
        page.locator('#closeSettings').click()
        compact_h = page.locator('.starter-card').first.bounding_box()["height"]
        check(compact_h < normal_h, "UX-SCALE-A7-BROWSER", "compact scale reduces actual card/button density")
        check(page.evaluate("document.documentElement.dataset.uiScale") == "compact", "UX-SCALE-A7-PERSIST", "selected UI scale is applied to the document")

        # Render seven evidence-backed cards from one source array: no text/card count split.
        sources = [{
            "title": f"Проверенная новость {i}",
            "url": f"https://dtf.ru/news/{i}",
            "domain": "dtf.ru",
            "status": "retrieved",
            "strategy": "browser",
            "kind": "news",
            "summary": f"Фактическое описание новости {i}",
            "published_date": f"2026-08-10T1{i}:00:00Z",
        } for i in range(1, 8)]
        page.evaluate("""sources => {
          const c=current(); c.messages=[];
          const m=addMessage({role:'assistant',content:'Нашёл семь проверенных материалов.',sources,metadata:{source_count:sources.length,duration_ms:812,web_ms:500,inference_ms:250}});
          state.animateMessageId=null; renderAll();
        }""", sources)
        expect(page.locator('.message-sources .result-card')).to_have_count(7)
        expect(page.locator('.sources-title')).to_contain_text('7')
        check(page.locator('.message-sources .result-card').count() == 7, "RESULT-A7-BROWSER-001", "seven verified sources render as seven result cards")

        # Clarification options use compact quick-reply chips.
        page.evaluate("""() => {
          const c=current(); c.messages=[];
          addMessage({role:'assistant',content:'Что вам сейчас интереснее?',metadata:{quick_replies:['Главное','Технологии','Игры','Россия','Мир','Бизнес','Наука','Спорт','Другое']}});
          renderAll();
        }""")
        expect(page.locator('.quick-reply')).to_have_count(9)
        expect(page.locator('.quick-reply').first).to_have_text('Главное')
        check(True, "NEWS-A7-BROWSER-001", "bounded news clarification is presented as one-tap quick replies")

        # Answer reveal is visibly progressive, then resolves to full rich text.
        full = "Это длинный проверяемый ответ, который появляется постепенно и остаётся доступным при отключённой анимации. " * 6
        page.evaluate("""content => {
          const c=current(); c.messages=[];
          const m=addMessage({role:'assistant',content,sources:[]});
          state.animateMessageId=m.id; renderAll();
        }""", full)
        bubble = page.locator('.msg.assistant').last
        page.wait_for_timeout(80)
        early = bubble.inner_text()
        check(len(early) < len(full), "UX-LIVE-A7-BROWSER-001", "new assistant answer is progressively revealed rather than painted as one block")
        page.wait_for_timeout(2300)
        final = bubble.inner_text()
        check(len(final) >= len(full.strip()) - 2, "UX-LIVE-A7-BROWSER-002", "progressive reveal finishes with the complete answer")

        # Stop any UI animation before tearing down the explicit context. Keeping
        # one owned context makes Playwright shutdown deterministic after the
        # progressive-reveal test instead of leaving an implicit page context.
        page.evaluate("state.animateMessageId=null")
        page.close(); context.close(); browser.close()
    print("PAR_V080_ALPHA7_LIVE_RESULTS_BROWSER PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
