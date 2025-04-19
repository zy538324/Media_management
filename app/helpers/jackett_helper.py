import requests
import re
import logging
import time
from config import Config
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

# Configure logging
LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure the logs directory exists
LOG_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_warnings.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5),  # Rotate logs
    ],
)

class JackettHelper:
    def __init__(self):
        config = Config()
        self.api_url = config.JACKETT_API_URL
        self.api_key = config.JACKETT_API_KEY
        self.failed_search_cache = {}
        self.categories = {
            "Movies": 2000,
            "TV": 5000,
            "Music": 3000
        }

        if not self.api_url or not self.api_key:
            logging.warning("Jackett API key or URL is missing. Check your configuration.")
            self.api_url = None
            self.api_key = None

    @staticmethod
    def format_query(query, category):
        """Format the query for Jackett search."""
        if category == "Movies":
            query = re.sub(r'\(\d{4}\)$', '', query)  # Remove year from movie titles
            query = re.sub(r'[^\w\s]', '', query)      # Remove special characters
            query = f"{query} 1080p" if "1080p" not in query else query  # Add resolution keyword
        elif category == "TV":
            query = re.sub(r'[^\w\s]', '', query)      # Remove special characters
            query = f"{query} S01" if "S01" not in query else query  # Add season keyword
        return query.strip()

    @staticmethod
    def normalize_media_type(media_type):
        """
        Normalize the media type to match Jackett's category naming convention.

        Args:
            media_type (str): Media type from external sources.

        Returns:
            str: Normalized category name.
        """
        mappings = {
            "TV Show": "TV",
            "Movie": "Movies",
            "Music": "Music"
        }
        return mappings.get(media_type, media_type)

    def search_jackett(self, query, category="Movies"):
        """
        Perform a search on Jackett for the given query and category.

        Args:
            query (str): Search term (e.g., movie or show name).
            category (str): Category of search (e.g., "Movies", "TV", "Music").

        Returns:
            list: A list of sorted results with seeders and magnet URIs.
        """
        logging.info(f"Searching Jackett for: {query} in category: {category}")

        # Format the query
        formatted_query = self.format_query(query, category)
        if formatted_query in self.failed_search_cache:
            logging.info(f"Skipping search for '{formatted_query}' (cached as failed).")
            return []

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Build request URL and parameters
                url = f"{self.api_url}/api/v2.0/indexers/all/results"
                params = {
                    'apikey': self.api_key,
                    'Query': formatted_query,
                    'Category[]': self.categories.get(category, 2000)  # Default to "Movies" category
                }

                # Send the request to Jackett
                logging.info(f"Sending request to Jackett: {url}")
                response = requests.get(url, params=params, timeout=10)  # Add a timeout
                response.raise_for_status()

                # Parse the response
                data = response.json()
                results = data.get('Results', [])
                if not results:
                    logging.warning(f"No results found for query: {formatted_query}.")
                    self.failed_search_cache[formatted_query] = time.time()
                    return []

                # Filter and sort results by seeders and ensure valid magnet links
                valid_results = [
                    {
                        'title': result.get('Title', 'Unknown Title'),
                        'seeders': result.get('Seeders', 0),
                        'magnet': result.get('MagnetUri')
                    }
                    for result in results
                    if result.get('Seeders', 0) > 0 and result.get('MagnetUri')
                ]
                sorted_results = sorted(valid_results, key=lambda r: r['seeders'], reverse=True)

                if not sorted_results:
                    logging.warning(f"No suitable results with seeders found for query: {formatted_query}.")
                    self.failed_search_cache[formatted_query] = time.time()
                    return []

                # Log the results
                logging.info(f"Results found: {len(sorted_results)}")
                for result in sorted_results:
                    logging.info(
                        f"Title: {result['title']} | Seeders: {result['seeders']} | Magnet: {result['magnet']}"
                    )

                return sorted_results

            except requests.RequestException as e:
                logging.error(f"Request error on attempt {attempt + 1}/{max_retries} for query '{formatted_query}': {e}")
                time.sleep(2 ** attempt)  # Exponential backoff for retries

            except Exception as e:
                logging.error(f"Unexpected error during search for query '{formatted_query}': {e}", exc_info=True)
                break

        logging.error(f"All attempts to contact Jackett failed for query: {formatted_query}")
        return []