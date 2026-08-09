param(
  [string]$TargetRoot = 'C:\AI\RusPersonalAgent',
  [switch]$Contract,
  [switch]$NoStart
)
$ErrorActionPreference='Stop'
$PackageRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$Version='0.7.4-local.3'
$AppRoot=Join-Path $TargetRoot 'app'
$ConfigRoot=Join-Path $TargetRoot 'config'
$LogsRoot=Join-Path $TargetRoot 'logs'
$BackupsRoot=Join-Path $TargetRoot 'backups'
$PackagesRoot=Join-Path $TargetRoot 'packages'
$DiagnosticsRoot=Join-Path $TargetRoot 'diagnostics'
$TempRoot=Join-Path $TargetRoot 'temp'
$DataRoot=Join-Path $TargetRoot 'data'
$WorkspaceRoot=Join-Path $TargetRoot 'workspace'
$ArtifactsRoot=Join-Path $TargetRoot 'artifacts'

function Say([string]$Level,[string]$Message,[ConsoleColor]$Color=[ConsoleColor]::Gray){Write-Host "[$Level] $Message" -ForegroundColor $Color}
function Fail([string]$Message){Say 'FAIL' $Message Red;throw $Message}

if($Contract){
  Write-Output "[CONTRACT] target-root|$TargetRoot"
  Write-Output "[CONTRACT] app-root|$AppRoot"
  Write-Output "[CONTRACT] config-root|$ConfigRoot"
  Write-Output "[CONTRACT] logs-root|$LogsRoot"
  Write-Output "[CONTRACT] install-mode|staged-in-place"
  Write-Output "[CONTRACT] preserve|env+docker-named-volumes+workspace+artifacts"
  Write-Output "[CONTRACT] start-after-install|$(-not $NoStart)"
  exit 0
}

Say 'INFO' 'Personal Agent Rus canonical installer/update.' Cyan
Say 'INFO' "Package: $PackageRoot" DarkGray
Say 'INFO' "Target:  $TargetRoot" DarkGray

$verify=Join-Path $PackageRoot 'VERIFY-PACKAGE.ps1'
if(-not (Test-Path -LiteralPath $verify)){Fail 'VERIFY-PACKAGE.ps1 is missing from the release package.'}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $verify
if($LASTEXITCODE -ne 0){Fail 'Release package verification failed. Nothing was installed.'}

foreach($dir in @($TargetRoot,$ConfigRoot,$LogsRoot,$BackupsRoot,$PackagesRoot,$DiagnosticsRoot,$TempRoot,$DataRoot,$WorkspaceRoot,$ArtifactsRoot)){
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# Preserve the most authoritative existing environment settings.
$preservedEnv=$null
$canonicalEnv=Join-Path $ConfigRoot '.env'
if(Test-Path -LiteralPath $canonicalEnv){$preservedEnv=$canonicalEnv}
elseif(Test-Path -LiteralPath (Join-Path $AppRoot '.env')){$preservedEnv=Join-Path $AppRoot '.env'}
else{
  $legacy=@(Get-ChildItem -LiteralPath $TargetRoot -Directory -ErrorAction SilentlyContinue | Where-Object {$_.Name -like 'personal-agent-rus-v*'} | Sort-Object LastWriteTime -Descending)
  foreach($folder in $legacy){$candidate=Join-Path $folder.FullName '.env';if(Test-Path -LiteralPath $candidate){$preservedEnv=$candidate;break}}
}
if($preservedEnv){Say 'INFO' "Preserving configuration from $preservedEnv" DarkGray}

$stage=Join-Path $TempRoot ("app-$Version-"+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $stage | Out-Null
try{
  # Copy only the signed payload. The package may be extracted directly into the canonical
  # root, which can also contain legacy releases/evidence/.idea/user files. Those are never staged.
  $manifestPath=Join-Path $PackageRoot 'SHA256SUMS.txt'
  foreach($line in Get-Content -LiteralPath $manifestPath){
    if([string]::IsNullOrWhiteSpace($line)){continue}
    $parts=$line -split '  ',2
    if($parts.Count -ne 2){Fail "Invalid manifest line during staging: $line"}
    $relative=([string]$parts[1]).Replace('/','\')
    if([System.IO.Path]::IsPathRooted($relative) -or $relative -match '(^|\\)\.\.(\\|$)'){Fail "Unsafe manifest path during staging: $relative"}
    $source=Join-Path $PackageRoot $relative
    $destination=Join-Path $stage $relative
    $parent=Split-Path -Parent $destination
    if($parent){New-Item -ItemType Directory -Force -Path $parent | Out-Null}
    Copy-Item -LiteralPath $source -Destination $destination -Force
  }
  Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $stage 'SHA256SUMS.txt') -Force
  if($preservedEnv){Copy-Item -LiteralPath $preservedEnv -Destination (Join-Path $stage '.env') -Force}

  $stageVerify=Join-Path $stage 'VERIFY-PACKAGE.ps1'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $stageVerify
  if($LASTEXITCODE -ne 0){Fail 'Staged application verification failed. Existing app was not changed.'}

  $backup=$null
  if(Test-Path -LiteralPath $AppRoot){
    $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup=Join-Path $BackupsRoot ("app-before-$Version-$stamp")
    Move-Item -LiteralPath $AppRoot -Destination $backup
    Say 'INFO' "Previous app saved to $backup" DarkGray
  }
  try{
    Move-Item -LiteralPath $stage -Destination $AppRoot
  }catch{
    if($backup -and (Test-Path -LiteralPath $backup) -and -not (Test-Path -LiteralPath $AppRoot)){Move-Item -LiteralPath $backup -Destination $AppRoot}
    throw
  }

  $installedEnv=Join-Path $AppRoot '.env'
  if(Test-Path -LiteralPath $installedEnv){Copy-Item -LiteralPath $installedEnv -Destination $canonicalEnv -Force}
  elseif(-not (Test-Path -LiteralPath $canonicalEnv)){Set-Content -LiteralPath $canonicalEnv -Value '# Personal Agent Rus canonical settings' -Encoding ASCII}

  # Stable root launchers: users never need version-specific release directories again.
  $launcherMap=[ordered]@{
    'START.cmd'='START.cmd';'STOP.cmd'='STOP.cmd';'RESTART.cmd'='RESTART.cmd';'STATUS.cmd'='STATUS.cmd';
    'VERIFY.cmd'='VERIFY.cmd';'REPAIR.cmd'='REPAIR.cmd';'ADMIN.cmd'='ADMIN.cmd';'LOGS.cmd'='LOGS.cmd';
    'FULL-ACCEPTANCE.cmd'='FULL-ACCEPTANCE.cmd';'RELEASE-ACCEPTANCE.cmd'='RELEASE-ACCEPTANCE.cmd';
    'WEB-ACCEPTANCE.cmd'='WEB-ACCEPTANCE.cmd';'CODE-ACCEPTANCE.cmd'='CODE-ACCEPTANCE.cmd';
    'LAN-ENABLE.cmd'='LAN-ENABLE.cmd';'LAN-STATUS.cmd'='LAN-STATUS.cmd';'LAN-DISABLE.cmd'='LAN-DISABLE.cmd'
  }
  foreach($name in $launcherMap.Keys){
    $body="@echo off`r`ncall `"%~dp0app\$($launcherMap[$name])`" %*`r`nexit /b %ERRORLEVEL%`r`n"
    Set-Content -LiteralPath (Join-Path $TargetRoot $name) -Value $body -Encoding ASCII
  }

  Say 'PASS' "Personal Agent Rus $Version installed to $AppRoot" Green
  Say 'PASS' 'Canonical root launchers created.' Green
  if(-not $NoStart){
    & (Join-Path $AppRoot 'REPAIR.cmd')
    if($LASTEXITCODE -ne 0){Fail 'Runtime repair/start failed after installation. The previous app backup was preserved.'}
    Start-Process 'http://127.0.0.1:3100'
    Say 'PASS' 'Runtime verified. Browser launch requested.' Green
  }else{Say 'INFO' 'NoStart requested; runtime was not changed.' DarkGray}
}catch{
  if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue}
  throw
}
