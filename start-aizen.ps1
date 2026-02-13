# AIZEN Quick Start Script
# This script helps you start both backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AIZEN AI Assistant - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (!(Test-Path ".\backend") -or !(Test-Path ".\frontend")) {
    Write-Host "Error: Please run this script from the Aizen project root directory" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Checking backend..." -ForegroundColor Yellow

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/4] Checking frontend..." -ForegroundColor Yellow

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Node.js not found. Please install Node.js" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/4] Checking Voice Agent..." -ForegroundColor Yellow
$agentFile = Join-Path $PSScriptRoot "backend\app\agent.py"
if (Test-Path $agentFile) {
    Write-Host "✓ Voice Agent code found." -ForegroundColor Green
}
else {
    Write-Host "✗ Voice Agent code not found." -ForegroundColor Red
}

Write-Host ""
Write-Host "[4/4] Starting servers..." -ForegroundColor Yellow
Write-Host ""

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"

# Start backend in new terminal
Write-Host "Starting backend server..." -ForegroundColor Cyan
$backendCmd = "cd '$backendDir'; .\venv\Scripts\activate; Write-Host 'Starting AIZEN Backend API...' -ForegroundColor Cyan; python -m app.main"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# Start Voice Agent in new terminal
Write-Host "Starting Voice Agent (Cloud Mode)..." -ForegroundColor Cyan
$agentCmd = "cd '$backendDir'; .\venv\Scripts\activate; Write-Host 'Starting AIZEN Voice Agent...' -ForegroundColor Cyan; python -c 'from app.agent import run_agent; run_agent()' dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $agentCmd

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in new terminal
Write-Host "Starting frontend server..." -ForegroundColor Cyan
$frontendCmd = "cd '$frontendDir'; Write-Host 'Starting AIZEN Frontend...' -ForegroundColor Cyan; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  AIZEN is starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API API: http://localhost:8001" -ForegroundColor Cyan
Write-Host "Voice Agent:    Gemini Live (Cloud)" -ForegroundColor Cyan
Write-Host "Frontend UI:    http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "NOTE: Ensure LIVEKIT_URL, API_KEY, and API_SECRET are set in backend/.env" -ForegroundColor Yellow
Write-Host ""
Write-Host "Check the new terminal windows for server logs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
