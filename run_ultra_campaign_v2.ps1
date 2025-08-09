#!/usr/bin/env pwsh

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🚀 ULTRA IMPROVED CAMPAIGN SYSTEM V2.0 🚀" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔧 FIXES APPLIED:" -ForegroundColor Yellow
Write-Host "✅ Real 400k+ professor database" -ForegroundColor Green
Write-Host "✅ Fixed research assistant methods" -ForegroundColor Green
Write-Host "✅ Enhanced SMTP error handling" -ForegroundColor Green
Write-Host "✅ Unicode text sanitization" -ForegroundColor Green
Write-Host "✅ Smart daily limit management" -ForegroundColor Green
Write-Host "✅ Improved email personalization" -ForegroundColor Green
Write-Host "✅ Real-time progress tracking" -ForegroundColor Green
Write-Host ""

Write-Host "📊 TARGET: 95%+ success rate with proper Gmail limits" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚡ Starting campaign..." -ForegroundColor Yellow
Write-Host ""

try {
    # Run the Python script
    python ultra_improved_campaign_v2.py
    
    Write-Host ""
    Write-Host "🎉 Campaign completed! Check the results CSV file." -ForegroundColor Green
}
catch {
    Write-Host "❌ Error running campaign: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
