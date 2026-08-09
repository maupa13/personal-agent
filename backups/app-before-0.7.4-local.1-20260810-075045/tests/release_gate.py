from __future__ import annotations

import json
import os
import pathlib
import platform
import signal
import subprocess
import sys
import time
import concurrent.futures

root = pathlib.Path(__file__).resolve().parents[1]
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
evidence_dir = pathlib.Path(os.getenv("PA_EVIDENCE_DIR", root / "release-evidence" / "0.7.3-local"))
evidence_dir.mkdir(parents=True, exist_ok=True)
steps = [
    (["FND-STATIC-001", "FND-ASSET-VERSION-001", "CODE-011"], "static", [sys.executable, str(root / "tests" / "static_checks.py")]),
    (["DIST-001", "DIST-002", "DIST-003"], "distribution", [sys.executable, str(root / "tests" / "distribution_acceptance.py")]),
    (["FND-WIN-CONTRACT-001"], "windows-contract-static", [sys.executable, str(root / "tests" / "windows_contract.py")]),
    (["TASK-006", "DEPLOY-001", "DEPLOY-002", "DEPLOY-003", "DEPLOY-004", "DEPLOY-005", "DEPLOY-006", "DEPLOY-007", "DEPLOY-008", "DEPLOY-009", "LAN-001"], "orchestrator-deployment-acceptance", [sys.executable, str(root / "tests" / "orchestrator_deployment_acceptance.py")]),
    # Run Chromium before JVM/process-heavy suites. The browser journey is independent,
    # and running it first avoids CI-host Chromium startup starvation without weakening any assertion.
    (["FND-BROWSER-OFFLINE-001", "FND-PRODUCT-SHELL-001", "FND-PRODUCT-SHELL-V2-001", "FND-PRESET-001", "PRV-001", "PRV-005", "AUTH-003", "WEB-004", "WEB-006", "FILE-017", "CODE-012", "BILL-006", "BILL-011", "TASK-001", "TASK-003", "DEPLOY-006", "OBS-001"], "browser-user-journeys", [sys.executable, str(root / "tests" / "browser_journeys.py")]),
    (["FND-API-001", "FND-CAPABILITY-HONESTY-001", "FND-PRESET-001", "PRV-001", "PRV-002", "PRV-003", "PRV-004", "PRV-005", "PRV-006", "PRV-008", "PRV-009", "AUTH-001", "AUTH-002", "AUTH-003", "AUTH-CSRF-001", "WEB-001", "WEB-002", "WEB-003", "WEB-004", "WEB-005", "WEB-006", "WEB-007", "WEB-008", "WEB-009", "WEB-010", *[f"FILE-{i:03d}" for i in range(1,17)], *[f"CODE-{i:03d}" for i in range(1,7)], "TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-005", "TASK-007", "DEPLOY-006", "OBS-001"], "api-acceptance", [sys.executable, str(root / "tests" / "run_acceptance.py")]),
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
                returncode = proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=10)
                returncode = 124
                log_handle.write("\n[FAIL] suite exceeded 120 second hard timeout; process group terminated\n")
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
    deterministic_steps = steps[3:]
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(deterministic_steps))) as pool:
        futures = {pool.submit(execute_step, step): step for step in deterministic_steps}
        for future in concurrent.futures.as_completed(futures):
            name, output, rc, step_records = future.result()
            results[name] = (output, rc, step_records)
    for step in deterministic_steps:
        name = step[1]
        output, rc, step_records = results[name]
        print(f"=== RELEASE GATE: {name} ===", flush=True)
        print(output, end="")
        records.extend(step_records)
        if rc != 0 and not failed_code:
            failed_code = rc or 1

summary = {
    "product": "Personal Agent Rus",
    "version": "0.7.3",
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
    ],
    "note": "Live CSP browser, real Windows lifecycle/reboot and clean-machine gates are separate environment-bound gates and are not promoted to PASS by this local release gate.",
}
(evidence_dir / "release-gate.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
if failed_code:
    raise SystemExit(failed_code)
print(f"PAR_RELEASE_GATE PASS: static asset-version windows-contract api presets provider-registry auth web-research files-workspace-artifacts code-sandbox billing-entitlements-payment-adapter orchestrator task-engine deployment monitoring lan browser product-shell-v2; evidence={evidence_dir}")
