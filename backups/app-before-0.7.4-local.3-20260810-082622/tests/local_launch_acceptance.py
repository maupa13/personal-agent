from __future__ import annotations
import pathlib,sys,yaml
root=pathlib.Path(__file__).resolve().parents[1]
errors=[]
compose=yaml.safe_load((root/"docker-compose-main.yaml").read_text(encoding="utf-8"))
core=compose["services"]["core"]
code=compose["services"]["code-worker"]
deps=core.get("depends_on") or {}
if "code-worker" in deps: errors.append("Core is still startup-blocked by code-worker")
if deps.get("ollama",{}).get("condition") != "service_healthy": errors.append("Ollama must remain required/healthy")
if deps.get("browser",{}).get("condition") != "service_healthy": errors.append("Browser must remain required/healthy")
if str((code.get("environment") or {}).get("PA_CODE_SOCKET_GID")) != "10001": errors.append("shared code socket GID must match Core GID 10001")
worker=(root/"services/code-worker/app/code_worker.py").read_text(encoding="utf-8")
core_df=(root/"services/core/Dockerfile").read_text(encoding="utf-8")
ps=(root/"scripts/pa.ps1").read_text(encoding="ascii")
main=(root/"services/core/app/main.py").read_text(encoding="utf-8")
for token in ("SOCKET_GID", "os.chown(SOCKET_PATH, 0, SOCKET_GID)", "os.chmod(SOCKET_PATH, 0o660)"):
    if token not in worker: errors.append("missing IPC permission contract: "+token)
if "groupadd --gid 10001 rpa" not in core_df or "useradd --uid 10001 --gid 10001" not in core_df: errors.append("Core UID/GID contract not explicit")
for token in ("function Start-CodeWorkerOptional", "Core will start in degraded-code mode", "--no-deps','--remove-orphans','core", "baseline local verification still passed"):
    if token not in ps: errors.append("missing fail-soft local lifecycle contract: "+token)
for token in ("$previousErrorActionPreference=$ErrorActionPreference", "$ErrorActionPreference='Continue'", "$nativeExitCode=$LASTEXITCODE", "$ErrorActionPreference=$previousErrorActionPreference"):
    if token not in ps: errors.append("missing Windows PowerShell 5.1 native stderr fail-soft contract: "+token)
if "if($nativeExitCode -ne 0)" not in ps:
    errors.append("optional Code startup must branch on explicit native exit code")
if '"code": {"status": "ready" if code_ready else "degraded"' not in main: errors.append("public capability honesty does not derive Code readiness from live worker")
if errors:
    print("\n".join("[FAIL] "+e for e in errors)); sys.exit(1)
print("PAR_LOCAL_LAUNCH_ACCEPTANCE PASS: required-runtime code-failsoft live-capability IPC-gid")
