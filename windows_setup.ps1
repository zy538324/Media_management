# Windows Server 2025 Setup Script for Media Management with Intelligent Routing
# Run as Administrator

param(
    [switch]$InstallService,
    [switch]$UninstallService,
    [switch]$RestartService,
    [switch]$CheckStatus
)

$ErrorActionPreference = "Stop"
$ServiceName = "MediaManagement"
$ServiceDisplayName = "Media Management with Intelligent Routing"
$ServiceDescription = "Intelligent media classification and *arr routing service"
$ScriptRoot = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Media Management - Windows Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Function to check if service exists
function Test-ServiceExists {
    param([string]$Name)
    $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
    return $null -ne $service
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "[1/7] Checking Python installation..." -ForegroundColor Green
    
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "  Found: $pythonVersion" -ForegroundColor Gray
    } catch {
        Write-Host "  ERROR: Python not found in PATH" -ForegroundColor Red
        Write-Host "  Install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "[2/7] Installing Python dependencies..." -ForegroundColor Green
    
    if (Test-Path "$ScriptRoot\venv") {
        Write-Host "  Virtual environment found" -ForegroundColor Gray
        & "$ScriptRoot\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
        & "$ScriptRoot\venv\Scripts\pip.exe" install -r "$ScriptRoot\requirements.txt" --quiet
    } else {
        Write-Host "  Creating virtual environment..." -ForegroundColor Gray
        python -m venv "$ScriptRoot\venv"
        & "$ScriptRoot\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
        & "$ScriptRoot\venv\Scripts\pip.exe" install -r "$ScriptRoot\requirements.txt" --quiet
    }
    
    Write-Host "  Checking musicbrainzngs..." -ForegroundColor Gray
    & "$ScriptRoot\venv\Scripts\pip.exe" show musicbrainzngs > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Installing musicbrainzngs..." -ForegroundColor Gray
        & "$ScriptRoot\venv\Scripts\pip.exe" install musicbrainzngs==0.7.1 --quiet
    }
    
    Write-Host "  All dependencies installed" -ForegroundColor Green
}

# Function to run database migration
function Invoke-DatabaseMigration {
    Write-Host ""
    Write-Host "[3/7] Database migration..." -ForegroundColor Green
    
    $dbPath = "$ScriptRoot\media_management.db"
    $migrationPath = "$ScriptRoot\migrations\add_classification_fields.sql"
    
    if (Test-Path $dbPath) {
        # Backup database
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "$ScriptRoot\media_management.db.backup.$timestamp"
        Copy-Item $dbPath $backupPath
        Write-Host "  Database backed up to: $backupPath" -ForegroundColor Gray
        
        # Check if already migrated
        $checkQuery = "PRAGMA table_info(requests);"
        $tableInfo = sqlite3 $dbPath $checkQuery 2>&1
        
        if ($tableInfo -match "arr_service") {
            Write-Host "  Migration already applied" -ForegroundColor Yellow
        } else {
            Write-Host "  Applying migration..." -ForegroundColor Gray
            Get-Content $migrationPath | sqlite3 $dbPath
            Write-Host "  Migration completed" -ForegroundColor Green
        }
    } else {
        Write-Host "  No database found (will be created on first run)" -ForegroundColor Yellow
    }
}

# Function to update app initialization
function Update-AppInit {
    Write-Host ""
    Write-Host "[4/7] Checking blueprint registration..." -ForegroundColor Green
    
    $initPath = "$ScriptRoot\app\__init__.py"
    
    if (Test-Path $initPath) {
        $content = Get-Content $initPath -Raw
        
        if ($content -match "unified_requests_bp") {
            Write-Host "  Blueprint already registered" -ForegroundColor Green
        } else {
            Write-Host "  Adding blueprint registration..." -ForegroundColor Gray
            
            # Find where to insert (after other blueprint imports)
            $lines = Get-Content $initPath
            $insertIndex = -1
            
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i] -match "register_blueprint") {
                    $insertIndex = $i + 1
                }
            }
            
            if ($insertIndex -eq -1) {
                # No blueprints found, add at end
                $insertIndex = $lines.Count
            }
            
            $newLines = @()
            $newLines += $lines[0..($insertIndex-1)]
            $newLines += ""
            $newLines += "# Intelligent routing blueprint"
            $newLines += "from app.routes.unified_requests import unified_requests_bp"
            $newLines += "app.register_blueprint(unified_requests_bp)"
            $newLines += $lines[$insertIndex..($lines.Count-1)]
            
            $newLines | Set-Content $initPath
            Write-Host "  Blueprint registered" -ForegroundColor Green
        }
    } else {
        Write-Host "  WARNING: app/__init__.py not found" -ForegroundColor Red
    }
}

# Function to verify configuration
function Test-Configuration {
    Write-Host ""
    Write-Host "[5/7] Verifying configuration..." -ForegroundColor Green
    
    $configPath = "$ScriptRoot\config.yaml"
    
    if (Test-Path $configPath) {
        Write-Host "  config.yaml found" -ForegroundColor Green
        
        $config = Get-Content $configPath -Raw
        $warnings = @()
        
        if ($config -notmatch "TMDb:[\s\S]*api_key:\s*\S+") {
            $warnings += "TMDb API key"
        }
        if ($config -notmatch "Sonarr:[\s\S]*api_key:\s*\S+") {
            $warnings += "Sonarr API key"
        }
        if ($config -notmatch "Radarr:[\s\S]*api_key:\s*\S+") {
            $warnings += "Radarr API key"
        }
        if ($config -notmatch "Lidarr:[\s\S]*api_key:\s*\S+") {
            $warnings += "Lidarr API key"
        }
        
        if ($warnings.Count -gt 0) {
            Write-Host "  WARNING: Missing API keys:" -ForegroundColor Yellow
            foreach ($warn in $warnings) {
                Write-Host "    - $warn" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  All API keys configured" -ForegroundColor Green
        }
    } else {
        Write-Host "  ERROR: config.yaml not found" -ForegroundColor Red
        Write-Host "  Copy config.yaml.example to config.yaml and configure" -ForegroundColor Yellow
    }
}

# Function to create Windows service using NSSM
function Install-WindowsService {
    Write-Host ""
    Write-Host "[6/7] Installing Windows Service..." -ForegroundColor Green
    
    # Check if NSSM is available
    $nssmPath = "$ScriptRoot\nssm.exe"
    
    if (-not (Test-Path $nssmPath)) {
        Write-Host "  Downloading NSSM (Non-Sucking Service Manager)..." -ForegroundColor Gray
        
        $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
        $nssmZip = "$ScriptRoot\nssm.zip"
        
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
        Expand-Archive -Path $nssmZip -DestinationPath "$ScriptRoot\nssm_temp" -Force
        
        # Copy 64-bit version
        Copy-Item "$ScriptRoot\nssm_temp\nssm-2.24\win64\nssm.exe" $nssmPath
        
        # Cleanup
        Remove-Item $nssmZip
        Remove-Item "$ScriptRoot\nssm_temp" -Recurse -Force
        
        Write-Host "  NSSM downloaded" -ForegroundColor Green
    }
    
    # Remove existing service if present
    if (Test-ServiceExists $ServiceName) {
        Write-Host "  Removing existing service..." -ForegroundColor Gray
        & $nssmPath stop $ServiceName confirm
        & $nssmPath remove $ServiceName confirm
        Start-Sleep -Seconds 2
    }
    
    # Create Python wrapper script
    $wrapperPath = "$ScriptRoot\service_wrapper.py"
    $wrapperContent = @"
import sys
import os
import logging
from pathlib import Path

# Set working directory
os.chdir(Path(__file__).parent)

# Configure logging
logging.basicConfig(
    filename='service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info('Media Management Service starting...')

try:
    from app import app
    from config import Config
    
    config = Config()
    logging.info('Configuration loaded')
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
except Exception as e:
    logging.error(f'Service error: {e}', exc_info=True)
    sys.exit(1)
"@
    $wrapperContent | Set-Content $wrapperPath
    
    # Install service
    $pythonExe = "$ScriptRoot\venv\Scripts\python.exe"
    $serviceScript = $wrapperPath
    
    Write-Host "  Creating service..." -ForegroundColor Gray
    & $nssmPath install $ServiceName $pythonExe $serviceScript
    & $nssmPath set $ServiceName DisplayName "$ServiceDisplayName"
    & $nssmPath set $ServiceName Description "$ServiceDescription"
    & $nssmPath set $ServiceName AppDirectory $ScriptRoot
    & $nssmPath set $ServiceName Start SERVICE_AUTO_START
    & $nssmPath set $ServiceName AppStdout "$ScriptRoot\service_stdout.log"
    & $nssmPath set $ServiceName AppStderr "$ScriptRoot\service_stderr.log"
    & $nssmPath set $ServiceName AppRotateFiles 1
    & $nssmPath set $ServiceName AppRotateBytes 1048576  # 1MB
    
    Write-Host "  Service created: $ServiceName" -ForegroundColor Green
}

# Function to start service
function Start-MediaService {
    Write-Host ""
    Write-Host "[7/7] Starting service..." -ForegroundColor Green
    
    if (Test-ServiceExists $ServiceName) {
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 3
        
        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq "Running") {
            Write-Host "  Service started successfully" -ForegroundColor Green
            Write-Host "  Application available at: http://localhost:5000" -ForegroundColor Cyan
        } else {
            Write-Host "  ERROR: Service failed to start" -ForegroundColor Red
            Write-Host "  Check logs: service.log" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ERROR: Service not installed" -ForegroundColor Red
    }
}

# Function to uninstall service
function Uninstall-MediaService {
    Write-Host "Uninstalling service..." -ForegroundColor Yellow
    
    if (Test-ServiceExists $ServiceName) {
        $nssmPath = "$ScriptRoot\nssm.exe"
        
        if (Test-Path $nssmPath) {
            & $nssmPath stop $ServiceName confirm
            & $nssmPath remove $ServiceName confirm
            Write-Host "Service uninstalled" -ForegroundColor Green
        } else {
            Write-Host "ERROR: NSSM not found" -ForegroundColor Red
        }
    } else {
        Write-Host "Service not installed" -ForegroundColor Yellow
    }
}

# Function to check service status
function Get-ServiceStatus {
    Write-Host "Service Status Check" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-ServiceExists $ServiceName) {
        $service = Get-Service -Name $ServiceName
        Write-Host "Service Name: $($service.Name)" -ForegroundColor Gray
        Write-Host "Display Name: $($service.DisplayName)" -ForegroundColor Gray
        Write-Host "Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
        Write-Host "Start Type: $($service.StartType)" -ForegroundColor Gray
        Write-Host ""
        
        if ($service.Status -eq "Running") {
            Write-Host "Application URL: http://localhost:5000" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Service not installed" -ForegroundColor Red
    }
}

# Main execution
try {
    if ($CheckStatus) {
        Get-ServiceStatus
    }
    elseif ($UninstallService) {
        Uninstall-MediaService
    }
    elseif ($RestartService) {
        Write-Host "Restarting service..." -ForegroundColor Yellow
        Restart-Service -Name $ServiceName
        Write-Host "Service restarted" -ForegroundColor Green
    }
    elseif ($InstallService -or $true) {
        # Full installation
        Install-Dependencies
        Invoke-DatabaseMigration
        Update-AppInit
        Test-Configuration
        Install-WindowsService
        Start-MediaService
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "Installation Complete!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Service Name: $ServiceName" -ForegroundColor Gray
        Write-Host "Application: http://localhost:5000" -ForegroundColor Cyan
        Write-Host "Logs: $ScriptRoot\service.log" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Useful commands:" -ForegroundColor Yellow
        Write-Host "  Check status:  .\windows_setup.ps1 -CheckStatus" -ForegroundColor Gray
        Write-Host "  Restart:       .\windows_setup.ps1 -RestartService" -ForegroundColor Gray
        Write-Host "  Uninstall:     .\windows_setup.ps1 -UninstallService" -ForegroundColor Gray
        Write-Host "  Windows Services: services.msc" -ForegroundColor Gray
        Write-Host ""
    }
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Red
    exit 1
}
