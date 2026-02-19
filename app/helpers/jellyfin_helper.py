import requests
import logging
from config import Config
from app.models import db, Media
from datetime import datetime
import sqlite3
import re

logging.basicConfig(level=logging.INFO)

def parse_jellyfin_date(date_string):
    """Parse Jellyfin datetime strings that may have 7 fractional second digits"""
    if not date_string:
        return None
    
    try:
        # Jellyfin sometimes returns 7 fractional digits instead of 6
        # Remove extra fractional seconds digits
        date_string = re.sub(r'(\.\d{6})\d+Z', r'\1Z', date_string)
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').date()
    except:
        return None

class JellyfinHelper:
    def __init__(self):
        config = Config()
        self.server_url = config.JELLYFIN_SERVER_URL
        self.api_key = config.JELLYFIN_API_KEY

        if not self.server_url or not self.api_key:
            logging.warning("Jellyfin configuration is missing 'server_url' or 'api_key'.")
            self.server_url = None
            self.api_key = None
    
    def get_media_items(self, media_type='Movie'):
        """Fetch all media items of a specific type from Jellyfin."""
        if not self.server_url or not self.api_key:
            logging.error("Jellyfin is not properly configured")
            return []

        # Determine the relevant Jellyfin collection type based on media_type
        collection_type = "movies" if media_type.lower() == 'movie' else "tvshows"
        
        # API endpoint for items
        endpoint = f"{self.server_url}/Items"
        
        # Parameters for the request
        params = {
            'api_key': self.api_key,
            'IncludeItemTypes': media_type,
            'Recursive': 'true',
            'SortBy': 'SortName',
            'SortOrder': 'Ascending'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('Items', [])
            logging.info(f"Retrieved {len(items)} {media_type}s from Jellyfin")
            return items
        except Exception as e:
            logging.error(f"Error retrieving {media_type}s from Jellyfin: {e}")
            return []
            
    def save_items_to_db(self):
        """Fetch movies and TV shows from Jellyfin and save them to the SQLite database."""
        movies = self.get_media_items('Movie')
        tv_shows = self.get_media_items('Series')
        
        try:
            # Clear the Media table - use SQLite syntax
            Media.query.delete()
            db.session.commit()
            
            # Add movies to database
            for movie in movies:
                media = Media(
                    media_type='Movie',
                    title=movie.get('Name', 'Unknown'),
                    release_date=parse_jellyfin_date(movie.get('PremiereDate')),
                    description=movie.get('Overview', ''),
                    path=movie.get('Path', ''),
                    status='Available'
                )
                db.session.add(media)
            
            # Add TV shows to database
            for show in tv_shows:
                media = Media(
                    media_type='TV Show',
                    title=show.get('Name', 'Unknown'),
                    release_date=parse_jellyfin_date(show.get('PremiereDate')),
                    description=show.get('Overview', ''),
                    path=show.get('Path', ''),
                    status='Available'
                )
                db.session.add(media)
            
            db.session.commit()
            logging.info(f"Successfully saved {len(movies)} movies and {len(tv_shows)} TV shows to database")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving media to database: {e}")
            return False