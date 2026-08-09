from __future__ import annotations
import json,pathlib,re,sys,yaml
root=pathlib.Path(__file__).resolve().parents[1]
errors=[]
VERSION='0.7.0'
for p in root.rglob('*.py'):
    if '__pycache__' in p.parts: continue
    try: compile(p.read_text(encoding='utf-8'),str(p),'exec')
    except Exception as e: errors.append(f'python {p}: {e}')
for p in root.rglob('*.json'):
    try: json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'json {p}: {e}')
for p in root.rglob('*'):
    if p.name=='__pycache__' or p.suffix=='.pyc': errors.append(f'generated artifact {p}')
try:
    compose=yaml.safe_load((root/'docker-compose-main.yaml').read_text(encoding='utf-8'))
    services=set((compose or {}).get('services',{}))
    expected={'ollama','searxng','browser','code-worker','core'}
    if services!=expected: errors.append(f'production compose services must be {sorted(expected)}, got {sorted(services)}')
    deps=compose['services']['core'].get('depends_on') or {}
    if deps.get('ollama',{}).get('condition')!='service_healthy': errors.append('core must depend on healthy ollama')
    if deps.get('browser',{}).get('condition')!='service_healthy': errors.append('core must depend on healthy browser')
    if deps.get('code-worker',{}).get('condition')!='service_healthy': errors.append('core must depend on healthy code-worker')
    code_service=compose['services'].get('code-worker') or {}
    if code_service.get('network_mode')!='none': errors.append('code-worker must have network_mode:none')
    if code_service.get('read_only') is not True: errors.append('code-worker root filesystem must be read-only')
    if code_service.get('pids_limit') is None or code_service.get('mem_limit') is None or code_service.get('cpus') is None: errors.append('code-worker resource limits missing')
    if any('docker.sock' in str(v) for v in code_service.get('volumes',[])): errors.append('code-worker must never mount Docker socket')
    if 'ALL' not in code_service.get('cap_drop',[]): errors.append('code-worker must drop all capabilities before explicit minimal add-back')
    if list((compose['services']['browser'].get('ports') or [])): errors.append('browser worker must not publish a host port')
    if list((compose['services']['searxng'].get('ports') or [])): errors.append('searxng must not publish a host port')
    vols=set((compose or {}).get('volumes',{}))
    if vols!={'par-rus-data','par-rus-models','par-rus-code-ipc'}: errors.append(f'volume contract changed: {sorted(vols)}')
except Exception as e: errors.append(f'compose parse: {e}')
ps=(root/'scripts/pa.ps1').read_text(encoding='ascii')
if re.search(r'\$args\b',ps,re.I): errors.append('PowerShell automatic $Args variable is forbidden')
if any(x in ps.lower() for x in ('down -v','volume prune','system prune')): errors.append('destructive Docker lifecycle operation found')
for call in (
 "Invoke-Compose -ComposeArgs @('config','--quiet')",
 "Invoke-Compose -ComposeArgs @('up','-d','ollama','searxng','browser')",
 "Invoke-Compose -ComposeArgs @('up','-d','--build','code-worker')",
 "Invoke-Compose -ComposeArgs @('up','-d','--build','--remove-orphans','core')",
 "Invoke-Compose -ComposeArgs @('stop')",
 "Invoke-Compose -ComposeArgs @('restart','ollama','searxng','browser','code-worker','core')",
):
    if call not in ps: errors.append(f'missing compose lifecycle contract: {call}')
if 'function Wait-WebServices' not in ps or 'function Test-WebAcceptance' not in ps: errors.append('Web lifecycle/acceptance functions missing')
if 'function Wait-CodeWorker' not in ps or 'function Test-CodeInternalSmoke' not in ps: errors.append('Code lifecycle/smoke functions missing')
index=(root/'services/core/app/static/index.html').read_text(encoding='utf-8')
user_js=(root/'services/core/app/static/app.js').read_text(encoding='utf-8')
admin_html=(root/'services/core/app/static/admin.html').read_text(encoding='utf-8')
admin_js=(root/'services/core/app/static/admin.js').read_text(encoding='utf-8')
public=(index+user_js).lower()
for token in ('qwen','ollama','model_id','par-rus-ollama'):
    if token in public: errors.append(f'public UI leak {token}')
if 'innerHTML' in user_js: errors.append('USER UI must use safe DOM/textContent, not innerHTML')
if 'innerHTML' in admin_js: errors.append('ADMIN UI must not use innerHTML for backend-controlled values')
for html,name in ((index,'USER'),(admin_html,'ADMIN')):
    if f'?v={VERSION}' not in html: errors.append(f'versioned {name} static asset URLs missing')
    if f'<meta name="app-version" content="{VERSION}">' not in html: errors.append(f'{name} UI version metadata mismatch')
for token in ('conversation-list','chatSearch','settingsEntry','filesEntry','codeEntry','fileInput','artifactList','createArtifact','clearAllShortcut','chatMenuButton','Администрирование'):
    if token not in index: errors.append(f'Product Shell v2 control missing: {token}')
for token in ('regenerateAt','renderRichText','exportCurrent','exportAll','renameCurrent','clearCurrent','clearAll','enforceUiVersion','intent_hint','message-sources','uploadSelectedFiles','renderArtifactList','createArtifactFromUi','file_ids','runCode','pollCodeJob','cancelCode'):
    if token not in user_js: errors.append(f'Product Shell/Web behavior missing: {token}')
for token in ('Тарифы и Usage','billingPlans','billingUsage','billingShopId','billingSecret','providerBillingClass'):
    if token not in admin_html: errors.append(f'Billing/Admin control missing: {token}')
account_html=(root/'services/core/app/static/account.html').read_text(encoding='utf-8')
auth_js=(root/'services/core/app/static/auth.js').read_text(encoding='utf-8')
for token in ('billingAccount','currentPlan','showTokens','planCatalog'):
    if token not in account_html: errors.append(f'Billing account control missing: {token}')
for token in ('/api/billing/me','/api/billing/plans','/api/billing/preferences'):
    if token not in auth_js: errors.append(f'Billing account behavior missing: {token}')
core=(root/'services/core/app/main.py').read_text(encoding='utf-8')
billing=(root/'services/core/app/billing_service.py').read_text(encoding='utf-8') if (root/'services/core/app/billing_service.py').exists() else ''
for token in ('PLAN_PRICES_RUB = {"LIGHT": 0, "MEDIUM": 500, "PRO": 1000}','PLATFORM_REMOTE','Idempotence-Key','save_payment_method','process_yookassa_webhook','renew_due','show_token_usage'):
    if token not in billing: errors.append(f'Billing implementation missing: {token}')
for token in ('validate_public_url','SafeRedirectHandler','fetch_static_url','fetch_browser_url','search_web','gather_web_evidence','WEB TOOL OBSERVATIONS','/api/web/search','/api/web/read','/api/research'):
    if token not in core: errors.append(f'Web implementation missing: {token}')
for token in ('ArtifactService','FILE TOOL OBSERVATIONS','/api/files/upload','/api/files/create','/api/files/','file_ids'):
    if token not in core: errors.append(f'Files implementation missing: {token}')
code_service=(root/'services/core/app/code_service.py').read_text(encoding='utf-8') if (root/'services/core/app/code_service.py').exists() else ''
code_worker=(root/'services/code-worker/app/code_worker.py').read_text(encoding='utf-8') if (root/'services/code-worker/app/code_worker.py').exists() else ''
for token in ('CodeWorkerClient','UnixHTTPConnection','/jobs'):
    if token not in code_service: errors.append(f'Code client contract missing: {token}')
for token in ('PRLIMIT_BIN','SETPRIV_BIN','--cpu=','--fsize=','--nofile=64:64','--nproc=64:64','--reuid=','--regid=','--clear-groups','start_new_session=True','terminate_process','powershell','javac','output_truncated'):
    if token not in code_worker: errors.append(f'Code worker sandbox contract missing: {token}')
if 'preexec_fn=' in code_worker: errors.append('Code worker must not use preexec_fn in threaded server')
code_docker=(root/'services/code-worker/Dockerfile').read_text(encoding='utf-8') if (root/'services/code-worker/Dockerfile').exists() else ''
for token in ('ubuntu:24.04','openjdk-21-jdk-headless','packages.microsoft.com','powershell','util-linux'):
    if token not in code_docker: errors.append(f'Code worker image contract missing: {token}')
artifact=(root/'services/core/app/artifact_service.py').read_text(encoding='utf-8') if (root/'services/core/app/artifact_service.py').exists() else ''
for token in ('SUPPORTED_FORMATS','validate_blob','_validate_zip_bytes','extract_text','create_document_bytes','validation_status','sha256'):
    if token not in artifact: errors.append(f'Artifact service contract missing: {token}')
requirements=(root/'services/core/requirements.txt').read_text(encoding='utf-8') if (root/'services/core/requirements.txt').exists() else ''
for dep in ('pypdf==6.15.0','python-docx==1.2.0','openpyxl==3.1.5','python-pptx==1.0.2','reportlab==5.0.0','defusedxml==0.7.1'):
    if dep not in requirements: errors.append(f'pinned file dependency missing: {dep}')
if 'no-store, max-age=0, must-revalidate' not in core: errors.append('asset no-store contract missing')
if 'unsafe-eval' in core: errors.append('production CSP must not enable unsafe-eval')
if 'по умолчанию отвечай на русском языке' not in core: errors.append('Rus edition Russian-default system policy missing')
if "PA_TEST_MODE" not in core or "PA_WEB_TEST_PUBLIC_HOSTS" not in core: errors.append('deterministic Web fixture hooks missing')
for f in ('docker-compose-main.yaml','compose.release.yaml','scripts/pa.ps1','scripts/pa.sh','.env.example'):
    txt=(root/f).read_text(encoding='utf-8')
    if 'PA_TEST_MODE' in txt or 'PA_WEB_TEST_PUBLIC_HOSTS' in txt: errors.append(f'test-only Web bypass leaked into runtime config: {f}')
if not (root/'services/browser/Dockerfile').exists() or not (root/'services/browser/app/browser_worker.py').exists(): errors.append('browser worker missing')
if not (root/'searxng/settings.yml').exists(): errors.append('SearXNG settings missing')
if not (root/'docs/specification/MASTER-SPEC.md').exists(): errors.append('canonical MASTER-SPEC missing')
if not (root/'tests/user-journeys-registry.json').exists(): errors.append('machine-readable user journey registry missing')
registry=root/'tests/acceptance-registry.json'
try:
    reg=json.loads(registry.read_text(encoding='utf-8')); ids={x.get('test_id') for x in reg.get('tests',[])}
    required={'FND-STATIC-001','FND-WIN-CONTRACT-001','FND-API-001','FND-BROWSER-OFFLINE-001','FND-PRODUCT-SHELL-V2-001','AUTH-001','AUTH-002','PRV-001','PRV-004',*(f'WEB-{i:03d}' for i in range(1,13)),*(f'FILE-{i:03d}' for i in range(1,18)),*(f'CODE-{i:03d}' for i in range(1,13)),'CODE-LIVE-001',*(f'BILL-{i:03d}' for i in range(1,12)),'BILL-LIVE-001','AUTH-CSRF-001','DEPLOY-007','DEPLOY-008','DEPLOY-009'}
    miss=required-ids
    if miss: errors.append(f'acceptance registry missing IDs: {sorted(miss)}')
except Exception as e: errors.append(f'acceptance registry: {e}')
live=(root/'tests/live_browser_e2e.py').read_text(encoding='utf-8')
if 'wait_for_function' in live or 'eval(' in live: errors.append('live browser acceptance contains CSP-incompatible eval polling')

code_cmd=root/'CODE-ACCEPTANCE.cmd'
if not code_cmd.exists(): errors.append('CODE-ACCEPTANCE.cmd missing')
elif '-action codeverify' not in code_cmd.read_text(encoding='ascii').lower(): errors.append('CODE-ACCEPTANCE.cmd does not invoke codeverify')
if 'function Test-CodeLiveAcceptance' not in ps: errors.append('Windows lifecycle missing Test-CodeLiveAcceptance')

verify_ps=(root/'VERIFY-PACKAGE.ps1').read_text(encoding='ascii')
for token in [
    '[CONTRACT] compose|up|-d|--build|code-worker',
    '[CONTRACT] compose|restart|ollama|searxng|browser|code-worker|core',
]:
    if token not in verify_ps: errors.append('VERIFY-PACKAGE Windows contract drift: '+token)
if errors:
    print('\n'.join('[FAIL] '+x for x in errors));sys.exit(1)
print('[PASS] Static package checks')
