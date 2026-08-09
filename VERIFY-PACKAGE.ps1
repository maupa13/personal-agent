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

# Parse every shipped PowerShell script with this machine's Windows PowerShell parser.
$psFiles=@(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter '*.ps1' -ErrorAction Stop)
$parseFailed=$false
foreach($psFile in $psFiles){
  $tokens=$null;$parseErrors=$null
  [void][System.Management.Automation.Language.Parser]::ParseFile($psFile.FullName,[ref]$tokens,[ref]$parseErrors)
  if($parseErrors -and $parseErrors.Count -gt 0){
    $relative=$psFile.FullName.Substring($Root.Length).TrimStart('\','/')
    foreach($e in $parseErrors){Write-Host "[FAIL] PowerShell parse [$relative]: $($e.Message)" -ForegroundColor Red}
    $parseFailed=$true
  }
}
if($parseFailed){exit 1}
Write-Host "[PASS] Windows PowerShell syntax verified for $($psFiles.Count) script(s)" -ForegroundColor Green

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
