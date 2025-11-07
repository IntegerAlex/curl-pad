# Install curlpad binary onto PATH (Windows)
# Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

param(
    [string]$Prefix = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Info { Write-ColorOutput Cyan $args }

# Usage
if ($Help) {
    Write-Output @"
Usage: $($MyInvocation.MyCommand.Name) [-Prefix DIR]

Options:
  -Prefix DIR   Install to DIR (default: `$env:LOCALAPPDATA\Programs\curlpad)
  -Help         Show this help message

Examples:
  .\install_curlpad.ps1
  .\install_curlpad.ps1 -Prefix C:\Tools\curlpad
"@
    exit 0
}

# Configuration
$REPO_URL = "https://github.com/IntegerAlex/curl-pad"
$BINARY_URL = "https://github.com/IntegerAlex/curl-pad/releases/latest/download/curlpad.exe"

if ($Prefix) {
    $INSTALL_DIR = $Prefix
} else {
    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Programs\curlpad"
}

$BINARY_PATH = Join-Path $INSTALL_DIR "curlpad.exe"

Write-Output ""
Write-Info "curlpad installer"
Write-Info "A simple curl editor for the command line"
Write-Output ""
Write-Output "Author:  Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>"
Write-Output "License: GPL-3.0-or-later"
Write-Output "Repo:    $REPO_URL"
Write-Output ""
Write-Info "Installing curlpad..."
Write-Output ""

# Check if running on Windows
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "[ERROR] PowerShell 5.0 or later is required."
    exit 1
}

# Check dependencies
if (-not (Get-Command curl -ErrorAction SilentlyContinue)) {
    Write-Error "[ERROR] curl is required but not installed."
    Write-Output "Install curl: https://curl.se/windows/"
    exit 1
}

# Create install directory
Write-Output "Creating install directory: $INSTALL_DIR"
New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null

# Download binary
Write-Output "Downloading curlpad binary..."
try {
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $BINARY_URL -OutFile $BINARY_PATH -UseBasicParsing
    Write-Success "[SUCCESS] Downloaded curlpad.exe"
} catch {
    Write-Error "[ERROR] Failed to download binary from $BINARY_URL"
    Write-Output "You can manually download from: $REPO_URL/releases"
    exit 1
}

Write-Success "[SUCCESS] curlpad installed to $BINARY_PATH"
Write-Output ""

# Check if directory is on PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathArray = $currentPath -split ';' | Where-Object { $_ -ne '' }

if ($pathArray -contains $INSTALL_DIR) {
    Write-Success "[OK] $INSTALL_DIR is on your PATH"
} else {
    Write-Warning "[WARNING] $INSTALL_DIR is not on your PATH."
    Write-Output ""
    Write-Output "Would you like to add it to your PATH? (Y/N)"
    $response = Read-Host
    
    if ($response -eq 'Y' -or $response -eq 'y') {
        try {
            $newPath = $currentPath
            if ($newPath -and -not $newPath.EndsWith(';')) {
                $newPath += ';'
            }
            $newPath += $INSTALL_DIR
            
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            Write-Success "[SUCCESS] Added $INSTALL_DIR to PATH"
            Write-Warning "[NOTE] You may need to restart your terminal for the PATH change to take effect."
        } catch {
            Write-Error "[ERROR] Failed to add to PATH: $_"
            Write-Output ""
            Write-Output "You can manually add it by:"
            Write-Output "1. Open System Properties > Environment Variables"
            Write-Output "2. Edit User PATH variable"
            Write-Output "3. Add: $INSTALL_DIR"
        }
    } else {
        Write-Output ""
        Write-Output "To use curlpad, either:"
        Write-Output "1. Add $INSTALL_DIR to your PATH manually"
        Write-Output "2. Or run: $BINARY_PATH"
    }
}

Write-Output ""
Write-Success "Installation complete! Run 'curlpad' to get started."
Write-Output ""

