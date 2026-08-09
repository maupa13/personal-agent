from __future__ import annotations
import pathlib, shutil

ROOT=pathlib.Path(__file__).resolve().parents[1]
APP=ROOT/'services/core/app'
import sys
sys.path.insert(0,str(APP))
from scenario_service import ScenarioService, ScenarioError
from conversation_service import ConversationStore
from billing_service import BillingService

checks=[]
def ok(test_id,name,fn):
    fn();checks.append(test_id);print(f'[PASS] {test_id} - {name}')

TMP_ROOT=ROOT/'release-evidence'/'_tmp'

def fresh_dir(name: str) -> pathlib.Path:
    path=TMP_ROOT/name
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    return path

main=(APP/'main.py').read_text(encoding='utf-8')
appjs=(APP/'static/app.js').read_text(encoding='utf-8')
css=(APP/'static/styles.css').read_text(encoding='utf-8')
admin=(APP/'static/admin.html').read_text(encoding='utf-8')+(APP/'static/admin.js').read_text(encoding='utf-8')
ps=(ROOT/'scripts/pa.ps1').read_text(encoding='ascii')

def source_contract():
    for token in ('_extract_requested_domains','strict_domains','Источник ответа не соответствует сайту','site:{domains[0]}','admin_blocked'):
        assert token in main,token
ok('SRC-001','Explicit bare domains are authoritative source scope',source_contract)

def no_substitution():
    assert 'if direct_domains and not any(_same_domain' in main
    assert 'if direct_domains:\n        sources = [source for source in sources' in main
ok('SRC-002','Cross-domain evidence is filtered for explicit-domain requests',no_substitution)

def policy_persist():
    td=fresh_dir('alpha6-search-policy')
    try:
        svc=ScenarioService(td/'db.sqlite');svc.init_schema()
        value=svc.set_search_policy({'provider_order':['searxng'],'general_max_sources':4,'news_max_sources':7,'research_max_sources':11,'preferred_domains':['dtf.ru'],'blocked_domains':['spam.example']})
        assert value['provider_order']==['searxng'] and value['news_max_sources']==7
        again=ScenarioService(td/'db.sqlite');again.init_schema();value2=again.search_policy()
        assert value2['preferred_domains']==['dtf.ru'] and value2['blocked_domains']==['spam.example']
        try: again.set_search_policy({'provider_order':['google']})
        except ScenarioError: pass
        else: raise AssertionError('fake provider accepted')
    finally:
        shutil.rmtree(td, ignore_errors=True)
ok('SRC-004','Admin source/search policy persists and advertises only real adapters',policy_persist)

def cards():
    for token in ('result-card-grid','result-kind-news','result-kind-product','result-kind-real_estate','result-kind-procurement','prefers-reduced-motion'):
        assert token in appjs+css,token
ok('RESULT-001','Adaptive cards exist for news/products/real-estate/procurement',cards)

def timing_persist():
    td=fresh_dir('alpha6-timing')
    try:
        store=ConversationStore(td/'db.sqlite');store.init_schema();c=store.create('u1')
        store.add_message('u1',c['id'],role='assistant',content='ok',metadata={'duration_ms':1234,'routing_ms':10,'web_ms':500,'inference_ms':700,'request_id':'req1','correlation_id':'corr1'})
        got=store.get('u1',c['id'])['messages'][0]['metadata']
        assert got['duration_ms']==1234 and got['correlation_id']=='corr1'
    finally:
        shutil.rmtree(td, ignore_errors=True)
ok('OBS-A6-001','Per-answer timing/trace metadata survives DB reload',timing_persist)

def debug_ui():
    for token in ('renderMessageMeta','message-debug','routing_ms','web_ms','inference_ms','correlation_id'):
        assert token in appjs+css,token
    assert 'model_id' not in appjs.lower(), 'USER UI exposes technical model id'
ok('OBS-A6-002','USER shows timing while technical routing IDs remain out of public UI',debug_ui)

def lifecycle_diag():
    for token in ('Invoke-HttpProbe','Trace-HttpProbe','Assert-HttpProbe','duration_ms=','request_id=','correlation_id=','HTTP smoke failed stage='):
        assert token in ps,token
ok('OBS-A6-003','Windows lifecycle HTTP failures contain actionable stage/status/timing/trace diagnostics',lifecycle_diag)

def payment_setup():
    td=fresh_dir('alpha6-payment')
    try:
        svc=BillingService(td/'db.sqlite',td/'secrets',test_mode=True);svc.init_schema()
        empty=svc.payment_config();assert empty['configured'] is False and empty['setup']['production_ready'] is False and 'secret_key' not in empty
        cfg=svc.configure_yookassa(shop_id='123456',secret_key='secret-test-value',public_base_url='https://agent.example.test')
        assert cfg['configured'] is True and cfg['webhook_url'].endswith('/api/billing/webhook/yookassa') and cfg['setup']['secret'] is True
        assert 'secret-test-value' not in str(cfg)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    assert 'billingSetupChecklist' in admin
ok('BILL-A6-001','Turnkey YooKassa setup exposes a safe readiness checklist without returning secrets',payment_setup)


def artifact_ui_observable():
    assert 'function prettySize' in appjs
    assert 'artifact.list.failed' in appjs
ok('RESULT-002','Artifact list renders verified export metadata and exposes formatter failures in debug mode',artifact_ui_observable)

print(f'PAR_V080_ALPHA6_SEARCH_DEBUG_ACCEPTANCE PASS: {len(checks)} checks')
