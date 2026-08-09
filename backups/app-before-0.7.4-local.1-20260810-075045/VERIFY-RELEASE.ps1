$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'VERIFY-PACKAGE.ps1')
if(-not $?){exit 1}
$generated=@(Get-ChildItem -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '__pycache__' -or $_.Extension -eq '.pyc' })
if($generated.Count -gt 0){
  foreach($item in $generated){Write-Host "[FAIL] Generated release artifact: $($item.FullName)" -ForegroundColor Red}
  exit 1
}
Write-Host '[PASS] Release hygiene verified' -ForegroundColor Green
