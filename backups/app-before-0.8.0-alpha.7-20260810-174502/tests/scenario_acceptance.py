from __future__ import annotations

import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = ROOT / "services" / "core" / "app"
sys.path.insert(0, str(CORE))

from scenario_service import BY_ID, ScenarioService, ScenarioError  # noqa: E402


def check(value: bool, test_id: str, message: str) -> None:
    if not value:
        raise AssertionError(f"{test_id}: {message}")
    print(f"[PASS] {test_id} - {message}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="par-scenarios-") as tmp:
        svc = ScenarioService(pathlib.Path(tmp) / "scenario.db")
        svc.init_schema()
        full = {name: {"enabled": True} for name in ("web", "research")}
        web_only = {"web": {"enabled": True}, "research": {"enabled": False}}
        ids = {item["id"] for item in svc.list_scenarios(full)}
        check({"clothing", "procurement", "real_estate", "gift", "product", "travel", "news"}.issubset(ids), "SCN-001", "Scenario Gallery exposes daily-life and work journeys")
        limited = {item["id"] for item in svc.list_scenarios(web_only)}
        check("clothing" in limited and "procurement" not in limited, "SCN-002", "Scenario Gallery follows backend entitlements")
        check(svc.detect("подбери мне летние шорты") and svc.detect("подбери мне летние шорты").scenario_id == "clothing", "SCN-003", "Auto detects clothing without a scenario-card click")
        check(svc.detect("привет, как дела") is None, "SCN-004", "Ordinary chat is not hijacked by Scenario Engine")
        check(svc.detect("https://rbc.ru/ какие новости сегодня?") is None, "SCN-004A", "Explicit URL routing has priority over Auto Scenario detection")

        first = svc.prepare(user_id="u1", conversation_id="c1", text="Подбери мне одежду")
        check(first["action"] == "clarify" and first["round"] == 1 and first["max_rounds"] == 1, "SCN-005", "Consumer scenario asks one grouped high-value clarification")
        second = svc.prepare(user_id="u1", conversation_id="c1", text="Мужчина, размер XL, бюджет до 15000 рублей, на лето")
        check(second["action"] == "execute" and "Дополнительные параметры" in second["combined_text"], "SCN-006", "Scenario continues after clarification with accumulated context")
        check("Дополнительные параметры" not in second["task_text"] and "XL" in second["task_text"], "SCN-006A", "Execution/search text contains user context without internal scaffolding")

        q1 = svc.prepare(user_id="u2", conversation_id="c2", text="Найди закупки")
        q2 = svc.prepare(user_id="u2", conversation_id="c2", text="Москва")
        q3 = svc.prepare(user_id="u2", conversation_id="c2", text="поставка серверов, до 10 млн, только актуальные")
        check(q1["action"] == "clarify" and q2["action"] == "clarify" and q3["action"] == "execute", "SCN-007", "Complex procurement scenario is bounded to at most two clarification rounds")
        check(svc._signal_count(BY_ID["procurement"], "Найди закупки\n\nДополнительные параметры пользователя: Москва") == 1, "SCN-007A", "Internal clarification scaffolding never counts as user evidence")

        prefs = svc.set_preferences("u1", {"search_scope": "selected", "region": "Москва", "allowed_domains": ["cian.ru", "zakupki.gov.ru"], "excluded_domains": ["example.com"], "prefer_russian": True})
        reopened = ScenarioService(pathlib.Path(tmp) / "scenario.db"); reopened.init_schema()
        check(reopened.preferences("u1") == prefs and prefs["search_scope"] == "selected", "SITE-001", "User Web/site preferences persist server-side")
        try:
            svc.set_preferences("u1", {"search_scope": "selected", "allowed_domains": ["http://bad/path"]})
            raise AssertionError("invalid domain accepted")
        except ScenarioError:
            pass
        check(True, "SITE-002", "Invalid site preference is rejected")
        profiles = svc.site_profiles(); check(any(p["id"] == "cian" for p in profiles), "SITE-003", "Known site profiles are seeded as Admin data")
        changed = svc.update_site_profile("cian", enabled=True, acquisition_order="browser,static,search", egress_region="ru")
        check(changed["acquisition_order"] == "browser,static,search" and changed["egress_region"] == "ru", "SITE-004", "Admin can persist technical site strategy")

    main_py = (CORE / "main.py").read_text(encoding="utf-8")
    app_js = (CORE / "static/app.js").read_text(encoding="utf-8")
    index = (CORE / "static/index.html").read_text(encoding="utf-8")
    admin_js = (CORE / "static/admin.js").read_text(encoding="utf-8")
    admin_html = (CORE / "static/admin.html").read_text(encoding="utf-8")
    check(all(x in main_py for x in ("/api/scenarios", "/api/preferences/web", "/api/admin/site-profiles", "SCENARIOS.prepare", "inject_scenario_instruction")), "SCN-008", "Core exposes Scenario/Preferences/Admin site contracts")
    check("scenario-grid" in app_js and "scenario_id:state.scenarioId" in app_js and "saveWebPreferences" in app_js, "SCN-009", "USER UI includes scenario-first flow and Web preferences")
    check("webSearchScope" in index and "webAllowedDomains" in index and "webExcludedDomains" in index, "SITE-005", "USER Web settings are understandable instead of technical site profiles")
    check("siteProfiles" in admin_js and "Сайты и поиск" in admin_html, "SITE-006", "Admin UI exposes technical site profiles separately from USER preferences")

    print("PAR_V080_ALPHA3_SCENARIO_ACCEPTANCE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
