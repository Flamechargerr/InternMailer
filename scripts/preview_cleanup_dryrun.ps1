param(
    [string]$Staging = "archive_to_review"
)

$ErrorActionPreference = "Stop"

Write-Host "Cleanup Preview (DRY-RUN)" -ForegroundColor Cyan
Write-Host "No files will be moved or deleted." -ForegroundColor Yellow

function List-Matches($title, $items) {
    if ($items -and $items.Count -gt 0) {
        Write-Host ("`n== {0} ==" -f $title) -ForegroundColor Green
        Write-Host ("Count: {0}" -f $items.Count)
        foreach ($i in $items) { Write-Host (" - {0}" -f $i.FullName) }
    } else {
        Write-Host ("`n== {0} ==" -f $title) -ForegroundColor Green
        Write-Host "None found"
    }
}

# 1) Logs
$logs = Get-ChildItem -Path . -Include *.log -Recurse -ErrorAction SilentlyContinue
List-Matches "Log files (*.log)" $logs

# 2) Extra README/report/summary docs
$docs = Get-ChildItem -Path . -Recurse -Include "README_*.md", "*REPORT*.md", "*SUMMARY*.md" -ErrorAction SilentlyContinue
List-Matches "Extra docs (README_*, *REPORT*, *SUMMARY*)" $docs

# 3) Professor CSV snapshots (excluding primary curated sets)
$coreKeep = @(
    "professors_database.csv",
    "professors_final.csv",
    "professors_formatted.csv",
    "professors_properly_cleaned.csv",
    "extended_professors_database.csv"
)
$profCsvs = Get-ChildItem -Path . -Recurse -Include "*professor*.csv", "*professors*.csv" -ErrorAction SilentlyContinue |
    Where-Object { $coreKeep -notcontains $_.Name }
List-Matches "Professor CSV snapshots (candidates to stage)" $profCsvs

# 4) __pycache__ and cleanup_backup* directories
$dirs = Get-ChildItem -Path . -Directory -Recurse -Include "__pycache__", "cleanup_backup*" -ErrorAction SilentlyContinue
List-Matches "Cache/backup directories (candidates to stage)" $dirs

# 5) Duplicate venv directories
$venvs = Get-ChildItem -Path . -Directory -Recurse -Include "venv", ".venv", "venv_dev" -ErrorAction SilentlyContinue
List-Matches "Virtual env directories (candidates to delete after confirmation)" $venvs

# 6) Duplicate .env files
$envs = Get-ChildItem -Path . -Recurse -Include ".env" -ErrorAction SilentlyContinue
List-Matches "Duplicate .env files (review to keep only root)" $envs

Write-Host "`nReview the above lists. To actually stage files, use scripts/preview_cleanup.ps1 (moves to $Staging)." -ForegroundColor Yellow
