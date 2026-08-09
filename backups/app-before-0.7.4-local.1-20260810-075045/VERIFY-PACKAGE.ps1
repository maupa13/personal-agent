$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest=Join-Path $Root 'SHA256SUMS.txt'
$Runtime=Join-Path $Root 'scripts\pa.ps1'
if(-not (Test-Path -LiteralPath $Manifest)){Write-Host '[FAIL] SHA256SUMS.txt missing' -ForegroundColor Red;exit 1}

# IMPORTANT: verification scope is the signed manifest only. The canonical install root may
# legitimately contain older releases, IDE metadata, evidence, backups, or user files.
# Unsigned neighbours must never make a valid package fail verification.
$manifestEntries=@()
$seen=@{}
$bad=0
foreach($line in Get-Content -LiteralPath $Manifest){
  if([string]::IsNullOrWhiteSpace($line)){continue}
  $parts=$line -split '  ',2
  if($parts.Count -ne 2){Write-Host "[FAIL] Invalid checksum line: $line" -ForegroundColor Red;$bad++;continue}
  $relative=([string]$parts[1]).Replace('/','\')
  if([System.IO.Path]::IsPathRooted($relative) -or $relative -match '(^|\\)\.\.(\\|$)'){
    Write-Host "[FAIL] Unsafe manifest path: $($parts[1])" -ForegroundColor Red;$bad++;continue
  }
  $key=$relative.ToLowerInvariant()
  if($seen.ContainsKey($key)){Write-Host "[FAIL] Duplicate manifest path: $($parts[1])" -ForegroundColor Red;$bad++;continue}
  $seen[$key]=$true
  $path=Join-Path $Root $relative
  if(-not (Test-Path -LiteralPath $path -PathType Leaf)){Write-Host "[FAIL] Missing: $($parts[1])" -ForegroundColor Red;$bad++;continue}
  $actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
  if($actual -ne $parts[0].ToLowerInvariant()){Write-Host "[FAIL] SHA256: $($parts[1])" -ForegroundColor Red;$bad++;continue}
  $manifestEntries += [pscustomobject]@{ Relative=$relative; Full=$path; Hash=$parts[0].ToLowerInvariant() }
}
if($bad -gt 0){exit 1}

# Parse only signed PowerShell scripts. Old releases/evidence beside the package are out of scope.
$psFiles=@($manifestEntries | Where-Object { $_.Relative -like '*.ps1' })
$parseFailed=$false
foreach($entry in $psFiles){
  $tokens=$null;$parseErrors=$null
  [void][System.Management.Automation.Language.Parser]::ParseFile($entry.Full,[ref]$tokens,[ref]$parseErrors)
  if($parseErrors -and $parseErrors.Count -gt 0){
    foreach($e in $parseErrors){Write-Host "[FAIL] PowerShell parse [$($entry.Relative)]: $($e.Message)" -ForegroundColor Red}
    $parseFailed=$true
  }
}
if($parseFailed){exit 1}
Write-Host "[PASS] Windows PowerShell syntax verified for $($psFiles.Count) signed script(s)" -ForegroundColor Green

# Execute the canonical installer contract without changing the machine.
$installer=Join-Path $Root 'INSTALL-OR-UPDATE.ps1'
$installOut=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Contract -NoStart 2>&1)
if($LASTEXITCODE -ne 0){$installOut|ForEach-Object{Write-Host $_};Write-Host '[FAIL] Canonical installer contract failed' -ForegroundColor Red;exit 1}
foreach($expectedInstall in @('[CONTRACT] app-root|C:\AI\RusPersonalAgent\app','[CONTRACT] install-mode|staged-in-place','[CONTRACT] preserve|env+docker-named-volumes+workspace+artifacts')){if($installOut -notcontains $expectedInstall){Write-Host "[FAIL] Missing installer contract output: $expectedInstall" -ForegroundColor Red;exit 1}}
Write-Host '[PASS] Canonical installer/update contract verified' -ForegroundColor Green

# Execute argument binding without touching Docker. This catches lost Compose arguments before START.
$out=@(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Runtime -Action contract -DryRun 2>&1)
if($LASTEXITCODE -ne 0){$out|ForEach-Object{Write-Host $_};Write-Host '[FAIL] Windows lifecycle contract self-test failed' -ForegroundColor Red;exit 1}
$expected=@(
  '[CONTRACT] compose|config|--quiet',
  '[CONTRACT] compose|up|-d|ollama|searxng|browser',
  '[CONTRACT] compose|exec|-T|ollama|ollama|list',
  '[CONTRACT] compose|up|-d|--build|code-worker',
  '[CONTRACT] compose|up|-d|--build|--remove-orphans|core',
  '[CONTRACT] compose|ps',
  '[CONTRACT] compose|stop',
  '[CONTRACT] compose|restart|ollama|searxng|browser|code-worker|core'
)
foreach($line in $expected){if($out -notcontains $line){Write-Host "[FAIL] Missing lifecycle contract output: $line" -ForegroundColor Red;Write-Host 'Actual:'; $out|ForEach-Object{Write-Host $_};exit 1}}
Write-Host '[PASS] Windows Docker command-binding self-test verified' -ForegroundColor Green
Write-Host '[PASS] Personal Agent Rus signed package integrity verified' -ForegroundColor Green
