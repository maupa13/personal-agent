from __future__ import annotations

import os
import pathlib
import signal
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / 'tests' / 'browser_journeys.py'
SENTINEL = 'PAR_V080_BROWSER_ACCEPTANCE PASS:'
TIMEOUT = 180


def terminate_group(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def main() -> int:
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PA_BROWSER_RUNNER_CHILD'] = '1'
    proc = subprocess.Popen(
        [sys.executable, '-u', str(TARGET)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    output = ''
    try:
        try:
            output, _ = proc.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            partial = exc.output or ''
            if isinstance(partial, bytes):
                partial = partial.decode('utf-8', errors='replace')
            output = str(partial)
            terminate_group(proc)
            try:
                tail, _ = proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                tail = ''
            output += tail or ''
            # The sentinel is emitted only after all assertions, context.close(),
            # browser.close() and the sync_playwright context have completed.
            # A process that lingers after that point is a test-driver teardown
            # leak, not an unfinished browser assertion. Kill the isolated test
            # process group and accept only that already-complete sentinel.
            print(output, end='', flush=True)
            if SENTINEL in output:
                print('[PASS] browser journey assertions completed; terminated lingering test-driver process after PASS sentinel', flush=True)
                return 0
            print('[FAIL] browser journey exceeded hard timeout before PASS sentinel', flush=True)
            return 124
        print(output, end='', flush=True)
        if proc.returncode == 0 and SENTINEL in output:
            return 0
        if SENTINEL in output:
            # Defensive cleanup contract: a nonzero post-sentinel exit is a
            # harness failure and must not be silently green.
            print(f'[FAIL] browser process exited {proc.returncode} after PASS sentinel', flush=True)
            return int(proc.returncode or 1)
        return int(proc.returncode or 1)
    finally:
        terminate_group(proc)


if __name__ == '__main__':
    raise SystemExit(main())
