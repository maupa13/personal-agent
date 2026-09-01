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

if "'BACKUP.cmd'='BACKUP.cmd'" not in installer or "'UPDATE.cmd'='UPDATE.cmd'" not in installer:
    errors.append('stable root backup/update launchers missing')
for token in ("@('VERIFY-PACKAGE.ps1','VERIFY-RELEASE.ps1')", "app\\$verifyName"):
    if token not in installer: errors.append('installed-root verifier proxy contract missing: '+token)
low=installer.lower()
for forbidden in ('docker compose down -v','docker volume prune','docker system prune','remove-item -literalpath $targetroot -recurse'):
    if forbidden in low: errors.append(f'destructive installer pattern found: {forbidden}')
# Protect Windows PowerShell 5.1 from interpolation like "$Name:" in signed scripts only.
# Unsigned legacy neighbours are intentionally outside package scope.
signed_paths=[]
for line in (root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    parts=line.split('  ',1)
    if len(parts)==2: signed_paths.append(parts[1])
for rel in signed_paths:
    if not rel.lower().endswith('.ps1'): continue
    p=root/rel
    txt=p.read_text(encoding='ascii')
    # PowerShell scope qualifiers such as $script:Var / $env:Var are legal. The historical
    # regression targeted accidental `$name:` interpolation inside double-quoted strings,
    # which PowerShell 5.1 can parse as a scoped-variable expression. Inspect string literals
    # and exclude the language's explicit scope prefixes instead of rejecting valid script scope.
    scope_prefixes={'script','global','local','private','env','using'}
    for string_match in re.finditer(r'"(?:`.|[^"`])*"',txt):
        literal=string_match.group(0)
        for m in re.finditer(r'(?<!\$)\$([A-Za-z_][A-Za-z0-9_]*):',literal):
            if m.group(1).lower() in scope_prefixes:
                continue
            errors.append(f'PowerShell 5.1 unsafe variable-colon interpolation: {p.relative_to(root)}:{string_match.start()+m.start()}:{m.group(0)}')
for p in root.glob('*.cmd'):
    txt=p.read_text(encoding='ascii').lower()
    if p.name in {'RUN-FIRST.cmd','INSTALL-OR-UPDATE.cmd','START.cmd','REPAIR.cmd','VERIFY.cmd','STATUS.cmd','FULL-ACCEPTANCE.cmd','RELEASE-ACCEPTANCE.cmd'} and '%~dp0' not in txt:
        errors.append(f'entrypoint is CWD-dependent: {p.name}')
runfirst=(root/'RUN-FIRST.cmd').read_text(encoding='ascii')
if 'INSTALL-OR-UPDATE.cmd' not in runfirst: errors.append('RUN-FIRST does not route to canonical installer')
verify=(root/'VERIFY-PACKAGE.ps1').read_text(encoding='ascii')
if "INSTALL-OR-UPDATE.ps1" not in verify or '-Contract' not in verify:
    errors.append('VERIFY-PACKAGE does not execute installer contract')

# Canonical-root isolation: only signed manifest paths are verification/staging scope.
verify=(root/'VERIFY-PACKAGE.ps1').read_text(encoding='ascii')
if "$manifestEntries" not in verify or "Where-Object { $_.Relative -like '*.ps1' }" not in verify:
    errors.append('VERIFY-PACKAGE must parse signed manifest PowerShell files only')
if "Get-ChildItem -LiteralPath $Root -Recurse -File -Filter '*.ps1'" in verify:
    errors.append('VERIFY-PACKAGE must not recursively parse unsigned neighboring PowerShell files')
if "Unsafe manifest path" not in verify or "Duplicate manifest path" not in verify:
    errors.append('VERIFY-PACKAGE manifest path hardening missing')
if "foreach($line in Get-Content -LiteralPath $manifestPath)" not in installer or "Get-ChildItem -LiteralPath $PackageRoot -Force" in installer:
    errors.append('installer must stage signed manifest payload only')

# Simulate the exact user layout: a valid package extracted into a root that may also contain
# unrelated unsigned neighbors. Those files must stay outside verification scope.
manifest_paths=[]
for line in (root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    parts=line.split('  ',1)
    if len(parts)==2: manifest_paths.append(parts[1].replace('\\','/'))
for unexpected in (
    'personal-agent-rus-v0.7.0-orchestrator-vps-deployment-release/scripts/pa.ps1',
    'app/scripts/pa.ps1',
):
    if unexpected in manifest_paths: errors.append('legacy mirror unexpectedly entered signed payload: '+unexpected)
if 'VERIFY-PACKAGE.ps1' not in manifest_paths or 'INSTALL-OR-UPDATE.ps1' not in manifest_paths:
    errors.append('canonical installer/verifier must themselves be signed payload entries')
runtime=(root/'scripts'/'pa.ps1').read_text(encoding='ascii')
if "PA_CODE_WORKER_IMAGE']='personal-agent-code-worker:1.0.0'" not in runtime:
    errors.append('existing code-worker image tag is not migrated during update')
if "function Start-CodeWorkerOptional" not in runtime:
    errors.append('local installer/runtime lacks optional Code startup contract')
for token,label in (("personal-agent-core:1.0.0",'Core'),("personal-agent-browser:1.0.0",'Browser'),("personal-agent-code-worker:1.0.0",'Code worker')):
    if token not in runtime: errors.append(f'alpha4 current {label} image tag missing from lifecycle migration/defaults')

# Windows PowerShell 5.1: Docker Compose emits normal build progress on stderr.
# Optional Code startup must not let native stderr become a terminating RemoteException.
for token in ("$previousErrorActionPreference=$ErrorActionPreference", "$ErrorActionPreference='Continue'", "$nativeExitCode=$LASTEXITCODE"):
    if token not in runtime: errors.append('PowerShell 5.1 native stderr fail-soft guard missing: '+token)
manifest=json.loads((root/'product-manifest.json').read_text(encoding='utf-8'))
if manifest.get('version')!='1.0.0': errors.append('manifest version mismatch')
if errors:
    print('\n'.join('[FAIL] '+e for e in errors));sys.exit(1)
print('PAR_DISTRIBUTION_ACCEPTANCE PASS: canonical-root run-first staged-update config-preservation stable-launchers powershell51-safety no-destructive-install')
