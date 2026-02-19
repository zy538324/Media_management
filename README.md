# Media Management Application

A comprehensive web-based media management system that integrates with Radarr (movies), Sonarr (TV shows), Lidarr (music), Jellyfin (library), and Spotify recommendations. The application provides a centralized dashboard for managing media requests and recommendations with intelligent duplicate detection.

---

## Table of Contents

1. [Features](#features)
2. [Requirements to Build](#requirements-to-build)
3. [Requirements to Use](#requirements-to-use)
4. [Architecture](#architecture)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Usage](#usage)
9. [API Integrations](#api-integrations)
10. [Troubleshooting](#troubleshooting)

---

## Features

✅ **Multi-Media Support**
- Movies (via Radarr)
- TV Shows (via Sonarr)
- Music/Artists (via Lidarr)

✅ **Smart Duplicate Detection**
- Checks Radarr library before adding movies
- Checks Sonarr library before adding TV shows
- Checks Lidarr library with fuzzy matching for artists
- Prevents duplicate requests to arr services

✅ **Content Filtering**
- English-language only torrent selection
- Cyrillic/Russian torrent exclusion
- Non-English audio filter (MVO, AVO, DVO)

✅ **User Features**
- User registration and authentication
- Request management dashboard
- Personalized recommendations from TMDb/Spotify
- Real-time request status tracking

✅ **Admin Features**
- Arr service configuration
- User management
- System logs and diagnostics
- Notification settings

✅ **Integrations**
- **Radarr** - Movie management (TMDb based)
- **Sonarr** - TV show management (TVDB based)
- **Lidarr** - Music/Artist management (MusicBrainz based)
- **Jellyfin** - Personal media library
- **TMDb** - Movie/TV metadata and recommendations
- **Spotify** - Music recommendations
- **qBittorrent** - Torrent management
- **PostgreSQL** - Persistent data storage

---

## Requirements to Build

### System Requirements
- **OS**: Linux (Ubuntu 20.04+) or macOS
- **Python**: 3.10 or higher (tested with 3.12)
- **RAM**: Minimum 512MB
- **Disk**: 1GB for application + database

### Build Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-dev \
  libpq-dev build-essential curl git postgresql-client
```

#### macOS
```bash
brew install python3 postgresql
```

### Python Dependencies
All dependencies are in `requirements.txt`:

```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Migrate==4.0.7
psycopg2-binary==2.9.11
SQLAlchemy==2.0.36
APScheduler==3.10.4
requests==2.32.3
gunicorn==21.2.0
python-dotenv==1.0.1
PyYAML==6.0.2
musicbrainzngs==0.7.1
spotipy==2.24.0
```

---

## Requirements to Use

### External Services (Required)

#### 1. **PostgreSQL Database**
- Minimum: PostgreSQL 12+
- Can be hosted locally or remotely
- Required credentials:
  - Host/IP address
  - Port (default 5432)
  - Username
  - Password
  - Database name

#### 2. **Radarr** (Movies)
- URL: `http://<host>:<port>` (default port 7878)
- API Key from Radarr settings
- One or more root folders configured in Radarr

#### 3. **Sonarr** (TV Shows)
- URL: `http://<host>:<port>` (default port 8989)
- API Key from Sonarr settings
- One or more root folders configured in Sonarr

#### 4. **Lidarr** (Music/Artists)
- URL: `http://<host>:<port>` (default port 8686)
- API Key from Lidarr settings
- One or more root folders configured in Lidarr

#### 5. **Jellyfin** (Optional - Library Integration)
- URL: `http://<host>:<port>` (default port 8096)
- API Key from Jellyfin settings
- Enables library browsing and duplicate detection

#### 6. **qBittorrent** (Torrent Management)
- URL: `http://<host>:<port>` (default port 8080)
- Username and password
- Must have Web UI enabled

#### 7. **Jackett** (Torrent Search)
- URL: `http://<host>:<port>` (default port 9117)
- API Key from Jackett
- Configured indexers for Movies, TV, and Music
- Category IDs: Movies (2000), TV (5000), Music (3000)

### Optional Services

#### **TMDb API** (Metadata & Recommendations)
- Sign up: https://www.themoviedb.org/settings/api
- Free tier available
- API Key required in config

#### **Spotify API** (Music Recommendations)
- Create app at: https://developer.spotify.com/dashboard
- Client ID and Client Secret required
- Optional - recommendations work without it

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser                              │
│              https://media.tamsilcms.com                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx                                  │
│            (Reverse Proxy + SSL/TLS)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Flask Application (Gunicorn)                     │
│      Media Management Dashboard & API                      │
│            (127.0.0.1:5000)                                │
└──────┬───────────┬──────────────┬──────────────┬───────────┘
       │           │              │              │
       ▼           ▼              ▼              ▼
┌────────────┐ ┌─────────┐ ┌─────────────┐ ┌──────────────┐
│ PostgreSQL │ │ Radarr  │ │   Sonarr    │ │   Lidarr     │
│ Database   │ │(Movies) │ │(TV Shows)   │ │(Music/Artist)│
└────────────┘ └─────────┘ └─────────────┘ └──────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │   Jellyfin       │
                                          │(Library Search)  │
                                          └──────────────────┘

Integration with:
- qBittorrent (Torrent Downloads)
- Jackett (Torrent Search Indexing)
- TMDb API (Movie/TV Metadata)
- Spotify API (Music Recommendations)
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Media_management
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Application

Create or edit `config.yaml` with your settings:

```yaml
Database:
  type: postgresql
  host: localhost
  port: 5432
  username: media_user
  password: YOUR_DB_PASSWORD_HERE
  database: media_management
  track_modifications: false

Radarr:
  api_key: YOUR_RADARR_API_KEY
  server_url: http://10.252.0.2:7878

Sonarr:
  api_key: YOUR_SONARR_API_KEY
  server_url: http://10.252.0.2:8989

Lidarr:
  api_key: YOUR_LIDARR_API_KEY
  server_url: http://10.252.0.2:8686

Jellyfin:
  api_key: YOUR_JELLYFIN_API_KEY
  server_url: http://10.252.0.2:8096

qBittorrent:
  host: http://10.252.0.2:8080
  username: admin
  password: YOUR_QBITTORRENT_PASSWORD

Jackett:
  api_key: YOUR_JACKETT_API_KEY
  server_url: http://10.252.0.2:9117/
  categories:
    Movies: '2000'
    TV: '5000'
    Music: '3000'

TMDb:
  api_key: YOUR_TMDB_API_KEY

Spotify:
  client_id: YOUR_SPOTIFY_CLIENT_ID
  client_secret: YOUR_SPOTIFY_CLIENT_SECRET

Secret_key: 'GENERATE_A_RANDOM_SECRET_KEY_HERE'
```

### 5. Create Database

```bash
# Run migrations
flask db upgrade

# Or create from scratch (if migrations not yet run)
python init_db.py
```

### 6. Run Application

**Development:**
```bash
python run.py
```

**Production (with Gunicorn):**
```bash
gunicorn --workers 2 --threads 4 --bind 0.0.0.0:5000 "app:create_app()"
```

---

## Configuration

### Environment Variables

Create `.env` file (optional):

```bash
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=postgresql://media_user:password@localhost:5432/media_management
SECRET_KEY=your-secret-key-here
```

### config.yaml Structure

All configuration should be in `config.yaml`. Key sections:

**Database Connection**
- Required for all operations
- Supports PostgreSQL and SQLite (fallback)

**Service Credentials**
- Each *arr service needs its API key
- Obtainable from respective service settings

**API Keys**
- TMDb: Free tier available at themoviedb.org
- Spotify: Create app at developer.spotify.com
- Jackett: Generated in Jackett UI

---

## Deployment

### Docker Deployment (Recommended)

```bash
# Build image
docker build -t media-management .

# Run container
docker run -d \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://... \
  -v /path/to/config.yaml:/app/config.yaml \
  media-management
```

### Linux Systemd Service

See [DEPLOYMENT_STEPS.md](DEPLOYMENT_STEPS.md) for complete systemd installation.

Quick start:
```bash
sudo bash setup.sh
```

### Nginx Reverse Proxy

See [nginx_setup.md](nginx_setup.md) for SSL/HTTPS configuration.

### Cloud Deployment

- **AWS**: EC2 + RDS + ELB
- **DigitalOcean**: Droplet + Managed PostgreSQL
- **Heroku**: With PostgreSQL add-on
- **Raspberry Pi**: See [CLEANUP_AND_MIGRATION.md](CLEANUP_AND_MIGRATION.md)

---

## Usage

### Access the Application

**Local Development**
```
http://localhost:5000
```

**Production**
```
https://media.tamsilcms.com
```

### Default Credentials

**Initial Admin Account:**
- Username: `admin`
- Password: `changeme123`

⚠️ **Change this immediately after first login!**

### Main Features

#### 1. **Dashboard**
- View recent requests and recommendations
- Quick stats on library size
- Service status overview

#### 2. **Add Request**
- Search for movies, TV shows, or music
- View duplicate detection status
- Submit request to arr service
- Track request status

#### 3. **Recommendations**
- Get personalized recommendations from TMDb/Spotify
- View recommendations from library items
- Add recommended items directly
- See which items already in library

#### 4. **Library**
- Browse your Jellyfin library
- View media details
- Search and filter
- See request history

#### 5. **User Management**
- Register new users
- Edit user profiles
- Admin user controls

#### 6. **Admin Panel**
- Configure arr services
- Add/manage users
- System logs
- Service health status
- Notification settings

---

## API Integrations

### Radarr Integration

**Purpose**: Movie management  
**Authentication**: API Key in header  
**Process**:
1. Check if movie exists (by TMDb ID)
2. Get available root folders
3. Add movie if not duplicate

**API Endpoints Used**:
- `GET /api/v3/movie` - List movies
- `GET /api/v3/rootfolder` - Get root paths
- `POST /api/v3/movie` - Add movie

### Sonarr Integration

**Purpose**: TV show management  
**Authentication**: API Key in header  
**Key Difference**: Uses TVDB ID (not TMDb)
**Process**:
1. Get TVDB ID from TMDb external_ids
2. Check if show exists (by TVDB ID)
3. Get available root folders
4. Add show if not duplicate

**API Endpoints Used**:
- `GET /api/v3/series` - List shows
- `GET /api/v3/rootfolder` - Get root paths
- `POST /api/v3/series` - Add show

### Lidarr Integration

**Purpose**: Music/Artist management  
**Authentication**: API Key in header  
**Key Feature**: MusicBrainz ID matching with fuzzy fallback
**Process**:
1. Search for artist in Lidarr
2. Extract MusicBrainz ID
3. Check if artist exists
4. Fall back to fuzzy name matching if search fails
5. Add artist if not duplicate

**API Endpoints Used**:
- `GET /api/v1/artist` - List artists
- `GET /api/v1/artist/lookup` - Search artists
- `GET /api/v1/rootfolder` - Get root paths
- `POST /api/v1/artist` - Add artist

### Jellyfin Integration

**Purpose**: Library browsing and duplicate detection  
**Process**:
1. Search library for media by title
2. Get media details (dates, ratings)
3. Filter recommendations to exclude library items
4. Display library statistics

**Features**:
- Date parsing with 7-digit fractional seconds support
- Media type detection (Movie/Series/MusicArtist)
- Collection browsing

### TMDb API Integration

**Purpose**: Movie/TV metadata and recommendations  
**Endpoints**:
- `/search/movie` - Search movies
- `/search/tv` - Search TV shows
- `/tv/{id}/external_ids` - Get TVDB ID for Sonarr
- `/movie/{id}/recommendations` - Get recommendations
- `/tv/{id}/recommendations` - Get TV recommendations

### Spotify Integration

**Purpose**: Music recommendations  
**Process**:
1. Authenticate with Client ID/Secret
2. Get user playlists and recommendations
3. Return artist recommendations

---

## Troubleshooting

### Database Connection Issues

**Error**: `FATAL: no pg_hba.conf entry for host`

**Solution**: 
1. Locate PostgreSQL on your network
2. Edit `/etc/postgresql/14/main/pg_hba.conf`
3. Add entry for your app host:
   ```
   host    media_management    media_user    YOUR_APP_IP/32    md5
   ```
4. Reload PostgreSQL: `sudo systemctl reload postgresql`

### Service Connection Failures

**Error**: Cannot connect to Radarr/Sonarr/Lidarr

**Debug**:
```bash
# Test connectivity
curl -I http://10.252.0.2:7878/api/v3/system/status
curl -H "X-Api-Key: YOUR_KEY" http://10.252.0.2:7878/api/v3/system/status

# Check logs
tail -f /var/www/media_manager/logs/error.log
```

### SSL Certificate Issues

**Error**: Certificate not found or expired

**Solution**:
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal
```

### Application Not Responding

**Debug**:
```bash
# Check service status
sudo systemctl status media-management

# View application logs
media-mgmt app-logs
# or
sudo tail -50 /var/www/media_manager/logs/error.log

# Check if port is in use
sudo lsof -i :5000

# Restart service
sudo systemctl restart media-management
```

### Duplicate Detection Not Working

**Debug**:
1. Verify arr service API keys in config.yaml
2. Check arr service is accessible
3. View logs for API errors
4. Test manually:
   ```bash
   curl -H "X-Api-Key: YOUR_KEY" http://10.252.0.2:7878/api/v3/movie
   ```

### Language Filtering Issues

**Issue**: Cyrillic/Russian torrents still appearing

**Solution**:
- Check Jackett categories are configured correctly
- Verify English language indexers
- Check qBittorrent download filter settings
- Review torrent naming patterns in logs

---

## File Structure

```
Media_management/
├── app/
│   ├── helpers/              # Service integrations
│   │   ├── radarr_helper.py
│   │   ├── sonarr_helper.py
│   │   ├── lidarr_helper.py
│   │   ├── jellyfin_helper.py
│   │   ├── jackett_helper.py
│   │   └── ...
│   ├── routes/               # Web routes
│   │   ├── web_routes.py
│   │   ├── admin_routes.py
│   │   ├── request_routes.py
│   │   └── ...
│   ├── templates/            # HTML templates
│   ├── static/               # CSS/JS files
│   ├── models.py             # Database models
│   ├── extensions.py         # Flask extensions
│   └── __init__.py           # Flask app factory
├── migrations/               # Database migrations
├── scripts/                  # Utility scripts
├── config.yaml               # Configuration (REDACTED)
├── config.py                 # Config loader
├── run.py                    # Development runner
├── setup.sh                  # Systemd installer
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit pull request

---

## License

[Specify your license here]

---

## Support

For issues and questions:
- Check logs: `media-mgmt app-logs`
- Review [Troubleshooting](#troubleshooting) section
- Check GitHub issues
- Contact: matt@tamsilcms.com

---

## Acknowledgments

Built with:
- Flask - Web framework
- SQLAlchemy - ORM
- PostgreSQL - Database
- Gunicorn - WSGI server
- Nginx - Reverse proxy

---

**Last Updated**: February 19, 2026  
**Version**: 2.0 (Production Ready)
