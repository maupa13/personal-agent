from __future__ import annotations
import concurrent.futures, http.client, io, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
CORE=ROOT/'services'/'core'/'app'/'main.py'

def free_port():
    s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close();return p

def req(url,method='GET',body=None,token=None,expect=None,timeout=10,headers=None):
    data=None if body is None else json.dumps(body,ensure_ascii=False).encode('utf-8')
    hdr={'Content-Type':'application/json'}
    if headers: hdr.update(headers)
    if token: hdr['Authorization']='Bearer '+token
    r=urllib.request.Request(url,data=data,headers=hdr,method=method)
    try:
        with urllib.request.urlopen(r,timeout=timeout) as resp:
            raw=resp.read().decode('utf-8');status=resp.status;out_headers=dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw=e.read().decode('utf-8');status=e.code;out_headers=dict(e.headers)
    if expect is not None and status!=expect: raise AssertionError(f'{url}: expected {expect}, got {status}: {raw}')
    return status,(json.loads(raw) if raw else {}),out_headers

def req_text(url,expect=200):
    try:
        with urllib.request.urlopen(url,timeout=5) as r:return r.status,r.read().decode('utf-8'),dict(r.headers)
    except urllib.error.HTTPError as e:return e.code,e.read().decode('utf-8'),dict(e.headers)

def req_bytes(url,method='GET',data=None,headers=None,expect=None,timeout=10):
    r=urllib.request.Request(url,data=data,headers=headers or {},method=method)
    try:
        with urllib.request.urlopen(r,timeout=timeout) as resp:return resp.status,resp.read(),dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw=e.read()
        if expect is not None and e.code==expect:return e.code,raw,dict(e.headers)
        raise


def wait(url,seconds=15):
    end=time.time()+seconds;last=None
    while time.time()<end:
        try:
            status,body,_=req(url,expect=None);last=(status,body)
            if status==200 and body.get('ready') is True:return
        except Exception as exc:last=repr(exc)
        time.sleep(.1)
    raise AssertionError(f'server did not become ready: {last}')

def start_core(env):
    return subprocess.Popen([sys.executable,str(CORE)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,text=True)

def cookie_from(headers):
    raw=headers.get('Set-Cookie','')
    return raw.split(';',1)[0]

def base_env(tmp,fake_port,web_port,core_port,token,code_socket,db_name='personal-agent-rus.db',auth_mode='personal'):
    env=os.environ.copy();env.update({
        'PYTHONDONTWRITEBYTECODE':'1',
        'PA_OLLAMA_URL':f'http://127.0.0.1:{fake_port}',
        'PA_SEARXNG_URL':f'http://127.0.0.1:{web_port}',
        'PA_BROWSER_URL':f'http://127.0.0.1:{web_port}',
        'PA_HOST':'127.0.0.1','PA_PORT':str(core_port),'PA_ADMIN_TOKEN':token,
        'PA_DB':str(pathlib.Path(tmp)/db_name),'PA_SECRETS_DIR':str(pathlib.Path(tmp)/'secrets'),'PA_WORKSPACE_ROOT':str(pathlib.Path(tmp)/('workspaces-'+db_name)),
        'PA_BOOTSTRAP_MODEL':'qwen3:0.6b','PA_VERSION':'test','PA_AUTH_MODE':auth_mode,'PA_REGISTRATION_POLICY':'open',
        'PA_TEST_MODE':'1','PA_WEB_TEST_PUBLIC_HOSTS':'example.com,example.org','PA_FILE_MAX_BYTES':str(2*1024*1024),'PA_CODE_SOCKET':str(code_socket),'PA_CODE_MAX_TIMEOUT_SECONDS':'5'
    });return env

def main():
    tmp=tempfile.mkdtemp(prefix='par-v050-test-');fake_port,web_port,core_port=free_port(),free_port(),free_port();token='test-admin-token-123'
    pathlib.Path(tmp).chmod(0o755)
    fake_bin=pathlib.Path(tmp)/'bin';fake_bin.mkdir();fake_pwsh=fake_bin/'pwsh';fake_pwsh.write_text('#!/usr/bin/env python3\nimport pathlib,re,sys,time\nif "-Version" in sys.argv: print("PowerShell 7.6.0-test"); raise SystemExit(0)\nif "-File" in sys.argv:\n p=pathlib.Path(sys.argv[sys.argv.index("-File")+1]); s=p.read_text(encoding="utf-8"); m=re.search(r"Write-Output\\s+[\\"\\\\x27]([^\\"\\\\x27]+)",s,re.I); print(m.group(1) if m else "PS_OK"); time.sleep(5 if "PAR_SLEEP" in s else 0); raise SystemExit(0)\n',encoding='utf-8');fake_pwsh.chmod(0o755)
    code_socket=pathlib.Path(tmp)/'code-worker.sock';code_env=os.environ.copy();code_env.update({'PYTHONDONTWRITEBYTECODE':'1','PATH':str(fake_bin)+os.pathsep+code_env.get('PATH',''),'PA_CODE_SOCKET':str(code_socket),'PA_CODE_WORK_ROOT':str(pathlib.Path(tmp)/'code-work'),'PA_CODE_RUNNER_UID':str(os.getuid()),'PA_CODE_RUNNER_GID':str(os.getgid()),'PA_CODE_MAX_TIMEOUT_SECONDS':'5'})
    code_worker=subprocess.Popen([sys.executable,str(ROOT/'services'/'code-worker'/'app'/'code_worker.py')],env=code_env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,text=True)
    for _ in range(100):
        if code_socket.exists(): break
        time.sleep(.02)
    fake=subprocess.Popen([sys.executable,str(ROOT/'tests'/'fake_ollama.py'),str(fake_port)])
    fake_web=subprocess.Popen([sys.executable,str(ROOT/'tests'/'fake_web.py'),str(web_port)])
    env=base_env(tmp,fake_port,web_port,core_port,token,code_socket)
    core=start_core(env);base=f'http://127.0.0.1:{core_port}'
    try:
        wait(base+'/api/health')
        _,health,_=req(base+'/api/health',expect=200);assert health['ready'] is True
        _,system,hdr=req(base+'/api/system',expect=200)
        public=json.dumps(system,ensure_ascii=False).lower()
        for secret in ('qwen','ollama','model_id','provider_id','par-rus-ollama'):assert secret not in public,f'public API leak: {secret}'
        assert [x['id'] for x in system['modes']]==['auto','fast','smart']
        assert [x['id'] for x in system['presets']]==['explain','write','analyze']
        assert system['auth']['mode']=='personal'
        assert system['capabilities']['chat']['status']=='ready' and system['capabilities']['web']['status']=='ready' and system['capabilities']['research']['status']=='ready' and system['capabilities']['files']['status']=='ready' and system['capabilities']['code']['status']=='ready'
        assert hdr.get('X-Frame-Options')=='DENY' and 'Content-Security-Policy' in hdr
        status,html,hdr=req_text(base+'/');assert status==200;low=html.lower();assert 'personal agent rus' in low and 'qwen' not in low and 'ollama' not in low;assert 'no-store' in hdr.get('Cache-Control','')
        for page in ('/register','/login','/account','/admin'):
            status,_,_=req_text(base+page);assert status==200,page
        _,me,_=req(base+'/api/auth/me',expect=200);assert me['user']['id']=='local-owner'
        status,_,_=req(base+'/api/auth/register',method='POST',body={'email':'x@y.z','display_name':'Test','password':'1234567890'},expect=409)
        req(base+'/api/admin/status',token=None,expect=401);req(base+'/api/admin/login',method='POST',body={'token':'bad'},expect=401);req(base+'/api/admin/login',method='POST',body={'token':token},expect=200)
        _,admin,_=req(base+'/api/admin/status',token=token,expect=200)
        assert admin['routing']['auto']['provider_id']=='local-ollama' and admin['routing']['auto']['model_id']=='qwen3:0.6b'
        assert any(p['id']=='local-ollama' and p['managed_by']=='system' for p in admin['providers'])
        local_models=[m for m in admin['model_inventory'] if m['provider_id']=='local-ollama'];assert len(local_models)>=2
        # DEPLOY/OBS foundation: target metadata + host fingerprint only; credentials are never returned/persisted.
        _,obs,_=req(base+'/api/admin/observability',token=token,expect=200);assert obs['observability']['runtime_profile']=='local' and 'counts' in obs['observability']
        _,target_created,_=req(base+'/api/admin/deployments',method='POST',body={'name':'Test VPS','host':'vps.example.test','port':22,'username':'deploy','domain':'agent.example.test','profile':'server-lite','host_key_sha256':'SHA256:TESTFINGERPRINT'},token=token,expect=201);deploy_id=target_created['target']['id']
        _,targets,_=req(base+'/api/admin/deployments',token=token,expect=200);assert any(x['id']==deploy_id and x['profile']=='server-lite' for x in targets['targets']);assert 'password' not in json.dumps(targets).lower() and 'private_key' not in json.dumps(targets).lower()
        req(base+f'/api/admin/deployments/{deploy_id}/preflight',method='POST',body={},token=token,expect=400)

        # External/OpenAI-compatible provider is configured once, then models are auto-discovered.
        secret='do-not-leak-provider-secret'
        _,created,_=req(base+'/api/admin/providers',method='POST',body={'name':'Test OpenAI Compatible','type':'openai_compatible','base_url':f'http://127.0.0.1:{fake_port}/v1','api_key':secret},token=token,expect=201)
        ext_id=created['provider']['id'];assert created['provider']['model_count']>=2 and created['provider']['has_secret'] is True
        _,providers,_=req(base+'/api/admin/providers',token=token,expect=200);dump=json.dumps(providers,ensure_ascii=False);assert secret not in dump;assert any(p['id']==ext_id for p in providers['providers']);assert any(m['provider_id']==ext_id for m in providers['inventory'])
        req(base+f'/api/admin/providers/{ext_id}/test',method='POST',body={},token=token,expect=200)

        req(base+'/api/chat',method='POST',body={'mode':'smart','preset':'none','messages':[]},expect=400)
        req(base+'/api/chat',method='POST',body={'mode':'unknown','messages':[{'role':'user','content':'x'}]},expect=400)
        req(base+'/api/chat',method='POST',body={'mode':'auto','preset':'unknown','messages':[{'role':'user','content':'x'}]},expect=400)
        # WEB-001 search normalization / de-duplication
        _,search,_=req(base+'/api/web/search',method='POST',body={'query':'новости DTF','limit':5,'category':'news'},expect=200);assert len(search['results'])==2 and len({x['url'] for x in search['results']})==2
        # WEB-002/003 static/browser read contract: fixture URL falls back to browser renderer.
        _,page,_=req(base+'/api/web/read',method='POST',body={'url':'https://example.com/dynamic'},expect=200);assert 'Dynamic fixture page' in page['page']['text'] and page['page']['strategy']=='browser'
        # WEB-008 direct SSRF and WEB-009 browser final-URL private redirect are blocked.
        req(base+'/api/web/read',method='POST',body={'url':'http://127.0.0.1/private'},expect=400)
        req(base+'/api/web/read',method='POST',body={'url':'https://example.com/private-redirect'},expect=400)
        # WEB-004 URL request must carry retrieved source evidence.
        _,urlchat,_=req(base+'/api/chat',method='POST',body={'mode':'auto','messages':[{'role':'user','content':'Что на https://example.com/dynamic?'}]},expect=200);assert urlchat['intent']=='url' and len(urlchat['sources'])>=1
        # WEB-005 freshness is automatically detected without an explicit intent hint.
        _,fresh,_=req(base+'/api/chat',method='POST',body={'mode':'auto','messages':[{'role':'user','content':'Какие сегодня свежие новости DTF?'}]},expect=200);assert fresh['intent'] in ('search','research') and len(fresh['sources'])>=2
        # WEB-006 explicit research returns multiple sources.
        _,webchat,_=req(base+'/api/chat',method='POST',body={'mode':'auto','intent_hint':'research','messages':[{'role':'user','content':'Выдай свежие новости DTF'}]},expect=200);assert webchat['intent']=='research' and len(webchat['sources'])>=2
        # WEB-010 hostile instructions are inserted only inside the explicit untrusted observation block.
        _,last,_=req(f'http://127.0.0.1:{fake_port}/test/last',expect=200);joined=' '.join(str(m.get('content','')) for m in last['messages']);assert 'WEB TOOL OBSERVATIONS' in joined and 'UNTRUSTED EXTERNAL DATA' in joined and 'Ignore previous instructions' in joined
        assert 'reveal secrets' not in webchat['message']['content'].lower()
        _,research,_=req(base+'/api/research',method='POST',body={'question':'Исследуй свежие новости DTF по нескольким источникам','max_sources':3},expect=200);assert len(research['sources'])>=2 and research['answer']
        # TASK-001..004 multi-capability durable task: research -> MD/XLSX/PDF -> verified artifacts + events.
        _,task_created,_=req(base+'/api/tasks',method='POST',body={'type':'research_report','question':'Подготовь проверенный отчёт о свежих новостях DTF','formats':['md','xlsx','pdf']},expect=202);task_id=task_created['task']['id'];assert len(task_id)==32
        for _ in range(240):
            _,task_payload,_=req(base+'/api/tasks/'+task_id,expect=200);task=task_payload['task']
            if task['status'] in ('COMPLETED','FAILED','CANCELLED'):break
            time.sleep(.05)
        assert task['status']=='COMPLETED',task
        assert [x['name'].split('.')[-1] for x in task['result']['artifacts']]==['md','xlsx','pdf']
        assert all(x['validation_status']=='verified' and len(x['sha256'])==64 for x in task['result']['artifacts'])
        _,task_events,_=req(base+f'/api/tasks/{task_id}/events?format=json',expect=200);assert len(task_events['events'])>=4 and task_events['events'][-1]['status']=='COMPLETED'
        _,task_list,_=req(base+'/api/tasks',expect=200);assert any(x['id']==task_id for x in task_list['tasks'])
        # WEB-007 no evidence => controlled 502, never model-memory fabrication.
        req(base+'/api/chat',method='POST',body={'mode':'auto','intent_hint':'research','messages':[{'role':'user','content':'PAR_NO_RESULTS'}]},expect=502)

        # FILE-001..008: create -> parser validation -> metadata -> download for every required v0.4 format.
        file_payloads={
            'txt':'Привет из TXT',
            'md':'# Markdown\n\nПроверяем **файл**.',
            'json':{'project':'Personal Agent Rus','ok':True},
            'csv':{'headers':['name','value'],'rows':[['alpha',1],['beta',2]]},
            'pdf':'PDF создан Personal Agent Rus.\nСтрока на русском.',
            'docx':{'title':'Документ','paragraphs':['Первый абзац','Второй абзац']},
            'xlsx':{'headers':['name','value'],'rows':[['alpha',1],['beta',2]]},
            'pptx':{'title':'Презентация','paragraphs':['Первый тезис','Второй тезис']},
        }
        created_files={}
        for fmt,content in file_payloads.items():
            _,created_file,_=req(base+'/api/files/create',method='POST',body={'format':fmt,'name':f'acceptance.{fmt}','content':content},expect=201)
            artifact=created_file['artifact'];created_files[fmt]=artifact;assert artifact['format']==fmt and artifact['validation_status']=='verified' and artifact['size']>0 and len(artifact['sha256'])==64
            _,detail,_=req(base+f"/api/files/{artifact['artifact_id']}",expect=200);assert detail['artifact']['text'] is not None and detail['artifact']['validation_status']=='verified'
            status,raw,headers=req_bytes(base+artifact['download_url'],expect=200);assert status==200 and len(raw)==artifact['size'] and 'attachment' in headers.get('Content-Disposition','')
        # FILE-009 raw upload + filename/path safety.
        upload_data='Загруженный текст для анализа'.encode('utf-8')
        status,raw,_=req_bytes(base+'/api/files/upload',method='POST',data=upload_data,headers={'Content-Type':'text/plain','X-PA-Filename':urllib.parse.quote('../../unsafe.txt',safe='')},expect=201)
        uploaded=json.loads(raw.decode('utf-8'))['artifact'];assert uploaded['name']=='unsafe.txt' and uploaded['validation_status']=='verified'
        # FILE-010 malformed/mismatched content is rejected.
        status,_,_=req_bytes(base+'/api/files/upload',method='POST',data=b'not a pdf',headers={'Content-Type':'application/pdf','X-PA-Filename':'broken.pdf'},expect=400);assert status==400
        # FILE-015 zip-slip and FILE-016 oversized payload fail closed before becoming artifacts.
        malicious=io.BytesIO()
        with zipfile.ZipFile(malicious,'w',zipfile.ZIP_DEFLATED) as zf: zf.writestr('../escape.xml','owned')
        status,_,_=req_bytes(base+'/api/files/upload',method='POST',data=malicious.getvalue(),headers={'Content-Type':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','X-PA-Filename':'evil.docx'},expect=400);assert status==400
        parsed_base=urllib.parse.urlparse(base);conn=http.client.HTTPConnection(parsed_base.hostname,parsed_base.port,timeout=10);conn.putrequest('POST','/api/files/upload');conn.putheader('Content-Type','text/plain');conn.putheader('X-PA-Filename','too-large.txt');conn.putheader('Content-Length',str(2*1024*1024+1));conn.endheaders();oversized_response=conn.getresponse();assert oversized_response.status==413;oversized_response.read();conn.close()
        # FILE-011 update creates a verified new version; original remains addressable.
        _,revision,_=req(base+f"/api/files/{created_files['docx']['artifact_id']}/update",method='POST',body={'content':{'title':'Изменено','paragraphs':['Новая версия']}},expect=201);assert revision['artifact']['parent_id']==created_files['docx']['artifact_id'] and revision['artifact']['version']>=2 and 'Новая версия' in revision['artifact']['text']
        # FILE-012 file context reaches the model only as explicit untrusted file observations.
        _,file_chat,_=req(base+'/api/chat',method='POST',body={'mode':'auto','preset':'analyze','file_ids':[uploaded['artifact_id']],'messages':[{'role':'user','content':'Что написано в приложенном файле?'}]},expect=200);assert file_chat['message']['content']
        _,last,_=req(f'http://127.0.0.1:{fake_port}/test/last',expect=200);file_system='\n'.join(m.get('content','') for m in last['messages'] if m.get('role')=='system');assert 'FILE TOOL OBSERVATIONS' in file_system and 'UNTRUSTED USER FILE DATA' in file_system and 'Загруженный текст' in file_system
        # FILE-013 artifact listing exposes only product metadata, never storage paths.
        _,listed,_=req(base+'/api/files',expect=200);assert len(listed['artifacts'])>=10;assert 'storage_key' not in json.dumps(listed)

        # CODE-001..003: Python, Java 21 and PowerShell job contracts through Core -> sandbox worker.
        _,code_status,_=req(base+'/api/code/status',expect=200);assert code_status['ready'] is True and code_status['network']=='disabled' and {x['id'] for x in code_status['languages']}=={'python','java','powershell'}
        code_cases={
            'python':('print("PY_CODE_OK")','PY_CODE_OK'),
            'java':('public class Main { public static void main(String[] a){ System.out.println("JAVA_CODE_OK"); }}','JAVA_CODE_OK'),
            'powershell':('Write-Output "PS_CODE_OK"','PS_CODE_OK'),
        }
        for language,(source,marker) in code_cases.items():
            _,created_job,_=req(base+'/api/code/jobs',method='POST',body={'language':language,'code':source,'timeout_seconds':4},expect=202);job_id=created_job['job']['id'];assert len(job_id)==32
            for _ in range(160):
                _,job_payload,_=req(base+'/api/code/jobs/'+job_id,expect=200);code_job=job_payload['job']
                if code_job['status'] in ('COMPLETED','FAILED','CANCELLED'):break
                time.sleep(.05)
            assert code_job['status']=='COMPLETED',code_job;assert marker in code_job['result']['stdout'] and code_job['result']['exit_code']==0
            if language=='java':assert code_job['compile']['exit_code']==0
        # CODE-004 validation and CODE-005 non-zero exit are explicit, never fake success.
        req(base+'/api/code/jobs',method='POST',body={'language':'ruby','code':'puts 1'},expect=400);req(base+'/api/code/jobs',method='POST',body={'language':'python','code':' '},expect=400)
        _,failed_job,_=req(base+'/api/code/jobs',method='POST',body={'language':'python','code':'raise SystemExit(7)','timeout_seconds':3},expect=202);failed_id=failed_job['job']['id']
        for _ in range(120):
            _,failed_payload,_=req(base+'/api/code/jobs/'+failed_id,expect=200);failed=failed_payload['job']
            if failed['status'] in ('COMPLETED','FAILED','CANCELLED'):break
            time.sleep(.05)
        assert failed['status']=='FAILED' and failed['result']['exit_code']==7
        # CODE-006 user ownership: another account must not read a foreign code job (checked again below in accounts mode).

        # Structured preset reaches provider and is independent from effort mode.
        _,answer,_=req(base+'/api/chat',method='POST',body={'mode':'auto','preset':'analyze','messages':[{'role':'user','content':'Сравни A и B'}]},expect=200);assert answer['preset']=='analyze'
        _,last,_=req(f'http://127.0.0.1:{fake_port}/test/last',expect=200);system_text=' '.join(m.get('content','') for m in last['messages'] if m.get('role')=='system');assert 'Проанализировать' in system_text
        _,rus,_=req(base+'/api/chat',method='POST',body={'mode':'auto','preset':'explain','messages':[{'role':'user','content':'ок'}]},expect=200);assert any(('а'<=ch.lower()<='я') or ch.lower()=='ё' for ch in rus['message']['content'])
        _,last,_=req(f'http://127.0.0.1:{fake_port}/test/last',expect=200);system_text=' '.join(m.get('content','') for m in last['messages'] if m.get('role')=='system');assert 'Объяснить' in system_text and 'ВАЖНО:' in system_text

        # Route through external provider; USER still receives no provider/model identifiers.
        req(base+'/api/admin/routing',method='POST',body={'routing':{'smart':{'provider_id':ext_id,'model_id':'qwen3:8b'}}},token=token,expect=200)
        _,chat,_=req(base+'/api/chat',method='POST',body={'mode':'smart','preset':'none','messages':[{'role':'user','content':'test'}]},expect=200);assert chat['message']['content']=='PAR_OPENAI_COMPAT_OK';out=json.dumps(chat).lower();assert ext_id not in out and 'qwen' not in out
        _,last,_=req(f'http://127.0.0.1:{fake_port}/test/last',expect=200);assert last['model']=='qwen3:8b'

        # Concurrent local chats after restoring route.
        req(base+'/api/admin/routing',method='POST',body={'routing':{'auto':{'provider_id':'local-ollama','model_id':'qwen3:0.6b'}}},token=token,expect=200)
        def one(i):
            _,x,_=req(base+'/api/chat',method='POST',body={'mode':'auto','preset':'none','messages':[{'role':'user','content':f'parallel-{i}'}]},expect=200);return x['message']['content']
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex: assert list(ex.map(one,range(12)))==['PAR_TEST_OK']*12

        # Managed pull is provider-specific and refreshes discovery.
        _,job,_=req(base+'/api/admin/models/pull',method='POST',body={'provider_id':'local-ollama','model':'testmodel:1b'},token=token,expect=202)
        for _ in range(50):
            _,st,_=req(base+'/api/admin/jobs/'+job['job_id'],token=token,expect=200)
            if st['status'] in ('completed','failed'):break
            time.sleep(.1)
        assert st['status']=='completed',st
        _,inv,_=req(base+'/api/admin/inventory',token=token,expect=200);assert any(m['provider_id']=='local-ollama' and m['model_id']=='testmodel:1b' for m in inv['models'])
        req(base+'/api/admin/routing',method='POST',body={'routing':{'fast':{'provider_id':'local-ollama','model_id':'testmodel:1b'}}},token=token,expect=200)

        # Provider+model routing persists after Core restart; secret is still redacted.
        core.terminate();core.wait(timeout=5);core=start_core(env);wait(base+'/api/health')
        _,admin,_=req(base+'/api/admin/status',token=token,expect=200);assert admin['routing']['smart']['provider_id']==ext_id and admin['routing']['fast']['model_id']=='testmodel:1b';assert secret not in json.dumps(admin)
        _,persisted_file,_=req(base+f"/api/files/{uploaded['artifact_id']}",expect=200);assert 'Загруженный текст' in persisted_file['artifact']['text']
        _,persisted_task,_=req(base+'/api/tasks/'+task_id,expect=200);assert persisted_task['task']['status']=='COMPLETED' and len(persisted_task['task']['result']['artifacts'])==3

        # Accounts mode: real registration/login/session flow.
        core.terminate();core.wait(timeout=5)
        accounts_port=free_port();accounts_env=base_env(tmp,fake_port,web_port,accounts_port,token,code_socket,'accounts.db','accounts');core=start_core(accounts_env);accounts=f'http://127.0.0.1:{accounts_port}';wait(accounts+'/api/health')
        req(accounts+'/api/auth/me',expect=401);req(accounts+'/api/chat',method='POST',body={'mode':'auto','messages':[{'role':'user','content':'test'}]},expect=401)
        _,registered,headers=req(accounts+'/api/auth/register',method='POST',body={'email':'user@example.test','display_name':'Тестовый пользователь','password':'strong-pass-123'},expect=201);cookie=cookie_from(headers);csrf=registered['csrf_token'];assert cookie.startswith('pa_session=')
        _,me,_=req(accounts+'/api/auth/me',headers={'Cookie':cookie},expect=200);assert me['user']['email']=='user@example.test';assert me['csrf_token']==csrf
        req(accounts+'/api/chat',method='POST',body={'mode':'auto','messages':[{'role':'user','content':'csrf-test'}]},headers={'Cookie':cookie},expect=403)
        _,chat,_=req(accounts+'/api/chat',method='POST',body={'mode':'auto','preset':'write','messages':[{'role':'user','content':'test'}]},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);assert chat['preset']=='write'
        req(accounts+'/api/auth/logout',method='POST',body={},headers={'Cookie':cookie,'X-CSRF-Token':csrf},expect=200);req(accounts+'/api/auth/me',headers={'Cookie':cookie},expect=401)
        _,login,headers=req(accounts+'/api/auth/login',method='POST',body={'email':'user@example.test','password':'strong-pass-123'},expect=200);cookie2=cookie_from(headers);csrf2=login['csrf_token'];assert cookie2.startswith('pa_session=')
        req(accounts+'/api/auth/login',method='POST',body={'email':'user@example.test','password':'wrong-password'},expect=401)
        # FILE-014 tenant/user boundary: a second account cannot read another user's artifact.
        _,acc_file,_=req(accounts+'/api/files/create',method='POST',body={'format':'txt','name':'private.txt','content':'private-user-one'},headers={'Cookie':cookie2,'X-CSRF-Token':csrf2},expect=201)
        _,other_registered,headers2=req(accounts+'/api/auth/register',method='POST',body={'email':'other@example.test','display_name':'Другой пользователь','password':'strong-pass-456'},expect=201);cookie_other=cookie_from(headers2);csrf_other=other_registered['csrf_token']
        req(accounts+f"/api/files/{acc_file['artifact']['artifact_id']}",headers={'Cookie':cookie_other},expect=404)
        req(accounts+f"/api/files/{acc_file['artifact']['artifact_id']}/download",headers={'Cookie':cookie_other},expect=404)
        _,account_code,_=req(accounts+'/api/code/jobs',method='POST',body={'language':'python','code':'print(123)','timeout_seconds':3},headers={'Cookie':cookie2,'X-CSRF-Token':csrf2},expect=202);req(accounts+'/api/code/jobs/'+account_code['job']['id'],headers={'Cookie':cookie_other},expect=404)
        _,account_task,_=req(accounts+'/api/tasks',method='POST',body={'type':'research_report','question':'Изолированный task','formats':['md']},headers={'Cookie':cookie2,'X-CSRF-Token':csrf2},expect=202);req(accounts+'/api/tasks/'+account_task['task']['id'],headers={'Cookie':cookie_other},expect=404)

        print('PAR_V070_API_ACCEPTANCE PASS: public-boundary presets providers auth web-research tasks files code-execution validation isolation routing persistence concurrency')
        return 0
    finally:
        for p in (core,fake,fake_web,code_worker):
            try:
                if p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        p.kill();p.wait(timeout=3)
            except Exception:
                try:
                    if p.poll() is None:
                        p.kill()
                    p.wait(timeout=3)
                except Exception:
                    pass
        shutil.rmtree(tmp,ignore_errors=True)

if __name__=='__main__':raise SystemExit(main())
