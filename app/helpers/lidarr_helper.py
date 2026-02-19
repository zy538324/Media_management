import logging
import requests # For type hinting and eventual use
from config import Config
import time

class LidarrHelper:
    def __init__(self):
        self.config = Config()
        self.api_url = self.config.LIDARR_API_URL
        self.api_key = self.config.LIDARR_API_KEY
        self.logger = logging.getLogger(__name__)

        if not self.api_url or not self.api_key:
            self.logger.warning("Lidarr API URL or API Key is not configured. LidarrHelper may not function.")

    def check_artist_exists(self, artist_name):
        """
        Check if an artist already exists in Lidarr by name (fuzzy match).
        Also searches Lidarr's API to verify against MusicBrainz.
        Returns True if exists, False otherwise.
        """
        if not self.api_url or not self.api_key:
            self.logger.error("Lidarr API URL or API Key is not configured.")
            return False

        try:
            # First, try searching Lidarr's lookup to get the MusicBrainz ID
            search_endpoint = f"{self.api_url.rstrip('/')}/api/v1/artist/lookup"
            headers = {'X-Api-Key': self.api_key}
            search_params = {'term': artist_name}
            
            try:
                search_response = requests.get(search_endpoint, params=search_params, headers=headers, timeout=10)
                search_response.raise_for_status()
                search_results = search_response.json()
                
                if search_results:
                    # Get the MusicBrainz ID from search result
                    musicbrainz_id = search_results[0].get('foreignArtistId')
                    self.logger.info(f"Found artist in search: MusicBrainz ID {musicbrainz_id}")
                    
                    # Now check if this MusicBrainz ID already exists in library
                    endpoint = f"{self.api_url.rstrip('/')}/api/v1/artist"
                    response = requests.get(endpoint, headers=headers, timeout=10)
                    response.raise_for_status()
                    artists = response.json()
                    
                    for artist in artists:
                        if artist.get('foreignArtistId') == musicbrainz_id:
                            self.logger.info(f"Artist '{artist_name}' (MBID: {musicbrainz_id}) already exists in Lidarr: {artist.get('artistName')}")
                            return True
                    
                    self.logger.info(f"Artist '{artist_name}' (MBID: {musicbrainz_id}) not found in Lidarr library")
                    return False
                    
            except Exception as search_err:
                self.logger.warning(f"Could not search Lidarr for artist: {search_err}, falling back to name match")
            
            # Fallback: Check by name (fuzzy match)
            endpoint = f"{self.api_url.rstrip('/')}/api/v1/artist"
            response = requests.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            artists = response.json()
            
            # Check if any artist has matching name (fuzzy - case insensitive, remove extra spaces)
            artist_name_normalized = ' '.join(artist_name.lower().split())
            for artist in artists:
                artist_normalized = ' '.join(artist.get('artistName', '').lower().split())
                # Exact match or partial match
                if artist_normalized == artist_name_normalized or artist_name_normalized in artist_normalized or artist_normalized in artist_name_normalized:
                    self.logger.info(f"Artist '{artist_name}' already exists in Lidarr: {artist.get('artistName')}")
                    return True
            
            self.logger.info(f"Artist '{artist_name}' not found in Lidarr")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking if artist exists in Lidarr: {e}")
            return False

    def get_root_folders(self):
        """
        Get available root folders from Lidarr
        """
        if not self.api_url or not self.api_key:
            self.logger.error("Lidarr API URL or API Key is not configured. Cannot get root folders.")
            return []

        endpoint = f"{self.api_url.rstrip('/')}/api/v1/rootfolder"
        headers = {'X-Api-Key': self.api_key}

        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            folders = response.json()
            self.logger.info(f"Found {len(folders)} root folders in Lidarr")
            for folder in folders:
                self.logger.info(f"  - {folder.get('path')}")
            return folders
        except Exception as e:
            self.logger.error(f"Error getting root folders from Lidarr: {e}")
            return []

    def search_musicbrainz_artist(self, artist_name):
        """
        Search MusicBrainz API directly for an artist.
        Returns the MusicBrainz ID if found, None otherwise.
        """
        self.logger.info(f"Searching MusicBrainz for artist: {artist_name}")
        
        try:
            # MusicBrainz API endpoint
            url = "https://musicbrainz.org/ws/2/artist"
            headers = {
                'User-Agent': 'MediaManagementApp/1.0 (contact: admin@localhost)'
            }
            params = {
                'query': f'artist:"{artist_name}"',
                'fmt': 'json',
                'limit': 5
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'artists' in data and len(data['artists']) > 0:
                # Get the first/best match
                artist = data['artists'][0]
                mbid = artist.get('id')
                name = artist.get('name')
                self.logger.info(f"Found MusicBrainz ID: {mbid} for artist: {name}")
                return mbid
            else:
                self.logger.warning(f"No MusicBrainz results for artist: {artist_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error searching MusicBrainz for artist '{artist_name}': {e}")
            return None

    def add_artist(self, artist_id, artist_name, root_folder_path=None, quality_profile_id=1, metadata_profile_id=1, monitored=True, search_for_albums=True):
        """
        Adds an artist to Lidarr by searching for them first.
        Note: Lidarr requires a MusicBrainz ID, so we search for the artist first.
        Falls back to MusicBrainz API if Lidarr lookup fails.
        """
        if not self.api_url or not self.api_key:
            self.logger.error("Lidarr API URL or API Key is not configured. Cannot add artist.")
            return False

        # If root_folder_path not provided, get it from Lidarr
        if not root_folder_path:
            folders = self.get_root_folders()
            if folders:
                root_folder_path = folders[0].get('path')
                self.logger.info(f"Using root folder from Lidarr: {root_folder_path}")
            else:
                self.logger.error("Could not determine root folder path for Lidarr")
                return False

        self.logger.info(
            f"Attempting to add artist to Lidarr: artist_name='{artist_name}', "
            f"root_folder_path='{root_folder_path}', quality_profile_id={quality_profile_id}, "
            f"metadata_profile_id={metadata_profile_id}"
        )

        # First, try to search for the artist in Lidarr to get the MusicBrainz ID
        self.logger.info(f"Searching Lidarr for artist: {artist_name}")
        search_endpoint = f"{self.api_url.rstrip('/')}/api/v1/artist/lookup"
        headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        search_params = {'term': artist_name}
        musicbrainz_id = None
        
        try:
            response = requests.get(search_endpoint, params=search_params, headers=headers, timeout=10)
            response.raise_for_status()
            search_results = response.json()
            
            if search_results and len(search_results) > 0:
                # Use the first result
                artist_data = search_results[0]
                musicbrainz_id = artist_data.get('foreignArtistId')
                self.logger.info(f"Found artist in Lidarr: {artist_data.get('artistName')} (MusicBrainz ID: {musicbrainz_id})")
            else:
                self.logger.warning(f"No results from Lidarr artist lookup for: {artist_name}")
                
        except requests.exceptions.HTTPError as e:
            # If Lidarr lookup fails (503, 500, etc.), fall back to MusicBrainz
            self.logger.warning(f"Lidarr artist lookup failed ({e.response.status_code}), falling back to MusicBrainz API")
            time.sleep(1)  # Rate limit - be nice to external APIs
            
        except Exception as e:
            self.logger.warning(f"Error during Lidarr artist lookup: {e}, falling back to MusicBrainz API")
            time.sleep(1)
        
        # If we don't have a MusicBrainz ID yet, try MusicBrainz directly
        if not musicbrainz_id:
            self.logger.info("Attempting to get MusicBrainz ID from MusicBrainz API")
            musicbrainz_id = self.search_musicbrainz_artist(artist_name)
        
        if not musicbrainz_id:
            self.logger.error(f"Could not find MusicBrainz ID for artist: {artist_name}")
            return False
        
        # Now add the artist using the MusicBrainz ID
        add_endpoint = f"{self.api_url.rstrip('/')}/api/v1/artist"
        
        payload = {
            'artistName': artist_name,
            'foreignArtistId': musicbrainz_id,  # Use the MusicBrainz ID
            'qualityProfileId': quality_profile_id,
            'metadataProfileId': metadata_profile_id,
            'rootFolderPath': root_folder_path,
            'monitored': monitored,
            'addOptions': {
                'searchForMissingAlbums': search_for_albums
            }
        }
        
        self.logger.info(f"Lidarr add_artist endpoint: {add_endpoint}")
        self.logger.info(f"Lidarr add_artist payload: {payload}")
        
        try:
            response = requests.post(add_endpoint, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Artist '{artist_name}' added to Lidarr successfully. Response: {response.json()}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error adding artist '{artist_name}' to Lidarr: {e}")
            try:
                self.logger.error(f"Lidarr response content: {response.text}")
            except:
                pass
            return False

    def search_artist(self, term):
        """
        Searches for artists in Lidarr based on a search term.
        (Placeholder implementation)
        """
        self.logger.info(f"Searching Lidarr for artist term: '{term}'")

        if not self.api_url or not self.api_key:
            self.logger.error("Lidarr API URL or API Key is not configured. Cannot search artist.")
            return []

        # Lidarr API endpoint for searching/looking up artists
        endpoint = f"{self.api_url.rstrip('/')}/api/v1/artist/lookup"

        headers = {
            'X-Api-Key': self.api_key
        }

        params = {
            'term': term
        }

        self.logger.info(f"Lidarr search_artist endpoint: {endpoint}")
        self.logger.info(f"Lidarr search_artist params: {params}")
        self.logger.info(f"Lidarr search_artist X-Api-Key: {headers.get('X-Api-Key', 'Key_Not_Set')[:5]}...")

        # Placeholder for the actual request:
        # try:
        #     response = requests.get(endpoint, params=params, headers=headers)
        #     response.raise_for_status()
        #     artist_list = response.json()
        #     self.logger.info(f"Lidarr search for '{term}' found {len(artist_list)} artist(s).")
        #     return artist_list
        # except requests.exceptions.RequestException as e:
        #     self.logger.error(f"Error searching Lidarr for '{term}': {e}")
        #     return []

        self.logger.info("Placeholder: Lidarr artist search 'simulated', returning empty list.")
        return []

if __name__ == '__main__':
    # Example usage (for testing purposes, if run directly)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Testing LidarrHelper...")

    class MockConfigLidarr: # Renamed for clarity
        LIDARR_API_URL = "http://localhost:8686" # Replace with your actual Lidarr URL if testing
        LIDARR_API_KEY = "YOUR_LIDARR_API_KEY"    # Replace with your actual Lidarr API key if testing
        # Provide other keys if Config class expects them, or make Mock more specific
        SONARR_API_URL = ""
        SONARR_API_KEY = ""
        RADARR_API_URL = ""
        RADARR_API_KEY = ""
        QB_API_URL = ""
        QB_USERNAME = ""
        QB_PASSWORD = ""
        JACKETT_API_URL = ""
        JACKETT_API_KEY = ""
        JACKETT_CATEGORIES = {}
        JELLYFIN_API_KEY = ""
        JELLYFIN_SERVER_URL = ""
        SPOTIFY_CLIENT_ID = ""
        SPOTIFY_CLIENT_SECRET = ""
        TMDB_API_KEY = ""
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SECRET_KEY = "testsecret"

    original_config_lidarr = Config # Save original Config
    Config = MockConfigLidarr # Temporarily override Config with mock

    helper = LidarrHelper()

    if helper.api_key == "YOUR_LIDARR_API_KEY" or not helper.api_url:
        logger.warning("Lidarr API URL or Key is using placeholder values from MockConfigLidarr. Update MockConfigLidarr for real testing.")
        if not helper.api_url: helper.api_url = "http://lidarr.example.com" # Dummy URL for test execution
        if helper.api_key == "YOUR_LIDARR_API_KEY": helper.api_key = "test_api_key_lidarr" # Dummy key

    helper.search_artist("Queen")
    helper.add_artist(musicbrainz_id="0383dadf-2a4e-4d10-a46a-e9e041da8eb3", artist_name="Queen", root_folder_path='/music/')

    Config = original_config_lidarr # Restore original Config
    logger.info("LidarrHelper test finished.")
