import os
import yaml

# Load configuration from the YAML file
CONFIG_PATH = 'config.yaml'

class Config:
    def __init__(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as file:
                config = yaml.safe_load(file)
        else:
            config = {}

        self.QB_API_URL = config.get('qBittorrent', {}).get('host', 'http://10.252.0.2:8080')
        self.QB_USERNAME = config.get('qBittorrent', {}).get('username', 'admin')
        self.QB_PASSWORD = config.get('qBittorrent', {}).get('password', 'changeme')

        self.JACKETT_API_URL = config.get('Jackett', {}).get('server_url', 'http://10.252.0.2:9117/')
        self.JACKETT_API_KEY = config.get('Jackett', {}).get('api_key', 'changeme')
        self.JACKETT_CATEGORIES = config.get('Jackett', {}).get('categories', {})

        self.JELLYFIN_API_KEY = config.get('Jellyfin', {}).get('api_key', 'changeme')
        self.JELLYFIN_SERVER_URL = config.get('Jellyfin', {}).get('server_url', 'http://10.252.0.2:8096')

        self.SPOTIFY_CLIENT_ID = config.get('Spotify', {}).get('client_id', '')
        self.SPOTIFY_CLIENT_SECRET = config.get('Spotify', {}).get('client_secret', '')

        self.TMDB_API_KEY = config.get('TMDb', {}).get('api_key', '')

        # Database Configuration - PostgreSQL
        db_config = config.get('Database', {})
        db_type = db_config.get('type', 'postgresql')
        
        if db_type == 'postgresql':
            db_host = db_config.get('host', 'localhost')
            db_port = db_config.get('port', 5432)
            db_username = db_config.get('username', 'media_user')
            db_password = db_config.get('password', 'changeme')
            db_name = db_config.get('database', 'media_management')
            self.SQLALCHEMY_DATABASE_URI = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'
        else:
            # Fallback to SQLite if postgresql not specified
            db_path = db_config.get('path', 'media_management.db')
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        
        self.SQLALCHEMY_TRACK_MODIFICATIONS = db_config.get('track_modifications', False)

        # Ensure the correct key casing for SECRET_KEY
        self.SECRET_KEY = config.get('Secret_key', 'default_secret_key')

        # Sonarr Configuration
        self.SONARR_API_URL = config.get('Sonarr', {}).get('api_url', 'http://10.252.0.2:8989')
        self.SONARR_API_KEY = config.get('Sonarr', {}).get('api_key', 'e6c10094e4dd457e8920d4d71736d535')

        # Radarr Configuration
        self.RADARR_API_URL = config.get('Radarr', {}).get('api_url', 'http://10.252.0.2:7878')
        self.RADARR_API_KEY = config.get('Radarr', {}).get('api_key', '99c592dd966c424abc0b5bb97e43c1c5')

        # Lidarr Configuration
        self.LIDARR_API_URL = config.get('Lidarr', {}).get('api_url', 'http://10.252.0.2:8686')
        self.LIDARR_API_KEY = config.get('Lidarr', {}).get('api_key', 'c8987dca3e874c548419f45d5bcbf52d')
