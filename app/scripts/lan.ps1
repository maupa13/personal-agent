param([ValidateSet('enable','disable','status')][string]$Action='status')
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$HomeRoot = if((Split-Path -Leaf $Root) -eq 'app'){Split-Path -Parent $Root}else{$Root}
$CanonicalConfig = Join-Path $HomeRoot 'config\.env'
$EnvFile = if(Test-Path -LiteralPath $CanonicalConfig){$CanonicalConfig}else{Join-Path $Root '.env'}
$Compose=Join-Path $Root 'compose.yaml'
$RuleName='Personal Agent Rus LAN'

function Is-Admin {
  $id=[Security.Principal.WindowsIdentity]::GetCurrent()
  $p=New-Object Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Elevate([string]$act){
  $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'),'-Action',$act)
  $proc=Start-Process -FilePath 'powershell.exe' -ArgumentList ($args -join ' ') -Verb RunAs -Wait -PassThru
  exit $proc.ExitCode
}
function Read-Env {
  $map=[ordered]@{}
  if(Test-Path -LiteralPath $EnvFile){foreach($line in Get-Content -LiteralPath $EnvFile){if($line -match '^\s*#' -or $line -notmatch '='){continue};$i=$line.IndexOf('=');$map[$line.Substring(0,$i)]=$line.Substring($i+1)}}
  return $map
}
function Write-Env($map){@('# Personal Agent Rus local settings')+@($map.Keys|ForEach-Object{"$_=$($map[$_])"})|Set-Content -LiteralPath $EnvFile -Encoding ASCII}
function Private-IPv4 {
  $items=Get-NetIPConfiguration -ErrorAction SilentlyContinue|Where-Object{$_.IPv4DefaultGateway -and $_.IPv4Address}
  foreach($item in $items){foreach($addr in @($item.IPv4Address)){if($addr.IPAddress -and $addr.IPAddress -notlike '169.254.*'){[string]$addr.IPAddress}}}
}
if(-not(Test-Path -LiteralPath $EnvFile)){Write-Host '[FAIL] .env not found. Run START/REPAIR first.' -ForegroundColor Red;exit 1}
$values=Read-Env;$port=if($values.Contains('PA_UI_PORT')){[string]$values['PA_UI_PORT']}else{'3100'}
if($Action -eq 'status'){
  $bind=if($values.Contains('PA_BIND_IP')){[string]$values['PA_BIND_IP']}else{'127.0.0.1'}
  $enabled=if($values.Contains('PA_LAN_ENABLED')){[string]$values['PA_LAN_ENABLED']}else{'0'}
  $publicUrl=if($values.Contains('PA_LAN_PUBLIC_URL')){[string]$values['PA_LAN_PUBLIC_URL']}else{''}
  Write-Host "LAN enabled: $enabled"
  Write-Host "LAN bind: $bind`:$port"
  if($publicUrl){Write-Host "Primary URL: $publicUrl"}
  foreach($ip in Private-IPv4){Write-Host "URL: http://$ip`:$port"}
  exit 0
}
if(-not(Is-Admin)){Elevate $Action}
if($Action -eq 'enable'){
  $values['PA_BIND_IP']='0.0.0.0'
  $values['PA_LAN_ENABLED']='1'
  $ips=@(Private-IPv4)
  if($ips.Count -gt 0){$values['PA_LAN_PUBLIC_URL']="http://$($ips[0]):$port"}
  Write-Env $values
  Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue|Remove-NetFirewallRule -ErrorAction SilentlyContinue
  New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort ([int]$port) -Profile Private | Out-Null
  & docker.exe compose --env-file $EnvFile -f $Compose up -d core
  if($LASTEXITCODE -ne 0){Write-Host '[FAIL] Core restart failed.' -ForegroundColor Red;exit 1}
  Write-Host '[PASS] LAN access enabled for Private networks.' -ForegroundColor Green
  foreach($ip in @($ips)){Write-Host "Open on phone/laptop: http://$ip`:$port" -ForegroundColor Cyan}
  if(-not $values.Contains('PA_AUTH_MODE') -or [string]$values['PA_AUTH_MODE'] -eq 'personal'){Write-Host 'Recommendation: for shared LAN access enable accounts mode so each person has an isolated profile.' -ForegroundColor Yellow}
  Write-Host 'Note: microphone/camera may require HTTPS Secure Context; chat/files work over LAN HTTP.' -ForegroundColor Yellow
}else{
  $values['PA_BIND_IP']='127.0.0.1'
  $values['PA_LAN_ENABLED']='0'
  $values['PA_LAN_PUBLIC_URL']=''
  Write-Env $values
  Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue|Remove-NetFirewallRule -ErrorAction SilentlyContinue
  & docker.exe compose --env-file $EnvFile -f $Compose up -d core
  if($LASTEXITCODE -ne 0){Write-Host '[FAIL] Core restart failed.' -ForegroundColor Red;exit 1}
  Write-Host '[PASS] LAN access disabled; UI is bound to localhost.' -ForegroundColor Green
}
