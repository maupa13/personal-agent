from __future__ import annotations
import json,pathlib,re,sys,yaml
root=pathlib.Path(__file__).resolve().parents[1]
errors=[]
compose={}
VERSION='1.0.3'
for p in root.rglob('*.py'):
    if '__pycache__' in p.parts: continue
    try: compile(p.read_text(encoding='utf-8'),str(p),'exec')
    except Exception as e: errors.append(f'python {p}: {e}')
for p in root.rglob('*.json'):
    try: json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'json {p}: {e}')
for p in root.rglob('*'):
    parts=set(p.parts)
    if '__pycache__' in parts or 'release-evidence' in parts or any(part.startswith('pytest-cache-files-') for part in parts) or p.suffix=='.pyc':
        continue
try:
    compose=yaml.safe_load((root/'compose.yaml').read_text(encoding='utf-8'))
    services=set((compose or {}).get('services',{}))
    expected={'ollama','searxng','browser','code-worker','core'}
    if services!=expected: errors.append(f'production compose services must be {sorted(expected)}, got {sorted(services)}')
    deps=compose['services']['core'].get('depends_on') or {}
    if deps.get('ollama',{}).get('condition')!='service_healthy': errors.append('core must depend on healthy ollama')
    if deps.get('browser',{}).get('condition')!='service_healthy': errors.append('core must depend on healthy browser')
    if 'code-worker' in deps: errors.append('core must not be startup-blocked by optional code-worker')
    code_service=compose['services'].get('code-worker') or {}
    if str((code_service.get('environment') or {}).get('PA_CODE_SOCKET_GID'))!='10001': errors.append('code-worker shared socket GID contract missing')
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
 "Invoke-Compose -ComposeArgs @('up','-d','--build','--no-deps','--remove-orphans','core')",
 "Invoke-Compose -ComposeArgs @('stop')",
 "Invoke-Compose -ComposeArgs @('restart','ollama','searxng','browser','core')",
):
    if call not in ps: errors.append(f'missing compose lifecycle contract: {call}')
if 'function Wait-WebServices' not in ps or 'function Test-WebAcceptance' not in ps: errors.append('Web lifecycle/acceptance functions missing')
if 'function Wait-CodeWorker' not in ps or 'function Start-CodeWorkerOptional' not in ps or 'function Test-CodeInternalSmoke' not in ps: errors.append('Code lifecycle/fail-soft/smoke functions missing')
index=(root/'services/core/app/static/index.html').read_text(encoding='utf-8')
user_js=(root/'services/core/app/static/app.js').read_text(encoding='utf-8')
admin_html=(root/'services/core/app/static/admin.html').read_text(encoding='utf-8')
admin_js=(root/'services/core/app/static/admin.js').read_text(encoding='utf-8')
core=(root/'services/core/app/main.py').read_text(encoding='utf-8')
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
for token in ('Подписки и Usage','billingPlans','billingUsage','billingShopId','billingSecret','providerBillingClass'):
    if token not in admin_html: errors.append(f'Billing/Admin control missing: {token}')

# v0.8 alpha.2 accounts / entitlement / LAN / PostgreSQL foundation contracts.
entitlement=(root/'services/core/app/entitlement_service.py').read_text(encoding='utf-8') if (root/'services/core/app/entitlement_service.py').exists() else ''
server_db=(root/'services/core/app/server_database.py').read_text(encoding='utf-8') if (root/'services/core/app/server_database.py').exists() else ''
server_compose=(root/'deploy/server/compose.postgres-foundation.yaml').read_text(encoding='utf-8') if (root/'deploy/server/compose.postgres-foundation.yaml').exists() else ''
pg_migration=(root/'migrations/postgres/0001_productization_foundation.sql').read_text(encoding='utf-8') if (root/'migrations/postgres/0001_productization_foundation.sql').exists() else ''
for token in ('class EntitlementService','plan_entitlements','mode_allowed','max_concurrent_tasks','storage_quota_mb','max_file_size_mb'):
    if token not in entitlement: errors.append(f'alpha2 entitlement contract missing: {token}')
for token in ('PA_DATABASE_URL','postgresql','driver_available'):
    if token not in server_db: errors.append(f'alpha2 PostgreSQL config contract missing: {token}')
for token in ('postgres:18.4-bookworm','par-server-postgres','Dockerfile.server','PA_DATABASE_URL'):
    if token not in server_compose: errors.append(f'alpha2 PostgreSQL compose foundation missing: {token}')
for token in ('CREATE TABLE IF NOT EXISTS users','CREATE TABLE IF NOT EXISTS conversations','CREATE TABLE IF NOT EXISTS plan_entitlements','CREATE INDEX IF NOT EXISTS idx_conversations_user_updated'):
    if token not in pg_migration: errors.append(f'alpha2 PostgreSQL migration contract missing: {token}')
for token in ('/api/auth/sessions','auth_login_attempts','remember_me','argon2','/api/admin/entitlements','/api/admin/auth/registration-policy','/api/admin/lan/qr.svg'):
    if token not in core: errors.append(f'alpha2 Core product contract missing: {token}')
for rel in ('services/core/requirements.server.txt','services/core/Dockerfile.server','deploy/server/README-POSTGRES-FOUNDATION.md','tests/accounts_entitlements_acceptance.py','tests/alpha2-registry.json'):
    if not (root/rel).exists(): errors.append(f'alpha2 distribution file missing: {rel}')
core_requirements=(root/'services/core/requirements.txt').read_text(encoding='utf-8') if (root/'services/core/requirements.txt').exists() else ''
req_server=(root/'services/core/requirements.server.txt').read_text(encoding='utf-8') if (root/'services/core/requirements.server.txt').exists() else ''
for dep in ('argon2-cffi==25.1.0','qrcode==8.2'):
    if dep not in core_requirements: errors.append(f'alpha2 core dependency missing: {dep}')
if 'psycopg[binary,pool]==3.3.4' not in req_server: errors.append('alpha2 PostgreSQL server driver pin missing')

# v0.8 alpha.3 Scenario Engine / bounded clarification / site preference contracts.
scenario=(root/'services/core/app/scenario_service.py').read_text(encoding='utf-8') if (root/'services/core/app/scenario_service.py').exists() else ''
for token in ('class ScenarioService','scenario_states','user_web_preferences','site_profiles','max_clarification_rounds','_assessment_text','task_text','explicit_scenario_id'):
    if token not in scenario: errors.append(f'alpha3 scenario contract missing: {token}')
for token in ('/api/scenarios','/api/preferences/web','/api/admin/site-profiles','SCENARIOS.prepare','scenario_task_text','task_text'):
    if token not in core: errors.append(f'alpha3 Core scenario contract missing: {token}')
for token in ('scenario-grid','scenario-card','webSearchScope','webAllowedDomains','webExcludedDomains','saveWebPreferences'):
    if token not in user_js+index: errors.append(f'alpha3 USER scenario/site UI missing: {token}')
for token in ('Сайты и поиск','siteProfiles','refreshSiteProfiles'):
    if token not in admin_html+admin_js: errors.append(f'alpha3 ADMIN site profile UI missing: {token}')
guide=(root/'services/core/app/static/user-guide.html').read_text(encoding='utf-8')
for token in ('С чего начать','Веб и сайты','не более двух'):
    if token not in guide: errors.append(f'alpha3 in-product guide missing: {token}')
for rel in ('tests/scenario_acceptance.py','tests/alpha3-registry.json'):
    if not (root/rel).exists(): errors.append(f'alpha3 distribution file missing: {rel}')
try:
    a3=json.loads((root/'tests/alpha3-registry.json').read_text(encoding='utf-8'));a3ids={x.get('test_id') for x in a3.get('tests',[])}
    required_a3={'SCN-001','SCN-003','SCN-004A','SCN-005','SCN-006A','SCN-007','SCN-007A','SCN-009','SITE-001','SITE-002','SITE-004','SITE-005','SITE-006'}
    if required_a3-a3ids: errors.append(f'alpha3 registry missing IDs: {sorted(required_a3-a3ids)}')
except Exception as e: errors.append(f'alpha3 registry: {e}')

# v0.8 alpha.4 UX / Admin hardening contracts.
experience=(root/'services/core/app/experience_service.py').read_text(encoding='utf-8') if (root/'services/core/app/experience_service.py').exists() else ''
for token in ('class ExperienceService','user_experience_preferences','feedback','conversation_shares','share_token_hash','set_preferences','create_share','revoke_share'):
    if token not in experience: errors.append(f'alpha4 experience/share/feedback contract missing: {token}')
for token in ('/api/preferences/experience','/api/feedback','/api/admin/feedback','/api/admin/auth-status','openai_responses','/responses','choose_route_for_execution_policy','apply_response_preferences','local owner admin access requires loopback-only mode'):
    if token not in core: errors.append(f'alpha4 Core UX/Admin contract missing: {token}')
for token in ('uiLanguage','responseLanguage','themeSelect','executionPolicy','tonePreset','toneButton','shareChatButton','feedbackEntry'):
    if token not in index+user_js: errors.append(f'alpha4 USER UX control missing: {token}')
for token in ('OpenAI API · Responses','providerType','providerUrl','feedbackList','adminAuthStatus'):
    if token not in admin_html+admin_js: errors.append(f'alpha4 ADMIN UX control missing: {token}')
css=(root/'services/core/app/static/styles.css').read_text(encoding='utf-8')
for token in ('html[data-theme="light"]','#webAllowedDomains,#webExcludedDomains,#artifactContent,#codeEditor','.sidebar.collapsed .folder-list','.settings-content .code-editor{width:100%'):
    if token not in css: errors.append(f'alpha4 responsive/theme CSS contract missing: {token}')
for rel in ('services/core/app/static/local-setup.html','services/core/app/static/admin-guide.html','tests/ux_admin_hardening_acceptance.py','tests/alpha4-registry.json'):
    if not (root/rel).exists(): errors.append(f'alpha4 distribution file missing: {rel}')
try:
    a4=json.loads((root/'tests/alpha4-registry.json').read_text(encoding='utf-8'));a4ids={x.get('test_id') for x in a4.get('tests',[])}
    required_a4={'UX-A4-001','UX-A4-002','FEEDBACK-A4-001','SHARE-A4-001','EXEC-A4-001','TONE-A4-001','ADMIN-A4-001','ADMIN-A4-002','UI-A4-001','GUIDE-A4-001','PRIV-A4-001'}
    if required_a4-a4ids: errors.append(f'alpha4 registry missing IDs: {sorted(required_a4-a4ids)}')
except Exception as e: errors.append(f'alpha4 registry: {e}')

# v0.8 Productization foundation contracts.
conversation_service=(root/'services/core/app/conversation_service.py').read_text(encoding='utf-8') if (root/'services/core/app/conversation_service.py').exists() else ''
for token in ('class ConversationStore','CREATE TABLE IF NOT EXISTS folders','CREATE TABLE IF NOT EXISTS conversations','CREATE TABLE IF NOT EXISTS messages','CREATE TABLE IF NOT EXISTS user_onboarding','user_id','import_legacy','onboarding_set','rename_folder','delete_folder','set_pinned','set_archived','export_all'):
    if token not in conversation_service: errors.append(f'Productization conversation contract missing: {token}')
observability_service=(root/'services/core/app/observability_service.py').read_text(encoding='utf-8') if (root/'services/core/app/observability_service.py').exists() else ''
for token in ('class StructuredLogger','self.path = self.root / f"{service}.jsonl"','[REDACTED]','def _rotate','def query','request_id','correlation_id','max_bytes','backups'):
    if token not in observability_service: errors.append(f'Productization observability contract missing: {token}')
for token in ('/api/conversations','/api/folders','/api/onboarding','/api/admin/logs','/api/admin/audit','/api/admin/diagnostics','/api/admin/diagnostics/download','diagnostics_bundle','ConversationStore','StructuredLogger','X-Request-ID','X-Correlation-ID','current_trace_headers','_is_internal_service_url'):
    if token not in core: errors.append(f'Productization Core API missing: {token}')
for token in ('sidebarResizer','collapseSidebar','newFolder','folders','brandHelp','restartTour','modeButton','executionQuick','adminEntry','tourLayer'):
    if token not in index: errors.append(f'Productization USER shell control missing: {token}')
for token in ('loadServerStore','loadConversation','startTour','renderTour',"key.toLowerCase()==='b'",'/api/conversations','/api/onboarding','actionSelect',"action==='move'","action==='archive'",'exportAll'):
    if token not in user_js: errors.append(f'Productization USER behavior missing: {token}')
if 'localStorage.setItem(STORAGE_KEY' in user_js: errors.append('Conversations must not be canonically persisted to localStorage')
for token in ('Логи и аудит','logLevel','logRequest','logCorrelation','adminAudit','Диагностика','downloadDiagnostics','adminTourButton','adminTourLayer'):
    if token not in admin_html: errors.append(f'Productization ADMIN shell control missing: {token}')
for token in ('refreshLogs','refreshDiagnostics','downloadDiagnostics','startAdminTour','/api/admin/logs','/api/admin/audit','/api/admin/diagnostics'):
    if token not in admin_js: errors.append(f'Productization ADMIN behavior missing: {token}')
for rel in ('services/core/app/static/favicon.svg','services/core/app/static/manifest.webmanifest','services/core/app/static/user-guide.html','services/core/app/static/why.html'):
    if not (root/rel).exists(): errors.append(f'Browser/help asset missing: {rel}')
admin_guide=(root/'docs/ADMIN-GUIDE.md').read_text(encoding='utf-8') if (root/'docs/ADMIN-GUIDE.md').exists() else ''
for token in ('Пользователи и регистрация','Провайдеры','Маршрутизация','Structured logs и audit','Диагностика','Backup / restore / update','Безопасность'):
    if token not in admin_guide: errors.append(f'Admin guide contract missing: {token}')


# v0.8 alpha.8 bootstrap smoke hardening.
for token in ('"think": False','"num_predict": 32','empty_final_content','content_length'):
    if token not in core: errors.append(f'alpha8 bootstrap smoke contract missing: {token}')
for token in ('HTTP 200 but no final answer','INFERENCE bootstrap model='):
    if token not in ps: errors.append(f'alpha8 Windows bootstrap diagnostics missing: {token}')
for rel in ('tests/alpha8_bootstrap_smoke_acceptance.py','tests/alpha8-registry.json','docs/0.8.0-ALPHA8-BOOTSTRAP-SMOKE-HARDENING.md'):
    if not (root/rel).exists(): errors.append(f'alpha8 distribution file missing: {rel}')
try:
    a8=json.loads((root/'tests/alpha8-registry.json').read_text(encoding='utf-8'));a8ids={x.get('test_id') for x in a8.get('tests',[])}
    required_a8={'REL-A8-001','PERF-A8-001','PERF-A8-002','OBS-A8-001','REG-A8-001'}
    if required_a8-a8ids: errors.append(f'alpha8 registry missing IDs: {sorted(required_a8-a8ids)}')
except Exception as e: errors.append(f'alpha8 registry: {e}')

# v0.8 alpha.6 Search Integrity / Debug Observability / Result Cards.
for token in ('_extract_requested_domains','public_source_card','strict_domains','DEBUG_DIAGNOSTICS','X-PA-Duration-Ms','metadata=safe_metadata'):
    if token not in core: errors.append(f'alpha6 Core contract missing: {token}')
if 'admin_search_policy' not in scenario: errors.append('alpha6 search policy persistence contract missing: admin_search_policy')
for token in ('result-card-grid','renderMessageMeta','message-debug','function prettySize','artifact.list.failed'):
    if token not in user_js+css: errors.append(f'alpha6 USER result/debug UI missing: {token}')
for token in ('Поиск и качество источников','billingSetupChecklist'):
    if token not in admin_html+admin_js: errors.append(f'alpha6 ADMIN contract missing: {token}')
for token in ('Invoke-HttpProbe','HTTP smoke failed stage=','duration_ms=','request_id=','correlation_id='):
    if token not in ps: errors.append(f'alpha6 Windows diagnostics contract missing: {token}')
for rel in ('tests/alpha6_search_debug_acceptance.py','tests/alpha6-registry.json','tests/browser_admin_journeys.py','tests/browser_journeys_runner.py','docs/PAYMENT-SETUP-YOOKASSA.md','docs/0.8.0-ALPHA6-SEARCH-INTEGRITY-DEBUG.md'):
    if not (root/rel).exists(): errors.append(f'alpha6 distribution file missing: {rel}')

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
for token in ('trace_headers','X-Request-ID','X-Correlation-ID'):
    if token not in code_service: errors.append(f'Code correlation contract missing: {token}')
for token in ('SOCKET_GID','os.chmod(SOCKET_PATH, 0o660)','RUNTIME_INVENTORY','RUNTIME_INVENTORY_LOCK','runtime_inventory()','PRLIMIT_BIN','SETPRIV_BIN','--cpu=','--fsize=','--nofile=64:64','--nproc=64:64','--reuid=','--regid=','--clear-groups','start_new_session=True','terminate_process','powershell','javac','output_truncated','os.chown(work_dir, -1, RUNNER_GID)','os.chmod(work_dir, 0o2770)'):
    if token not in code_worker: errors.append(f'Code worker sandbox contract missing: {token}')
if 'CAP_DAC_OVERRIDE' in str((compose['services'].get('code-worker') or {}).get('cap_add') or []): errors.append('code-worker must not regain CAP_DAC_OVERRIDE')
for token in ('Code smoke diagnostics:','Code capability is DEGRADED after real execution smoke'):
    if token not in ps: errors.append(f'Code fail-soft diagnostics missing: {token}')
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
for f in ('compose.yaml','compose.release.yaml','scripts/pa.ps1','scripts/pa.sh','.env.example'):
    txt=(root/f).read_text(encoding='utf-8')
    if 'PA_TEST_MODE' in txt or 'PA_WEB_TEST_PUBLIC_HOSTS' in txt: errors.append(f'test-only Web bypass leaked into runtime config: {f}')
if not (root/'services/browser/Dockerfile').exists() or not (root/'services/browser/app/browser_worker.py').exists(): errors.append('browser worker missing')
browser_worker=(root/'services/browser/app/browser_worker.py').read_text(encoding='utf-8') if (root/'services/browser/app/browser_worker.py').exists() else ''
for token in ('X-Request-ID','X-Correlation-ID','request_id=','correlation_id='):
    if token not in browser_worker: errors.append(f'Browser correlation contract missing: {token}')
if not (root/'searxng/settings.yml').exists(): errors.append('SearXNG settings missing')
if not (root/'docs/specification/MASTER-SPEC.md').exists(): errors.append('canonical MASTER-SPEC missing')
if not (root/'tests/user-journeys-registry.json').exists(): errors.append('machine-readable user journey registry missing')
if not (root/'tests/productization-registry.json').exists(): errors.append('machine-readable productization registry missing')
else:
    try:
        preg=json.loads((root/'tests/productization-registry.json').read_text(encoding='utf-8')); pids={x.get('test_id') for x in preg.get('tests',[])}
        required_productization={'UX-001','UX-004','UX-005','UX-006','UX-007','UX-010','ONB-001','ONB-101','CONV-001','CONV-002','CONV-004','CONV-005','CONV-006','CONV-007','OBS-001','OBS-003','OBS-004','GUIDE-001'}
        if required_productization-pids: errors.append(f'productization registry missing IDs: {sorted(required_productization-pids)}')
    except Exception as e: errors.append(f'productization registry: {e}')
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
    '[CONTRACT] compose|restart|ollama|searxng|browser|core',
]:
    if token not in verify_ps: errors.append('VERIFY-PACKAGE Windows contract drift: '+token)
if errors:
    print('\n'.join('[FAIL] '+x for x in errors));sys.exit(1)
print('[PASS] Static package checks')
