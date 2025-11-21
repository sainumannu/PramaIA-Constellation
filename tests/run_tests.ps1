# PramaIA Test Suite Runner - PowerShell
# Script per esecuzione test suite da PowerShell

param(
    [ValidateSet("all", "inventory", "crud", "e2e")]
    [string]$Suite = "all",
    
    [switch]$Verbose,
    [switch]$ShowOutput,
    [switch]$StopOnFailure,
    [switch]$Coverage,
    [switch]$Html
)

# Configurazione
$TestDir = "tests"
$PytestCmd = "pytest"

# Mappa suite a file
$SuiteMap = @{
    "all"       = "tests/"
    "inventory" = "tests/test_inventory.py"
    "crud"      = "tests/test_crud_operations.py"
    "e2e"       = "tests/test_e2e_pipeline.py"
}

$TestPath = $SuiteMap[$Suite]

# Costruisci argomenti pytest
$PytestArgs = @($TestPath)

# Verbosity
if ($Verbose) {
    $PytestArgs += "-vv"
} else {
    $PytestArgs += "-v"
}

# Output
if ($ShowOutput) {
    $PytestArgs += "-s"
}

# Stop on failure
if ($StopOnFailure) {
    $PytestArgs += "-x"
}

# Coverage
if ($Coverage) {
    $PytestArgs += "--cov=backend"
    $PytestArgs += "--cov-report=html"
}

# HTML Report
if ($Html) {
    $PytestArgs += "--html=test_report.html"
    $PytestArgs += "--self-contained-html"
}

# Header
Write-Host "`n" -NoNewline
Write-Host ("=" * 80)
Write-Host "  PramaIA Test Suite"
Write-Host ("=" * 80)
Write-Host "`n"
Write-Host "📋 Test Suite: $Suite"
Write-Host "📝 Command: $PytestCmd $($PytestArgs -join ' ')`n"

# Esegui pytest
& python -m $PytestCmd @PytestArgs
$ExitCode = $LASTEXITCODE

# Report
Write-Host "`n" -NoNewline
Write-Host ("=" * 80)
if ($ExitCode -eq 0) {
    Write-Host "  ✅ Tests completed successfully"
} else {
    Write-Host "  ❌ Tests failed (exit code: $ExitCode)"
}
Write-Host ("=" * 80)
Write-Host "`n"

# Additional reports
if ($Html) {
    Write-Host "📊 HTML Report: .\test_report.html"
}
if ($Coverage) {
    Write-Host "📊 Coverage Report: .\htmlcov\index.html"
}

Write-Host "`n"
exit $ExitCode
