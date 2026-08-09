from __future__ import annotations
import pathlib,re,sys
root=pathlib.Path(__file__).resolve().parents[1]
ps=(root/'scripts'/'pa.ps1').read_text(encoding='ascii')
errors=[]
if re.search(r'\$args\b',ps,re.I): errors.append('automatic $Args variable is forbidden')
for marker in [
 "Invoke-Compose -ComposeArgs @('config','--quiet')",
 "Invoke-Compose -ComposeArgs @('up','-d','ollama','searxng','browser')",
 "Invoke-Compose -ComposeArgs @('exec','-T','ollama','ollama','list')",
 "Invoke-Compose -ComposeArgs @('up','-d','--build','code-worker')",
 "Invoke-Compose -ComposeArgs @('up','-d','--build','--remove-orphans','core')",
 "Invoke-Compose -ComposeArgs @('stop')",
 "Invoke-Compose -ComposeArgs @('restart','ollama','searxng','browser','code-worker','core')",
]:
    if marker not in ps: errors.append('missing lifecycle command '+marker)
if "[ValidateSet('start','stop','restart','status','verify','webverify','codeverify','fullverify','releaseverify','logs','admin','backup','update','repair','contract')]" not in ps:
    errors.append('action contract incomplete')
entries={'START.cmd':'start','STOP.cmd':'stop','STATUS.cmd':'status','VERIFY.cmd':'verify','WEB-ACCEPTANCE.cmd':'webverify','CODE-ACCEPTANCE.cmd':'codeverify','ADMIN.cmd':'admin','RESTART.cmd':'restart','REPAIR.cmd':'repair','LOGS.cmd':'logs','FULL-ACCEPTANCE.cmd':'fullverify','RELEASE-ACCEPTANCE.cmd':'releaseverify'}
for fn,action in entries.items():
    p=root/fn
    if not p.exists(): errors.append(f'missing {fn}'); continue
    txt=p.read_text(encoding='ascii').lower()
    if f'-action {action}' not in txt: errors.append(f'{fn} does not use named -Action {action}')
    if 'exit /b %ec%' not in txt: errors.append(f'{fn} does not propagate exit code')
if 'function Wait-WebServices' not in ps or 'function Test-WebAcceptance' not in ps:
    errors.append('Windows lifecycle does not include Web service readiness/live acceptance')
if 'function Wait-CodeWorker' not in ps or 'function Test-CodeInternalSmoke' not in ps or 'function Test-CodeLiveAcceptance' not in ps:
    errors.append('Windows lifecycle does not include Code sandbox readiness/smoke/live acceptance')
if errors:
    print('\n'.join('[FAIL] '+e for e in errors));sys.exit(1)
print('[PASS] Windows launcher static contract')
