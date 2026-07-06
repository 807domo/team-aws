# Lambda deploy ZIP creator (Linux x86_64)
# Run: powershell -ExecutionPolicy Bypass -File .\scripts\create_lambda_zip.ps1

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "=== Lambda Deploy ZIP (Linux x86_64) ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

$TempDir = Join-Path $env:TEMP "lambda_deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
Write-Host "Temp dir: $TempDir"

Write-Host ""
Write-Host "[1/4] Installing dependencies (Linux x86_64)..." -ForegroundColor Yellow

Write-Host "  Binary packages..." -ForegroundColor Gray
$ErrorActionPreference = "Continue"
& pip install -r requirements.txt -t "$TempDir" --no-cache-dir --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.13 --implementation cp 2>$null
$ErrorActionPreference = "Continue"

Write-Host "  Pure-Python packages..." -ForegroundColor Gray
& pip install -r requirements.txt -t "$TempDir" --no-cache-dir --no-deps 2>$null

Get-ChildItem -Path $TempDir -Recurse -Filter "*.pyd" -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host "  Done" -ForegroundColor Green

Write-Host "[2/4] Copying application code..." -ForegroundColor Yellow

Copy-Item "main.py" -Destination $TempDir
Copy-Item "app" -Destination "$TempDir\app" -Recurse

if (Test-Path "migrations") {
    Copy-Item "migrations" -Destination "$TempDir\migrations" -Recurse
}

Write-Host "[3/4] Cleaning up..." -ForegroundColor Yellow

Get-ChildItem -Path $TempDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path $TempDir -Recurse -Filter "*.dll" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -Path $TempDir -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host "[4/4] Creating ZIP..." -ForegroundColor Yellow

$ZipPath = Join-Path $ProjectRoot "lambda_deploy.zip"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Add-Type -Assembly "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $ZipPath)

$ZipSize = (Get-Item $ZipPath).Length / 1MB
Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "ZIP: $ZipPath"
Write-Host "Size: $([math]::Round($ZipSize, 1)) MB"

if ($ZipSize -gt 50) {
    Write-Host "WARNING: ZIP > 50MB. Need S3 upload." -ForegroundColor Red
}
else {
    Write-Host ""
    Write-Host "Next: Lambda console -> EhimeAI2026-api -> Code -> Upload from -> .zip file" -ForegroundColor Cyan
}

Remove-Item $TempDir -Recurse -Force
Write-Host "Cleanup done"
