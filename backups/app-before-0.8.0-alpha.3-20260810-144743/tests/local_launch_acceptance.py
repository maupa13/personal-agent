from __future__ import annotations
import pathlib,re,sys,yaml
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
if "if($native.ExitCode -ne 0)" not in ps:
    errors.append("optional Code startup must branch on explicit native exit code")
if '"code": {"status": "ready" if code_ready else "degraded"' not in main: errors.append("public capability honesty does not derive Code readiness from live worker")

# Regression for the real Windows local.2 failure: readiness probes can emit Python
# traceback to stderr while services are still starting. Every expected native Docker
# probe must go through the PowerShell 5.1-safe wrapper.
for token in (
    "function Invoke-DockerSafe",
    "$probe=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'exec','-T','browser'",
    "if($probe.ExitCode -eq 0){Pass 'Web/Search and browser services are ready.'",
):
    if token not in ps: errors.append("missing PowerShell 5.1-safe Web readiness contract: "+token)
# Docker health must never generate real external search traffic. That caused rate limits,
# health timeouts and BrokenPipe loops on the Windows reference machine.
health_start=main.find('if path == "/api/health":')
health_end=main.find('if path == "/api/system":', health_start)
health_block=main[health_start:health_end] if health_start >= 0 and health_end > health_start else ''
if '/search?' in health_block or 'personal-agent-health' in health_block:
    errors.append("Core /api/health must not execute external SearXNG searches")
for token in ('request_reachable(f"{SEARXNG_URL}/", timeout=1.5)', 'except (BrokenPipeError, ConnectionResetError)'):
    if token not in main: errors.append("missing bounded/noise-free Core health contract: "+token)
if not re.search(r'CODE_WORKER\.health\(timeout=1\.0(?:,\s*trace_headers=current_trace_headers\(\))?\)', health_block):
    errors.append("Core /api/health must keep the Code worker probe bounded to 1.0s while allowing trace propagation")


# Regression for the Windows local.3 failure: with cap_drop: ALL the root supervisor
# does not retain CAP_DAC_OVERRIDE. A 0700 job directory owned by runner locks the
# supervisor out before it can create main.py. Keep supervisor ownership and grant
# runner access by group instead of broadening container capabilities.
for token in (
    "os.chown(work_dir, -1, RUNNER_GID)",
    "os.chmod(work_dir, 0o2770)",
    "Code smoke diagnostics:",
    "Code capability is DEGRADED after real execution smoke",
):
    target = worker if token.startswith("os.") else ps
    if token not in target: errors.append("missing local.3 Code execution regression contract: "+token)
if "CAP_DAC_OVERRIDE" in str(code.get("cap_add") or []):
    errors.append("Code worker must not regain CAP_DAC_OVERRIDE just to fix job-directory ownership")

for token in (
    "function Assert-CoreImageCurrent",
    "Stale Core image is running:",
    "Assert-CoreImageCurrent",
):
    if token not in ps: errors.append("missing stale-Core version guard: "+token)

if errors:
    print("\n".join("[FAIL] "+e for e in errors)); sys.exit(1)
print("PAR_LOCAL_LAUNCH_ACCEPTANCE PASS: required-runtime code-failsoft live-capability IPC-gid manager-runner-permissions")
