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
TMP_ROOT = ROOT / 'release-evidence' / '_tmp' / 'code-worker'
TMP_ROOT.mkdir(parents=True, exist_ok=True)
WORKER = ROOT / 'services' / 'code-worker' / 'app' / 'code_worker.py'


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class UnixConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str):
        super().__init__('localhost', timeout=10)
        self.socket_path = socket_path
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


class TCPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int):
        super().__init__(host, port=port, timeout=10)


def request(socket_path: str, method: str, path: str, body=None):
    raw = None if body is None else json.dumps(body).encode()
    if socket_path.startswith('tcp://'):
        parsed = socket_path.removeprefix('tcp://')
        host, _, port_text = parsed.rpartition(':')
        conn = TCPConnection(host or '127.0.0.1', int(port_text))
    else:
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
    tmp=TMP_ROOT / f"par-code-worker-{os.getpid()}-{int(time.time()*1000)}";tmp.mkdir(parents=True, exist_ok=True);bin_dir=tmp/'bin';bin_dir.mkdir();pwsh_cmd=bin_dir/'pwsh.cmd';pwsh_sh=bin_dir/'pwsh';pwsh_stub=bin_dir/'pwsh_stub.py'
    pwsh_stub.write_text('import base64,pathlib,re,sys,time\nif "-Version" in sys.argv: print("PowerShell 7.6.0-test"); raise SystemExit(0)\nif "-EncodedCommand" in sys.argv:\n s=base64.b64decode(sys.argv[sys.argv.index("-EncodedCommand")+1]).decode("utf-16le"); m=re.search(r"Write-Output\\s+[\\\"\\x27]([^\\\"\\x27]+)",s,re.I); print(m.group(1) if m else "PS_OK"); raise SystemExit(0)\nif "-File" in sys.argv:\n p=pathlib.Path(sys.argv[sys.argv.index("-File")+1]); s=p.read_text(encoding="utf-8"); m=re.search(r"Write-Output\\s+[\\\"\\x27]([^\\\"\\x27]+)",s,re.I); print(m.group(1) if m else "PS_OK"); time.sleep(10 if "PAR_SLEEP" in s else 0); raise SystemExit(0)\n',encoding='utf-8');pwsh_cmd.write_text(f'@echo off\r\n\"{sys.executable}\" \"%~dp0pwsh_stub.py\" %*\r\n',encoding='utf-8');pwsh_sh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$(dirname "$0")/pwsh_stub.py" "$@"\n',encoding='utf-8');pwsh_sh.chmod(0o755)
    socket_path=f'tcp://127.0.0.1:{free_port()}';env=os.environ.copy();env.update({'PYTHONDONTWRITEBYTECODE':'1','PATH':str(bin_dir)+os.pathsep+env.get('PATH',''),'PA_CODE_SOCKET':socket_path,'PA_CODE_WORK_ROOT':str(tmp/'work'),'PA_CODE_RUNNER_UID':str(getattr(os, "getuid", lambda: 0)()),'PA_CODE_RUNNER_GID':str(getattr(os, "getgid", lambda: 0)()),'PA_CODE_SOCKET_GID':str(getattr(os, "getgid", lambda: 0)()),'PA_CODE_MAX_TIMEOUT_SECONDS':'5','PA_CODE_MAX_OUTPUT_BYTES':'2048','PA_CODE_MAX_FILE_BYTES':str(1024*1024),'PA_ADMIN_TOKEN':'MUST_NOT_REACH_CHILD'})
    worker_log=(tmp/'worker.log').open('w',encoding='utf-8',newline='')
    worker=subprocess.Popen([sys.executable,str(WORKER)],env=env,stdout=worker_log,stderr=subprocess.STDOUT,text=True)
    try:
        host,_,port_text=socket_path.removeprefix('tcp://').rpartition(':')
        end=time.time()+10
        while time.time()<end:
            try:
                with socket.create_connection((host or '127.0.0.1', int(port_text)), timeout=1):
                    break
            except OSError:
                time.sleep(.05)
        end = time.time() + 10
        last = None
        while time.time() < end:
            try:
                status, health = request(socket_path, 'GET', '/health')
                if status == 200 and health.get('ready') is True:
                    break
                last = (status, health)
            except Exception as exc:
                last = repr(exc)
            time.sleep(.05)
        else:
            raise AssertionError(last)
        status,health=request(str(socket_path),'GET','/health');assert status==200 and health['network']=='disabled'
        # CODE-W01 Python real execution and environment secret isolation.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'python','code':'import os\nprint("PY_OK")\nprint(os.environ.get("PA_ADMIN_TOKEN","NO_SECRET"))','timeout_seconds':5});job=await_job(str(socket_path),created['id']);assert job['status']=='COMPLETED' and 'PY_OK' in job.get('result',{}).get('stdout','') and 'NO_SECRET' in job.get('result',{}).get('stdout','') and 'MUST_NOT_REACH_CHILD' not in job.get('result',{}).get('stdout',''), job
        # CODE-W02 Java 21 compile + execute.
        _,created=request(str(socket_path),'POST','/jobs',{'language':'java','code':'public class Main { public static void main(String[] a){ System.out.println("JAVA_OK"); }}','timeout_seconds':3});job=await_job(str(socket_path),created['id']);assert job['status']=='COMPLETED' and job['compile']['exit_code']==0 and 'JAVA_OK' in job['result']['stdout']
        # CODE-W03 PowerShell command contract (actual pwsh runtime is verified by Docker/reference-host gate).
        _,created=request(str(socket_path),'POST','/jobs',{'language':'powershell','code':'Write-Output "PS_OK"','timeout_seconds':5});job=await_job(str(socket_path),created['id']);assert job['status']=='COMPLETED' and 'PS_OK' in job['result']['stdout'], job
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
