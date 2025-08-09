param(
    [string]$App = "app.py",
    [switch]$Enhanced
)

$ErrorActionPreference = "Stop"

# Ensure Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not on PATH. Install Python 3.10+ and try again."
    exit 1
}

# Create and activate venv if not present
$venvPath = Join-Path $PSScriptRoot "..\venv_audit"  # reuse existing if present
if (-not (Test-Path $venvPath)) {
    $venvPath = Join-Path $PSScriptRoot "..\.venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment at $venvPath" -ForegroundColor Cyan
        python -m venv $venvPath
    }
}

# Activate venv
$activate = Join-Path $venvPath "Scripts\Activate.ps1"
. $activate

# Install requirements if needed
try {
    pip install --upgrade pip > $null
    if (Test-Path (Join-Path $PSScriptRoot "..\requirements.txt")) {
        Write-Host "Installing dependencies from requirements.txt" -ForegroundColor Cyan
        pip install -r (Join-Path $PSScriptRoot "..\requirements.txt")
    } else {
        Write-Host "requirements.txt not found, installing core packages" -ForegroundColor Yellow
        pip install streamlit pandas requests python-dotenv plotly
    }
}
catch {
    Write-Error "Dependency installation failed: $_"
    exit 1
}

# Choose app file
if ($Enhanced) {
    $App = "enhanced_streamlit_app.py"
}

# Verify app file
$AppPath = Join-Path $PSScriptRoot "..\$App"
if (-not (Test-Path $AppPath)) {
    Write-Error "App file not found: $AppPath"
    exit 1
}

# Run Streamlit
Write-Host "Launching Streamlit UI: $App" -ForegroundColor Green
streamlit run $AppPath
