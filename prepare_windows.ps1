$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
    throw 'Python Launcher (py.exe) was not found. Install Python 3.11-3.14.'
}

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    & py -3.14 -m venv .venv
    if ($LASTEXITCODE -ne 0) { & py -3.13 -m venv .venv }
    if ($LASTEXITCODE -ne 0) { & py -3.12 -m venv .venv }
    if ($LASTEXITCODE -ne 0) { & py -3.11 -m venv .venv }
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item -Force config\default.json config\config.local.json
Write-Host 'Windows environment prepared.'
