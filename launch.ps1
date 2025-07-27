#!/usr/bin/env powershell

Write-Host "🚀 Starting InternMailer..." -ForegroundColor Green
Write-Host ""
Write-Host "📂 Changing to InternMailer directory..." -ForegroundColor Yellow
Set-Location "C:\Users\anama\OneDrive\Desktop\internmailing\InternMailer"

Write-Host "🌐 Starting streamlit server..." -ForegroundColor Yellow
Write-Host "   URL: http://localhost:8505" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Red
Write-Host ""

try {
    streamlit run app.py --server.port=8505
} catch {
    Write-Host "❌ Error starting application: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
