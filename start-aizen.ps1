# AIZEN Integrated Start Script (Hardened Version)
# ===============================================

$ErrorActionPreference = "Continue"
$PSScriptRoot = Get-Location

# --- UI Helpers ---
function Write-Header($text) {
    Write-Host "`n====================================================" -ForegroundColor Cyan
    Write-Host "  $text"
    Write-Host "====================================================`n"
}

function Write-Step($step, $text) {
    Write-Host "[$step] $text..." -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "  [OK] $text" -ForegroundColor Green
}

function Write-Error-Msg($text) {
    Write-Host "  [ERROR] $text" -ForegroundColor Red
}

# --- Execution ---
Write-Header "AIZEN AI Assistant - Unified Startup"

# 1. Directory Validation
Write-Step "1/4" "Validating project structure"
if (!(Test-Path ".\backend") -or !(Test-Path ".\frontend")) {
    Write-Error-Msg "Error: Must be run from AIZEN root directory."
    exit 1
}
Write-Success "Project structure validated."

# 2. Dependency Checks
Write-Step "2/4" "Checking system dependencies"

# Python
try {
    $pythonVer = python --version 2>&1
    Write-Success "Python found: $pythonVer"
} catch {
    Write-Error-Msg "Python 3.11+ is required but not found."
    exit 1
}

# Node.js
try {
    $nodeVer = node --version 2>&1
    Write-Success "Node.js found: $nodeVer"
} catch {
    Write-Error-Msg "Node.js is required but not found."
    exit 1
}

# 3. Virtual Environment & Node Modules
Write-Step "3/4" "Verifying local environments"

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"

# Backend Venv
if (!(Test-Path "$backendDir\venv")) {
    Write-Error-Msg "Backend venv missing."
} else {
    Write-Success "Backend virtual environment found."
}

# Frontend Modules
if (!(Test-Path "$frontendDir\node_modules")) {
    Write-Error-Msg "Frontend node_modules missing."
} else {
    Write-Success "Frontend node_modules found."
}

# 4. Starting Services
Write-Step "4/4" "Launching services"

# Launch Backend
Write-Host "  > Launching AIZEN Backend API..." -ForegroundColor Cyan
$backendCmd = "cd `"$backendDir`"; .\venv\Scripts\activate; python -m app.main"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# Wait for backend initialization
Write-Host "  > Waiting for backend to warm up..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Launch Frontend
Write-Host "  > Launching AIZEN Frontend (Vite)..." -ForegroundColor Cyan
$frontendCmd = "cd `"$frontendDir`"; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

# Final Report
Write-Host "`n"
Write-Host "====================================================" -ForegroundColor Green
Write-Host "  AIZEN SERVICES LAUNCHED SUCCESSFULLY"
Write-Host "===================================================="
Write-Host ""
Write-Host "  ➜ Backend API: http://localhost:8001"
Write-Host "  ➜ Frontend UI: http://localhost:8080"
Write-Host ""
Write-Host "  Logs are available in the separate terminal windows."
Write-Host ""
Write-Host "Launcher session complete."
