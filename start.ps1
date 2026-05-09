$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        & py -3 -m venv .venv
    }
    else {
        $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $PythonCommand) {
            throw "Python 3.11+ was not found. Install Python or add it to PATH."
        }
        & python -m venv .venv
    }
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
& $Python samples\make_sample_workbook.py

$PortUsers = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

foreach ($ProcessId in $PortUsers) {
    Write-Host "Stopping process on port 8000: $ProcessId"
    Stop-Process -Id $ProcessId -Force
}

Write-Host ""
Write-Host "Starting RR-FE Excel Workspace..."
Write-Host "URL: http://127.0.0.1:8000/"
Write-Host "Press Ctrl+C to stop."
Write-Host ""

Start-Process "http://127.0.0.1:8000/"
& $Python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
