from __future__ import annotations
import io, json, pathlib, sys, tarfile, tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services'/'core'/'app'))
from orchestrator_service import TaskStore
from deployment_service import server_bundle,add_core_to_bundle,preflight,deploy,rollback,host_key_sha256,DeploymentError,resolve_remote_root,public_hot_verify,bootstrap_runtime

class FakeSession:
    def __init__(self,memory=2048):self.commands=[];self.uploads={};self.memory=memory
    def run(self,command,timeout=120):
        self.commands.append(command)
        if "uname -srm" in command:return 0,"Linux 6.8 x86_64\n",""
        if "docker --version" in command:return 0,"Docker version 29.6.2\n",""
        if "docker compose version" in command:return 0,"Docker Compose version v5.3.1\n",""
        if "MemTotal" in command:return 0,str(self.memory)+"\n",""
        if "df -Pk" in command:return 0,str(20*1024*1024)+"\n",""
        if "id -un" in command:return 0,"deploy\n",""
        if "$(id -u)" in command:return 0,"1000\n/home/deploy\n",""
        return 0,"ok\n",""
    def put_bytes(self,path,data):self.uploads[path]=data
    def close(self):pass

def main():
    # TASK-STORE: durable schema, event ordering, cancellation and recovery discovery.
    with tempfile.TemporaryDirectory(prefix='par-task-store-') as tmp:
        store=TaskStore(pathlib.Path(tmp)/'state.db');store.init_schema()
        task=store.create('u1','research_report','Test',{'question':'q','formats':['md']},[{'capability':'web.research','title':'web'},{'capability':'artifact.verify','title':'verify'}])
        assert task['status']=='CREATED' and len(task['steps'])==2
        store.set_task(task['id'],status='RUNNING',phase='web',progress=20,started=True);store.set_step(task['id'],0,status='STARTED');store.set_step(task['id'],0,status='VERIFIED',output={'sources':2})
        store.event(task['id'],'u1','task.progress','RUNNING','web',20,'Ищу')
        events=store.events('u1',task['id']);assert [e['id'] for e in events]==sorted(e['id'] for e in events) and len(events)>=2
        assert task['id'] in store.recoverable()
        assert store.request_cancel('u2',task['id']) is False
        assert store.request_cancel('u1',task['id']) is True and store.cancelled(task['id']) is True
        assert store.get('u2',task['id']) is None

    # DEPLOY bundle: server-lite never requires local Ollama/GPU/browser/code worker.
    bundle=server_bundle('0.7.0','server-lite','agent.example.test','ADMIN_TOKEN_TEST')
    full=add_core_to_bundle(bundle,ROOT/'services'/'core')
    with tarfile.open(fileobj=io.BytesIO(full),mode='r:gz') as tf:
        names=set(tf.getnames());assert {'compose.yaml','.env.server','Caddyfile','core/app/main.py','core/Dockerfile'}<=names
        compose=tf.extractfile('compose.yaml').read().decode();env=tf.extractfile('.env.server').read().decode();caddy=tf.extractfile('Caddyfile').read().decode()
        assert 'caddy:2.11.2' in compose and 'ollama:' not in compose and 'code-worker:' not in compose and 'browser:' not in compose
        assert 'PA_RUNTIME_PROFILE=server' in env and 'PA_AUTH_MODE=accounts' in env and 'PA_SECURE_COOKIES=1' in env and 'PA_OLLAMA_URL=' in env
        assert 'agent.example.test' in caddy and 'reverse_proxy core:8080' in caddy
        assert 'ADMIN_TOKEN_TEST' in env

    # Weak VPS profile selection and required Docker checks.
    session=FakeSession(memory=2048);pf=preflight(session);assert pf['ok'] is True and pf['recommended_profile']=='server-lite' and pf['memory_mb']==2048
    session2=FakeSession(memory=8192);assert preflight(session2)['recommended_profile']=='server-standard'
    assert resolve_remote_root(session)=='/home/deploy/.local/share/personal-agent'

    class RootBootstrapSession(FakeSession):
        def run(self,command,timeout=120):
            self.commands.append(command)
            if command=='id -u':return 0,'0\n',''
            if 'cat /etc/os-release' in command:return 0,'ID=ubuntu\nID_LIKE=debian\n',''
            return 0,'ok\n',''
    bootstrap_session=RootBootstrapSession();bootstrap=bootstrap_runtime(bootstrap_session);assert bootstrap['ok'] and bootstrap['docker'] and bootstrap['compose']
    bootstrap_commands='\n'.join(bootstrap_session.commands);assert 'apt-get install' in bootstrap_commands and 'curl' not in bootstrap_commands and 'get.docker.com' not in bootstrap_commands


    # Staged deploy/hot-verify/rollback contract with no destructive volume commands.
    result=deploy(session,full,'0.7.0');assert result['hot_verify']=='PASS' and len(session.uploads)==1
    joined='\n'.join(session.commands);assert 'ln -sfn' in joined and ' current' in joined and 'previous' in joined and 'docker compose' in joined and '/api/health' in joined
    for forbidden in ('down -v','volume prune','system prune'):assert forbidden not in joined.lower()
    rb=rollback(session);assert rb['status']=='ROLLED_BACK';joined='\n'.join(session.commands);assert 'readlink -f previous' in joined

    # Host-key fingerprint format is stable and explicit.
    fp=host_key_sha256(b'test-host-key');assert fp.startswith('SHA256:') and len(fp)>20

    class FakeResponse:
        status=200
        def __enter__(self):return self
        def __exit__(self,*_):return False
        def read(self):return json.dumps({'product':'Personal Agent Rus','version':'0.7.0'}).encode()
    verify=public_hot_verify('agent.example.test','0.7.0',timeout_seconds=5,opener=lambda *_a,**_k:FakeResponse())
    assert verify['ok'] and verify['https'] and verify['url']=='https://agent.example.test/api/system'


    # Optional remote provider bootstrap makes server-lite usable without re-entering the API key on the VPS.
    import importlib
    core_main=importlib.import_module('main')
    original=(core_main.get_provider,core_main.read_provider_secret,core_main.routing,core_main.public_admin_json)
    calls=[]
    try:
        core_main.get_provider=lambda _pid:{'id':'provider-remote','name':'Remote API','type':'openai_compatible','base_url':'https://api.example.test/v1','billing_class':'BYOK','cost_input_per_million_rub':0,'cost_output_per_million_rub':0}
        core_main.read_provider_secret=lambda _p:'TOP-SECRET'
        core_main.routing=lambda:{'auto':{'provider_id':'provider-remote','model_id':'model-a'},'fast':{'provider_id':'provider-remote','model_id':'model-a'},'smart':{'provider_id':'provider-remote','model_id':'model-a'}}
        def fake_admin(domain,token,path,method='GET',body=None,timeout=20):
            calls.append((domain,token,path,method,body))
            if path=='/api/admin/providers':return 201,{'ok':True}
            if path=='/api/admin/inventory':return 200,{'models':[{'provider_id':'provider-remote','model_id':'model-a'}]}
            if path=='/api/admin/routing':return 200,{'ok':True}
            return 404,{}
        core_main.public_admin_json=fake_admin
        seeded=core_main.seed_remote_provider_to_vps('agent.example.test','SERVER-ADMIN','provider-remote')
        assert seeded['ok'] and seeded['model_count']==1 and seeded['secret_transferred'] is True
        assert calls[0][4]['api_key']=='TOP-SECRET' and 'TOP-SECRET' not in json.dumps(seeded)
        assert calls[-1][2]=='/api/admin/routing'
    finally:
        core_main.get_provider,core_main.read_provider_secret,core_main.routing,core_main.public_admin_json=original

    # Credentials are intentionally absent from persisted target schema.
    main_src=(ROOT/'services'/'core'/'app'/'main.py').read_text(encoding='utf-8')
    schema=main_src[main_src.index('CREATE TABLE IF NOT EXISTS deployment_targets'):main_src.index(');',main_src.index('CREATE TABLE IF NOT EXISTS deployment_targets'))]
    for forbidden in ('password','private_key','passphrase','secret'):assert forbidden not in schema.lower()

    lan=(ROOT/'scripts'/'lan.ps1').read_text(encoding='utf-8')
    assert 'PA_BIND_IP' in lan and 'New-NetFirewallRule' in lan and '-Profile Private' in lan
    for forbidden in ('down -v','volume prune','system prune'):assert forbidden not in lan.lower()

    print('PAR_V070_ORCHESTRATOR_DEPLOYMENT_ACCEPTANCE PASS: task-store events cancel isolation recovery server-lite bundle preflight staged-deploy internal/public-hot-verify rollback host-key no-secret-persistence LAN-contract')
    return 0
if __name__=='__main__':raise SystemExit(main())
