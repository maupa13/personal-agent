$ErrorActionPreference = 'Stop'

$base = 'http://127.0.0.1:3100'

function Assert-True {
    param(
        [Parameter(Mandatory=$true)][bool]$Condition,
        [Parameter(Mandatory=$true)][string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

Write-Host '[1/5] Runtime auth contract'
$providers = Invoke-RestMethod -Uri "$base/api/auth/providers" -Method Get
Assert-True ($providers.auth_mode -eq 'accounts') 'AUTH-001: auth_mode is not accounts'
Assert-True ($providers.registration_policy -eq 'open') 'AUTH-001: registration policy is not open'
Assert-True ([bool]$providers.providers.password.enabled) 'AUTH-001: password auth is not enabled'
Write-Host '[PASS] AUTH-001 accounts/open active'

Write-Host '[2/5] Anonymous root must serve auth surface'
$root = Invoke-WebRequest -UseBasicParsing -Uri "$base/" -Method Get
Assert-True ($root.StatusCode -eq 200) 'AUTH-002: root did not return HTTP 200'

# Structural check only: avoid localized strings so Windows PowerShell 5.1
# cannot break this test because of source-file encoding.
$looksLikeAuth = (
    ($root.Content -match '(?i)<form') -and
    (
        ($root.Content -match '(?i)type\s*=\s*["'']password["'']') -or
        ($root.Content -match '(?i)/api/auth/login') -or
        ($root.Content -match '(?i)/login') -or
        ($root.Content -match '(?i)/register')
    )
)
Assert-True $looksLikeAuth 'AUTH-002: anonymous root does not look like an authentication surface'
Write-Host '[PASS] AUTH-002 root is auth-gated'

Write-Host '[3/5] Anonymous user data access must be rejected'
try {
    Invoke-WebRequest -UseBasicParsing -Uri "$base/api/conversations" -Method Get -ErrorAction Stop | Out-Null
    throw 'AUTH-003: anonymous conversations unexpectedly allowed'
}
catch {
    $response = $_.Exception.Response
    if ($null -eq $response) {
        throw
    }

    $status = [int]$response.StatusCode
    Assert-True ($status -eq 401) "AUTH-003: expected HTTP 401, got $status"
}
Write-Host '[PASS] AUTH-003 anonymous user API denied'

Write-Host '[4/5] VK ID capability state must be explicit'
Assert-True ($null -ne $providers.providers.vk_id) 'AUTH-004: VK ID provider state missing'
Assert-True ($null -ne $providers.providers.vk_id.configured) 'AUTH-004: VK ID configured state missing'
Assert-True ($null -ne $providers.providers.vk_id.enabled) 'AUTH-004: VK ID enabled state missing'
Write-Host ("[PASS] AUTH-004 VK ID configured={0} enabled={1}" -f `
    $providers.providers.vk_id.configured, `
    $providers.providers.vk_id.enabled)

Write-Host '[5/5] Health must remain independent of auth'
$health = Invoke-RestMethod -Uri "$base/api/health" -Method Get
Assert-True ([bool]$health.ready) 'AUTH-005: health is not ready'
Write-Host '[PASS] AUTH-005 health ready'

Write-Host ''
Write-Host 'AUTH ACCOUNTS FOUNDATION PASS' -ForegroundColor Green
