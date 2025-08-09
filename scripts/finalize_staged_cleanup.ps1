param(
    [switch]$Force
)

$dir = Join-Path -Path $PSScriptRoot -ChildPath "..\archive_to_review"
$dir = (Resolve-Path $dir -ErrorAction SilentlyContinue)
if (-not $dir) {
    Write-Host "archive_to_review not found. Nothing to delete." -ForegroundColor Yellow
    exit 0
}

Write-Host "You are about to permanently delete: $dir" -ForegroundColor Red

if (-not $Force) {
    $answer = Read-Host "Type DELETE to confirm"
    if ($answer -ne "DELETE") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 1
    }
}

Remove-Item -Recurse -Force "$dir\*"
Write-Host "Deleted contents of $dir" -ForegroundColor Green
