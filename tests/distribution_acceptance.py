from __future__ import annotations
import json, pathlib, re, sys
root=pathlib.Path(__file__).resolve().parents[1]
errors=[]
required=[
    'RUN-FIRST.cmd','INSTALL-OR-UPDATE.cmd','INSTALL-OR-UPDATE.ps1','VERIFY-PACKAGE.ps1',
    'START.cmd','REPAIR.cmd','FULL-ACCEPTANCE.cmd','RELEASE-ACCEPTANCE.cmd','README-FIRST.md'
]
for name in required:
    if not (root/name).is_file(): errors.append(f'missing top-level distribution entrypoint: {name}')
installer=(root/'INSTALL-OR-UPDATE.ps1').read_text(encoding='ascii')
for token in (
    "[string]$TargetRoot = 'C:\\AI\\RusPersonalAgent'",
    "$AppRoot=Join-Path $TargetRoot 'app'",
    "$ConfigRoot=Join-Path $TargetRoot 'config'",
    "$LogsRoot=Join-Path $TargetRoot 'logs'",
    "$BackupsRoot=Join-Path $TargetRoot 'backups'",
    "$WorkspaceRoot=Join-Path $TargetRoot 'workspace'",
    "$ArtifactsRoot=Join-Path $TargetRoot 'artifacts'",
    "Move-Item -LiteralPath $stage -Destination $AppRoot",
    "Previous app saved to $backup",
    "VERIFY-PACKAGE.ps1",
    "REPAIR.cmd",
):
    if token not in installer: errors.append(f'installer contract missing: {token}')
low=installer.lower()
for forbidden in ('docker compose down -v','docker volume prune','docker system prune','remove-item -literalpath $targetroot -recurse'):
    if forbidden in low: errors.append(f'destructive installer pattern found: {forbidden}')
# Protect Windows PowerShell 5.1 from interpolation like "$Name:" in shipped scripts.
for p in root.rglob('*.ps1'):
    txt=p.read_text(encoding='ascii')
    for m in re.finditer(r'(?<!\$)\$[A-Za-z_][A-Za-z0-9_]*:',txt):
        errors.append(f'PowerShell 5.1 unsafe variable-colon interpolation: {p.relative_to(root)}:{m.start()}:{m.group(0)}')
for p in root.glob('*.cmd'):
    txt=p.read_text(encoding='ascii').lower()
    if p.name in {'RUN-FIRST.cmd','INSTALL-OR-UPDATE.cmd','START.cmd','REPAIR.cmd','VERIFY.cmd','STATUS.cmd','FULL-ACCEPTANCE.cmd','RELEASE-ACCEPTANCE.cmd'} and '%~dp0' not in txt:
        errors.append(f'entrypoint is CWD-dependent: {p.name}')
runfirst=(root/'RUN-FIRST.cmd').read_text(encoding='ascii')
if 'INSTALL-OR-UPDATE.cmd' not in runfirst: errors.append('RUN-FIRST does not route to canonical installer')
verify=(root/'VERIFY-PACKAGE.ps1').read_text(encoding='ascii')
if "INSTALL-OR-UPDATE.ps1" not in verify or '-Contract' not in verify:
    errors.append('VERIFY-PACKAGE does not execute installer contract')
manifest=json.loads((root/'product-manifest.json').read_text(encoding='utf-8'))
if manifest.get('version')!='0.7.2': errors.append('manifest version mismatch')
if errors:
    print('\n'.join('[FAIL] '+e for e in errors));sys.exit(1)
print('PAR_DISTRIBUTION_ACCEPTANCE PASS: canonical-root run-first staged-update config-preservation stable-launchers powershell51-safety no-destructive-install')
