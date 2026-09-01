param(
  [ValidateSet('start','stop','restart','status','verify','webverify','codeverify','fullverify','releaseverify','logs','admin','backup','update','repair','contract')]
  [string]$Action = 'start',
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$script:TotalWatch = [System.Diagnostics.Stopwatch]::StartNew()
$script:StepWatch = $null
$script:StepTitle = ''
$Root = Split-Path -Parent $PSScriptRoot
$HomeRoot = if((Split-Path -Leaf $Root) -eq 'app'){Split-Path -Parent $Root}else{$Root}
$CanonicalConfig = Join-Path $HomeRoot 'config\.env'
$EnvFile = if(Test-Path -LiteralPath $CanonicalConfig){$CanonicalConfig}else{Join-Path $Root '.env'}
$Compose = Join-Path $Root 'compose.yaml'
$LogDir = if((Split-Path -Leaf $Root) -eq 'app'){Join-Path $HomeRoot 'logs'}else{Join-Path $Root 'logs'}
$LogFile = Join-Path $LogDir 'PERSONAL-AGENT-LAST.log'
if(-not $DryRun){ New-Item -ItemType Directory -Force -Path $LogDir | Out-Null; Set-Content -LiteralPath $LogFile -Value '' -Encoding ASCII }

function Emit([string]$Level,[string]$Message,[ConsoleColor]$Color=[ConsoleColor]::Gray){
  $elapsedMs=[int64]$script:TotalWatch.ElapsedMilliseconds
  $line = "[$Level] $Message"
  Write-Host $line -ForegroundColor $Color
  if(-not $DryRun){ Add-Content -LiteralPath $LogFile -Value ((Get-Date -Format o) + " elapsed_ms=$elapsedMs " + $line) -Encoding UTF8 }
}
function Fail([string]$Message){ Emit 'FAIL' $Message Red; throw $Message }
function Info([string]$Message){ Emit 'INFO' $Message Cyan }
function Warn([string]$Message){ Emit 'WARN' $Message Yellow }
function Pass([string]$Message){ Emit 'PASS' $Message Green }
function Finish-StepTimer {
  if($script:StepWatch){
    $script:StepWatch.Stop()
    $seconds=[Math]::Round($script:StepWatch.Elapsed.TotalSeconds,2)
    Emit 'TIME' ("{0} duration={1}s total={2}s" -f $script:StepTitle,$seconds,[Math]::Round($script:TotalWatch.Elapsed.TotalSeconds,2)) DarkGray
    $script:StepWatch=$null;$script:StepTitle=''
  }
}
function Step([int]$N,[int]$Total,[string]$Title,[string]$Flavor=''){
  Finish-StepTimer
  $script:StepTitle=$Title;$script:StepWatch=[System.Diagnostics.Stopwatch]::StartNew()
  Write-Host ''
  Write-Host ("[STEP {0:D2}/{1:D2}] {2}" -f $N,$Total,$Title) -ForegroundColor White
  if($Flavor){ Write-Host ("             " + $Flavor) -ForegroundColor DarkGray }
  if(-not $DryRun){ Add-Content -LiteralPath $LogFile -Value ((Get-Date -Format o) + " elapsed_ms=$([int64]$script:TotalWatch.ElapsedMilliseconds) [STEP $N/$Total] $Title") -Encoding UTF8 }
}
function Read-HttpErrorBody($Response){
  if(-not $Response){return ''}
  try{
    $stream=$Response.GetResponseStream();if(-not $stream){return ''}
    $reader=New-Object System.IO.StreamReader($stream)
    try{return $reader.ReadToEnd()}finally{$reader.Dispose();$stream.Dispose()}
  }catch{return ''}
}
function Invoke-HttpProbe([string]$Stage,[string]$Uri,[string]$Method='GET',[string]$Body='',[string]$ContentType='application/json; charset=utf-8',[int]$TimeoutSec=10,[hashtable]$ExtraHeaders=@{}){
  $requestId=[guid]::NewGuid().ToString('N');$correlationId=[guid]::NewGuid().ToString('N');$watch=[System.Diagnostics.Stopwatch]::StartNew()
  $headers=@{'X-Request-ID'=$requestId;'X-Correlation-ID'=$correlationId}
  foreach($key in $ExtraHeaders.Keys){$headers[$key]=$ExtraHeaders[$key]}
  try{
    $webRequestParams=@{UseBasicParsing=$true;Uri=$Uri;Method=$Method;TimeoutSec=$TimeoutSec;Headers=$headers;ErrorAction='Stop'}
    if($Body){$webRequestParams.Body=$Body;$webRequestParams.ContentType=$ContentType}
    $response=Invoke-WebRequest @webRequestParams;$watch.Stop()
    return [pscustomobject]@{Stage=$Stage;Uri=$Uri;Method=$Method;Status=[int]$response.StatusCode;Content=[string]$response.Content;DurationMs=[int64]$watch.ElapsedMilliseconds;RequestId=$requestId;CorrelationId=$correlationId;Error=''}
  }catch{
    $watch.Stop();$status=0;$content='';$error=$_.Exception.Message
    if($_.Exception.Response){try{$status=[int]$_.Exception.Response.StatusCode}catch{};$content=Read-HttpErrorBody $_.Exception.Response}
    return [pscustomobject]@{Stage=$Stage;Uri=$Uri;Method=$Method;Status=$status;Content=[string]$content;DurationMs=[int64]$watch.ElapsedMilliseconds;RequestId=$requestId;CorrelationId=$correlationId;Error=$error}
  }
}
function Trace-HttpProbe($Probe){
  $path=$Probe.Uri;try{$path=([uri]$Probe.Uri).PathAndQuery}catch{}
  Info ("HTTP stage={0} method={1} endpoint={2} status={3} duration_ms={4} request_id={5} correlation_id={6}" -f $Probe.Stage,$Probe.Method,$path,$Probe.Status,$Probe.DurationMs,$Probe.RequestId,$Probe.CorrelationId)
}
function Assert-HttpProbe($Probe,[int[]]$ExpectedStatus){
  Trace-HttpProbe $Probe
  if($ExpectedStatus -notcontains [int]$Probe.Status){
    $body=([string]$Probe.Content).Trim();if($body.Length -gt 600){$body=$body.Substring(0,600)+'...'}
    Fail ("HTTP smoke failed stage={0} endpoint={1} status={2} expected={3} duration_ms={4} request_id={5} correlation_id={6} body={7} error={8}" -f $Probe.Stage,$Probe.Uri,$Probe.Status,($ExpectedStatus -join ','),$Probe.DurationMs,$Probe.RequestId,$Probe.CorrelationId,$body,$Probe.Error)
  }
}
function Ensure-Env {
  $defaults = [ordered]@{
    'PA_BIND_IP'='127.0.0.1'
    'PA_UI_PORT'='3100'
    'PA_BOOTSTRAP_MODEL'='qwen3:0.6b'
    'PA_OLLAMA_IMAGE'='ollama/ollama:0.32.6'
    'PA_CORE_IMAGE'='personal-agent-core:1.0.3'
    'PA_BROWSER_IMAGE'='personal-agent-browser:1.0.3'
    'PA_SEARXNG_IMAGE'='searxng/searxng:2026.8.5-1689cb1b5'
    'PA_CODE_WORKER_IMAGE'='personal-agent-code-worker:1.0.3'
    'PA_AUTH_MODE'='personal'
    'PA_REGISTRATION_POLICY'='open'
    'PA_DEBUG_DIAGNOSTICS'='1'
  }
  if(Test-Path -LiteralPath $EnvFile){
    $raw = @(Get-Content -LiteralPath $EnvFile)
    $values = [ordered]@{}
    foreach($line in $raw){
      if($line -match '^\s*#' -or [string]::IsNullOrWhiteSpace($line)){continue}
      $idx=$line.IndexOf('=');if($idx -le 0){continue}
      $values[$line.Substring(0,$idx).Trim()]=$line.Substring($idx+1)
    }
    $legacy = [ordered]@{
      'RPA_BIND_IP'='PA_BIND_IP';'RPA_UI_PORT'='PA_UI_PORT';'RPA_ADMIN_TOKEN'='PA_ADMIN_TOKEN';
      'RPA_BOOTSTRAP_MODEL'='PA_BOOTSTRAP_MODEL';'RPA_OLLAMA_IMAGE'='PA_OLLAMA_IMAGE';'RPA_CORE_IMAGE'='PA_CORE_IMAGE'
    }
    $changed=$false
    foreach($old in $legacy.Keys){
      $new=$legacy[$old]
      if($values.Contains($old) -and -not $values.Contains($new)){$values[$new]=$values[$old];$changed=$true}
      if($values.Contains($old)){$values.Remove($old);$changed=$true}
    }
    foreach($key in $defaults.Keys){if(-not $values.Contains($key)){$values[$key]=$defaults[$key];$changed=$true}}
    if(-not $values.Contains('PA_ADMIN_TOKEN') -or [string]::IsNullOrWhiteSpace([string]$values['PA_ADMIN_TOKEN']) -or $values['PA_ADMIN_TOKEN'] -eq 'CHANGE_ME'){
      $bytes=New-Object byte[] 32;$rng=[System.Security.Cryptography.RandomNumberGenerator]::Create();try{$rng.GetBytes($bytes)}finally{$rng.Dispose()}
      $values['PA_ADMIN_TOKEN']=-join($bytes|ForEach-Object{$_.ToString('x2')});$changed=$true
    }
    if(-not $values.Contains('PA_SEARXNG_SECRET') -or [string]::IsNullOrWhiteSpace([string]$values['PA_SEARXNG_SECRET']) -or $values['PA_SEARXNG_SECRET'] -eq 'CHANGE_ME'){
      $bytes=New-Object byte[] 32;$rng=[System.Security.Cryptography.RandomNumberGenerator]::Create();try{$rng.GetBytes($bytes)}finally{$rng.Dispose()}
      $values['PA_SEARXNG_SECRET']=-join($bytes|ForEach-Object{$_.ToString('x2')});$changed=$true
    }
    if(([string]$values['PA_CORE_IMAGE']) -match '^(rus-personal-agent-core|personal-agent-core):'){ $values['PA_CORE_IMAGE']='personal-agent-core:1.0.3';$changed=$true }
    if($values.Contains('PA_BROWSER_IMAGE') -and ([string]$values['PA_BROWSER_IMAGE']) -match '^personal-agent-browser:'){ $values['PA_BROWSER_IMAGE']='personal-agent-browser:1.0.3';$changed=$true }
    if($values.Contains('PA_CODE_WORKER_IMAGE') -and ([string]$values['PA_CODE_WORKER_IMAGE']) -match '^personal-agent-code-worker:'){ $values['PA_CODE_WORKER_IMAGE']='personal-agent-code-worker:1.0.3';$changed=$true }
    if($changed){
      @('# Personal Agent Rus local settings') + @($values.Keys|ForEach-Object{"$_=$($values[$_])"}) | Set-Content -LiteralPath $EnvFile -Encoding ASCII
      Pass 'Migrated local environment to the Personal Agent family contract.'
    }
    return
  }
  $bytes = New-Object byte[] 32
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try{$rng.GetBytes($bytes)}finally{$rng.Dispose()}
  $token = -join ($bytes | ForEach-Object { $_.ToString('x2') })
  $bytes2 = New-Object byte[] 32
  $rng2 = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try{$rng2.GetBytes($bytes2)}finally{$rng2.Dispose()}
  $searchToken = -join ($bytes2 | ForEach-Object { $_.ToString('x2') })
  @(
    '# Personal Agent Rus local settings',
    'PA_BIND_IP=127.0.0.1',
    'PA_UI_PORT=3100',
    "PA_ADMIN_TOKEN=$token",
    "PA_SEARXNG_SECRET=$searchToken",
    'PA_BOOTSTRAP_MODEL=qwen3:0.6b',
    'PA_OLLAMA_IMAGE=ollama/ollama:0.32.6',
    'PA_CORE_IMAGE=personal-agent-core:1.0.3',
    'PA_BROWSER_IMAGE=personal-agent-browser:1.0.3',
    'PA_SEARXNG_IMAGE=searxng/searxng:2026.8.5-1689cb1b5',
    'PA_CODE_WORKER_IMAGE=personal-agent-code-worker:1.0.3',
    'PA_AUTH_MODE=personal',
    'PA_REGISTRATION_POLICY=open',
    'PA_DEBUG_DIAGNOSTICS=1'
  ) | Set-Content -LiteralPath $EnvFile -Encoding ASCII
  Pass 'Created local .env with a random admin token.'
}
function Get-EnvValue([string]$Name){
  if(-not (Test-Path -LiteralPath $EnvFile)){return ''}
  $line = Get-Content -LiteralPath $EnvFile | Where-Object { $_ -like "$Name=*" } | Select-Object -First 1
  if(-not $line){return ''}
  return $line.Substring($Name.Length+1)
}
function Invoke-DockerSafe([string[]]$DockerArguments,[switch]$Quiet){
  # Windows PowerShell 5.1 converts native stderr into ErrorRecord objects and,
  # under ErrorActionPreference=Stop, may throw RemoteException before callers
  # can inspect LASTEXITCODE. Docker/Compose legitimately use stderr for progress
  # and failed readiness probes. Capture under Continue and trust the process exit code.
  $previousErrorActionPreference=$ErrorActionPreference
  $nativeOutput=@()
  $nativeExitCode=1
  try{
    $ErrorActionPreference='Continue'
    $nativeOutput=@(& docker.exe @DockerArguments 2>&1)
    $nativeExitCode=$LASTEXITCODE
  }catch{
    $nativeOutput += ("{0}: {1}" -f $_.Exception.GetType().Name,$_.Exception.Message)
    $nativeExitCode=1
  }finally{
    $ErrorActionPreference=$previousErrorActionPreference
  }
  if(-not $Quiet){foreach($line in $nativeOutput){Write-Host ([string]$line)}}
  return [pscustomobject]@{ExitCode=$nativeExitCode;Output=$nativeOutput}
}
function Require-Docker {
  if(-not (Get-Command docker.exe -ErrorAction SilentlyContinue)){Fail 'Docker Desktop / Docker CLI is required.'}
  $info=Invoke-DockerSafe -DockerArguments @('info') -Quiet
  if($info.ExitCode -ne 0){Fail 'Docker engine is not ready. Start Docker Desktop and retry.'}
  $composeVersion=Invoke-DockerSafe -DockerArguments @('compose','version') -Quiet
  if($composeVersion.ExitCode -ne 0){Fail 'Docker Compose is not available.'}
  $shortVersion=Invoke-DockerSafe -DockerArguments @('compose','version','--short') -Quiet
  $v=([string]($shortVersion.Output | Select-Object -First 1)).Trim()
  Pass "Docker engine and Compose are ready ($v)."
}
function Invoke-Compose([string[]]$ComposeArgs){
  if(-not $ComposeArgs -or $ComposeArgs.Count -eq 0){Fail 'Internal error: docker compose command is empty.'}
  if($DryRun){Write-Output ('[CONTRACT] compose|' + ($ComposeArgs -join '|'));return}
  $dockerArgs=@('compose','--env-file',$EnvFile,'-f',$Compose)+$ComposeArgs
  $native=Invoke-DockerSafe -DockerArguments $dockerArgs
  if($native.ExitCode -ne 0){Fail "docker compose failed: $($ComposeArgs -join ' ')"}
}
function Wait-Ollama {
  Info 'Waiting for local AI engine...'
  for($i=1;$i -le 60;$i++){
    $probe=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'exec','-T','ollama','ollama','list') -Quiet
    if($probe.ExitCode -eq 0){Pass 'Local AI engine is ready.';return}
    if(($i % 10)-eq 0){Info "Local AI engine is still starting ($i/60)..."}
    Start-Sleep -Seconds 2
  }
  Invoke-Compose -ComposeArgs @('ps')
  Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'logs','--tail','120','ollama') | Out-Null
  Fail 'Local AI engine did not become ready.'
}
function Wait-WebServices {
  Info 'Waiting for Web/Search and browser services...'
  for($i=1;$i -le 60;$i++){
    $probe=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'exec','-T','browser','python','-c',"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3); urllib.request.urlopen('http://searxng:8080/',timeout=3)") -Quiet
    if($probe.ExitCode -eq 0){Pass 'Web/Search and browser services are ready.';return}
    if(($i % 10)-eq 0){Info "Web services are still starting ($i/60)..."}
    Start-Sleep -Seconds 2
  }
  Invoke-Compose -ComposeArgs @('ps')
  Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'logs','--tail','120','searxng','browser') | Out-Null
  Fail 'Web/Search or browser service did not become ready.'
}
function Wait-CodeWorker {
  Info 'Waiting for isolated Code sandbox...'
  for($i=1;$i -le 60;$i++){
    $probe=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'exec','-T','code-worker','python3','-c',"import json,socket; s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(3); s.connect('/ipc/code-worker.sock'); s.sendall(b'GET /health HTTP/1.1\r\nHost: local\r\nConnection: close\r\n\r\n'); data=b''; exec('while True:\n c=s.recv(65536)\n if not c: break\n data+=c'); body=data.split(b'\r\n\r\n',1)[1]; x=json.loads(body); raise SystemExit(0 if x.get('ready') else 1)") -Quiet
    if($probe.ExitCode -eq 0){Pass 'Code sandbox is ready: Python, Java and PowerShell.';return}
    if(($i % 10)-eq 0){Info "Code sandbox is still starting ($i/60)..."}
    Start-Sleep -Seconds 2
  }
  Invoke-Compose -ComposeArgs @('ps')
  Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'logs','--tail','160','code-worker') | Out-Null
  Fail 'Code sandbox did not become ready.'
}
function Test-CodeWorkerReadyOnce {
  $probe=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'exec','-T','code-worker','python3','-c',"import json,socket; s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(2); s.connect('/ipc/code-worker.sock'); s.sendall(b'GET /health HTTP/1.1\r\nHost: local\r\nConnection: close\r\n\r\n'); data=b''; exec('while True:\n c=s.recv(65536)\n if not c: break\n data+=c'); body=data.split(b'\r\n\r\n',1)[1]; x=json.loads(body); raise SystemExit(0 if x.get('ready') else 1)") -Quiet
  return ($probe.ExitCode -eq 0)
}
function Start-CodeWorkerOptional {
  Info 'Starting optional isolated Code sandbox...'

  # Windows PowerShell 5.1 wraps native stderr records as RemoteException when
  # ErrorActionPreference=Stop. Docker Compose writes normal build progress to
  # stderr, so an optional worker build must capture native output under
  # Continue and decide solely from the native process exit code.
  $native=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'up','-d','--build','code-worker')
  if($native.ExitCode -ne 0){
    Warn "Code sandbox build/start failed (exit $($native.ExitCode)). Chat, Web, Research and Files will still start."
    return $false
  }
  for($i=1;$i -le 20;$i++){
    if(Test-CodeWorkerReadyOnce){Pass 'Code sandbox is ready: Python, Java and PowerShell.';return $true}
    Start-Sleep -Seconds 1
  }
  Warn 'Code sandbox is not ready. Core will start in degraded-code mode; CODE-ACCEPTANCE remains strict.'
  Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'logs','--tail','80','code-worker') -Quiet | Out-Null
  return $false
}
function Test-CodeInternalSmoke([switch]$Strict) {
  $base=Get-BaseUrl
  $job=$null
  try{
    $status=Invoke-RestMethod -Uri ($base+'/api/code/status') -TimeoutSec 10
    if($status.ready -ne $true -or $status.network -ne 'disabled'){throw 'Code sandbox public contract is not ready or network is not disabled.'}
    $payload=@{language='python';code='print("PAR_CODE_OK")';timeout_seconds=5}|ConvertTo-Json -Compress
    $created=Invoke-RestMethod -Method Post -Uri ($base+'/api/code/jobs') -ContentType 'application/json; charset=utf-8' -Body $payload -TimeoutSec 10
    $jobId=[string]$created.job.id
    if(-not $jobId){throw 'Code sandbox did not return a job id.'}
    for($i=1;$i -le 80;$i++){
      $job=(Invoke-RestMethod -Uri ($base+'/api/code/jobs/'+$jobId) -TimeoutSec 10).job
      if($job.status -in @('COMPLETED','FAILED','CANCELLED')){break}
      Start-Sleep -Milliseconds 250
    }
    if(-not $job){throw 'Code sandbox returned no job state.'}
    if($job.status -ne 'COMPLETED'){throw ("Code job ended with status={0}; error={1}" -f $job.status,$job.error)}
    if(-not ([string]$job.result.stdout).Contains('PAR_CODE_OK')){throw 'Code job completed but expected stdout marker is missing.'}
  }catch{
    $reason=$_.Exception.Message
    if($job){
      try{$diag=$job|ConvertTo-Json -Depth 8 -Compress}catch{$diag='<job serialization failed>'}
      Warn ("Code smoke diagnostics: {0}" -f $diag)
    }
    if($Strict){Fail ("Real Code sandbox smoke failed: {0}" -f $reason)}
    Warn ("Code capability is DEGRADED after real execution smoke: {0}" -f $reason)
    return $false
  }
  Pass 'Code sandbox smoke passed: isolated Python execution returned verified output.'
  return $true
}
function Invoke-CodeJobAndVerify([string]$Language,[string]$Code,[string]$Expected,[int]$TimeoutSeconds=10) {
  $base=Get-BaseUrl
  $payload=@{language=$Language;code=$Code;timeout_seconds=$TimeoutSeconds}|ConvertTo-Json -Compress
  $created=Invoke-RestMethod -Method Post -Uri ($base+'/api/code/jobs') -ContentType 'application/json; charset=utf-8' -Body $payload -TimeoutSec 15
  $jobId=[string]$created.job.id
  if(-not $jobId){Fail "Code acceptance did not return a job id for $Language."}
  $job=$null
  for($i=1;$i -le 120;$i++){
    $job=(Invoke-RestMethod -Uri ($base+'/api/code/jobs/'+$jobId) -TimeoutSec 10).job
    if($job.status -in @('COMPLETED','FAILED','CANCELLED')){break}
    Start-Sleep -Milliseconds 250
  }
  if(-not $job -or $job.status -ne 'COMPLETED'){Fail "Code acceptance failed for ${Language}: status=$($job.status)"}
  if(-not ([string]$job.result.stdout).Contains($Expected)){Fail "Code acceptance output mismatch for $Language."}
  return $job
}
function Test-CodeLiveAcceptance {
  Wait-CodeWorker;Wait-Core
  $status=Invoke-RestMethod -Uri ((Get-BaseUrl)+'/api/code/status') -TimeoutSec 10
  if($status.ready -ne $true -or $status.network -ne 'disabled'){Fail 'Code sandbox live contract is not ready or network isolation is disabled.'}
  Invoke-CodeJobAndVerify -Language 'python' -Code 'print("PAR_PYTHON_LIVE_OK")' -Expected 'PAR_PYTHON_LIVE_OK' | Out-Null
  Invoke-CodeJobAndVerify -Language 'java' -Code 'public class Main { public static void main(String[] args) { System.out.println("PAR_JAVA_LIVE_OK"); } }' -Expected 'PAR_JAVA_LIVE_OK' -TimeoutSeconds 20 | Out-Null
  Invoke-CodeJobAndVerify -Language 'powershell' -Code 'Write-Output "PAR_POWERSHELL_LIVE_OK"' -Expected 'PAR_POWERSHELL_LIVE_OK' | Out-Null

  $inspectResult=Invoke-DockerSafe -DockerArguments @('inspect','par-rus-code-worker') -Quiet
  if($inspectResult.ExitCode -ne 0){Fail 'Could not inspect the Code worker container.'}
  $inspect=@(($inspectResult.Output -join "`n")|ConvertFrom-Json)[0]
  if($inspect.HostConfig.NetworkMode -ne 'none'){Fail 'Code worker Docker network mode is not none.'}
  if($inspect.HostConfig.ReadonlyRootfs -ne $true){Fail 'Code worker root filesystem is not read-only.'}
  foreach($bind in @($inspect.HostConfig.Binds)){if(([string]$bind).ToLower().Contains('docker.sock')){Fail 'Code worker unexpectedly mounts the Docker socket.'}}
  if([int64]$inspect.HostConfig.Memory -le 0){Fail 'Code worker memory limit is missing.'}
  if([int64]$inspect.HostConfig.PidsLimit -le 0){Fail 'Code worker PID limit is missing.'}
  Pass 'CODE LIVE ACCEPTANCE passed: Python, Java 21, PowerShell and Docker sandbox isolation.'
}
function Ensure-BootstrapModel {
  $model=Get-EnvValue 'PA_BOOTSTRAP_MODEL';if(-not $model){$model='qwen3:0.6b'}
  $listResult=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'exec','-T','ollama','ollama','list') -Quiet
  if($listResult.ExitCode -ne 0){Fail 'Could not query installed local models.'}
  $list=@($listResult.Output)
  if(($list -join "`n") -match [regex]::Escape($model)){Pass 'Bootstrap inference model is already available.';return}
  Info 'Downloading the small bootstrap model used only for product smoke tests and fallback.'
  Write-Host '             A small brain first. The admin can choose the serious one later.' -ForegroundColor DarkGray
  $pull=Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'exec','-T','ollama','ollama','pull',$model)
  if($pull.ExitCode -ne 0){Fail 'Bootstrap model download failed.'}
  Pass 'Bootstrap inference model is ready.'
}
function Get-BaseUrl {
  $port=Get-EnvValue 'PA_UI_PORT';if(-not $port){$port='3100'}
  return "http://127.0.0.1:$port"
}
function Wait-Core {
  $url=(Get-BaseUrl)+'/api/health'
  Info 'Waiting for Personal Agent Rus Core...'
  for($i=1;$i -le 90;$i++){
    try{$r=Invoke-RestMethod -Uri $url -TimeoutSec 3;if($r.ready -eq $true){Pass 'Personal Agent Rus Core is ready.';return}}catch{}
    if(($i % 10)-eq 0){Info "Core is still starting ($i/90)..."}
    Start-Sleep -Seconds 2
  }
  Invoke-Compose -ComposeArgs @('ps')
  Invoke-DockerSafe -DockerArguments @('compose','--env-file',$EnvFile,'-f',$Compose,'logs','--tail','160','core') | Out-Null
  Fail 'Personal Agent Rus Core did not become ready.'
}
function Assert-CoreImageCurrent {
  $expected=Get-EnvValue 'PA_CORE_IMAGE'
  if(-not $expected){$expected='personal-agent-core:1.0.3'}
  $inspect=Invoke-DockerSafe -DockerArguments @('inspect','--format={{.Config.Image}}','par-rus-core') -Quiet
  if($inspect.ExitCode -ne 0){Fail 'Personal Agent Rus Core container is missing.'}
  $actual=([string]($inspect.Output | Select-Object -First 1)).Trim()
  if($actual -ne $expected){Fail "Stale Core image is running: $actual; expected $expected. Run REPAIR.cmd."}
}
function Test-Runtime {
  $verificationWatch=[System.Diagnostics.Stopwatch]::StartNew()
  Assert-CoreImageCurrent
  $base=Get-BaseUrl
  $healthProbe=Invoke-HttpProbe -Stage 'health' -Uri ($base+'/api/health') -TimeoutSec 10;Assert-HttpProbe $healthProbe @(200)
  try{$health=$healthProbe.Content|ConvertFrom-Json}catch{Fail 'Health response is not valid JSON.'}
  if($health.ready -ne $true){Fail 'Health contract is not ready.'}
  $systemProbe=Invoke-HttpProbe -Stage 'public-system' -Uri ($base+'/api/system') -TimeoutSec 10;Assert-HttpProbe $systemProbe @(200);$system=$systemProbe.Content
  foreach($forbidden in @('qwen','ollama','par-rus-ollama','model_id')){if($system.ToLower().Contains($forbidden)){Fail "Public API leaked internal token: $forbidden"}}
  $uiProbe=Invoke-HttpProbe -Stage 'public-ui' -Uri ($base+'/') -TimeoutSec 10;Assert-HttpProbe $uiProbe @(200);$html=$uiProbe.Content
  foreach($forbidden in @('qwen','ollama','par-rus-ollama','model_id')){if($html.ToLower().Contains($forbidden)){Fail "Public UI leaked internal token: $forbidden"}}
  $authMode=(Get-EnvValue 'PA_AUTH_MODE').Trim().ToLower();if(-not $authMode){$authMode='personal'}
  $adminProbe=Invoke-HttpProbe -Stage 'admin-boundary' -Uri ($base+'/api/admin/status') -TimeoutSec 10
  if($authMode -eq 'personal'){Assert-HttpProbe $adminProbe @(200)}else{Assert-HttpProbe $adminProbe @(401)}

  # Installation/VERIFY must prove the small bootstrap pipeline, not accidentally cold-load
  # whichever heavy production model an administrator assigned to Auto/Fast/Smart.
  $adminToken=(Get-EnvValue 'PA_ADMIN_TOKEN').Trim()
  if(-not $adminToken){Fail 'Admin token is missing; bootstrap inference smoke cannot authenticate.'}
  $bootstrapHeaders=@{'Authorization'="Bearer $adminToken"}
  $bootstrapProbe=Invoke-HttpProbe -Stage 'bootstrap-inference' -Uri ($base+'/api/admin/inference/smoke') -Method 'POST' -Body '{}' -TimeoutSec 120 -ExtraHeaders $bootstrapHeaders
  Assert-HttpProbe $bootstrapProbe @(200)
  try{$resp=$bootstrapProbe.Content|ConvertFrom-Json}catch{Fail 'Bootstrap inference response is not valid JSON.'}
  $t=$resp.timing
  Info ("INFERENCE bootstrap model={0} ok={1} reason={2} content_length={3} wall_ms={4} provider_total_ms={5} load_ms={6} prompt_eval_ms={7} generation_ms={8} prompt_tokens={9} output_tokens={10} tokens_per_sec={11}" -f $resp.model,$resp.ok,$resp.reason,$resp.content_length,$t.wall_ms,$t.provider_total_ms,$t.load_ms,$t.prompt_eval_ms,$t.generation_ms,$t.prompt_tokens,$t.output_tokens,$t.tokens_per_sec)
  if(-not $resp.ok -or -not $resp.output_nonempty){
    Warn ("Bootstrap inference returned HTTP 200 but no final answer. model={0} reason={1} output_tokens={2} wall_ms={3}. For thinking-capable models the smoke explicitly requests think=false." -f $resp.model,$resp.reason,$t.output_tokens,$t.wall_ms)
    Fail 'Bootstrap inference smoke test failed.'
  }
  if([int64]$t.wall_ms -gt 15000){Warn 'Bootstrap inference is unusually slow (>15s). Check GPU/VRAM/model runtime in Admin -> Diagnostics before judging normal chat performance.'}
  $verificationWatch.Stop()
  Pass ("Runtime verification passed: health, public boundary, admin boundary and bootstrap inference. verification_duration={0}s command_elapsed={1}s" -f [Math]::Round($verificationWatch.Elapsed.TotalSeconds,2),[Math]::Round($script:TotalWatch.Elapsed.TotalSeconds,2))
}

function Test-WebInternalSmoke {
  $base=Get-BaseUrl
  $systemProbe=Invoke-HttpProbe -Stage 'web-capabilities' -Uri ($base+'/api/system') -TimeoutSec 10;Assert-HttpProbe $systemProbe @(200)
  try{$system=$systemProbe.Content|ConvertFrom-Json}catch{Fail 'Public capability response is not valid JSON.'}
  if($system.capabilities.web.status -ne 'ready' -or $system.capabilities.research.status -ne 'ready'){Fail 'Public capability contract does not report Web/Research ready.'}
  $ssrfBody=@{url='http://127.0.0.1:11434/api/tags'}|ConvertTo-Json -Compress
  $ssrfProbe=Invoke-HttpProbe -Stage 'ssrf-policy' -Uri ($base+'/api/web/read') -Method 'POST' -Body $ssrfBody -TimeoutSec 10;Assert-HttpProbe $ssrfProbe @(400)
  Pass 'Web capability contract and SSRF policy smoke passed.'
}

function Test-WebAcceptance {
  $base=Get-BaseUrl
  Info 'Running live Web/Search/Research acceptance with DTF canary...'
  $searchBody=@{query='DTF news';limit=8;category='news'}|ConvertTo-Json -Compress
  try{$search=Invoke-RestMethod -Method Post -Uri ($base+'/api/web/search') -ContentType 'application/json; charset=utf-8' -Body $searchBody -TimeoutSec 60}
  catch{Emit 'BLOCKED_EXTERNAL' ('Search canary unavailable: '+$_.Exception.Message) Yellow;throw}
  if(-not $search.ok -or @($search.results).Count -lt 1){Emit 'BLOCKED_EXTERNAL' 'Search returned no usable results.' Yellow;throw 'WEB live canary has no search results.'}
  $readBody=@{url='https://dtf.ru/'}|ConvertTo-Json -Compress
  try{$read=Invoke-RestMethod -Method Post -Uri ($base+'/api/web/read') -ContentType 'application/json; charset=utf-8' -Body $readBody -TimeoutSec 90}
  catch{Emit 'BLOCKED_EXTERNAL' ('DTF read canary unavailable: '+$_.Exception.Message) Yellow;throw}
  if(-not $read.ok -or -not $read.page.text -or ([string]$read.page.text).Length -lt 200){Emit 'BLOCKED_EXTERNAL' 'DTF returned insufficient readable content.' Yellow;throw 'DTF live canary returned insufficient content.'}
  $chatBody=@{mode='smart';intent_hint='research';preset='analyze';messages=@(@{role='user';content='Show fresh news from https://dtf.ru/ and cite the retrieved sources.'})}|ConvertTo-Json -Depth 6 -Compress
  $chat=Invoke-RestMethod -Method Post -Uri ($base+'/api/chat') -ContentType 'application/json; charset=utf-8' -Body $chatBody -TimeoutSec 300
  if(-not $chat.ok -or -not $chat.message.content){Fail 'DTF research chat returned no answer.'}
  if(@($chat.sources).Count -lt 1){Fail 'DTF research chat returned no source evidence.'}
  if(([string]$chat.intent) -eq 'chat'){Fail 'DTF request was routed as plain chat instead of Web/Research.'}
  try{
    $ssrfBody=@{url='http://127.0.0.1:11434/api/tags'}|ConvertTo-Json -Compress
    Invoke-WebRequest -UseBasicParsing -Method Post -Uri ($base+'/api/web/read') -ContentType 'application/json' -Body $ssrfBody -TimeoutSec 10 -ErrorAction Stop | Out-Null
    Fail 'SSRF probe unexpectedly succeeded.'
  } catch {
    if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -ne 400){throw}
  }
  Pass 'WEB ACCEPTANCE passed: search, DTF read, evidence-backed research and SSRF blocking.'
}
function Get-AcceptanceArtifactsRoot {
  $artifacts=Join-Path $LogDir 'acceptance-artifacts'
  if(Test-Path -LiteralPath $artifacts){Remove-Item -LiteralPath $artifacts -Recurse -Force}
  New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
  return $artifacts
}
function Invoke-PlaywrightJourney([string]$BaseUrl,[string]$Token,[string]$Bootstrap,[string]$Artifacts,[string]$Network='',[switch]$DeterministicBackend){
  New-Item -ItemType Directory -Force -Path $Artifacts | Out-Null
  $tests=Join-Path $Root 'tests'
  $DockerArgs=@('run','--rm')
  if($Network){$DockerArgs+=@('--network',$Network)}
  $DockerArgs+=@('--env',"PA_BASE_URL=$BaseUrl",'--env',"PA_ADMIN_TOKEN=$Token",'--env',"PA_BOOTSTRAP_MODEL=$Bootstrap",'--env','PA_ARTIFACT_DIR=/artifacts')
  if($DeterministicBackend){$DockerArgs+=@('--env','PA_DETERMINISTIC_BACKEND=1')}
  $DockerArgs+=@('-v',"${tests}:/tests:ro",'-v',"${Artifacts}:/artifacts",'mcr.microsoft.com/playwright/python:v1.61.0-noble','bash','-lc','python -m pip install --no-cache-dir playwright==1.61.0 >/tmp/pip.log 2>&1 && python /tests/live_browser_e2e.py')
  $journey=Invoke-DockerSafe -DockerArguments $DockerArgs
  if($journey.ExitCode -ne 0){Fail "Browser journey failed for $BaseUrl"}
}
function Test-LiveBrowserJourney([string]$ArtifactsRoot) {
  $token=Get-EnvValue 'PA_ADMIN_TOKEN'
  if(-not $token){Fail 'Admin token is missing; cannot run live browser acceptance.'}
  $port=Get-EnvValue 'PA_UI_PORT';if(-not $port){$port='3100'}
  $bootstrap=Get-EnvValue 'PA_BOOTSTRAP_MODEL';if(-not $bootstrap){$bootstrap='qwen3:0.6b'}
  $artifacts=Join-Path $ArtifactsRoot 'real-runtime'
  Info 'Running real-model desktop/mobile/admin browser journeys with production CSP...'
  Write-Host '             Real model output is validated as non-empty behavior, never as an exact stochastic string.' -ForegroundColor DarkGray
  try{Invoke-PlaywrightJourney -BaseUrl "http://host.docker.internal:$port" -Token $token -Bootstrap $bootstrap -Artifacts $artifacts}
  catch{Info "Browser failure artifacts: $artifacts";throw}
  Pass 'Real-model live browser user journeys passed.'
}
function Test-DeterministicBrowserSecurity([string]$ArtifactsRoot) {
  $bootstrap=Get-EnvValue 'PA_BOOTSTRAP_MODEL';if(-not $bootstrap){$bootstrap='qwen3:0.6b'}
  $coreImage=Get-EnvValue 'PA_CORE_IMAGE';if(-not $coreImage){$coreImage='personal-agent-core:1.0.3'}
  $tests=Join-Path $Root 'tests'
  $artifacts=Join-Path $ArtifactsRoot 'deterministic-security'
  $suffix="$PID-$([System.Guid]::NewGuid().ToString('N').Substring(0,8))"
  $network="par-accept-$suffix"
  $fakeName="par-accept-fake-$suffix"
  $fakeWebName="par-accept-web-$suffix"
  $coreName="par-accept-core-$suffix"
  $testToken='par-deterministic-browser-token'
  Info 'Running deterministic XSS/admin browser acceptance through an isolated production Core...'
  Write-Host '             Controlled provider fixtures test exact hostile output; production runtime remains untouched.' -ForegroundColor DarkGray
  try{
    $networkCreate=Invoke-DockerSafe -DockerArguments @('network','create',$network) -Quiet
    if($networkCreate.ExitCode -ne 0){Fail 'Could not create isolated acceptance network.'}
    $fakeStart=Invoke-DockerSafe -DockerArguments @('run','-d','--rm','--name',$fakeName,'--network',$network,'--env','PA_FAKE_HOST=0.0.0.0','-v',"${tests}:/tests:ro",$coreImage,'python','/tests/fake_ollama.py','11434') -Quiet
    if($fakeStart.ExitCode -ne 0){Fail 'Could not start deterministic provider fixture.'}
    $fakeWebStart=Invoke-DockerSafe -DockerArguments @('run','-d','--rm','--name',$fakeWebName,'--network',$network,'-v',"${tests}:/tests:ro",$coreImage,'python','/tests/fake_web.py','8000') -Quiet
    if($fakeWebStart.ExitCode -ne 0){Fail 'Could not start deterministic Web fixture.'}
    $coreStart=Invoke-DockerSafe -DockerArguments @('run','-d','--rm','--name',$coreName,'--network',$network,'--env','PA_PRODUCT_FAMILY=Personal Agent','--env','PA_PRODUCT_NAME=Personal Agent Rus','--env','PA_EDITION=rus','--env','PA_LOCALE=ru-RU','--env','PA_VERSION=1.0.0-security-fixture','--env','PA_HOST=0.0.0.0','--env','PA_PORT=8080','--env',"PA_OLLAMA_URL=http://${fakeName}:11434",'--env',"PA_SEARXNG_URL=http://${fakeWebName}:8000",'--env',"PA_BROWSER_URL=http://${fakeWebName}:8000",'--env',"PA_BOOTSTRAP_MODEL=$bootstrap",'--env',"PA_ADMIN_TOKEN=$testToken",'--env','PA_DB=/data/security-fixture.db',$coreImage) -Quiet
    if($coreStart.ExitCode -ne 0){Fail 'Could not start isolated production Core security fixture.'}
    $ready=$false
    for($i=1;$i -le 60;$i++){
      $probe=Invoke-DockerSafe -DockerArguments @('exec',$coreName,'python','-c',"import json,urllib.request; x=json.load(urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=3)); raise SystemExit(0 if x.get('ready') else 1)") -Quiet
      if($probe.ExitCode -eq 0){$ready=$true;break}
      Start-Sleep -Milliseconds 500
    }
    if(-not $ready){Fail 'Isolated production Core security fixture did not become ready.'}
    Invoke-PlaywrightJourney -BaseUrl "http://${coreName}:8080" -Token $testToken -Bootstrap $bootstrap -Artifacts $artifacts -Network $network -DeterministicBackend
    Pass 'Deterministic browser security journey passed through production Core and CSP.'
  } finally {
    Invoke-DockerSafe -DockerArguments @('rm','-f',$coreName,$fakeName,$fakeWebName) -Quiet | Out-Null
    Invoke-DockerSafe -DockerArguments @('network','rm',$network) -Quiet | Out-Null
  }
}
function Test-FullAcceptance {
  Test-Runtime
  $artifacts=Get-AcceptanceArtifactsRoot
  Test-LiveBrowserJourney -ArtifactsRoot $artifacts
  Test-DeterministicBrowserSecurity -ArtifactsRoot $artifacts
  Info 'Testing Core restart persistence...'
  Invoke-Compose -ComposeArgs @('restart','core');Wait-Core;Test-Runtime
  Info 'Testing Core recovery after an intentional stop...'
  Invoke-Compose -ComposeArgs @('stop','core')
  Invoke-Compose -ComposeArgs @('up','-d','core');Wait-Core;Test-Runtime
  Pass 'FULL ACCEPTANCE passed: real inference, real-model browser, deterministic security browser, restart and recovery.'
}
function Test-ReferenceReleaseAcceptance {
  Info 'REFERENCE RELEASE ACCEPTANCE: full browser/runtime acceptance.'
  Test-FullAcceptance
  Info 'REFERENCE RELEASE ACCEPTANCE: restart all runtime services.'
  Invoke-Compose -ComposeArgs @('restart','ollama','searxng','browser','core');Wait-Ollama;Wait-WebServices;Wait-Core;Test-Runtime
  Info 'REFERENCE RELEASE ACCEPTANCE: idempotent repair without deleting named volumes.'
  Invoke-Compose -ComposeArgs @('up','-d','--build','--force-recreate','--remove-orphans','ollama','searxng','browser','code-worker','core');Wait-Ollama;Wait-WebServices;Ensure-BootstrapModel;Wait-Core;Test-Runtime
  Info 'REFERENCE RELEASE ACCEPTANCE: full STOP then START.'
  Invoke-Compose -ComposeArgs @('stop')
  Invoke-Compose -ComposeArgs @('up','-d','ollama','searxng','browser');Wait-Ollama;Wait-WebServices;Ensure-BootstrapModel
  Invoke-Compose -ComposeArgs @('up','-d','--build','code-worker');Wait-CodeWorker
  Invoke-Compose -ComposeArgs @('up','-d','--build','--no-deps','--remove-orphans','core');Wait-Core;Test-Runtime
  Pass 'REFERENCE RELEASE ACCEPTANCE passed: FULL-ACCEPTANCE, RESTART, REPAIR and STOP/START.'
  Write-Host 'Next mandatory environment gate: real Windows reboot, then VERIFY.cmd.' -ForegroundColor Yellow
}

function Start-Runtime([switch]$OpenBrowser){
  $total=10
  Step 1 $total 'Environment and Docker preflight' 'Check the floor before teaching the house to think.'
  Ensure-Env;Require-Docker
  Step 2 $total 'Compose contract validation' 'Boring checks are cheaper than exciting failures.'
  Invoke-Compose -ComposeArgs @('config','--quiet');Pass 'Compose configuration is valid.'
  Step 3 $total 'Starting local AI and Web engines' 'Waking the local brain and the evidence tools.'
  Invoke-Compose -ComposeArgs @('up','-d','ollama','searxng','browser');Wait-Ollama;Wait-WebServices
  Step 4 $total 'Preparing bootstrap inference' 'This model proves the pipeline; admins choose production models.'
  Ensure-BootstrapModel
  Step 5 $total 'Starting isolated Code sandbox' 'Code is valuable, but it may not take down Chat/Web/Files if its image has a problem.'
  $codeReady=Start-CodeWorkerOptional
  Step 6 $total 'Building and starting Personal Agent Rus Core' 'Now assembling the part users are actually supposed to see.'
  Invoke-Compose -ComposeArgs @('up','-d','--build','--no-deps','--remove-orphans','core')
  Step 7 $total 'Readiness checks' 'Checking the pulse. Here it is measured in HTTP status codes.'
  Wait-Core
  Step 8 $total 'End-to-end smoke verification' 'We ask it a real question before calling anything ready.'
  Test-Runtime
  Step 9 $total 'Capability safety smoke' 'Web evidence is mandatory; Code is verified when its isolated worker is available.'
  Test-WebInternalSmoke
  if($codeReady){$codeReady=[bool](Test-CodeInternalSmoke)}else{Warn 'Code capability is DEGRADED. Run CODE-ACCEPTANCE.cmd after fixing the worker; the rest of the product is usable.'}
  Step 10 $total 'Ready' 'Green means the local user-facing vertical slice earned it.'
  Pass 'Personal Agent Rus is ready for local use.'
  if(-not $codeReady){Warn 'Local launch completed with Code degraded; Chat/Web/Research/Files remain available.'}
  if($OpenBrowser){Start-Process ((Get-BaseUrl)+'/')}
  Finish-StepTimer
}


try{
  Set-Location $Root
  if($Action -eq 'contract'){
    Invoke-Compose -ComposeArgs @('config','--quiet')
    Invoke-Compose -ComposeArgs @('up','-d','ollama','searxng','browser')
    Invoke-Compose -ComposeArgs @('exec','-T','ollama','ollama','list')
    Invoke-Compose -ComposeArgs @('up','-d','--build','code-worker')
    Invoke-Compose -ComposeArgs @('up','-d','--build','--no-deps','--remove-orphans','core')
    Invoke-Compose -ComposeArgs @('ps')
    Invoke-Compose -ComposeArgs @('stop')
    Invoke-Compose -ComposeArgs @('restart','ollama','searxng','browser','core')
    exit 0
  }
  Ensure-Env
  switch($Action){
    'start'{Start-Runtime -OpenBrowser}
    'stop'{Require-Docker;Info 'Stopping containers without deleting data or models...';Invoke-Compose -ComposeArgs @('stop');Pass 'Stopped. Persistent volumes are preserved.'}
    'restart'{Require-Docker;Info 'Restarting required runtime...';Invoke-Compose -ComposeArgs @('restart','ollama','searxng','browser','core');Wait-Ollama;Wait-WebServices;Wait-Core;$codeReady=Start-CodeWorkerOptional;Test-Runtime;if($codeReady){$codeReady=[bool](Test-CodeInternalSmoke)};Pass 'Restart verification passed.'}
    'repair'{Require-Docker;Info 'Repairing required runtime without deleting named volumes...';Invoke-Compose -ComposeArgs @('up','-d','--build','--force-recreate','--remove-orphans','ollama','searxng','browser');Wait-Ollama;Wait-WebServices;Ensure-BootstrapModel;$codeReady=Start-CodeWorkerOptional;Invoke-Compose -ComposeArgs @('up','-d','--build','--no-deps','--force-recreate','--remove-orphans','core');Wait-Core;Test-Runtime;Test-WebInternalSmoke;if($codeReady){$codeReady=[bool](Test-CodeInternalSmoke)};Pass ("Repair verification passed. command_elapsed={0}s" -f [Math]::Round($script:TotalWatch.Elapsed.TotalSeconds,2))}
    'status'{Require-Docker;Invoke-Compose -ComposeArgs @('ps')}
    'logs'{Require-Docker;$previousErrorActionPreference=$ErrorActionPreference;try{$ErrorActionPreference='Continue';& docker.exe compose --env-file $EnvFile -f $Compose logs --tail 200 -f;$ec=$LASTEXITCODE}finally{$ErrorActionPreference=$previousErrorActionPreference};if($ec -ne 0){Fail 'Docker log stream failed.'}}
    'admin'{$token=Get-EnvValue 'PA_ADMIN_TOKEN';Write-Host '';Write-Host 'Admin token:' -ForegroundColor Yellow;Write-Host $token;Start-Process ((Get-BaseUrl)+'/admin')}
    'verify'{Require-Docker;Wait-Ollama;Wait-WebServices;Wait-Core;Test-Runtime;Test-WebInternalSmoke;$codeReady=Test-CodeWorkerReadyOnce;if($codeReady){$codeReady=[bool](Test-CodeInternalSmoke)}else{Warn 'Code capability is degraded; baseline local verification still passed.'}}
    'webverify'{Require-Docker;Wait-Ollama;Wait-WebServices;Wait-Core;Test-Runtime;Test-WebAcceptance}
    'codeverify'{Require-Docker;Wait-Ollama;Wait-WebServices;Wait-CodeWorker;Wait-Core;Test-Runtime;Test-CodeLiveAcceptance}
    'fullverify'{Require-Docker;Wait-Ollama;Wait-WebServices;Wait-CodeWorker;Wait-Core;Test-FullAcceptance;Test-CodeInternalSmoke -Strict | Out-Null}
    'releaseverify'{Require-Docker;Wait-Ollama;Wait-WebServices;Wait-CodeWorker;Wait-Core;Test-ReferenceReleaseAcceptance;Test-CodeInternalSmoke -Strict | Out-Null}
    'backup'{Require-Docker;$dir=Join-Path $Root ('backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'));New-Item -ItemType Directory -Path $dir|Out-Null;Info 'Exporting persistent volumes...';$dataBackup=Invoke-DockerSafe -DockerArguments @('run','--rm','-v','par-rus-data:/source','-v',"${dir}:/backup",'alpine:3.22','sh','-c','cd /source && tar czf /backup/par-rus-data.tgz .');if($dataBackup.ExitCode-ne 0){Fail 'Failed to backup Personal Agent data volume.'};$modelBackup=Invoke-DockerSafe -DockerArguments @('run','--rm','-v','par-rus-models:/source','-v',"${dir}:/backup",'alpine:3.22','sh','-c','cd /source && tar czf /backup/par-models.tgz .');if($modelBackup.ExitCode-ne 0){Fail 'Failed to backup model volume.'};Copy-Item -LiteralPath $EnvFile -Destination (Join-Path $dir '.env');Pass "Backup created: $dir"}
    'update'{Require-Docker;Info 'Updating runtime images and rebuilding local Core...';Invoke-Compose -ComposeArgs @('pull','--ignore-buildable');Start-Runtime}
  }
  exit 0
}catch{
  try{Finish-StepTimer}catch{}
  try{Emit 'FAIL' ("{0}: {1}" -f $_.Exception.GetType().Name,$_.Exception.Message) Red}catch{}
  try{Write-Host '';Write-Host "Log: $LogFile" -ForegroundColor Yellow}catch{}
  exit 1
}
