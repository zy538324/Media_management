# PowerShell Setup Script for Intelligent Media Classification & *arr Routing
# This script automates the installation of the intelligent routing feature on Windows

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Intelligent Routing Setup (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "run.py")) {
    Write-Host "Error: Please run this script from the Media_management root directory" -ForegroundColor Red
    exit 1
}

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = (python --version 2>&1) -replace "Python ", ""
    Write-Host "   Found Python $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   Error: Python not found in PATH" -ForegroundColor Red
    Write-Host "   Please install Python 3.8+ and add to PATH" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "   Warning: Virtual environment not found" -ForegroundColor Yellow
    Write-Host "   It's recommended to create one:" -ForegroundColor Yellow
    Write-Host "   python -m venv venv" -ForegroundColor Yellow
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    $continue = Read-Host "   Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Install/verify dependencies
Write-Host ""
Write-Host "[2/6] Checking dependencies..." -ForegroundColor Yellow

# Check musicbrainzngs
try {
    python -c "import musicbrainzngs" 2>$null
    Write-Host "   `u{2713} musicbrainzngs already installed" -ForegroundColor Green
} catch {
    Write-Host "   Installing musicbrainzngs..." -ForegroundColor Yellow
    pip install musicbrainzngs==0.7.1
    Write-Host "   `u{2713} musicbrainzngs installed" -ForegroundColor Green
}

# Check spotipy
try {
    python -c "import spotipy" 2>$null
    Write-Host "   `u{2713} spotipy already installed" -ForegroundColor Green
} catch {
    Write-Host "   Installing spotipy..." -ForegroundColor Yellow
    pip install spotipy
    Write-Host "   `u{2713} spotipy installed" -ForegroundColor Green
}

# Backup database
Write-Host ""
Write-Host "[3/6] Backing up database..." -ForegroundColor Yellow
if (Test-Path "media_management.db") {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "media_management.db.backup.$timestamp"
    Copy-Item "media_management.db" $backupFile
    Write-Host "   `u{2713} Database backed up to: $backupFile" -ForegroundColor Green
} else {
    Write-Host "   ! No database found (will be created on first run)" -ForegroundColor Yellow
}

# Run database migration
Write-Host ""
Write-Host "[4/6] Running database migration..." -ForegroundColor Yellow
if (Test-Path "media_management.db") {
    # Check if columns already exist
    $tableInfo = sqlite3 media_management.db "PRAGMA table_info(requests);" 2>$null
    if ($tableInfo -match "arr_service") {
        Write-Host "   ! Migration already applied (arr_service column exists)" -ForegroundColor Yellow
    } else {
        Write-Host "   Applying migration..." -ForegroundColor Yellow
        Get-Content "migrations\add_classification_fields.sql" | sqlite3 media_management.db
        Write-Host "   `u{2713} Migration completed successfully" -ForegroundColor Green
    }
} else {
    Write-Host "   Skipping migration (database doesn't exist yet)" -ForegroundColor Yellow
}

# Verify configuration
Write-Host ""
Write-Host "[5/6] Checking configuration..." -ForegroundColor Yellow

if (-not (Test-Path "config.yaml")) {
    Write-Host "   `u{26a0} Warning: config.yaml not found!" -ForegroundColor Yellow
    Write-Host "   Please create config.yaml from config.yaml.example" -ForegroundColor Yellow
} else {
    Write-Host "   `u{2713} config.yaml found" -ForegroundColor Green
    
    # Check for required API keys
    $configContent = Get-Content "config.yaml" -Raw
    $missingKeys = @()
    
    if (-not ($configContent -match "api_key:\s*\S+")) {
        $missingKeys += "TMDb API key"
    }
    
    if (-not ($configContent -match "Spotify:[\s\S]*?client_id:\s*\S+")) {
        $missingKeys += "Spotify client_id"
    }
    
    if (-not ($configContent -match "Sonarr:[\s\S]*?api_key:\s*\S+")) {
        $missingKeys += "Sonarr API key"
    }
    
    if (-not ($configContent -match "Radarr:[\s\S]*?api_key:\s*\S+")) {
        $missingKeys += "Radarr API key"
    }
    
    if (-not ($configContent -match "Lidarr:[\s\S]*?api_key:\s*\S+")) {
        $missingKeys += "Lidarr API key"
    }
    
    if ($missingKeys.Count -gt 0) {
        Write-Host "   `u{26a0} Warning: Missing API keys in config.yaml:" -ForegroundColor Yellow
        foreach ($key in $missingKeys) {
            Write-Host "      - $key" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "   The system will still work but some features may be limited." -ForegroundColor Yellow
        Write-Host "   See INTELLIGENT_ROUTING.md for configuration details." -ForegroundColor Yellow
    } else {
        Write-Host "   `u{2713} All required API keys configured" -ForegroundColor Green
    }
}

# Register blueprint (check if already registered)
Write-Host ""
Write-Host "[6/6] Checking blueprint registration..." -ForegroundColor Yellow
if (Test-Path "app\__init__.py") {
    $initContent = Get-Content "app\__init__.py" -Raw
    if ($initContent -match "unified_requests_bp") {
        Write-Host "   `u{2713} Blueprint already registered" -ForegroundColor Green
    } else {
        Write-Host "   `u{26a0} Blueprint not registered in app\__init__.py" -ForegroundColor Yellow
        Write-Host "   Please add the following to app\__init__.py:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   from app.routes.unified_requests import unified_requests_bp" -ForegroundColor Cyan
        Write-Host "   app.register_blueprint(unified_requests_bp)" -ForegroundColor Cyan
        Write-Host ""
    }
} else {
    Write-Host "   `u{2717} app\__init__.py not found" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Ensure config.yaml has all required API keys" -ForegroundColor White
Write-Host "2. Register the blueprint in app\__init__.py (if not already done)" -ForegroundColor White
Write-Host "3. Restart the application: python run.py" -ForegroundColor White
Write-Host "4. Test classification:" -ForegroundColor White
Write-Host "   python -c `"from app.helpers.media_classifier import MediaClassifier; c = MediaClassifier(); print(c.classify('Dexter'))`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "Documentation: INTELLIGENT_ROUTING.md" -ForegroundColor Yellow
Write-Host "Support: https://github.com/zy538324/Media_management/issues" -ForegroundColor Yellow
Write-Host ""

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
