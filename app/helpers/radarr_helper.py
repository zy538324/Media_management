import logging
import requests # For type hinting and eventual use
from config import Config

class RadarrHelper:
    def __init__(self):
        self.config = Config()
        self.api_url = self.config.RADARR_API_URL
        self.api_key = self.config.RADARR_API_KEY
        self.logger = logging.getLogger(__name__)

        if not self.api_url or not self.api_key:
            self.logger.warning("Radarr API URL or API Key is not configured. RadarrHelper may not function.")

    def add_movie(self, tmdb_id, title, quality_profile_id=1, root_folder_path='/movies/'):
        """
        Adds a movie to Radarr.
        (Placeholder implementation)
        """
        self.logger.info(
            f"Attempting to add movie to Radarr: tmdb_id={tmdb_id}, title='{title}', "
            f"quality_profile_id={quality_profile_id}, root_folder_path='{root_folder_path}'"
        )

        if not self.api_url or not self.api_key:
            self.logger.error("Radarr API URL or API Key is not configured. Cannot add movie.")
            return False

        # Radarr API endpoint for adding a movie
        endpoint = f"{self.api_url.rstrip('/')}/api/v3/movie"

        # Request payload structure
        payload = {
            'title': title,
            'tmdbId': tmdb_id,
            'qualityProfileId': quality_profile_id,
            'rootFolderPath': root_folder_path,
            'monitored': True,  # Typically you want to monitor new additions
            'addOptions': {
                'searchForMovie': True  # Search for the movie after adding
            }
        }

        # Headers for the API request
        headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }

        self.logger.info(f"Radarr add_movie endpoint: {endpoint}")
        self.logger.info(f"Radarr add_movie payload: {payload}")
        self.logger.info(f"Radarr add_movie headers: {headers.get('X-Api-Key', 'Key_Not_Set')[:5]}...") # Log first 5 chars of key for verification

        # Placeholder for the actual request:
        # try:
        #     response = requests.post(endpoint, json=payload, headers=headers)
        #     response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        #     self.logger.info(f"Movie '{title}' added to Radarr successfully. Response: {response.json()}")
        #     return True
        # except requests.exceptions.RequestException as e:
        #     self.logger.error(f"Error adding movie '{title}' to Radarr: {e}")
        #     return False

        self.logger.info("Placeholder: Movie add operation 'simulated' successfully.")
        return True # Simulate success for now

    def search_movie(self, term):
        """
        Searches for movies in Radarr based on a search term.
        (Placeholder implementation)
        """
        self.logger.info(f"Searching Radarr for movie term: '{term}'")

        if not self.api_url or not self.api_key:
            self.logger.error("Radarr API URL or API Key is not configured. Cannot search movie.")
            return []

        # Radarr API endpoint for searching movies
        # The term should be URL encoded by requests library if passed in params
        endpoint = f"{self.api_url.rstrip('/')}/api/v3/movie/lookup"

        headers = {
            'X-Api-Key': self.api_key
        }

        params = {
            'term': term
        }

        self.logger.info(f"Radarr search_movie endpoint: {endpoint}")
        self.logger.info(f"Radarr search_movie params: {params}")
        self.logger.info(f"Radarr search_movie headers: {headers.get('X-Api-Key', 'Key_Not_Set')[:5]}...")

        # Placeholder for the actual request:
        # try:
        #     response = requests.get(endpoint, params=params, headers=headers)
        #     response.raise_for_status()
        #     movies = response.json()
        #     self.logger.info(f"Radarr search for '{term}' found {len(movies)} movie(s).")
        #     return movies
        # except requests.exceptions.RequestException as e:
        #     self.logger.error(f"Error searching Radarr for '{term}': {e}")
        #     return []

        self.logger.info("Placeholder: Radarr movie search 'simulated', returning empty list.")
        return []

if __name__ == '__main__':
    # Example usage (for testing purposes, if run directly)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Testing RadarrHelper...")

    # Mock Config for direct script execution if config.yaml isn't fully set up for Radarr
    class MockConfig:
        RADARR_API_URL = "http://localhost:7878" # Replace with your actual Radarr URL if testing
        RADARR_API_KEY = "YOUR_RADARR_API_KEY"    # Replace with your actual Radarr API key if testing

    # Monkey patch Config for this test block
    original_config = Config
    Config = MockConfig

    helper = RadarrHelper()
    if not helper.api_url or not helper.api_key or helper.api_key == "YOUR_RADARR_API_KEY":
        logger.warning("Radarr API URL or Key is not set in MockConfig. Using placeholder values for test.")
        # Provide dummy values if not configured, to allow test execution
        if not helper.api_url: helper.api_url = "http://radarr.example.com"
        if not helper.api_key or helper.api_key == "YOUR_RADARR_API_KEY": helper.api_key = "test_api_key_radarr"


    helper.search_movie("Inception")
    helper.add_movie(tmdb_id=157336, title="Interstellar")

    # Restore original Config
    Config = original_config
    logger.info("RadarrHelper test finished.")
