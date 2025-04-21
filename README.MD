# Media Management System

A comprehensive media management solution to organize, request, and download your media library. This application integrates with popular services such as Jellyfin, Jackett, qBittorrent, TMDb, and Spotify.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Ubuntu/Linux Installation](#ubuntulinux-installation)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
  - [Setting Up Required APIs](#setting-up-required-apis)
  - [Additional Configuration](#additional-configuration)
- [Usage](#usage)
- [First-Time Setup](#first-time-setup)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

This Media Management System allows you to track, request, download, and organize your media collection. With integrations to popular media services, you can easily manage your entire library from a single interface.

## Features

- **Media Library Management**: Track your movies, TV shows, and music
- **Media Requests**: Allow users to request new content
- **Automated Downloads**: Automatically search and download requested media using Jackett and qBittorrent
- **Recommendations**: Get personalized recommendations based on your library from TMDb
- **Multi-user Support**: User account management with different permission levels
- **Jellyfin Integration**: Sync with your Jellyfin media server
- **Lightweight Database**: Uses SQLite for simple deployment and maintenance

## Requirements

- Python 3.8+
- qBittorrent (with Web UI enabled)
- Jackett
- Jellyfin (optional)
- API keys for:
  - TMDb
  - Spotify (optional)

## Installation

### Ubuntu/Linux Installation

We provide an automated installer for Ubuntu and other Linux distributions:

1. Download the installer script:

```bash
curl -O https://raw.githubusercontent.com/zy538324/Media_management/main/install_service.sh
```

2. Make it executable:

```bash
chmod +x install_service.sh
```

3. Run the installer:

```bash
sudo ./install_service.sh
```

4. Access your application at http://your-server-ip:5000

### Manual Installation

1. Clone the repository:

```bash
git clone https://github.com/zy538324/Media_management.git
cd Media_management
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install requirements:

```bash
pip install -r requirements.txt
```

4. Initialize the database:

```bash
python init_db.py
```

5. Run the application:

```bash
python run.py
```

## Configuration

Copy the example configuration file and edit it:

```bash
cp config.yaml.example config.yaml
```

### Setting Up Required APIs

#### TMDb API

1. Go to [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
2. Create an account if needed
3. Request an API key (select "Developer" option)
4. Add the API key to your `config.yaml` file

#### Spotify API (Optional)

1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new application
3. Note your Client ID and Client Secret
4. Add these to your `config.yaml` file

#### Jackett Configuration

1. Install Jackett from [Jackett's GitHub](https://github.com/Jackett/Jackett/releases)
2. Access the Jackett web interface (default: http://localhost:9117)
3. Add your preferred torrent indexers
4. Copy the API Key from Jackett's dashboard
5. Add the API Key and server URL to `config.yaml`

#### qBittorrent Setup

1. Install qBittorrent
2. Enable Web UI in Preferences > Web UI
3. Set a username and password
4. Add these credentials to `config.yaml`

#### Jellyfin Setup (Optional)

1. Install Jellyfin from [jellyfin.org](https://jellyfin.org/downloads)
2. Complete the initial setup
3. Generate an API key in Admin > Dashboard > API Keys
4. Add the API key and server URL to `config.yaml`

### Additional Configuration

Edit `config.yaml` with your configuration values:

```yaml
Database:
  path: media_management.db
  track_modifications: false
Jackett:
  api_key: your_jackett_api_key_here
  categories:
    Movies: '2000'
    Music: '3000'
    TV: '5000'
  server_url: http://localhost:9117/
Jellyfin:
  api_key: your_jellyfin_api_key_here
  server_url: http://localhost:8096
Secret_key: generate_a_secure_random_string
Spotify:
  client_id: your_spotify_client_id
  client_secret: your_spotify_client_secret
TMDb:
  api_key: your_tmdb_api_key
qBittorrent:
  host: http://localhost:8080
  password: your_qbittorrent_password
  username: your_qbittorrent_username
```

## Usage

After installation and configuration:

1. Start the application:
   - For Ubuntu service installation: `sudo media_management start`
   - For manual installation: `python run.py`

2. Access the web interface at: http://localhost:5000

3. Register a user account (the first account will be created as admin)

4. Start managing your media library!

## First-Time Setup

When you first run the application, you can create an admin user by running:

```bash
python user.py
```

This will create a default admin user with the username "Lisa" (you can modify the script to change these credentials before running).

## Managing the Service (Ubuntu Installation)

If you installed using the service script, you can manage the application with:

```bash
media_management start    # Start the service
media_management stop     # Stop the service
media_management restart  # Restart the service
media_management status   # Check status
media_management logs     # View logs
media_management update   # Update from GitHub
```

## Troubleshooting

### Service Won't Start

Check the logs for detailed error messages:

```bash
sudo journalctl -u media_management -n 50
```

Common issues:
- Database path isn't writable
- Configuration file missing or has invalid values
- Required services (qBittorrent, Jackett) are not accessible

### API Connections Failing

Ensure your API keys are correct and the services are accessible from your server:

```bash
# Test qBittorrent connection
python -c "import requests; print(requests.get('http://your-qbittorrent-host:port/api/v2/app/version'))"

# Test Jackett connection
python -c "import requests; print(requests.get('http://your-jackett-host:port/api/v2.0/indexers/status', headers={'X-Api-Key': 'your-api-key'}))"
```

### Template Not Found Errors

If you're seeing template errors in the logs, ensure all templates are correctly named and located in the `app/templates` directory.

### Database Errors

If you encounter database errors, try reinitializing the database:

```bash
python init_db.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 



## Disclaimer
I take no responsibility for the usage of this I have built this purely as an educational project, any usage of this application is down to the end user.

---

For any questions or issues, please open an issue on the [GitHub repository](https://github.com/zy538324/Media_management).
