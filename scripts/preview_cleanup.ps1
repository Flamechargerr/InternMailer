param(
    [string]$Staging = "archive_to_review"
)

$ErrorActionPreference = "Stop"

function Ensure-Dir($path) {
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Force -Path $path | Out-Null }
}

# 1) Create staging directory
Ensure-Dir $Staging
Write-Host "Staging redundant files to: $Staging" -ForegroundColor Cyan
try { $resolved = Resolve-Path -LiteralPath $Staging -ErrorAction SilentlyContinue; if ($resolved) { Write-Host "Resolved to: $resolved" -ForegroundColor DarkCyan } } catch {}

# 2) Move logs
try {
    $logs = Get-ChildItem -Path . -Include *.log -Recurse -ErrorAction SilentlyContinue
    if ($logs) {
        Write-Host ("Moving {0} log files" -f $logs.Count)
        $logs | Move-Item -Destination $Staging -Force
    } else { Write-Host "No logs found" }
}
catch { Write-Warning "Failed moving logs: $_" }

# 3) Move extra READMEs / reports / summaries
try {
    $docs = Get-ChildItem -Path . -Recurse -Include "README_*.md", "*REPORT*.md", "*SUMMARY*.md" -ErrorAction SilentlyContinue
    if ($docs) {
        Write-Host ("Moving {0} docs (reports/summaries)" -f $docs.Count)
        $docs | Move-Item -Destination $Staging -Force
    } else { Write-Host "No extra docs found" }
}
catch { Write-Warning "Failed moving extra docs: $_" }

# 4) Move professor CSV snapshots (preserve core curated sets)
$coreKeep = @(
    "professors_database.csv",
    "professors_final.csv",
    "professors_formatted.csv",
    "professors_properly_cleaned.csv",
    "extended_professors_database.csv"
)
try {
    $csvs = Get-ChildItem -Path . -Recurse -Include "*professor*.csv", "*professors*.csv" -ErrorAction SilentlyContinue |
        Where-Object { $coreKeep -notcontains $_.Name }
    if ($csvs) {
        Write-Host ("Moving {0} professor CSV snapshots" -f $csvs.Count)
        $csvs | Move-Item -Destination $Staging -Force
    } else { Write-Host "No redundant professor CSVs found" }
}
catch { Write-Warning "Failed moving professor CSV snapshots: $_" }

# 5) Move __pycache__ and backup directories (cleanup_backup*)
try {
    $dirs = Get-ChildItem -Path . -Directory -Recurse -Include "__pycache__", "cleanup_backup*" -ErrorAction SilentlyContinue
    foreach ($d in $dirs) {
        $dest = Join-Path $Staging ($d.FullName -replace ":", "_").Substring($PWD.Path.Length).TrimStart('\\')
        Ensure-Dir (Split-Path $dest)
        Write-Host ("Moving directory: {0}" -f $d.FullName)
        Move-Item -Path $d.FullName -Destination $Staging -Force
    }
    if (-not $dirs) { Write-Host "No __pycache__/backup directories found" }
}
catch { Write-Warning "Failed moving cached/backup directories: $_" }

Write-Host "Done. Review staged content in: $Staging" -ForegroundColor Green
Write-Host "If satisfied, you may delete that folder or selectively restore files." -ForegroundColor Yellow
