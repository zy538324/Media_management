# Windows Server 2025 Deployment Guide

## Complete Setup - From Zero to Running Service

### Prerequisites

- ✅ Windows Server 2025 (or Windows 10/11)
- ✅ Python 3.8+ installed and in PATH
- ✅ SQLite3 (usually bundled with Python)
- ✅ Administrator access
- ✅ Internet connection

### Quick Start (5 Minutes)

#### 1. Download/Clone Repository

```powershell
cd C:\inetpub\  # Or your preferred location
git clone https://github.com/zy538324/Media_management.git
cd Media_management
```

#### 2. Run Automated Setup

**Right-click PowerShell → Run as Administrator:**

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\windows_setup.ps1
```

This script will:
- ✅ Check Python installation
- ✅ Create/activate virtual environment
- ✅ Install all dependencies (including musicbrainzngs)
- ✅ Backup database
- ✅ Run database migration (add classification fields)
- ✅ Register unified_requests blueprint
- ✅ Verify API key configuration
- ✅ Download NSSM (service manager)
- ✅ Install Windows service
- ✅ Start the service

**Expected output:**
```
========================================
Media Management - Windows Setup
========================================

[1/7] Checking Python installation...
  Found: Python 3.11.5

[2/7] Installing Python dependencies...
  All dependencies installed

[3/7] Database migration...
  Database backed up to: media_management.db.backup.20260218_154500
  Migration completed

[4/7] Checking blueprint registration...
  Blueprint registered

[5/7] Verifying configuration...
  config.yaml found
  All API keys configured

[6/7] Installing Windows Service...
  NSSM downloaded
  Service created: MediaManagement

[7/7] Starting service...
  Service started successfully
  Application available at: http://localhost:5000

========================================
Installation Complete!
========================================

Service Name: MediaManagement
Application: http://localhost:5000
Logs: C:\inetpub\Media_management\service.log
```

#### 3. Start System Tray Monitor (Optional)

```powershell
python system_tray_app.py
```

Creates a system tray icon with:
- ● Service status indicator (Running/Stopped)
- Quick access to web interface
- Start/Stop/Restart service controls
- Log viewer
- Test runner

**Add to Startup (Optional):**
```powershell
# Create shortcut in Startup folder
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\MediaManagement.lnk")
$Shortcut.TargetPath = "pythonw.exe"  # Use pythonw to hide console
$Shortcut.Arguments = "$(Get-Location)\system_tray_app.py"
$Shortcut.WorkingDirectory = Get-Location
$Shortcut.Save()
```

#### 4. Verify Service is Running

**Check via PowerShell:**
```powershell
Get-Service MediaManagement
```

**Check via GUI:**
```powershell
services.msc
# Look for "Media Management with Intelligent Routing"
```

**Test web interface:**
```powershell
Start-Process http://localhost:5000
```

### Configuration

#### API Keys in `config.yaml`

```yaml
TMDb:
  api_key: your_tmdb_api_key_here  # Get from https://www.themoviedb.org/settings/api

Spotify:
  client_id: your_spotify_client_id
  client_secret: your_spotify_client_secret
  # Get from https://developer.spotify.com/dashboard

Sonarr:
  api_url: http://localhost:8989
  api_key: your_sonarr_api_key
  # Found in Sonarr → Settings → General → API Key

Radarr:
  api_url: http://localhost:7878
  api_key: your_radarr_api_key
  # Found in Radarr → Settings → General → API Key

Lidarr:
  api_url: http://localhost:8686
  api_key: your_lidarr_api_key
  # Found in Lidarr → Settings → General → API Key
```

**After updating config.yaml, restart service:**
```powershell
Restart-Service MediaManagement
```

### Service Management

#### Using PowerShell

```powershell
# Check status
.\windows_setup.ps1 -CheckStatus

# Restart service
.\windows_setup.ps1 -RestartService

# Or use native commands:
Get-Service MediaManagement
Start-Service MediaManagement
Stop-Service MediaManagement
Restart-Service MediaManagement
```

#### Using Services GUI

```powershell
services.msc
```

Find **"Media Management with Intelligent Routing"**
- Right-click → Start/Stop/Restart
- Properties → Startup type: Automatic (Delayed Start)
- Recovery tab: Configure restart on failure

#### Using System Tray App

1. Double-click tray icon OR right-click
2. **Start Service** / **Stop Service** / **Restart Service**
3. **Open Web Interface** - Opens http://localhost:5000
4. **View Logs** - Shows service.log in real-time
5. **Run Tests** - Launches test_classifier.py

### Troubleshooting

#### Service Won't Start

**Check logs:**
```powershell
Get-Content .\service.log -Tail 50
Get-Content .\service_stderr.log -Tail 50
```

**Common issues:**

1. **Port 5000 already in use:**
   ```powershell
   netstat -ano | findstr :5000
   # Kill process using port:
   taskkill /PID <process_id> /F
   ```

2. **Missing dependencies:**
   ```powershell
   .\venv\Scripts\pip.exe install -r requirements.txt
   Restart-Service MediaManagement
   ```

3. **Python not found:**
   ```powershell
   # Verify Python in PATH
   python --version
   
   # If not found, reinstall service with full path:
   $pythonPath = (Get-Command python).Source
   .\nssm.exe set MediaManagement Application $pythonPath
   ```

4. **Database locked:**
   ```powershell
   # Stop service
   Stop-Service MediaManagement
   
   # Check for locks
   Get-Process | Where-Object {$_.MainWindowTitle -like "*media_management*"}
   
   # Restart
   Start-Service MediaManagement
   ```

#### Classification Not Working

**Test API connections:**
```powershell
python test_classifier.py
```

**Expected output:**
```
✓ Configuration
✓ TMDb Connection
✓ Spotify Connection
✓ MusicBrainz Connection
✓ Classification
✓ ALL TESTS PASSED!
```

**If tests fail:**

1. **TMDb Connection Failed:**
   - Verify `TMDb.api_key` in config.yaml
   - Test: `curl https://api.themoviedb.org/3/movie/550?api_key=YOUR_KEY`

2. **Spotify Connection Failed:**
   - Verify `Spotify.client_id` and `client_secret`
   - Test credentials at https://developer.spotify.com/console/post-oauth2-token/

3. **MusicBrainz Connection Failed:**
   - Usually means rate limiting (1 req/sec)
   - Wait 60 seconds and retry

#### Web Interface Not Accessible

**Firewall rule:**
```powershell
New-NetFirewallRule -DisplayName "Media Management" `
                     -Direction Inbound `
                     -LocalPort 5000 `
                     -Protocol TCP `
                     -Action Allow
```

**IIS conflict (if running IIS):**
```powershell
# Change port in service_wrapper.py:
# app.run(host='0.0.0.0', port=5001, ...)  # Use 5001 instead

Restart-Service MediaManagement
```

**Check service is listening:**
```powershell
netstat -ano | findstr :5000
# Should show: TCP    0.0.0.0:5000    0.0.0.0:0    LISTENING
```

### Advanced Configuration

#### Change Port

Edit `service_wrapper.py`:
```python
app.run(
    host='0.0.0.0',
    port=8080,  # Change port here
    debug=False,
    use_reloader=False
)
```

Restart service:
```powershell
Restart-Service MediaManagement
```

#### Enable HTTPS (Production)

**Option 1: Use IIS as reverse proxy**

1. Install IIS with Application Request Routing
2. Create reverse proxy rule:
   ```xml
   <rewrite>
     <rules>
       <rule name="Media Management">
         <match url="(.*)" />
         <action type="Rewrite" url="http://localhost:5000/{R:1}" />
       </rule>
     </rules>
   </rewrite>
   ```

**Option 2: Use Flask-Talisman (HTTPS redirect)**

```powershell
.\venv\Scripts\pip.exe install flask-talisman
```

Edit `service_wrapper.py`:
```python
from flask_talisman import Talisman

app = app
Talisman(app, force_https=True)
```

#### Run on Boot

**Already configured!** Service is set to `Automatic` start type.

Verify:
```powershell
Get-Service MediaManagement | Select-Object Name, StartType, Status
```

Configure delayed start:
```powershell
sc.exe config MediaManagement start= delayed-auto
```

#### Resource Limits

**Set memory limit:**
```powershell
.\nssm.exe set MediaManagement AppEnvironmentExtra +JOB_MEMORY_LIMIT=512M
```

**Set CPU affinity:**
```powershell
.\nssm.exe set MediaManagement AppAffinity 0x0F  # Use first 4 cores
```

### Monitoring

#### Event Viewer

```powershell
eventvwr.msc
# Navigate to: Windows Logs → Application
# Filter by: Source = MediaManagement
```

#### Performance Monitor

```powershell
perfmon.msc
# Add counters:
# - Process → Private Bytes → python.exe
# - Process → % Processor Time → python.exe
# - Network Interface → Bytes Total/sec
```

#### Custom Health Check Script

```powershell
# health_check.ps1
$response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "✓ Service healthy"
    exit 0
} else {
    Write-Host "✗ Service unhealthy"
    Restart-Service MediaManagement
    exit 1
}
```

**Schedule with Task Scheduler:**
```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
          -Argument "-File C:\inetpub\Media_management\health_check.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "MediaManagementHealthCheck" `
                       -Action $action `
                       -Trigger $trigger `
                       -User "SYSTEM"
```

### Backup and Restore

#### Backup

```powershell
# Stop service
Stop-Service MediaManagement

# Backup script
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "C:\Backups\MediaManagement_$timestamp"
New-Item -ItemType Directory -Path $backupDir

Copy-Item .\media_management.db "$backupDir\"
Copy-Item .\config.yaml "$backupDir\"
Copy-Item .\service.log "$backupDir\"

# Restart service
Start-Service MediaManagement

Write-Host "Backup created: $backupDir"
```

#### Restore

```powershell
Stop-Service MediaManagement

Copy-Item "C:\Backups\MediaManagement_20260218_154500\media_management.db" .\media_management.db
Copy-Item "C:\Backups\MediaManagement_20260218_154500\config.yaml" .\config.yaml

Start-Service MediaManagement
```

### Uninstallation

```powershell
# Run as Administrator
.\windows_setup.ps1 -UninstallService

# Or manually:
Stop-Service MediaManagement
.\nssm.exe remove MediaManagement confirm

# Remove files
cd ..
Remove-Item .\Media_management -Recurse -Force
```

### Security Considerations

#### Service Account

By default, service runs as **Local System**. To use dedicated account:

```powershell
# Create service account
$password = ConvertTo-SecureString "YourSecurePassword" -AsPlainText -Force
New-LocalUser -Name "MediaManagementSvc" -Password $password -Description "Media Management Service Account"

# Grant permissions
Add-LocalGroupMember -Group "Users" -Member "MediaManagementSvc"
icacls "C:\inetpub\Media_management" /grant "MediaManagementSvc:(OI)(CI)F" /T

# Configure service
.\nssm.exe set MediaManagement ObjectName ".\MediaManagementSvc" "YourSecurePassword"
Restart-Service MediaManagement
```

#### API Key Protection

```powershell
# Encrypt config.yaml
$configContent = Get-Content .\config.yaml -Raw
$secureConfig = ConvertTo-SecureString $configContent -AsPlainText -Force
$encryptedConfig = ConvertFrom-SecureString $secureConfig
$encryptedConfig | Out-File .\config.encrypted

# Restrict permissions
icacls .\config.yaml /inheritance:r
icacls .\config.yaml /grant:r "$env:USERNAME:(F)"
icacls .\config.yaml /grant:r "SYSTEM:(F)"
```

### Performance Tuning

#### Production Settings

Edit `service_wrapper.py`:
```python
app.run(
    host='0.0.0.0',
    port=5000,
    debug=False,           # Disable debug mode
    use_reloader=False,    # Disable reloader
    threaded=True,         # Enable threading
    processes=4            # Multi-process (if needed)
)
```

#### Enable Request Caching

```powershell
.\venv\Scripts\pip.exe install flask-caching
```

Add to `app/__init__.py`:
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

### Summary

**Quick commands:**
```powershell
# Install everything
.\windows_setup.ps1

# Check status
Get-Service MediaManagement

# View logs
Get-Content .\service.log -Tail 50 -Wait

# Test classification
python test_classifier.py

# Restart
Restart-Service MediaManagement

# Open web UI
Start-Process http://localhost:5000

# System tray
python system_tray_app.py
```

**Files created:**
- Service: `C:\Windows\System32\nssm.exe` (if downloaded)
- Logs: `service.log`, `service_stdout.log`, `service_stderr.log`
- Database: `media_management.db`
- Virtual env: `venv\`

**Ports used:**
- 5000: Flask web interface
- 8989: Sonarr (if local)
- 7878: Radarr (if local)
- 8686: Lidarr (if local)

**Resources:**
- Documentation: `INTELLIGENT_ROUTING.md`
- Quick start: `QUICKSTART_INTELLIGENT_ROUTING.md`
- Repository: https://github.com/zy538324/Media_management
