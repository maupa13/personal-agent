from __future__ import annotations
import os, pathlib, signal, subprocess, sys, time

ROOT=pathlib.Path(__file__).resolve().parents[1]
TARGET=ROOT/'tests'/'browser_journeys.py'
SENTINEL='PAR_V080_BROWSER_ACCEPTANCE PASS:'
TIMEOUT=180

def main()->int:
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PA_BROWSER_RUNNER_CHILD']='1'
    proc=subprocess.Popen([sys.executable,'-u',str(TARGET)],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
    assert proc.stdout is not None
    deadline=time.monotonic()+TIMEOUT
    passed=False
    try:
        while time.monotonic()<deadline:
            line=proc.stdout.readline()
            if line:
                print(line,end='',flush=True)
                if SENTINEL in line:
                    passed=True
                    break
                continue
            if proc.poll() is not None:
                break
        if passed:
            # All assertions, browser.close() and sync_playwright cleanup happen before the sentinel.
            # Terminate the test-only process group so a lingering Playwright/Node transport cannot
            # keep release-runner pipes open. This is harness cleanup, not a product retry.
            # The PASS sentinel is emitted only after browser assertions and browser.close().
            # Kill the isolated test process group immediately so any Node/Chromium transport
            # inherited pipes cannot outlive the deterministic test process.
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: return 124
            return 0
        rc=proc.poll()
        if rc is None:
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait(timeout=5)
            print('[FAIL] browser journey exceeded hard timeout before PASS sentinel',flush=True)
            return 124
        return int(rc)
    finally:
        if proc.poll() is None:
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass

if __name__=='__main__':
    raise SystemExit(main())
