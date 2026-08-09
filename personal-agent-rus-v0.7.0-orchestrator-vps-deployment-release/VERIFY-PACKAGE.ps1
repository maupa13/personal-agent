$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest=Join-Path $Root 'SHA256SUMS.txt'
$Runtime=Join-Path $Root 'scripts\pa.ps1'
if(-not (Test-Path -LiteralPath $Manifest)){Write-Host '[FAIL] SHA256SUMS.txt missing' -ForegroundColor Red;exit 1}
$bad=0
foreach($line in Get-Content -LiteralPath $Manifest){
  if([string]::IsNullOrWhiteSpace($line)){continue}
  $parts=$line -split '  ',2
  if($parts.Count -ne 2){Write-Host "[FAIL] Invalid checksum line: $line" -ForegroundColor Red;$bad++;continue}
  $path=Join-Path $Root $parts[1]
  if(-not (Test-Path -LiteralPath $path)){Write-Host "[FAIL] Missing: $($parts[1])" -ForegroundColor Red;$bad++;continue}
  $actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
  if($actual -ne $parts[0].ToLowerInvariant()){Write-Host "[FAIL] SHA256: $($parts[1])" -ForegroundColor Red;$bad++}
}
if($bad -gt 0){exit 1}
$generated=@(Get-ChildItem -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '__pycache__' -or $_.Extension -eq '.pyc' })
if($generated.Count -gt 0){Write-Host "[INFO] Ignoring $($generated.Count) local generated Python cache artifact(s); they are not part of the signed payload." -ForegroundColor DarkGray}

# Parse the real lifecycle script with this machine's Windows PowerShell parser.
$tokens=$null;$parseErrors=$null
[void][System.Management.Automation.Language.Parser]::ParseFile($Runtime,[ref]$tokens,[ref]$parseErrors)
if($parseErrors -and $parseErrors.Count -gt 0){
  foreach($e in $parseErrors){Write-Host "[FAIL] PowerShell parse: $($e.Message)" -ForegroundColor Red}
  exit 1
}
Write-Host '[PASS] Windows PowerShell lifecycle syntax verified' -ForegroundColor Green

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
