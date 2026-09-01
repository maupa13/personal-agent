from __future__ import annotations
import json, os, pathlib, shutil, subprocess, sys, tempfile, time, urllib.request
from run_acceptance import free_port, req, wait, cookie_from, base_env, start_core

ROOT=pathlib.Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / 'release-evidence' / '_tmp' / 'billing'
TMP_ROOT.mkdir(parents=True, exist_ok=True)

def main():
    tmp=TMP_ROOT / f"par-billing-test-{os.getpid()}-{int(time.time()*1000)}";tmp.mkdir(parents=True, exist_ok=True);fake_port,web_port,pay_port,core_port=free_port(),free_port(),free_port(),free_port();token='billing-admin-token-123'
    fake=subprocess.Popen([sys.executable,str(ROOT/'tests'/'fake_ollama.py'),str(fake_port)])
    fake_web=subprocess.Popen([sys.executable,str(ROOT/'tests'/'fake_web.py'),str(web_port)])
    fake_pay=subprocess.Popen([sys.executable,str(ROOT/'tests'/'fake_payment.py'),str(pay_port)])
    env=base_env(tmp,fake_port,web_port,core_port,token,pathlib.Path(tmp)/'no-code.sock','billing.db','accounts')
    env['PA_PAYMENT_API_BASE']=f'http://127.0.0.1:{pay_port}/v3'
    env['PA_VERSION']='0.8.0-alpha.7-test'
    core=start_core(env);base=f'http://127.0.0.1:{core_port}'
    try:
        wait(base+'/api/health')
        # BILL-001 fixed service-support catalog: local is unlimited; remote quota is admin-configurable.
        _,plans,_=req(base+'/api/billing/plans',expect=200)
        prices={p['id']:p['price_rub'] for p in plans['plans']};assert prices=={'LIGHT':0,'MEDIUM':500,'PRO':1000},prices
        assert all(p['local_unlimited'] is True for p in plans['plans'])
        assert all(p['remote_token_limit']==0 for p in plans['plans'])

        _,registered,headers=req(base+'/api/auth/register',method='POST',body={'email':'bill@example.test','display_name':'Billing User','password':'strong-pass-123'},expect=201);cookie=cookie_from(headers);csrf=registered['csrf_token']
        _,me,_=req(base+'/api/auth/me',headers={'Cookie':cookie},expect=200);assert me['user']['role']=='OWNER'
        _,snap,_=req(base+'/api/billing/me',headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert snap['plan']['id']=='LIGHT' and snap['quota']['platform_remote_tokens_limit']==0  # RBAC role != commercial plan

        # Local inference is always allowed and is metered only for monitoring.
        req(base+'/api/billing/preferences',method='POST',body={'show_token_usage':True},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200)
        _,chat,_=req(base+'/api/chat',method='POST',body={'mode':'auto','messages':[{'role':'user','content':'Привет'}]},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200)
        assert chat['usage']['billing_class']=='LOCAL' and chat['usage']['total_tokens']==25 and chat['usage']['exact'] is True
        _,snap,_=req(base+'/api/billing/me',headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert snap['usage']['by_class']['LOCAL']['total_tokens']>=25

        # BILL-002/005: platform-paid remote provider is quota controlled and falls back local when LIGHT has no allowance.
        _,created,_=req(base+'/api/admin/providers',method='POST',body={'name':'Platform Remote Test','type':'openai_compatible','base_url':f'http://127.0.0.1:{fake_port}/v1','api_key':'platform-secret','billing_class':'PLATFORM_REMOTE','cost_input_per_million_rub':10,'cost_output_per_million_rub':20},token=token,expect=201)
        remote_id=created['provider']['id']
        req(base+'/api/admin/routing',method='POST',body={'routing':{'smart':{'provider_id':remote_id,'model_id':'qwen3:8b'}}},token=token,expect=200)
        _,fallback,_=req(base+'/api/chat',method='POST',body={'mode':'smart','messages':[{'role':'user','content':'remote please'}]},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200)
        assert fallback['usage']['billing_class']=='LOCAL' and 'выполнен локально' in fallback.get('billing_notice','')

        # Admin sets quota without deploy/restart and assigns Medium. Remote usage then succeeds and consumes quota.
        _,plan,_=req(base+'/api/admin/billing/plans/MEDIUM',method='POST',body={'remote_token_limit':1000,'remote_cost_limit_rub':50},token=token,expect=200);assert plan['plan']['price_rub']==500 and plan['plan']['remote_token_limit']==1000
        _,users,_=req(base+'/api/admin/users',token=token,expect=200);uid=next(u['id'] for u in users['users'] if u['email']=='bill@example.test')
        _,balance,_=req(base+'/api/admin/billing/balance',method='POST',body={'user_id':uid,'delta_rub':200,'reason':'theme purchase test'},token=token,expect=200);assert balance['balance']['balance_rub']==200
        _,theme,_=req(base+'/api/billing/themes/purchase',method='POST',body={'theme_id':'ocean'},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert theme['owned'] and theme['balance']['balance_rub']==101
        _,owned_again,_=req(base+'/api/billing/themes/purchase',method='POST',body={'theme_id':'ocean'},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert owned_again['already_owned'] and owned_again['balance']['balance_rub']==101
        _,snap,_=req(base+'/api/billing/me',headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert 'ocean' in snap['owned_themes'] and any(item['id']=='ocean' and item['owned'] for item in snap['themes'])
        req(base+f'/api/admin/users/{uid}/plan',method='POST',body={'plan_id':'MEDIUM'},token=token,expect=200)
        _,remote,_=req(base+'/api/chat',method='POST',body={'mode':'smart','messages':[{'role':'user','content':'remote now'}]},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200)
        assert remote['message']['content']=='PAR_OPENAI_COMPAT_OK' and remote['usage']['billing_class']=='PLATFORM_REMOTE' and remote['usage']['total_tokens']==30
        _,snap,_=req(base+'/api/billing/me',headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert snap['plan']['id']=='MEDIUM' and snap['quota']['platform_remote_tokens_remaining']==970

        # BILL-004 BYOK is separated from platform cost/quota, but remains visible in monitoring.
        _,created2,_=req(base+'/api/admin/providers',method='POST',body={'name':'User BYOK Test','type':'openai_compatible','base_url':f'http://127.0.0.1:{fake_port}/v1','api_key':'user-owned-key','billing_class':'BYOK','cost_input_per_million_rub':999,'cost_output_per_million_rub':999},token=token,expect=201);byok_id=created2['provider']['id']
        req(base+'/api/admin/users/'+uid+'/plan',method='POST',body={'plan_id':'LIGHT'},token=token,expect=200)
        req(base+'/api/admin/routing',method='POST',body={'routing':{'fast':{'provider_id':byok_id,'model_id':'qwen3:8b'}}},token=token,expect=200)
        _,byok,_=req(base+'/api/chat',method='POST',body={'mode':'fast','messages':[{'role':'user','content':'byok'}]},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert byok['usage']['billing_class']=='BYOK'

        # BILL-003 deterministic payment adapter: credentials/config live in Admin; checkout + verified idempotent webhook activate plan.
        _,cfg,_=req(base+'/api/admin/billing/payment-config',method='POST',body={'provider':'yookassa','shop_id':'test-shop-1','secret_key':'test-secret-key','public_base_url':base},token=token,expect=200);assert cfg['payment_config']['configured'] is True and 'test-secret-key' not in json.dumps(cfg)
        _,checkout,_=req(base+'/api/billing/checkout',method='POST',body={'plan_id':'PRO'},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=201);assert checkout['confirmation_url'].startswith('https://pay.example.test/')
        notice={'type':'notification','event':'payment.succeeded','object':{'id':checkout['provider_payment_id']}}
        _,processed,_=req(base+'/api/billing/webhook/yookassa',method='POST',body=notice,expect=200);assert processed['status']=='PAID' and processed['plan_id']=='PRO'
        _,duplicate,_=req(base+'/api/billing/webhook/yookassa',method='POST',body=notice,expect=200);assert duplicate.get('duplicate') is True
        _,snap,_=req(base+'/api/billing/me',headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert snap['plan']['id']=='PRO' and snap['subscription']['auto_renew'] is True
        _,payment,_=req(base+'/api/billing/payments/'+checkout['payment_id'],headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert payment['payment']['status']=='PAID'

        # Cancellation preserves paid period; no destructive immediate downgrade.
        _,cancel,_=req(base+'/api/billing/cancel',method='POST',body={},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert cancel['subscription']['status']=='CANCEL_AT_PERIOD_END' and cancel['subscription']['cancel_at_period_end']==1

        _,admin,_=req(base+'/api/admin/billing',token=token,expect=200)
        assert admin['payment_config']['configured'] is True
        assert {p['id']:p['price_rub'] for p in admin['plans']}=={'LIGHT':0,'MEDIUM':500,'PRO':1000}
        assert any(x['billing_class']=='LOCAL' for x in admin['usage']) and any(x['billing_class']=='PLATFORM_REMOTE' for x in admin['usage']) and any(x['billing_class']=='BYOK' for x in admin['usage'])

        print('PAR_V080_BILLING_ACCEPTANCE PASS: plans local-unlimited token-display remote-quota local-fallback byok-separation payment-adapter verified-webhook idempotency cancel-period-end admin-usage')
        return 0
    finally:
        for p in (core,fake,fake_web,fake_pay):
            try:
                if p.poll() is None:p.terminate();p.wait(timeout=3)
            except Exception:
                try:p.kill()
                except Exception:pass
        shutil.rmtree(tmp,ignore_errors=True)
if __name__=='__main__': raise SystemExit(main())
