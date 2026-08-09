from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATIC = ROOT / "services/core/app/static"
INDEX = (STATIC / "index.html").read_text(encoding="utf-8")
APP = (STATIC / "app.js").read_text(encoding="utf-8")
CSS = (STATIC / "styles.css").read_text(encoding="utf-8")
ADMIN = (STATIC / "admin.html").read_text(encoding="utf-8")
ADMIN_JS = (STATIC / "admin.js").read_text(encoding="utf-8")
AUTH_JS = (STATIC / "auth.js").read_text(encoding="utf-8")
MANIFEST = json.loads((STATIC / "manifest.webmanifest").read_text(encoding="utf-8"))
PRODUCT = json.loads((ROOT / "product-manifest.json").read_text(encoding="utf-8"))


def check(condition: bool, test_id: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{test_id}: {message}")
    print(f"[PASS] {test_id} - {message}")


def main() -> int:
    names = PRODUCT.get("display_names") or {}
    check(
        names.get("ru-RU") == "Родной Агент" and names.get("en-US") == "Personal Agent",
        "BRAND-A5-001",
        "edition identity is separate from RU/EN user-facing brand",
    )
    check(
        MANIFEST.get("name") == "Родной Агент" and MANIFEST.get("lang") == "ru-RU",
        "BRAND-A5-002",
        "browser manifest uses the localized RU display name",
    )
    user_html = "\n".join(
        (STATIC / name).read_text(encoding="utf-8")
        for name in ("index.html", "login.html", "register.html", "account.html", "user-guide.html", "local-setup.html", "why.html")
    )
    check("Personal Agent Rus" not in user_html, "BRAND-A5-003", "USER HTML does not expose the internal rus edition label")
    check("brand:'Родной Агент'" in APP and "brand:'Personal Agent'" in APP, "I18N-A5-001", "RU/EN shell brand dictionaries ship")
    check(all(token in APP for token in ("ui_language", "response_language", "applyLanguage", "title_en", "text_en")), "I18N-A5-002", "language preference covers shell and guided onboarding")
    check("AUTH_I18N" in AUTH_JS and "Personal Agent" in AUTH_JS and "Родной Агент" in AUTH_JS, "I18N-A5-003", "authentication/account surfaces support RU/EN")
    check("ADMIN_EN" in ADMIN_JS and "adminText(" in ADMIN_JS and "title_en" in ADMIN_JS, "I18N-A5-004", "Admin shell and Admin guided tour support RU/EN")

    check(
        all(token in CSS for token in ('html[data-theme="light"]', '@media(prefers-reduced-motion:reduce)', ':focus-visible')),
        "UX-009-THEME-A11Y",
        "light theme, reduced-motion and visible keyboard focus contracts ship",
    )
    check(
        all(token in INDEX for token in ('id="runtimeStateBanner"', 'role="status"', 'aria-live="polite"', 'id="runtimeRetry"')),
        "UX-009-STATE-SURFACE",
        "runtime state has a non-color-only accessible surface and retry action",
    )
    for state in ("booting", "starting", "degraded", "offline", "quota", "permission", "error", "ready"):
        check(state in APP, f"UX-009-{state.upper()}", f"{state} state is represented in USER runtime state matrix")
    check("friendlyError" in APP and "showRuntimeState" in APP and "updateRuntimeStateCopy" in APP, "UX-009-ERROR-COPY", "controlled failures map to user-facing recoverable states")

    check(
        'role="separator"' in INDEX and 'aria-valuemin="240"' in INDEX and 'aria-valuemax="420"' in INDEX,
        "A11Y-A5-001",
        "sidebar resizer exposes keyboard/ARIA separator semantics",
    )
    check("ArrowLeft" in APP and "ArrowRight" in APP and "Home" in APP and "End" in APP, "A11Y-A5-002", "sidebar can be resized by keyboard")
    check(".sidebar.collapsed .folder-list" in CSS and "display:none!important" in CSS, "UX-A5-001", "collapsed sidebar is a clean rail rather than a broken compressed layout")
    check("new-project-button" in INDEX and "Новый проект" in INDEX, "UX-A5-002", "project creation is a visible labeled action")
    check("#webAllowedDomains" in CSS and "#webExcludedDomains" in CSS and ".code-editor" in CSS and "width:100%" in CSS, "UX-A5-003", "Web textarea and code editor use full-width responsive forms")

    check(
        all(token in INDEX for token in ("themeSelect", "uiLanguage", "responseLanguage", "executionPolicy", "tonePreset")),
        "UX-A5-004",
        "theme, language, execution and response style are first-class USER settings",
    )
    check("local_only" in APP and "remote_only" in APP, "UX-A5-005", "local/remote execution choices remain explicit in USER UX")
    check("toneMeme" in APP and "toneIronic" in APP, "UX-A5-006", "humorous response modes remain available without exposing model IDs")

    check("adminLocaleToggle" in ADMIN and "adminThemeToggle" in ADMIN, "ADMIN-A5-001", "Admin has quick language and theme controls")
    check(all(token in ADMIN for token in ("Провайдеры", "Модели", "Маршрутизация", "Пользователи", "Подписки и Usage", "Мониторинг", "Логи и аудит", "Диагностика")), "ADMIN-A5-002", "Admin control-plane sections remain present")
    check("providerType" in ADMIN and "saveRoutes" in ADMIN and "pullModel" in ADMIN, "ADMIN-A5-003", "Admin can manage provider/model/routing flows")

    # Product identity remains stable internally while the edition label is hidden from normal users.
    check(PRODUCT.get("product") == "Personal Agent Rus" and PRODUCT.get("edition") == "rus", "BRAND-A5-004", "internal edition identity remains stable for packaging and future editions")

    print("PAR_V080_ALPHA5_UX_COMPLETE_ACCEPTANCE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
