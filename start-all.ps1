# PramaIA - Script di avvio completo (basato su PramaIA-Commons)
# Avvia tutti i servizi dell'ecosistema PramaIA con configurazione centralizzata

param(
    [string]$PDKLogLevel = "INFO",
    [switch]$Verbose,
    [switch]$SkipDependencyCheck,
    [string]$ConfigFile = "PramaIAServer\.env"
)

Write-Host "🚀 PramaIA - Avvio completo dell'ecosistema" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Controllo prerequisiti (se non saltato)
if (-not $SkipDependencyCheck) {
    Write-Host "🔍 Verifica prerequisiti..." -ForegroundColor Cyan
    
    # Verifica Node.js per PDK
    try {
        $nodeVersion = node --version 2>$null
        Write-Host "   ✓ Node.js: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Node.js non trovato (richiesto per PDK Server)" -ForegroundColor Red
    }
    
    # Verifica Python
    try {
        $pythonVersion = python --version 2>$null
        Write-Host "   ✓ Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Python non trovato" -ForegroundColor Red
    }
    
    # Verifica NPM (per frontend)
    try {
        $npmVersion = npm --version 2>$null
        Write-Host "   ✓ NPM: $npmVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ NPM non trovato (richiesto per Frontend React)" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Funzione per caricare variabili d'ambiente dal file .env (migliorata)
function Load-EnvFile {
    param([string]$EnvFilePath)
    
    if (Test-Path $EnvFilePath) {
        Write-Host "📁 Caricamento configurazioni da: $EnvFilePath" -ForegroundColor Yellow
        $envContent = Get-Content $EnvFilePath
        $loadedVars = 0
        
        foreach ($line in $envContent) {
            # Ignora linee vuote e commenti
            if ($line -match '^\s*#' -or $line -match '^\s*$') { continue }
            
            # Pattern per variabili d'ambiente (supporta valori con spazi e quote)
            if ($line -match '^([^#][^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                
                # Rimuovi quote se presenti
                if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                
                [Environment]::SetEnvironmentVariable($name, $value, [EnvironmentVariableTarget]::Process)
                if ($Verbose) {
                    Write-Host "   ✓ $name=$value" -ForegroundColor Gray
                }
                $loadedVars++
            }
        }
        
        Write-Host "   📊 Caricate $loadedVars variabili d'ambiente" -ForegroundColor Green
    } else {
        Write-Host "⚠️  File .env non trovato: $EnvFilePath" -ForegroundColor Yellow
        Write-Host "   💡 Utilizzo configurazioni predefinite" -ForegroundColor Gray
    }
}

# Carica configurazioni dal file specificato
if (Test-Path $ConfigFile) {
    Load-EnvFile $ConfigFile
} else {
    Write-Host "⚠️  File configurazione non trovato: $ConfigFile" -ForegroundColor Yellow
    Write-Host "   💡 Utilizzo configurazioni predefinite" -ForegroundColor Gray
}

# Configurazioni con supporto per più servizi (basato su documentazione Commons)
$BACKEND_PORT = [Environment]::GetEnvironmentVariable("BACKEND_PORT") ?? "8000"
$FRONTEND_PORT = [Environment]::GetEnvironmentVariable("FRONTEND_PORT") ?? "3000"
$PDK_SERVER_PORT = [Environment]::GetEnvironmentVariable("PDK_SERVER_PORT") ?? "3001"
$PLUGIN_PDF_MONITOR_PORT = [Environment]::GetEnvironmentVariable("PLUGIN_PDF_MONITOR_PORT") ?? "8001"
$VECTORSTORE_SERVICE_PORT = [Environment]::GetEnvironmentVariable("VECTORSTORE_SERVICE_PORT") ?? "8090"
$LOG_SERVICE_PORT = [Environment]::GetEnvironmentVariable("LOG_SERVICE_PORT") ?? "8081"
$RECONCILIATION_SERVICE_PORT = [Environment]::GetEnvironmentVariable("RECONCILIATION_SERVICE_PORT") ?? "8091"

# URL calcolati automaticamente
$BACKEND_BASE_URL = [Environment]::GetEnvironmentVariable("BACKEND_BASE_URL") ?? "http://localhost:$BACKEND_PORT"
$FRONTEND_BASE_URL = [Environment]::GetEnvironmentVariable("FRONTEND_BASE_URL") ?? "http://localhost:$FRONTEND_PORT"
$PDK_SERVER_BASE_URL = [Environment]::GetEnvironmentVariable("PDK_SERVER_BASE_URL") ?? "http://localhost:$PDK_SERVER_PORT"

Write-Host ""
Write-Host "📊 Configurazioni attive:" -ForegroundColor Cyan
Write-Host "   Backend FastAPI:    $BACKEND_BASE_URL" -ForegroundColor White
Write-Host "   Frontend React:     $FRONTEND_BASE_URL" -ForegroundColor White
Write-Host "   PDK Server:         $PDK_SERVER_BASE_URL" -ForegroundColor White
Write-Host "   PDF Monitor:        http://localhost:$PLUGIN_PDF_MONITOR_PORT" -ForegroundColor White
Write-Host "   VectorStore:        http://localhost:$VECTORSTORE_SERVICE_PORT" -ForegroundColor White
Write-Host "   Log Service:        http://localhost:$LOG_SERVICE_PORT" -ForegroundColor White
Write-Host "   Reconciliation:     http://localhost:$RECONCILIATION_SERVICE_PORT" -ForegroundColor White
Write-Host "   PDK Log Level:      $PDKLogLevel" -ForegroundColor White
Write-Host ""

# Funzione per avviare un servizio in background (migliorata)
function Start-Service {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Command,
        [string]$Icon = "🟢",
        [int]$StartupDelay = 2,
        [switch]$Critical = $false
    )
    
    Write-Host "$Icon Avvio $Name..." -ForegroundColor Green
    
    if (Test-Path $Path) {
        # Imposta variabili d'ambiente per il servizio
        $env:PDK_LOG_LEVEL = $PDKLogLevel
        $env:BACKEND_PORT = $BACKEND_PORT
        $env:FRONTEND_PORT = $FRONTEND_PORT
        $env:PDK_SERVER_PORT = $PDK_SERVER_PORT
        
        $job = Start-Job -ScriptBlock {
            param($workDir, $cmd, $logLevel, $backendPort, $frontendPort, $pdkPort, $verbose)
            
            Set-Location $workDir
            
            # Imposta variabili d'ambiente nel job
            $env:PDK_LOG_LEVEL = $logLevel
            $env:BACKEND_PORT = $backendPort
            $env:FRONTEND_PORT = $frontendPort
            $env:PDK_SERVER_PORT = $pdkPort
            $env:BACKEND_BASE_URL = "http://localhost:$backendPort"
            $env:FRONTEND_BASE_URL = "http://localhost:$frontendPort"
            $env:PDK_SERVER_BASE_URL = "http://localhost:$pdkPort"
            
            if ($verbose) {
                Write-Output "Avvio comando: $cmd"
                Write-Output "Directory: $(Get-Location)"
                Write-Output "PDK_LOG_LEVEL: $env:PDK_LOG_LEVEL"
            }
            
            try {
                Invoke-Expression $cmd
            } catch {
                Write-Error "Errore nell'avvio del servizio: $($_.Exception.Message)"
                throw
            }
        } -ArgumentList $Path, $Command, $PDKLogLevel, $BACKEND_PORT, $FRONTEND_PORT, $PDK_SERVER_PORT, $Verbose
        
        Write-Host "   ✓ $Name avviato (Job ID: $($job.Id))" -ForegroundColor Gray
        
        # Attendi startup del servizio
        if ($StartupDelay -gt 0) {
            Start-Sleep -Seconds $StartupDelay
        }
        
        return $job
    } else {
        $message = "   ❌ Percorso non trovato: $Path"
        if ($Critical) {
            Write-Host $message -ForegroundColor Red
            Write-Host "   🚨 ERRORE CRITICO: Servizio essenziale non disponibile!" -ForegroundColor Red
        } else {
            Write-Host $message -ForegroundColor Yellow
        }
        return $null
    }
}

# Array per tenere traccia dei job avviati
$jobs = @()
$criticalServices = 0
$optionalServices = 0

Write-Host "🔄 Avvio servizi in sequenza..." -ForegroundColor Cyan
Write-Host ""

# 1. Avvio PDK Server (Critico)
Write-Host "1️⃣  PDK Server (Critico)" -ForegroundColor Magenta
if (Test-Path "PramaIA-PDK\server") {
    $pdkJob = Start-Service -Name "PDK Server" -Path "PramaIA-PDK\server" -Command "node plugin-api-server.js" -Icon "🔌" -StartupDelay 3 -Critical
    if ($pdkJob) { 
        $jobs += $pdkJob
        $criticalServices++
    }
} else {
    Write-Host "⚠️  PDK Server non trovato in PramaIA-PDK\server" -ForegroundColor Yellow
}

# 2. Avvio Backend FastAPI (Critico)
Write-Host "2️⃣  Backend FastAPI (Critico)" -ForegroundColor Magenta
if (Test-Path "PramaIAServer") {
    $backendJob = Start-Service -Name "Backend FastAPI" -Path "PramaIAServer" -Command "python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT" -Icon "🐍" -StartupDelay 5 -Critical
    if ($backendJob) { 
        $jobs += $backendJob
        $criticalServices++
    }
} elseif (Test-Path "backend") {
    $backendJob = Start-Service -Name "Backend FastAPI" -Path "." -Command "python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT" -Icon "🐍" -StartupDelay 5 -Critical
    if ($backendJob) { 
        $jobs += $backendJob
        $criticalServices++
    }
} else {
    Write-Host "⚠️  Backend non trovato" -ForegroundColor Red
}

# 3. Avvio Frontend React (Critico)
Write-Host "3️⃣  Frontend React (Critico)" -ForegroundColor Magenta
if (Test-Path "PramaIAServer\frontend\client") {
    $frontendJob = Start-Service -Name "Frontend React" -Path "PramaIAServer\frontend\client" -Command "npm start" -Icon "⚛️" -StartupDelay 3 -Critical
    if ($frontendJob) { 
        $jobs += $frontendJob
        $criticalServices++
    }
} elseif (Test-Path "frontend\client") {
    $frontendJob = Start-Service -Name "Frontend React" -Path "frontend\client" -Command "npm start" -Icon "⚛️" -StartupDelay 3 -Critical
    if ($frontendJob) { 
        $jobs += $frontendJob
        $criticalServices++
    }
} else {
    Write-Host "⚠️  Frontend non trovato" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔄 Avvio servizi opzionali..." -ForegroundColor Cyan
Write-Host ""

# 4. Avvio VectorStore Service (Opzionale)
Write-Host "4️⃣  VectorStore Service (Opzionale)" -ForegroundColor Blue
if (Test-Path "PramaIA-VectorstoreService") {
    $vectorJob = Start-Service -Name "VectorStore Service" -Path "PramaIA-VectorstoreService" -Command "python main.py" -Icon "🗄️" -StartupDelay 2
    if ($vectorJob) { 
        $jobs += $vectorJob
        $optionalServices++
    }
} else {
    Write-Host "⚠️  VectorStore Service non trovato" -ForegroundColor Yellow
}

# 5. Avvio PDF Monitor Agent (Opzionale)
Write-Host "5️⃣  PDF Monitor Agent (Opzionale)" -ForegroundColor Blue
if (Test-Path "PramaIA-Agents\document-folder-monitor-agent") {
    $monitorJob = Start-Service -Name "PDF Monitor Agent" -Path "PramaIA-Agents\document-folder-monitor-agent" -Command "python main.py" -Icon "📄" -StartupDelay 2
    if ($monitorJob) { 
        $jobs += $monitorJob
        $optionalServices++
    }
} else {
    Write-Host "⚠️  PDF Monitor Agent non trovato" -ForegroundColor Yellow
}

# 6. Avvio Log Service (Opzionale)
Write-Host "6️⃣  Log Service (Opzionale)" -ForegroundColor Blue
if (Test-Path "PramaIA-LogService") {
    $logJob = Start-Service -Name "Log Service" -Path "PramaIA-LogService" -Command "python main.py" -Icon "📝" -StartupDelay 2
    if ($logJob) { 
        $jobs += $logJob
        $optionalServices++
    }
} else {
    Write-Host "⚠️  Log Service non trovato" -ForegroundColor Yellow
}

# 7. Avvio Reconciliation Service (Opzionale)
Write-Host "7️⃣  Reconciliation Service (Opzionale)" -ForegroundColor Blue
if (Test-Path "PramaIA-Reconciliation") {
    $reconJob = Start-Service -Name "Reconciliation Service" -Path "PramaIA-Reconciliation" -Command "python main.py" -Icon "🔄" -StartupDelay 2
    if ($reconJob) { 
        $jobs += $reconJob
        $optionalServices++
    }
} else {
    Write-Host "⚠️  Reconciliation Service non trovato" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Avvio completato!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "📊 Riepilogo servizi:" -ForegroundColor Cyan
Write-Host "   🔴 Servizi critici:   $criticalServices/3" -ForegroundColor White
Write-Host "   🟡 Servizi opzionali: $optionalServices/4" -ForegroundColor White
Write-Host "   📈 Totale processi:   $($jobs.Count)" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Accessi diretti:" -ForegroundColor Cyan
Write-Host "   📱 Frontend:          $FRONTEND_BASE_URL" -ForegroundColor White
Write-Host "   🔧 API Backend:       $BACKEND_BASE_URL/docs" -ForegroundColor White
Write-Host "   🔌 PDK Server:        $PDK_SERVER_BASE_URL" -ForegroundColor White
Write-Host "   🗄️  VectorStore:       http://localhost:$VECTORSTORE_SERVICE_PORT" -ForegroundColor White
Write-Host "   📝 Log Service:       http://localhost:$LOG_SERVICE_PORT" -ForegroundColor White
Write-Host ""

# Controllo salute servizi critici
if ($criticalServices -lt 3) {
    Write-Host "⚠️  ATTENZIONE: Non tutti i servizi critici sono stati avviati!" -ForegroundColor Red
    Write-Host "   Verifica i percorsi e le dipendenze dei servizi mancanti." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "💡 Comandi utili:" -ForegroundColor Yellow
Write-Host "   - Ctrl+C per fermare questo script" -ForegroundColor Gray
Write-Host "   - Get-Job per vedere lo stato dei servizi" -ForegroundColor Gray
Write-Host "   - Stop-Job <ID> per fermare un servizio specifico" -ForegroundColor Gray
Write-Host "   - Remove-Job * per pulire tutti i job" -ForegroundColor Gray
Write-Host "   - .\start-all.ps1 -Verbose per output dettagliato" -ForegroundColor Gray
Write-Host "   - .\start-all.ps1 -PDKLogLevel DEBUG per debug PDK" -ForegroundColor Gray
Write-Host ""

# Attendi input dell'utente per terminare
Write-Host "🔄 Servizi in esecuzione... Premi Ctrl+C per fermare tutto" -ForegroundColor Green
Write-Host "🔄 Servizi in esecuzione... Premi Ctrl+C per fermare tutto" -ForegroundColor Green

try {
    # Mantieni lo script attivo e mostra periodicamente lo stato
    while ($true) {
        Start-Sleep -Seconds 30
        $runningJobs = $jobs | Where-Object { $_.State -eq "Running" }
        Write-Host "📊 Servizi attivi: $($runningJobs.Count)/$($jobs.Count)" -ForegroundColor Cyan
    }
} finally {
    Write-Host ""
    Write-Host "🛑 Arresto servizi..." -ForegroundColor Red
    
    # Ferma tutti i job
    $jobs | ForEach-Object {
        if ($_.State -eq "Running") {
            Write-Host "   Fermando Job $($_.Id)..." -ForegroundColor Gray
            Stop-Job $_ -PassThru | Remove-Job
        }
    }
    
    Write-Host "✅ Tutti i servizi sono stati fermati" -ForegroundColor Green
}