#!/usr/bin/env python3
"""
Intelligent Routing Installation Checker
Verifies all components are properly installed and configured
"""

import sys
import os
import sqlite3

def check_files():
    """Check if all required files exist."""
    print("\n" + "="*70)
    print("FILE CHECK")
    print("="*70)
    
    required_files = {
        'app/helpers/media_classifier.py': 'Classification engine',
        'app/routes/unified_requests.py': 'API endpoints',
        'app/helpers/request_processor.py': 'Request processor',
        'migrations/add_classification_fields.sql': 'Database migration',
        'test_classifier.py': 'Test suite',
    }
    
    all_present = True
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"  ✅ {file_path:50} ({description})")
        else:
            print(f"  ❌ {file_path:50} MISSING")
            all_present = False
    
    return all_present

def check_blueprint():
    """Check if blueprint is registered."""
    print("\n" + "="*70)
    print("BLUEPRINT REGISTRATION CHECK")
    print("="*70)
    
    try:
        with open('app/__init__.py', 'r') as f:
            content = f.read()
        
        import_present = 'from app.routes.unified_requests import unified_requests_bp' in content
        register_present = 'app.register_blueprint(unified_requests_bp)' in content
        
        if import_present:
            print("  ✅ Blueprint import found")
        else:
            print("  ❌ Blueprint import MISSING")
        
        if register_present:
            print("  ✅ Blueprint registration found")
        else:
            print("  ❌ Blueprint registration MISSING")
        
        if import_present and register_present:
            print("\n  ✅ Blueprint properly configured!")
            return True
        else:
            print("\n  ⚠️  Add these lines to app/__init__.py:")
            if not import_present:
                print("     from app.routes.unified_requests import unified_requests_bp")
            if not register_present:
                print("     app.register_blueprint(unified_requests_bp)")
            return False
            
    except FileNotFoundError:
        print("  ❌ app/__init__.py not found")
        return False
    except Exception as e:
        print(f"  ❌ Error reading app/__init__.py: {e}")
        return False

def check_database():
    """Check if database migration has been applied."""
    print("\n" + "="*70)
    print("DATABASE MIGRATION CHECK")
    print("="*70)
    
    db_path = "media_management.db"
    
    if not os.path.exists(db_path):
        print(f"  ⚠️  Database not found: {db_path}")
        print("     This is normal if you haven't run the app yet.")
        print("     Migration will be applied on first run.")
        return None  # Not an error, just not created yet
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(requests);")
        columns = cursor.fetchall()
        
        if not columns:
            print("  ❌ 'requests' table not found")
            conn.close()
            return False
        
        column_names = [col[1] for col in columns]
        
        required_fields = ['arr_service', 'arr_id', 'external_id', 'confidence_score', 'classification_data']
        missing_fields = [f for f in required_fields if f not in column_names]
        
        if not missing_fields:
            print("  ✅ All classification fields present")
            
            # Show statistics
            cursor.execute("SELECT COUNT(*) FROM requests WHERE arr_service IS NOT NULL")
            classified = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM requests")
            total = cursor.fetchone()[0]
            
            print(f"\n  Database Statistics:")
            print(f"    Total requests: {total}")
            print(f"    Classified: {classified}")
            if total > 0:
                print(f"    Rate: {(classified/total)*100:.1f}%")
            
            conn.close()
            return True
        else:
            print("  ❌ Missing fields:", ', '.join(missing_fields))
            print("\n  To apply migration:")
            print("     sqlite3 media_management.db < migrations/add_classification_fields.sql")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"  ❌ Database error: {e}")
        return False

def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n" + "="*70)
    print("DEPENDENCY CHECK")
    print("="*70)
    
    dependencies = {
        'requests': 'HTTP client',
        'flask': 'Web framework',
        'sqlalchemy': 'Database ORM',
    }
    
    optional_dependencies = {
        'spotipy': 'Spotify integration (recommended for music)',
    }
    
    all_present = True
    
    print("\n  Required:")
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"    ✅ {package:20} ({description})")
        except ImportError:
            print(f"    ❌ {package:20} MISSING - {description}")
            all_present = False
    
    print("\n  Optional:")
    for package, description in optional_dependencies.items():
        try:
            __import__(package)
            print(f"    ✅ {package:20} ({description})")
        except ImportError:
            print(f"    ⚠️  {package:20} Not installed - {description}")
    
    return all_present

def check_config():
    """Check configuration file."""
    print("\n" + "="*70)
    print("CONFIGURATION CHECK")
    print("="*70)
    
    if not os.path.exists('config.yaml'):
        print("  ❌ config.yaml not found")
        return False
    
    try:
        # Try to load config
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config import Config
        
        config = Config()
        
        checks = {
            'TMDb API Key': bool(config.TMDB_API_KEY),
            'Spotify Client ID': bool(config.SPOTIFY_CLIENT_ID),
            'Spotify Client Secret': bool(config.SPOTIFY_CLIENT_SECRET),
            'Sonarr API Key': bool(config.SONARR_API_KEY),
            'Radarr API Key': bool(config.RADARR_API_KEY),
            'Lidarr API Key': bool(config.LIDARR_API_KEY),
        }
        
        critical_missing = []
        optional_missing = []
        
        for key, present in checks.items():
            if present:
                print(f"  ✅ {key}")
            else:
                if 'Spotify' in key:
                    print(f"  ⚠️  {key:25} (optional - for music classification)")
                    optional_missing.append(key)
                else:
                    print(f"  ❌ {key:25} MISSING")
                    critical_missing.append(key)
        
        if critical_missing:
            print("\n  ⚠️  Configure missing API keys in config.yaml")
            return False
        elif optional_missing:
            print("\n  ✅ All critical API keys configured")
            print("     (Spotify optional for enhanced music classification)")
            return True
        else:
            print("\n  ✅ All API keys configured!")
            return True
            
    except Exception as e:
        print(f"  ❌ Error loading config: {e}")
        return False

def main():
    """Run all checks."""
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  Intelligent Media Routing - Installation Status".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    
    results = {
        'Files': check_files(),
        'Blueprint': check_blueprint(),
        'Database': check_database(),
        'Dependencies': check_dependencies(),
        'Configuration': check_config(),
    }
    
    # Summary
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  INSTALLATION SUMMARY".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    print()
    
    for component, status in results.items():
        if status is True:
            print(f"  ✅ {component:.<60} READY")
        elif status is None:
            print(f"  ⚠️  {component:.<60} PENDING")
        else:
            print(f"  ❌ {component:.<60} INCOMPLETE")
    
    print("\n" + "="*70)
    
    # Determine overall status
    critical_complete = all(v in [True, None] for v in results.values())
    
    if critical_complete:
        print("✅ INSTALLATION COMPLETE")
        print("\nThe intelligent routing system is ready to use!")
        print("\nNext steps:")
        print("  1. Start the application: python run.py")
        print("  2. Test classification: python test_classifier.py")
        print("  3. Create a request and watch it auto-route!")
        exit_code = 0
    else:
        print("⚠️  INSTALLATION INCOMPLETE")
        print("\nPlease complete the steps marked with ❌ above.")
        print("\nQuick fix:")
        print("  chmod +x setup_intelligent_routing.sh")
        print("  ./setup_intelligent_routing.sh")
        exit_code = 1
    
    print("="*70 + "\n")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
