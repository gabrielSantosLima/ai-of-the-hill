$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python is not installed or is not available in PATH."
}

if (-not (Test-Path $RequirementsFile)) {
    throw "requirements.txt was not found at: $RequirementsFile"
}

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python virtual environment at: $VenvDir"
    python -m venv $VenvDir
}
else {
    Write-Host "Python virtual environment already exists at: $VenvDir"
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment Python executable was not found at: $VenvPython"
}

Write-Host "Upgrading pip..."
& $VenvPython -m pip install --upgrade pip

Write-Host "Installing requirements from: $RequirementsFile"
& $VenvPython -m pip install -r $RequirementsFile

Write-Host ""
Write-Host "Setup complete."
Write-Host "To activate the environment, run:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
