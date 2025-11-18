#!/usr/bin/env pwsh
# Script di avvio per PramaIAServer Backend

param(
    [string]$Port = "8000",
    [string]$Host = "127.0.0.1",
    [switch]$NoReload,
    [switch]$Debug
)

Write-Host "🚀 Avvio PramaIAServer Backend..." -ForegroundColor Green
Write-Host "   Porta: $Port" -ForegroundColor Gray
Write-Host "   Host: $Host" -ForegroundColor Gray

# Verifica che la directory backend esista
if (-not (Test-Path "C:\PramaIA\PramaIAServer\backend")) {
    Write-Host "❌ Directory backend non trovata: C:\PramaIA\PramaIAServer\backend" -ForegroundColor Red
    Read-Host "Premi Enter per uscire"
    exit 1
}

Set-Location "C:\PramaIA\PramaIAServer"

# Configura parametri uvicorn
$uvicornArgs = @(
    "backend.main:app"
    "--host", $Host
    "--port", $Port
)

if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

if ($Debug) {
    $uvicornArgs += "--log-level", "debug"
}

try {
    Write-Host "Comando: python -m uvicorn $($uvicornArgs -join ' ')" -ForegroundColor Yellow
    python -m uvicorn @uvicornArgs
} catch {
    Write-Host "❌ Errore avvio backend: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Suggerimenti:" -ForegroundColor Yellow
    Write-Host "   - Verifica che Python sia installato e nel PATH" -ForegroundColor Gray
    Write-Host "   - Controlla che le dipendenze siano installate: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "   - Assicurati che la porta $Port non sia già in uso" -ForegroundColor Gray
    Read-Host "Premi Enter per uscire"
}