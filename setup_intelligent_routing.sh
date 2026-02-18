#!/bin/bash

# Setup script for Intelligent Media Classification & *arr Routing
# This script automates the installation of the intelligent routing feature

set -e  # Exit on error

echo "========================================"
echo "Intelligent Routing Setup"
echo "========================================"
echo ""

# Check if we're in the correct directory
if [ ! -f "run.py" ]; then
    echo "Error: Please run this script from the Media_management root directory"
    exit 1
fi

# Check Python version
echo "[1/6] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "   Warning: Virtual environment not found. It's recommended to create one:"
    echo "   python3 -m venv venv && source venv/bin/activate"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install/verify dependencies
echo ""
echo "[2/6] Checking dependencies..."
if ! python3 -c "import musicbrainzngs" 2>/dev/null; then
    echo "   Installing musicbrainzngs..."
    pip install musicbrainzngs==0.7.1
else
    echo "   ✓ musicbrainzngs already installed"
fi

if ! python3 -c "import spotipy" 2>/dev/null; then
    echo "   Installing spotipy..."
    pip install spotipy
else
    echo "   ✓ spotipy already installed"
fi

# Backup database
echo ""
echo "[3/6] Backing up database..."
if [ -f "media_management.db" ]; then
    backup_file="media_management.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp media_management.db "$backup_file"
    echo "   ✓ Database backed up to: $backup_file"
else
    echo "   ! No database found (will be created on first run)"
fi

# Run database migration
echo ""
echo "[4/6] Running database migration..."
if [ -f "media_management.db" ]; then
    # Check if columns already exist
    if sqlite3 media_management.db "PRAGMA table_info(requests);" | grep -q "arr_service"; then
        echo "   ! Migration already applied (arr_service column exists)"
    else
        echo "   Applying migration..."
        sqlite3 media_management.db < migrations/add_classification_fields.sql
        echo "   ✓ Migration completed successfully"
    fi
else
    echo "   Skipping migration (database doesn't exist yet)"
fi

# Verify configuration
echo ""
echo "[5/6] Checking configuration..."

if [ ! -f "config.yaml" ]; then
    echo "   ⚠ Warning: config.yaml not found!"
    echo "   Please create config.yaml from config.yaml.example"
    missing_config=true
else
    echo "   ✓ config.yaml found"
    
    # Check for required API keys
    missing_keys=()
    
    if ! grep -q "api_key:" config.yaml || grep -q "api_key: ''" config.yaml; then
        missing_keys+=("TMDb API key")
    fi
    
    if ! grep -A2 "Spotify:" config.yaml | grep -q "client_id:" || grep -A2 "Spotify:" config.yaml | grep -q "client_id: ''" ; then
        missing_keys+=("Spotify client_id")
    fi
    
    if ! grep -A2 "Sonarr:" config.yaml | grep -q "api_key:" ; then
        missing_keys+=("Sonarr API key")
    fi
    
    if ! grep -A2 "Radarr:" config.yaml | grep -q "api_key:" ; then
        missing_keys+=("Radarr API key")
    fi
    
    if ! grep -A2 "Lidarr:" config.yaml | grep -q "api_key:" ; then
        missing_keys+=("Lidarr API key")
    fi
    
    if [ ${#missing_keys[@]} -gt 0 ]; then
        echo "   ⚠ Warning: Missing API keys in config.yaml:"
        for key in "${missing_keys[@]}"; do
            echo "      - $key"
        done
        echo ""
        echo "   The system will still work but some features may be limited."
        echo "   See INTELLIGENT_ROUTING.md for configuration details."
    else
        echo "   ✓ All required API keys configured"
    fi
fi

# Register blueprint (check if already registered)
echo ""
echo "[6/6] Checking blueprint registration..."
if grep -q "unified_requests_bp" app/__init__.py 2>/dev/null; then
    echo "   ✓ Blueprint already registered"
else
    echo "   ⚠ Blueprint not registered in app/__init__.py"
    echo "   Please add the following to app/__init__.py:"
    echo ""
    echo "   from app.routes.unified_requests import unified_requests_bp"
    echo "   app.register_blueprint(unified_requests_bp)"
    echo ""
fi

# Summary
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Ensure config.yaml has all required API keys"
echo "2. Register the blueprint in app/__init__.py (if not already done)"
echo "3. Restart the application: python run.py"
echo "4. Test classification:"
echo "   python -c 'from app.helpers.media_classifier import MediaClassifier; c = MediaClassifier(); print(c.classify(\"Dexter\"))'"
echo ""
echo "Documentation: INTELLIGENT_ROUTING.md"
echo "Support: https://github.com/zy538324/Media_management/issues"
echo ""
