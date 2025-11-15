# Script PowerShell per verificare che il workflow sia stato inserito correttamente

# Ottieni il token di autenticazione
Write-Host "Ottenimento token di autenticazione..." -ForegroundColor Cyan
$authResponse = Invoke-WebRequest -Uri "http://localhost:8000/auth/token/local" -Method POST -Body @{username="admin"; password="admin"} -ContentType "application/x-www-form-urlencoded"
$authData = $authResponse.Content | ConvertFrom-Json
$token = $authData.access_token
Write-Host "Token ottenuto con successo" -ForegroundColor Green

# Lista dei workflows
Write-Host "Recupero lista workflows..." -ForegroundColor Cyan
$workflowResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/workflows/" -Method GET -Headers @{Authorization="Bearer $token"}
$workflows = $workflowResponse.Content | ConvertFrom-Json

# Cerca il nostro workflow
Write-Host "Ricerca PDF Semantic Processing Pipeline..." -ForegroundColor Cyan
$pdfWorkflow = $workflows | Where-Object { $_.name -eq "PDF Semantic Processing Pipeline" }

if ($pdfWorkflow) {
    Write-Host "Workflow trovato nel database!" -ForegroundColor Green
    Write-Host "ID:" $pdfWorkflow.workflow_id -ForegroundColor White
    Write-Host "Nome:" $pdfWorkflow.name -ForegroundColor White
    Write-Host "Descrizione:" $pdfWorkflow.description -ForegroundColor White
    Write-Host "Attivo:" $pdfWorkflow.is_active -ForegroundColor White
    Write-Host "Pubblico:" $pdfWorkflow.is_public -ForegroundColor White
    
    # Dettagli workflow specifico
    Write-Host "Dettagli del workflow:" -ForegroundColor Cyan
    $detailResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/workflows/$($pdfWorkflow.workflow_id)" -Method GET -Headers @{Authorization="Bearer $token"}
    $workflowDetail = $detailResponse.Content | ConvertFrom-Json
    
    Write-Host "Nodi:" $workflowDetail.nodes.Count -ForegroundColor White
    Write-Host "Connessioni:" $workflowDetail.connections.Count -ForegroundColor White
    
    Write-Host "Verifica completata con successo!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
    
} else {
    Write-Host "Workflow non trovato nel database!" -ForegroundColor Red
    Write-Host "Workflows disponibili:" -ForegroundColor Yellow
    foreach ($wf in $workflows) {
        Write-Host "- Nome:" $wf.name "ID:" $wf.workflow_id -ForegroundColor Gray
    }
}