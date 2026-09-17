"""End-to-end regression for the September VPS product repair (fake inference)."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from run_acceptance import base_env, cookie_from, free_port, req, req_text, start_core, wait

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="pa-product-repair-") as directory:
        tmp = Path(directory)
        fake_port, web_port, port = free_port(), free_port(), free_port()
        token = "product-repair-admin-test"
        env = base_env(tmp, fake_port, web_port, port, token, tmp / "no-code.sock", auth_mode="accounts")
        env["PA_EMAIL_VERIFICATION_REQUIRED"] = "0"
        processes = [subprocess.Popen([sys.executable, str(ROOT / "tests" / file), str(p)], stdout=subprocess.DEVNULL)
                     for file, p in [("fake_ollama.py", fake_port), ("fake_web.py", web_port)]]
        processes.append(start_core(env))
        base = f"http://127.0.0.1:{port}"
        try:
            wait(base + "/api/health")
            assert "Попробовать без регистрации" in req_text(base + "/")[1]
            _, demo, headers = req(base + "/api/demo/chat", expect=200)
            guest = {"Cookie": cookie_from(headers)}
            assert demo["remaining"] == 2
            req(base + "/api/demo/chat", method="POST", body={"message": "Hello", "file_ids": ["x"]}, headers=guest, expect=400)
            req(base + "/api/demo/chat", method="POST", body={"message": "Hello"}, headers={**guest, "Origin": "https://other.test"}, expect=403)
            def demo_call(_):
                return req(base + "/api/demo/chat", method="POST", body={"message": "Hello"}, headers=guest)[0]
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                statuses = list(pool.map(demo_call, range(3)))
            assert statuses.count(200) == 2 and statuses.count(429) == 1, statuses
            assert req(base + "/api/demo/chat", expect=200)[1]["remaining"] == 0  # new cookie, same IP
            req(base + "/api/files", headers=guest, expect=401)
            print("PASS DEMO: public entry, two atomic requests, file/origin rejection, no account access")

            def register(email):
                _, data, hdr = req(base + "/api/auth/register", method="POST", body={"email": email, "display_name": "Repair Test", "password": "strong-pass-123"}, expect=201)
                return {"Cookie": cookie_from(hdr), "X-CSRF-Token": data["csrf_token"]}
            owner = register("owner@example.test")
            user = register("user@example.test")
            owner_id = req(base + "/api/auth/me", headers=owner)[1]["user"]["id"]
            user_id = req(base + "/api/auth/me", headers=user)[1]["user"]["id"]
            req(base + "/api/admin/billing/balance", method="POST", token=token, body={"user_id": owner_id, "delta_rub": 10000, "reason": "acceptance"}, expect=200)
            snap = req(base + "/api/billing/me", headers=owner)[1]
            assert snap["balance"]["balance_rub"] == 10000 and snap["subscription"]["billing_exempt"]
            for path, body in [("/api/web/search", {"query": "test"}), ("/api/research", {"question": "test"}), ("/api/files/create", {"format": "txt", "content": "test"}), ("/api/code/jobs", {"code": "print(1)"})]:
                req(base + path, method="POST", body=body, headers=user, expect=403)
            for body in [{"mode": "smart", "messages": [{"role": "user", "content": "Hello"}]}, {"file_ids": ["file"], "messages": [{"role": "user", "content": "Hello"}]}]:
                req(base + "/api/chat", method="POST", body=body, headers=user, expect=403)
            for _ in range(2):
                req(base + "/api/chat", method="POST", body={"messages": [{"role": "user", "content": "Hello"}]}, headers=user, expect=200)
            print("PASS ACCESS: OWNER exempt, LIGHT text-only, repeated chat works")

            req(base + "/api/billing/subscribe-balance", method="POST", body={"plan_id": "MEDIUM"}, headers=user, expect=400)
            req(base + "/api/admin/billing/balance", method="POST", token=token, body={"user_id": user_id, "delta_rub": 1000, "reason": "acceptance"}, expect=200)
            for _ in range(2):
                req(base + "/api/billing/subscribe-balance", method="POST", body={"plan_id": "MEDIUM"}, headers=user, expect=200)
            snap = req(base + "/api/billing/me", headers=user)[1]
            assert snap["balance"]["balance_rub"] == 500 and snap["plan"]["id"] == "MEDIUM"
            req(base + "/api/files/create", method="POST", body={"format": "txt", "name": "test.txt", "content": "Acceptance"}, headers=user, expect=201)
            for _ in range(2):
                req(base + "/api/billing/themes/purchase", method="POST", body={"theme_id": "sunset"}, headers=user, expect=200)
            assert req(base + "/api/billing/me", headers=user)[1]["balance"]["balance_rub"] == 351
            req(base + "/api/preferences/experience", method="POST", body={"theme": "sunset"}, headers=user, expect=200)
            print("PASS WALLET: insufficient funds, no double debit, paid files, theme purchase/application")

            if os.getenv("PA_SKIP_BROWSER") != "1":
                from playwright.sync_api import sync_playwright
                with sync_playwright() as pw:
                    browser = pw.chromium.launch()
                    context = browser.new_context()
                    context.add_cookies([{"name": "pa_session", "value": user["Cookie"].split("=", 1)[1], "url": base}])
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(base + "/account")
                    page.wait_for_function("() => document.querySelector('#walletAmount').textContent.includes('351')")
                    assert "Каталог дополнительных тем пока пуст" not in page.locator("#themeIntro").inner_text()
                    page.locator(".theme-row").filter(has_text="Закат").get_by_role("button", name="Применить").click()
                    page.wait_for_function("() => document.documentElement.dataset.theme === 'sunset'")
                    page.reload()
                    page.wait_for_function("() => document.documentElement.dataset.theme === 'sunset'")
                    for width in [390, 1280]:
                        page.set_viewport_size({"width": width, "height": 900})
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
                    page.goto(base)
                    page.wait_for_function("() => document.querySelector('#accountEntry .account-label').textContent.includes('351')")
                    assert not errors, errors
                    browser.close()
                print("PASS BROWSER: wallet amount, themes applied/persisted, mobile/desktop layout, no JS errors")
        finally:
            for process in reversed(processes):
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
