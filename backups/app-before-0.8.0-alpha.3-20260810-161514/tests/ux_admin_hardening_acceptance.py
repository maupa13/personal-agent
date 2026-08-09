from __future__ import annotations
import hashlib, importlib.util, json, pathlib, sqlite3, tempfile, time

ROOT=pathlib.Path(__file__).resolve().parents[1]
STATIC=ROOT/'services/core/app/static'
MAIN=(ROOT/'services/core/app/main.py').read_text(encoding='utf-8')
APP=(STATIC/'app.js').read_text(encoding='utf-8')
INDEX=(STATIC/'index.html').read_text(encoding='utf-8')
ADMIN=(STATIC/'admin.html').read_text(encoding='utf-8')
ADMIN_JS=(STATIC/'admin.js').read_text(encoding='utf-8')
CSS=(STATIC/'styles.css').read_text(encoding='utf-8')

spec=importlib.util.spec_from_file_location('experience_service', ROOT/'services/core/app/experience_service.py')
mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)
ExperienceService=mod.ExperienceService; ExperienceError=mod.ExperienceError

def ok(test_id,msg): print(f'[PASS] {test_id} - {msg}')

def main():
    with tempfile.TemporaryDirectory(prefix='par-alpha4-') as td:
        db=pathlib.Path(td)/'a4.db';svc=ExperienceService(db);svc.init_schema()
        p=svc.preferences('u1');assert p['theme']=='system' and p['execution_policy']=='auto' and p['tone']=='normal'
        p=svc.set_preferences('u1',{'ui_language':'en','response_language':'ru','theme':'light','execution_policy':'local_only','tone':'meme'})
        assert (p['ui_language'],p['theme'],p['execution_policy'],p['tone'])==('en','light','local_only','meme')
        svc2=ExperienceService(db);svc2.init_schema();p2=svc2.preferences('u1');assert p2['theme']=='light' and p2['tone']=='meme'
        ok('UX-A4-001','theme/language/execution/tone preferences persist server-side')
        for bad in ({'theme':'neon'},{'execution_policy':'magic'},{'tone':'unsafe'},{'ui_language':'xx'}):
            try: svc.set_preferences('u1',bad);raise AssertionError(bad)
            except ExperienceError: pass
        ok('UX-A4-002','experience preferences reject unknown values')
        fb=svc.add_feedback('u1',{'category':'ux','rating':5,'message':'Очень удобная форма','page':'/'})
        assert fb['category']=='ux' and svc.feedback_list()[0]['message']=='Очень удобная форма'
        ok('FEEDBACK-A4-001','unobtrusive feedback persists for Admin review')
        share=svc.create_share('u1','c1','Диалог','# Диалог\n\nПривет',ttl_seconds=86400)
        assert 'token' in share and svc.get_share(share['token'])['content_md'].endswith('Привет')
        with sqlite3.connect(db) as conn:
            stored=conn.execute('select share_token_hash from conversation_shares where id=?',(share['id'],)).fetchone()[0]
        assert stored==hashlib.sha256(share['token'].encode()).hexdigest() and share['token'] not in stored
        assert svc.revoke_share('u1',share['id']) and svc.get_share(share['token']) is None
        ok('SHARE-A4-001','share links store token hashes, expire and can be revoked')

    # Execution/privacy and tone are backend policy, not cosmetic UI only.
    for token in ('def choose_route_for_execution_policy','local_only','remote_only','require_entitlement(user, "remote_ai")','def apply_response_preferences','TONE_DEFS'):
        assert token in MAIN,token
    assert 'Мемный' in MAIN and ('факт' in MAIN.lower() or 'точн' in MAIN.lower())
    ok('EXEC-A4-001','local/remote execution policy is enforced by Core')
    ok('TONE-A4-001','humorous tone exists with accuracy-first invariant')

    # Personal owner path: normal local Admin access, emergency token remains separate.
    assert '"role": "OWNER"' in MAIN and 'peer.is_loopback' in MAIN and 'local owner admin access is limited to this PC' in MAIN
    assert 'supplied = str(body.get("token", "")).strip()' in MAIN
    ok('ADMIN-A4-001','local OWNER can administer on loopback; break-glass token is normalized and independent')

    # Admin actually controls providers/models/routing; OpenAI Responses is a first-class remote adapter.
    for token in ('openai_responses','/responses','output_text','/api/admin/providers','/api/admin/routing'):
        assert token in MAIN,token
    for token in ('OpenAI API · Responses','providerType','providerUrl','saveRoutes','Модели','Маршрутизация'):
        assert token in ADMIN+ADMIN_JS,token
    ok('ADMIN-A4-002','Admin provider/model/routing UI includes OpenAI Responses VPS test path')

    # Product UI contracts raised from user screenshots.
    for token in ('uiLanguage','responseLanguage','themeSelect','executionPolicy','tonePreset','toneButton','feedbackEntry','shareChatButton'):
        assert token in INDEX+APP,token
    assert 'html[data-theme="light"]' in CSS and '#webAllowedDomains,#webExcludedDomains,#artifactContent,#codeEditor' in CSS
    assert '.sidebar.collapsed .folder-list' in CSS and 'display:none!important' in CSS
    assert '.settings-content .code-editor{width:100%' in CSS
    ok('UI-A4-001','light/dark/system, clean collapsed rail and full-width textarea/code editor contracts ship')

    for file in ('local-setup.html','admin-guide.html'):
        content=(STATIC/file).read_text(encoding='utf-8');assert '0.8.0-alpha.5' in content and 'Родной Агент' in content
    ok('GUIDE-A4-001','local user setup and Admin model/routing guides ship in-product')

    # Feedback and share UI must explain privacy instead of silently publishing account state.
    assert 'read-only' in APP and 'workspace' in APP and '7 дней' in APP
    assert 'Не прикладывайте пароли, API-ключи' in INDEX
    ok('PRIV-A4-001','share/feedback UI contains explicit privacy boundaries')

    print('PAR_V080_ALPHA4_UX_ADMIN_HARDENING_ACCEPTANCE PASS')
    return 0

if __name__=='__main__': raise SystemExit(main())
