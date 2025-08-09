$dir = Join-Path -Path $PSScriptRoot -ChildPath "..\archive_to_review"
$dir = (Resolve-Path $dir -ErrorAction SilentlyContinue)
if (-not $dir) {
    Write-Host "archive_to_review not found." -ForegroundColor Yellow
    exit 0
}
Write-Host "Listing staged cleanup at: $dir" -ForegroundColor Cyan
Get-ChildItem -Recurse -Force $dir | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize
