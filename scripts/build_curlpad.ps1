# Build a standalone curlpad binary using PyInstaller (Windows)

$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT_DIR

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "python not found"
    exit 1
}

# Activate venv if present
if (Test-Path ".venv") {
    & ".venv\Scripts\Activate.ps1"
}

# Upgrade pip and install requirements
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

# Remove existing binary if it exists (to avoid permission errors)
$binaryPath = Join-Path $ROOT_DIR "dist\curlpad.exe"
if (Test-Path $binaryPath) {
    Write-Host "Removing existing binary: $binaryPath"
    
    # Try to kill any running processes first
    $processes = Get-Process | Where-Object { $_.Path -eq $binaryPath -or $_.Name -eq "curlpad" } -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "Found running curlpad processes, attempting to close them..."
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }
    
    try {
        # Try multiple times with delays
        $maxRetries = 5
        $retryCount = 0
        while ($retryCount -lt $maxRetries) {
            try {
                Remove-Item -Path $binaryPath -Force -ErrorAction Stop
                break
            } catch {
                $retryCount++
                if ($retryCount -lt $maxRetries) {
                    Write-Host "Retry $retryCount/$maxRetries: Waiting before retry..."
                    Start-Sleep -Milliseconds 500
                } else {
                    throw
                }
            }
        }
    } catch {
        Write-Warning "Could not remove existing binary (may be in use): $_"
        Write-Host "Please close any running instances of curlpad.exe and try again."
        Write-Host "Or run: Remove-Item -Path '$binaryPath' -Force"
        exit 1
    }
}

# Build using spec file
Write-Host "Building binary..."
python -m PyInstaller --clean curlpad.spec

$outputPath = Join-Path $ROOT_DIR "dist\curlpad.exe"
if (Test-Path $outputPath) {
    Write-Host "Built binary at: $outputPath" -ForegroundColor Green
} else {
    Write-Error "Build failed - binary not found at: $outputPath"
    exit 1
}

