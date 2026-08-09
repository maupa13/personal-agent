from __future__ import annotations

import pathlib
import tempfile
import os
import shutil
import time
from contextlib import contextmanager

ROOT = pathlib.Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / 'release-evidence' / '_tmp' / 'alpha7-live-results'
TMP_ROOT.mkdir(parents=True, exist_ok=True)
@contextmanager
def repo_tmp(prefix: str):
    td = TMP_ROOT / f"{prefix}-{os.getpid()}-{int(time.time() * 1000)}"
    td.mkdir(parents=True, exist_ok=True)
    try:
        yield td
    finally:
        shutil.rmtree(td, ignore_errors=True)

APP = ROOT / "services" / "core" / "app"
import sys
sys.path.insert(0, str(APP))

from scenario_service import ScenarioService

checks: list[str] = []

def ok(test_id: str, name: str, fn) -> None:
    fn(); checks.append(test_id); print(f"[PASS] {test_id} - {name}")

main = (APP / "main.py").read_text(encoding="utf-8")
appjs = (APP / "static" / "app.js").read_text(encoding="utf-8")
css = (APP / "static" / "styles.css").read_text(encoding="utf-8")
index = (APP / "static" / "index.html").read_text(encoding="utf-8")
admin = (APP / "static" / "admin.html").read_text(encoding="utf-8")


def min_seven_contract():
    assert 'PA_LIST_RESULT_MINIMUM", "7"' in main
    assert 'configured_limit = max(configured_limit, LIST_RESULT_MINIMUM)' in main
    assert 'news = bounded("news_max_sources", current["news_max_sources"], 7, 20)' in (APP / "scenario_service.py").read_text(encoding="utf-8")
    assert 'id="searchNewsLimit" type="number" min="7"' in admin
    assert 'id="searchResearchLimit" type="number" min="7"' in admin
ok("RESULT-A7-001", "news/research list target is never configured below seven", min_seven_contract)


def evidence_only_contract():
    for token in (
        'concrete news/product/object/tender list',
        'Missing items are never invented',
        'card_sources = usable if result_kind in LIST_RESULT_KINDS else sources',
        'недостающие варианты не добавляю по памяти',
    ):
        assert token in main, token
ok("RESULT-A7-002", "list text and cards share the same verified evidence set with no padding", evidence_only_contract)


def news_clarification_and_interests():
    with repo_tmp("alpha7") as td:
        svc = ScenarioService(pathlib.Path(td) / "db.sqlite")
        svc.init_schema()
        first = svc.prepare(user_id="u", conversation_id="c1", text="Собери свежие новости по интересующей меня теме и объясни главное", explicit_scenario_id="news")
        assert first["action"] == "clarify"
        assert "Главное" in first["options"] and len(first["options"]) >= 7
        second = svc.prepare(user_id="u", conversation_id="c1", text="Главное")
        assert second["action"] == "execute"
        assert second["task_text"] == "главные свежие новости сегодня"

        svc.set_preferences("u2", {"news_interests": ["Технологии", "Игры"]})
        saved = svc.prepare(user_id="u2", conversation_id="c2", text="Собери свежие новости по интересующей меня теме и объясни главное", explicit_scenario_id="news")
        assert saved["action"] == "execute"
        assert "Технологии" in saved["task_text"] and "Игры" in saved["task_text"]
ok("NEWS-A7-001", "generic news asks once; Main and saved interests become concise search intent", news_clarification_and_interests)


def selection_contract():
    assert "state.scenarioId=null;if(kind==='preset'){state.intentHint='auto'" in appjs
    assert "state.preset='none';localStorage.setItem(PRESET_KEY,'none');state.intentHint=item.id" not in appjs
    assert "state.scenarioId=item.id;state.preset='none';state.intentHint='auto'" in appjs
    assert ".scenario-card.active" in css and ".starter-card.active" in css
    assert ":focus-visible" in css
ok("UX-SELECT-A7-001", "scenario and quick-action selection are mutually exclusive and focus is distinct", selection_contract)


def scale_animation_contract():
    for token in ('id="uiScale"', 'compact', 'large'):
        assert token in index, token
    for token in ('function applyUiScale', 'function progressiveReveal', 'prefers-reduced-motion', 'data-ui-scale="compact"', 'data-ui-scale="large"'):
        assert token in appjs + css, token
ok("UX-LIVE-A7-001", "UI scale and reduced-motion-safe progressive answer reveal ship", scale_animation_contract)


def interest_ui_contract():
    assert 'id="webNewsInterests"' in index
    assert 'News topics I care about' in appjs
ok("NEWS-A7-002", "news interests are editable and localized in USER settings", interest_ui_contract)

print(f"PAR_V080_ALPHA7_LIVE_RESULTS_ACCEPTANCE PASS: {len(checks)} checks")
