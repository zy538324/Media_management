import logging
import requests # For type hinting and eventual use
from config import Config

class SonarrHelper:
    def __init__(self):
        self.config = Config()
        self.api_url = self.config.SONARR_API_URL
        self.api_key = self.config.SONARR_API_KEY
        self.logger = logging.getLogger(__name__)

        if not self.api_url or not self.api_key:
            self.logger.warning("Sonarr API URL or API Key is not configured. SonarrHelper may not function.")

    def check_series_exists(self, tvdb_id):
        """
        Check if a series already exists in Sonarr by TVDB ID.
        Returns True if exists, False otherwise.
        """
        if not self.api_url or not self.api_key:
            self.logger.error("Sonarr API URL or API Key is not configured.")
            return False

        try:
            endpoint = f"{self.api_url.rstrip('/')}/api/v3/series"
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            series_list = response.json()
            
            # Check if any series has matching TVDB ID
            for series in series_list:
                if series.get('tvdbId') == tvdb_id:
                    self.logger.info(f"Series with TVDB ID {tvdb_id} already exists in Sonarr: {series.get('title')}")
                    return True
            
            self.logger.info(f"Series with TVDB ID {tvdb_id} not found in Sonarr")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking if series exists in Sonarr: {e}")
            return False

    def get_root_folders(self):
        """
        Get available root folders from Sonarr
        """
        if not self.api_url or not self.api_key:
            self.logger.error("Sonarr API URL or API Key is not configured. Cannot get root folders.")
            return []

        endpoint = f"{self.api_url.rstrip('/')}/api/v3/rootfolder"
        headers = {'X-Api-Key': self.api_key}

        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            folders = response.json()
            self.logger.info(f"Found {len(folders)} root folders in Sonarr")
            for folder in folders:
                self.logger.info(f"  - {folder.get('path')}")
            return folders
        except Exception as e:
            self.logger.error(f"Error getting root folders from Sonarr: {e}")
            return []

    def add_series(self, tvdb_id, title, quality_profile_id=1, root_folder_path=None, language_profile_id=1, season_folder=True, monitored=True, search_for_missing_episodes=True):
        """
        Adds a series to Sonarr.

        Standard quality_profile_id and language_profile_id is 1.
        Adjust if your Sonarr setup uses different defaults.
        """
        if not self.api_url or not self.api_key:
            self.logger.error("Sonarr API URL or API Key is not configured. Cannot add series.")
            return False

        # If root_folder_path not provided, get it from Sonarr
        if not root_folder_path:
            folders = self.get_root_folders()
            if folders:
                root_folder_path = folders[0].get('path')
                self.logger.info(f"Using root folder from Sonarr: {root_folder_path}")
            else:
                self.logger.error("Could not determine root folder path for Sonarr")
                return False

        self.logger.info(
            f"Attempting to add series to Sonarr: tvdb_id={tvdb_id}, title='{title}', "
            f"quality_profile_id={quality_profile_id}, root_folder_path='{root_folder_path}', "
            f"language_profile_id={language_profile_id}"
        )

        # Sonarr API endpoint for adding a series
        endpoint = f"{self.api_url.rstrip('/')}/api/v3/series"

        # Request payload structure
        # Sonarr requires tvdbId, qualityProfileId, languageProfileId, rootFolderPath, title
        # It also needs seasonFolder, monitored, and addOptions for behavior
        payload = {
            'title': title,
            'tvdbId': tvdb_id,
            'qualityProfileId': quality_profile_id,
            'languageProfileId': language_profile_id, # Typically 1 for English, check your Sonarr setup
            'rootFolderPath': root_folder_path,
            'seasons': [], # Add all seasons by default, or specify particular seasons
            'seasonFolder': season_folder, # Create a folder for each season
            'monitored': monitored,  # Monitor the series for new episodes
            'addOptions': {
                'ignoreEpisodesWithFiles': False,
                'ignoreEpisodesWithoutFiles': False,
                'searchForMissingEpisodes': search_for_missing_episodes  # Search for missing episodes after adding
            }
        }

        # Headers for the API request
        headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }

        self.logger.info(f"Sonarr add_series endpoint: {endpoint}")
        self.logger.info(f"Sonarr add_series payload: {payload}")
        self.logger.info(f"Sonarr add_series X-Api-Key: {headers.get('X-Api-Key', 'Key_Not_Set')[:5]}...") # Log first 5 chars

        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            self.logger.info(f"Series '{title}' added to Sonarr successfully. Response: {response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error adding series '{title}' to Sonarr: {e}")
            if response is not None:
                self.logger.error(f"Sonarr response content: {response.text}")
            return False

    def search_series(self, term):
        """
        Searches for series in Sonarr based on a search term.
        (Placeholder implementation)
        """
        self.logger.info(f"Searching Sonarr for series term: '{term}'")

        if not self.api_url or not self.api_key:
            self.logger.error("Sonarr API URL or API Key is not configured. Cannot search series.")
            return []

        # Sonarr API endpoint for searching/looking up series
        endpoint = f"{self.api_url.rstrip('/')}/api/v3/series/lookup"

        headers = {
            'X-Api-Key': self.api_key
        }

        params = {
            'term': term # Sonarr uses 'term' for lookup
        }

        self.logger.info(f"Sonarr search_series endpoint: {endpoint}")
        self.logger.info(f"Sonarr search_series params: {params}")
        self.logger.info(f"Sonarr search_series X-Api-Key: {headers.get('X-Api-Key', 'Key_Not_Set')[:5]}...")

        # Placeholder for the actual request:
        # try:
        #     response = requests.get(endpoint, params=params, headers=headers)
        #     response.raise_for_status()
        #     series_list = response.json()
        #     self.logger.info(f"Sonarr search for '{term}' found {len(series_list)} series.")
        #     return series_list
        # except requests.exceptions.RequestException as e:
        #     self.logger.error(f"Error searching Sonarr for '{term}': {e}")
        #     return []

        self.logger.info("Placeholder: Sonarr series search 'simulated', returning empty list.")
        return []

if __name__ == '__main__':
    # Example usage (for testing purposes, if run directly)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__) # Use __name__ for the logger in the main block too
    logger.info("Testing SonarrHelper...")

    # Mock Config for direct script execution if config.yaml isn't fully set up for Sonarr
    class MockConfigSonarr: # Renamed to avoid conflict if other helpers are tested together
        SONARR_API_URL = "http://localhost:8989" # Replace with your actual Sonarr URL if testing
        SONARR_API_KEY = "YOUR_SONARR_API_KEY"    # Replace with your actual Sonarr API key if testing
        # Need to provide other keys if Config class expects them, or make Mock more specific
        RADARR_API_URL = ""
        RADARR_API_KEY = ""
        LIDARR_API_URL = ""
        LIDARR_API_KEY = ""
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


    original_config_sonarr = Config # Save original Config
    Config = MockConfigSonarr # Temporarily override Config with mock

    helper = SonarrHelper()

    # Check if the mock values are still the placeholder ones
    if helper.api_key == "YOUR_SONARR_API_KEY" or not helper.api_url:
        logger.warning("Sonarr API URL or Key is using placeholder values from MockConfigSonarr. Update MockConfigSonarr for real testing.")
        # Provide dummy values if not configured, to allow test execution without real creds
        if not helper.api_url: helper.api_url = "http://sonarr.example.com"
        if helper.api_key == "YOUR_SONARR_API_KEY": helper.api_key = "test_api_key_sonarr"


    helper.search_series("The Simpsons")
    helper.add_series(tvdb_id=71663, title="The Simpsons", quality_profile_id=1, root_folder_path='/tv/')

    Config = original_config_sonarr # Restore original Config
    logger.info("SonarrHelper test finished.")
