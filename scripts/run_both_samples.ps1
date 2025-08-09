param(
    [string]$PythonExe = "python",
    [string]$Recipient = $env:TEST_RECIPIENT_EMAIL
)

if (-not $Recipient) {
    $Recipient = "tripathy.anamay23@gmail.com"
}

Write-Host "Using recipient: $Recipient" -ForegroundColor Cyan
$env:TEST_RECIPIENT_EMAIL = $Recipient

& $PythonExe -u "tools/run_both_samples.py"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "run_both_samples.py exited with code $LASTEXITCODE"
}
