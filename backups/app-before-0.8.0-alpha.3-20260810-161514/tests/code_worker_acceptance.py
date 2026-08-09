from __future__ import annotations

import http.client
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKER = ROOT / 'services' / 'code-worker' / 'app' / 'code_worker.py'


class UnixConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str):
        super().__init__('localhost', timeout=10)
        self.socket_path = socket_path
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


def request(socket_path: str, method: str, path: str, body=None):
    raw = None if body is None else json.dumps(body).encode()
    conn = UnixConnection(socket_path)
    conn.request(method, path, body=raw, headers={'Content-Type':'application/json'} if raw else {})
    response = conn.getresponse(); data = response.read(); status = response.status; conn.close()
    return status, json.loads(data or b'{}')


def await_job(socket_path: str, job_id: str, seconds=12):
    end=time.time()+seconds; last=None
    while time.time()<end:
        _,payload=request(socket_path,'GET','/jobs/'+job_id);last=payload
        if payload.get('status') in {'COMPLETED','FAILED','CANCELLED'}: return payload
        time.sleep(.05)
    raise AssertionError(last)


def main():
    worker_source=WORKER.read_text(encoding='utf-8')
    # Regression for Windows/Docker Desktop EPERM: child HOME/TMP/source files must
    # not require UID ownership transfer to RUNNER_UID. Group access is sufficient.
    assert 'os.chown(p, RUNNER_UID' not in worker_source and 'os.chown(source, RUNNER_UID' not in worker_source
    assert 'os.chmod(work_dir, 0o2770)' in worker_source
    tmp=pathlib.Path(tempfile.mkdtemp(prefix='par-code-worker-'));tmp.chmod(0o755);bin_dir=tmp/'bin';bin_dir.mkdir();pwsh=bin_dir/'pwsh'
    pwsh.write_text('#!/usr/bin/env python3\nimport pathlib,re,sys,time\nif "-Version" in sys.argv: print("PowerShell 7.6.0-test"); raise SystemExit(0)\nif "-File" in sys.argv:\n p=pathlib.Path(sys.argv[sys.argv.index("-File")+1]); s=p.read_text(); m=re.search(r"Write-Output\\s+[\\\"\\x27]([^\\\"\\x27]+)",s,re.I); print(m.group(1) if m else "PS_OK"); time.sleep(10 if "PAR_SLEEP" in s else 0); raise SystemExit(0)\n',encoding='utf-8');pwsh.chmod(0o755)
    socket_path=tmp/'worker.sock';env=os.environ.copy();env.update({'PYTHONDONTWRITEBYTECODE':'1','PATH':str(bin_dir)+os.pathsep+env.get('PATH',''),'PA_CODE_SOCKET':str(socket_path),'PA_CODE_WORK_ROOT':str(tmp/'work'),'PA_CODE_RUNNER_UID':str(os.getuid()),'PA_CODE_RUNNER_GID':str(os.getgid()),'PA_CODE_SOCKET_GID':str(os.getgid()),'PA_CODE_MAX_TIMEOUT_SECONDS':'3','PA_CODE_MAX_OUTPUT_BYTES':'2048','PA_CODE_MAX_FILE_BYTES':str(1024*1024),'PA_ADMIN_TOKEN':'MUST_NOT_REACH_CHILD'})
    worker_log=(tmp/'worker.log').open('w',encoding='utf-8',newline='')
    worker=subprocess.Popen([sys.executable,str(WORKER)],env=env,stdout=worker_log,stderr=subprocess.STDOUT,text=True)
    try:
        for _ in range(100):
            if socket_path.exists():break
            time.sleep(.02)
        status,health=request(str(socket_path),'GET','/health');assert status==200 and health['network']=='disabled'
        # CODE-W01 Python real execution and environment secret isolation.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'python','code':'import os\nprint("PY_OK")\nprint(os.environ.get("PA_ADMIN_TOKEN","NO_SECRET"))','timeout_seconds':2});job=await_job(str(socket_path),created['id']);assert job['status']=='COMPLETED' and 'PY_OK' in job.get('result',{}).get('stdout','') and 'NO_SECRET' in job.get('result',{}).get('stdout','') and 'MUST_NOT_REACH_CHILD' not in job.get('result',{}).get('stdout',''), job
        # CODE-W02 Java 21 compile + execute.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'java','code':'public class Main { public static void main(String[] a){ System.out.println("JAVA_OK"); }}','timeout_seconds':3});job=await_job(str(socket_path),created['id']);assert job['status']=='COMPLETED' and job['compile']['exit_code']==0 and 'JAVA_OK' in job['result']['stdout']
        # CODE-W03 PowerShell command contract (actual pwsh runtime is verified by Docker/reference-host gate).
        _,created=request(str(socket_path),'POST','/jobs',{'language':'powershell','code':'Write-Output "PS_OK"','timeout_seconds':2});job=await_job(str(socket_path),created['id']);assert job['status']=='COMPLETED' and 'PS_OK' in job['result']['stdout']
        # CODE-W04 compile failure is reported as FAIL, never success.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'java','code':'public class Main { broken }','timeout_seconds':2});job=await_job(str(socket_path),created['id']);assert job['status']=='FAILED' and job['error']=='compile failed' and job['compile']['exit_code']!=0
        # CODE-W05 hard timeout kills process group.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'python','code':'import time\ntime.sleep(5)','timeout_seconds':1});job=await_job(str(socket_path),created['id'],5);assert job['status']=='FAILED' and job['result']['timed_out'] is True
        # CODE-W06 explicit cancel terminates a long-running process.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'python','code':'import time\ntime.sleep(20)','timeout_seconds':3});jid=created['id'];time.sleep(.15);_,cancelled=request(str(socket_path),'POST','/jobs/'+jid+'/cancel',{});assert cancelled['status']=='CANCELLED'
        # CODE-W07 output returned to client is bounded.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'python','code':'print("X"*20000)','timeout_seconds':2});job=await_job(str(socket_path),created['id']);assert len(job['result']['stdout'].encode())<=2048 and job['result']['output_truncated'] is True
        # CODE-W08 invalid language/source validation.
        assert request(str(socket_path),'POST','/jobs',{'language':'ruby','code':'puts 1'})[0]==400
        assert request(str(socket_path),'POST','/jobs',{'language':'python','code':' '})[0]==400
        print('PAR_CODE_WORKER_ACCEPTANCE PASS: python java powershell-contract compile-failure timeout cancel output-limit secret-isolation validation docker-desktop-permission-regression')
        return 0
    finally:
        worker.terminate()
        try:worker.wait(timeout=3)
        except subprocess.TimeoutExpired:
            worker.kill();worker.wait(timeout=3)
        worker_log.close()
        shutil.rmtree(tmp,ignore_errors=True)

if __name__=='__main__':raise SystemExit(main())
