$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$dirs=@(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force -Filter '__pycache__' -ErrorAction SilentlyContinue)
foreach($d in $dirs){Remove-Item -LiteralPath $d.FullName -Recurse -Force}
$pyc=@(Get-ChildItem -LiteralPath $Root -Recurse -File -Force -Filter '*.pyc' -ErrorAction SilentlyContinue)
foreach($f in $pyc){Remove-Item -LiteralPath $f.FullName -Force}
Write-Host "[PASS] Local Python cache cleaned: dirs=$($dirs.Count), files=$($pyc.Count)" -ForegroundColor Green
