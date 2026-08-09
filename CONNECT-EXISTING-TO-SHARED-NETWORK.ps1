$ErrorActionPreference = 'Stop'
$network = 'local-ai-network'
$containers = @('par-rus-core','par-rus-code-worker','par-rus-browser')
docker network inspect $network *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Network '$network' does not exist. Start local-ai first."
}
foreach ($c in $containers) {
    docker inspect $c *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Container not found: $c"
        continue
    }
    docker network connect $network $c 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] connected $c -> $network" -ForegroundColor Green
    } else {
        Write-Host "[INFO] $c is probably already connected to $network"
    }
}
Write-Host ""
Write-Host "Shared service DNS from connected containers:"
Write-Host "  http://ollama:11434"
Write-Host "  http://searxng:8080"
Write-Host "  http://whisper:9000"
Write-Host "  http://speaches:8000"
Write-Host "  http://comfyui:8188"
