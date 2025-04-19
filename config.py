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

        self.QB_API_URL = config.get('qBittorrent', {}).get('host', 'http://127.0.0.1:8080')
        self.QB_USERNAME = config.get('qBittorrent', {}).get('username', 'admin')
        self.QB_PASSWORD = config.get('qBittorrent', {}).get('password', '')

        self.JACKETT_API_URL = config.get('Jackett', {}).get('server_url', 'http://127.0.0.1:9117/')
        self.JACKETT_API_KEY = config.get('Jackett', {}).get('api_key', '')
        self.JACKETT_CATEGORIES = config.get('Jackett', {}).get('categories', {})

        self.JELLYFIN_API_KEY = config.get('Jellyfin', {}).get('api_key', '')
        self.JELLYFIN_SERVER_URL = config.get('Jellyfin', {}).get('server_url', '')

        self.SPOTIFY_CLIENT_ID = config.get('Spotify', {}).get('client_id', '')
        self.SPOTIFY_CLIENT_SECRET = config.get('Spotify', {}).get('client_secret', '')

        self.TMDB_API_KEY = config.get('TMDb', {}).get('api_key', '')

        # SQLite Configuration - replaces MySQL config
        db_path = config.get('Database', {}).get('path', 'media_management.db')
        self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        self.SQLALCHEMY_TRACK_MODIFICATIONS = config.get('Database', {}).get('track_modifications', False)

        # Ensure the correct key casing for SECRET_KEY
        self.SECRET_KEY = config.get('Secret_key', 'default_secret_key')