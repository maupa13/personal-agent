from __future__ import annotations

import pathlib
import os
import shutil
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = ROOT / "services" / "core" / "app"
TMP_ROOT = ROOT / "release-evidence" / "_tmp" / "scenario-acceptance"
TMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(CORE))

from scenario_service import BY_ID, ScenarioService, ScenarioError  # noqa: E402


def check(value: bool, test_id: str, message: str) -> None:
    if not value:
        raise AssertionError(f"{test_id}: {message}")
    print(f"[PASS] {test_id} - {message}")


def main() -> int:
    tmp = TMP_ROOT / f"par-scenarios-{os.getpid()}-{int(time.time())}"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        svc = ScenarioService(tmp / "scenario.db")
        svc.init_schema()
        full = {name: {"enabled": True} for name in ("web", "research")}
        web_only = {"web": {"enabled": True}, "research": {"enabled": False}}
        ids = {item["id"] for item in svc.list_scenarios(full)}
        check({"clothing", "procurement", "real_estate", "gift", "product", "travel", "news"}.issubset(ids), "SCN-001", "Scenario Gallery exposes daily-life and work journeys")
        limited = {item["id"] for item in svc.list_scenarios(web_only)}
        check("clothing" in limited and "procurement" not in limited, "SCN-002", "Scenario Gallery follows backend entitlements")
        check(svc.detect("\u043e\u0434\u0435\u0436\u0434") and svc.detect("\u043e\u0434\u0435\u0436\u0434").scenario_id == "clothing", "SCN-003", "Auto detects clothing without a scenario-card click")
        check(svc.detect("Р С—РЎР‚Р С‘Р Р†Р ВµРЎвЂљ, Р С”Р В°Р С” Р Т‘Р ВµР В»Р В°") is None, "SCN-004", "Ordinary chat is not hijacked by Scenario Engine")
        check(svc.detect("https://rbc.ru/ Р С”Р В°Р С”Р С‘Р Вµ Р Р…Р С•Р Р†Р С•РЎРѓРЎвЂљР С‘ РЎРѓР ВµР С–Р С•Р Т‘Р Р…РЎРЏ?") is None, "SCN-004A", "Explicit URL routing has priority over Auto Scenario detection")

        first = svc.prepare(user_id="u1", conversation_id="c1", text="\u043f\u043e\u0434\u0431\u0435\u0440\u0438 \u043c\u043d\u0435 \u043e\u0434\u0435\u0436\u0434\u0443")
        check(first["action"] == "clarify" and first["round"] == 1 and first["max_rounds"] == 1, "SCN-005", "Consumer scenario asks one grouped high-value clarification")
        second = svc.prepare(user_id="u1", conversation_id="c1", text="\u041c\u0443\u0436\u0447\u0438\u043d\u0430, \u0440\u0430\u0437\u043c\u0435\u0440 XL, \u0431\u044e\u0434\u0436\u0435\u0442 \u0434\u043e 15000 \u0440\u0443\u0431\u043b\u0435\u0439, \u043d\u0430 \u043b\u0435\u0442\u043e")
        check(second["action"] == "execute" and "\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b" in second["combined_text"] and "XL" in second["combined_text"], "SCN-006", "Scenario continues after clarification with accumulated context")
        check("\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b" not in second["task_text"] and "XL" in second["task_text"], "SCN-006A", "Execution/search text contains user context without internal scaffolding")

        q1 = svc.prepare(user_id="u2", conversation_id="c2", text="\u041d\u0430\u0439\u0434\u0438 \u0437\u0430\u043a\u0443\u043f\u043a\u0438")
        q2 = svc.prepare(user_id="u2", conversation_id="c2", text="\u041c\u043e\u0441\u043a\u0432\u0430")
        q3 = svc.prepare(user_id="u2", conversation_id="c2", text="\u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432, \u0434\u043e 10 \u043c\u043b\u043d, \u0442\u043e\u043b\u044c\u043a\u043e \u0430\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0435")
        check(q1["action"] == "clarify" and q2["action"] == "clarify" and q3["action"] == "execute", "SCN-007", "Complex procurement scenario is bounded to at most two clarification rounds")
        check(svc._signal_count(BY_ID["procurement"], "\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f:") == 0, "SCN-007A", "Internal clarification scaffolding never counts as user evidence")

        generic_news = svc.prepare(user_id="news-new", conversation_id="news-c1", text="\u0421\u043e\u0431\u0435\u0440\u0438 \u0441\u0432\u0435\u0436\u0438\u0435 \u043d\u043e\u0432\u043e\u0441\u0442\u0438 \u043f\u043e \u0438\u043d\u0442\u0435\u0440\u0435\u0441\u0443\u044e\u0449\u0435\u0439 \u043c\u0435\u043d\u044f \u0442\u0435\u043c\u0435 \u0438 \u043e\u0431\u044a\u044f\u0441\u043d\u0438 \u0433\u043b\u0430\u0432\u043d\u043e\u0435")
        check(generic_news["action"] == "clarify" and "\u0413\u043b\u0430\u0432\u043d\u043e\u0435" in generic_news.get("options", []) and len(generic_news.get("options", [])) >= 7, "SCN-007B", "Generic news starter asks one bounded topic clarification with quick choices")
        svc.set_preferences("news-returning", {"search_scope": "internet", "news_interests": ["\u0422\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0438", "\u0418\u0433\u0440\u044b"]})
        personalized_news = svc.prepare(user_id="news-returning", conversation_id="news-c2", text="\u0421\u043e\u0431\u0435\u0440\u0438 \u0441\u0432\u0435\u0436\u0438\u0435 \u043d\u043e\u0432\u043e\u0441\u0442\u0438 \u043f\u043e \u0438\u043d\u0442\u0435\u0440\u0435\u0441\u0443\u044e\u0449\u0435\u0439 \u043c\u0435\u043d\u044f \u0442\u0435\u043c\u0435 \u0438 \u043e\u0431\u044a\u044f\u0441\u043d\u0438 \u0433\u043b\u0430\u0432\u043d\u043e\u0435")
        check(personalized_news["action"] == "execute" and "\u0422\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0438" in personalized_news["task_text"] and "\u0418\u0433\u0440\u044b" in personalized_news["task_text"], "SCN-007C", "Saved news interests avoid repeated clarification and become search context")

        prefs = svc.set_preferences("u1", {"search_scope": "selected", "region": "Р СљР С•РЎРѓР С”Р Р†Р В°", "allowed_domains": ["cian.ru", "zakupki.gov.ru"], "excluded_domains": ["example.com"], "prefer_russian": True, "news_interests": ["Р СћР ВµРЎвЂ¦Р Р…Р С•Р В»Р С•Р С–Р С‘Р С‘", "Р вЂР С‘Р В·Р Р…Р ВµРЎРѓ"]})
        reopened = ScenarioService(tmp / "scenario.db"); reopened.init_schema()
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
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    main_py = (CORE / "main.py").read_text(encoding="utf-8")
    app_js = (CORE / "static/app.js").read_text(encoding="utf-8")
    index = (CORE / "static/index.html").read_text(encoding="utf-8")
    admin_js = (CORE / "static/admin.js").read_text(encoding="utf-8")
    admin_html = (CORE / "static/admin.html").read_text(encoding="utf-8")
    check(all(x in main_py for x in ("/api/scenarios", "/api/preferences/web", "/api/admin/site-profiles", "SCENARIOS.prepare", "inject_scenario_instruction")), "SCN-008", "Core exposes Scenario/Preferences/Admin site contracts")
    check("scenario-grid" in app_js and "scenario_id:state.scenarioId" in app_js and "saveWebPreferences" in app_js, "SCN-009", "USER UI includes scenario-first flow and Web preferences")
    check("webSearchScope" in index and "webAllowedDomains" in index and "webExcludedDomains" in index and "webNewsInterests" in index, "SITE-005", "USER Web settings are understandable instead of technical site profiles")
    check("siteProfiles" in admin_js and "Сайты и поиск" in admin_html, "SITE-006", "Admin UI exposes technical site profiles separately from USER preferences")

    print("PAR_V080_ALPHA3_SCENARIO_ACCEPTANCE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


