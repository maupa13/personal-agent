from __future__ import annotations

import json
import os
import pathlib
import platform
import signal
import subprocess
import sys
import time

root = pathlib.Path(__file__).resolve().parents[1]
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
evidence_dir = pathlib.Path(os.getenv("PA_EVIDENCE_DIR", root / "release-evidence" / "0.8.0-alpha.6-local"))
evidence_dir.mkdir(parents=True, exist_ok=True)
steps = [
    (["FND-STATIC-001", "FND-ASSET-VERSION-001", "CODE-011"], "static", [sys.executable, str(root / "tests" / "static_checks.py")]),
    (["DIST-001", "DIST-002", "DIST-003"], "distribution", [sys.executable, str(root / "tests" / "distribution_acceptance.py")]),
    (["FND-WIN-CONTRACT-001"], "windows-contract-static", [sys.executable, str(root / "tests" / "windows_contract.py")]),
    (["LOCAL-START-001"], "local-launch-contract", [sys.executable, str(root / "tests" / "local_launch_acceptance.py")]),
    (["PLAN-001", "PLAN-002", "PLAN-003", "PLAN-ADMIN-001", "PLAN-PERSIST-001", "AUTH-005", "AUTH-006", "ADMIN-002", "LAN-001", "LAN-002", "PG-FOUNDATION-001", "PG-FOUNDATION-002", "PG-FOUNDATION-003"], "accounts-entitlements-acceptance", [sys.executable, str(root / "tests" / "accounts_entitlements_acceptance.py")]),
    (["SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-004A", "SCN-005", "SCN-006", "SCN-006A", "SCN-007", "SCN-007A", "SCN-008", "SCN-009", "SITE-001", "SITE-002", "SITE-003", "SITE-004", "SITE-005", "SITE-006"], "scenario-site-preferences-acceptance", [sys.executable, str(root / "tests" / "scenario_acceptance.py")]),
    (["SRC-001", "SRC-002", "SRC-004", "RESULT-001", "RESULT-002", "OBS-A6-001", "OBS-A6-002", "OBS-A6-003", "BILL-A6-001"], "alpha6-search-debug-acceptance", [sys.executable, str(root / "tests" / "alpha6_search_debug_acceptance.py")]),
    (["UX-A4-001", "UX-A4-002", "FEEDBACK-A4-001", "SHARE-A4-001", "EXEC-A4-001", "TONE-A4-001", "ADMIN-A4-001", "ADMIN-A4-002", "UI-A4-001", "GUIDE-A4-001", "PRIV-A4-001"], "ux-admin-hardening-acceptance", [sys.executable, str(root / "tests" / "ux_admin_hardening_acceptance.py")]),
    (["BRAND-A5-001", "BRAND-A5-002", "BRAND-A5-003", "BRAND-A5-004", "I18N-A5-001", "I18N-A5-002", "I18N-A5-003", "I18N-A5-004", "UX-009", "A11Y-A5-001", "A11Y-A5-002", "UX-A5-001", "UX-A5-002", "UX-A5-003", "UX-A5-004", "UX-A5-005", "UX-A5-006", "ADMIN-A5-001", "ADMIN-A5-002", "ADMIN-A5-003"], "ux-complete-acceptance", [sys.executable, str(root / "tests" / "ux_complete_acceptance.py")]),
    (["UX-009", "I18N-A5-001", "I18N-A5-002", "I18N-A5-003", "I18N-A5-004", "A11Y-A5-001", "A11Y-A5-002"], "ux-complete-browser", [sys.executable, str(root / "tests" / "ux_complete_browser.py")]),
    (["TASK-006", "DEPLOY-001", "DEPLOY-002", "DEPLOY-003", "DEPLOY-004", "DEPLOY-005", "DEPLOY-006", "DEPLOY-007", "DEPLOY-008", "DEPLOY-009", "LAN-001"], "orchestrator-deployment-acceptance", [sys.executable, str(root / "tests" / "orchestrator_deployment_acceptance.py")]),
    # Run Chromium before JVM/process-heavy suites. The browser journey is independent,
    # and running it first avoids CI-host Chromium startup starvation without weakening any assertion.
    (["FND-BROWSER-OFFLINE-001", "FND-PRODUCT-SHELL-001", "FND-PRODUCT-SHELL-V2-001", "FND-CHAT-EXPORT-001", "FND-PRESET-001", "PRV-001", "PRV-005", "AUTH-003", "WEB-004", "WEB-006", "FILE-017", "CODE-012", "BILL-006", "BILL-011", "TASK-001", "TASK-003", "DEPLOY-006", "OBS-001"], "browser-user-journeys", [sys.executable, str(root / "tests" / "browser_journeys_runner.py")]),
    (["ADMIN-A6-BROWSER-001", "ADMIN-A6-BROWSER-002"], "admin-browser-journeys", [sys.executable, str(root / "tests" / "browser_admin_journeys.py")]),
    (["FND-API-001", "FND-CAPABILITY-HONESTY-001", "FND-PRESET-001", "PRV-001", "PRV-002", "PRV-003", "PRV-004", "PRV-005", "PRV-006", "PRV-008", "PRV-009", "AUTH-001", "AUTH-002", "AUTH-003", "AUTH-CSRF-001", "WEB-001", "WEB-002", "WEB-003", "WEB-004", "WEB-005", "WEB-006", "WEB-007", "WEB-008", "WEB-009", "WEB-010", "WEB-013", "WEB-014", *[f"FILE-{i:03d}" for i in range(1,17)], *[f"CODE-{i:03d}" for i in range(1,7)], "TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-005", "TASK-007", "DEPLOY-006", "OBS-001", "OBS-002"], "api-acceptance", [sys.executable, str(root / "tests" / "run_acceptance.py")]),
    (["UX-001", "UX-003", "UX-004", "UX-005", "UX-006", "UX-007", "UX-010", "ONB-001", "ONB-002", "ONB-004", "ONB-005", "ONB-101", "CONV-001", "CONV-002", "CONV-004", "CONV-005", "CONV-007", "OBS-001", "OBS-002", "OBS-003", "OBS-004", "GUIDE-003"], "productization-acceptance", [sys.executable, str(root / "tests" / "productization_acceptance.py")]),
    (["BILL-001", "BILL-002", "BILL-003", "BILL-004", "BILL-005", "BILL-007", "BILL-008", "BILL-009", "BILL-010"], "billing-acceptance", [sys.executable, str(root / "tests" / "billing_acceptance.py")]),
    (["CODE-007", "CODE-008", "CODE-009", "CODE-010"], "code-worker-acceptance", [sys.executable, str(root / "tests" / "code_worker_acceptance.py")]),
]

records = []


def execute_step(step):
    test_ids, name, cmd = step
    started = time.time()
    shared_log = f"{test_ids[0]}.log"
    log_path = evidence_dir / shared_log
    proc = None
    returncode = 1
    try:
        with log_path.open("w", encoding="utf-8", newline="") as log_handle:
            proc = subprocess.Popen(
                cmd, cwd=root, env=env, text=True,
                stdout=log_handle, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                returncode = proc.wait(timeout=180)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=10)
                returncode = 124
                log_handle.write("\n[FAIL] suite exceeded 180 second hard timeout; process group terminated\n")
    except Exception as exc:
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try: proc.wait(timeout=10)
            except Exception: pass
        log_path.write_text(f"[FAIL] release runner exception: {type(exc).__name__}: {exc}\n", encoding="utf-8")
        returncode = 1
    finished = time.time()
    output = log_path.read_text(encoding="utf-8", errors="replace")
    status = "PASS" if returncode == 0 else "FAIL"
    step_records = [{
        "test_id": test_id, "name": name, "status": status,
        "started_at": started, "finished_at": finished,
        "duration_sec": round(finished - started, 3), "exit_code": returncode,
        "output_file": shared_log,
    } for test_id in test_ids]
    return name, output, returncode, step_records


# Static/package contracts run first. Remaining deterministic suites use isolated ports/workspaces
# and may run concurrently to keep the local release gate bounded without weakening assertions.
failed_code = 0
for step in steps[:3]:
    print(f"=== RELEASE GATE: {step[1]} ===", flush=True)
    name, output, rc, step_records = execute_step(step)
    print(output, end="")
    records.extend(step_records)
    if rc != 0:
        failed_code = rc or 1
        break

if not failed_code:
    # Process-heavy acceptance suites intentionally run sequentially. Running Playwright,
    # multiple code workers, JVM compilation and API acceptance concurrently caused host-load
    # dependent timeouts on otherwise healthy code. A release gate must be deterministic first;
    # individual product concurrency is tested inside the targeted suites themselves.
    for step in steps[3:]:
        print(f"=== RELEASE GATE: {step[1]} ===", flush=True)
        name, output, rc, step_records = execute_step(step)
        print(output, end="")
        records.extend(step_records)
        if rc != 0:
            failed_code = rc or 1
            break

summary = {
    "product": "Personal Agent Rus",
    "version": "0.8.0-alpha.6",
    "environment": {
        "platform": platform.platform(),
        "python": sys.version,
        "executable": sys.executable,
    },
    "results": records,
    "counts": {s: sum(1 for x in records if x["status"] == s) for s in ("PASS", "FAIL")},
    "environment_bound": [
        {"test_id": "FND-BROWSER-LIVE-REAL-001", "status": "BLOCKED_ENVIRONMENT", "reason": "authoritative on reference Windows runtime"},
        {"test_id": "FND-BROWSER-LIVE-SECURITY-001", "status": "BLOCKED_ENVIRONMENT", "reason": "authoritative on reference Windows Docker runtime"},
        {"test_id": "FND-RUS-LANGUAGE-001", "status": "BLOCKED_ENVIRONMENT", "reason": "stochastic real-model language behavior is authoritative on reference Windows runtime"},
        {"test_id": "FND-REFERENCE-SEQUENCE-001", "status": "BLOCKED_ENVIRONMENT", "reason": "runs RELEASE-ACCEPTANCE.cmd on reference Windows Docker runtime"},
        {"test_id": "FND-REBOOT-001", "status": "BLOCKED_ENVIRONMENT", "reason": "requires real Windows reboot"},
        {"test_id": "WEB-011", "status": "BLOCKED_ENVIRONMENT", "reason": "live DTF canary is authoritative on reference Windows with external internet"},
        {"test_id": "WEB-012", "status": "BLOCKED_ENVIRONMENT", "reason": "live Web diagnostics are captured by WEB-ACCEPTANCE.cmd on reference Windows"},
        {"test_id": "CODE-LIVE-001", "status": "BLOCKED_ENVIRONMENT", "reason": "real Docker code-worker image with Python/Java/PowerShell is authoritative on reference Windows Docker runtime"},
        {"test_id": "BILL-LIVE-001", "status": "BLOCKED_ENVIRONMENT", "reason": "requires real YooKassa merchant credentials plus public HTTPS callback/webhook endpoint"},
        {"test_id": "DEPLOY-LIVE-001", "status": "BLOCKED_ENVIRONMENT", "reason": "requires a real Linux VPS, SSH credential, DNS and public HTTPS"},
        {"test_id": "LAN-LIVE-001", "status": "BLOCKED_ENVIRONMENT", "reason": "requires a physical second LAN device and Windows Private-network firewall"},
        {"test_id": "CONV-003", "status": "BLOCKED_ENVIRONMENT", "reason": "requires same account on a second physical LAN device"},
    ],
    "deferred_not_applicable_to_alpha6": [
        {"test_id": "PG-RUNTIME-001", "status": "NOT_IMPLEMENTED", "mandatory_from": "0.8.0-beta.1", "reason": "PostgreSQL server schema/compose are present, but canonical Core persistence switch/migration/rollback is a separate vertical slice"},
        {"test_id": "VPS-EGRESS-001", "status": "NOT_IMPLEMENTED", "mandatory_from": "0.9.0", "reason": "site profile egress_region is policy metadata; real RU/global worker routing requires multi-region VPS integration and policy tests"}
    ],
    "note": "Live CSP browser, real Windows lifecycle/reboot and clean-machine gates are separate environment-bound gates and are not promoted to PASS by this local release gate.",
}
(evidence_dir / "release-gate.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
if failed_code:
    raise SystemExit(failed_code)
print(f"PAR_RELEASE_GATE PASS: static asset-version windows-contract api presets provider-registry auth web-research files-workspace-artifacts code-sandbox accounts-entitlements billing-foundation orchestrator task-engine deployment monitoring lan browser product-shell-v2 productization-conversations-onboarding-rbac-observability scenario-engine-bounded-clarification-site-preferences ux-admin-hardening-execution-policy-share-feedback ux-complete-localization-state-matrix-accessibility search-integrity-result-cards-debug-observability; evidence={evidence_dir}")
