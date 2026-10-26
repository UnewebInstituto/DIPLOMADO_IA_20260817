# Ejecuta este script UNA VEZ dentro de la carpeta donde está docker-compose.yml.
# Genera .env (con secretos aleatorios) y searxng-settings.yml.

function Nuevo-Secreto { -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) }) }

if (Test-Path ".env") {
    Write-Host "Ya existe .env; no se sobrescribe. Bórralo si quieres regenerarlo." -ForegroundColor Yellow
    exit 1
}

$apiKey   = Nuevo-Secreto   # La que pegarás en n8n (campo "API key")
$regToken = Nuevo-Secreto   # Token de registro del runner
$runKey   = Nuevo-Secreto   # Clave entre la API y el runner

$env = @"
SANDBOX_API_KEYS=$apiKey
SANDBOX_API_RUNNER_REGISTRATION_TOKEN=$regToken
SANDBOX_API_RUNNER_API_KEY=$runKey

SANDBOX_RUNNER_API_KEYS=$runKey
SANDBOX_RUNNER_REGISTRATION_TOKEN=$regToken

SEARXNG_SECRET=$(Nuevo-Secreto)
"@

$settings = @"
use_default_settings: true
search:
  formats:
    - html
    - json
"@

# UTF-8 sin BOM, para que Compose lea bien la primera variable
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText("$PWD\.env", $env, $utf8)
[System.IO.File]::WriteAllText("$PWD\searxng-settings.yml", $settings, $utf8)

Write-Host ""
Write-Host "Listo. Archivos creados: .env y searxng-settings.yml" -ForegroundColor Green
Write-Host "API key para n8n (SANDBOX_API_KEYS):" -ForegroundColor Cyan
Write-Host $apiKey
