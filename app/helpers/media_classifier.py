import logging
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MediaService(Enum):
    """Target service for media request routing."""
    SONARR = "sonarr"
    RADARR = "radarr"
    LIDARR = "lidarr"
    UNKNOWN = "unknown"


class MediaType(Enum):
    """Detected media type."""
    MOVIE = "movie"
    TV_SERIES = "tv"
    MUSIC = "music"
    UNKNOWN = "unknown"


@dataclass
class MediaMatch:
    """Represents a potential media match with classification metadata."""
    title: str
    media_type: MediaType
    service: MediaService
    confidence: float  # 0.0 to 1.0
    external_id: Optional[str] = None  # TMDB ID, TVDB ID, or MusicBrainz ID
    year: Optional[int] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    additional_data: Optional[Dict] = None

    def __repr__(self):
        return f"MediaMatch('{self.title}', {self.media_type.value}, confidence={self.confidence:.2f})"


class MediaClassifier:
    """
    Intelligent media classification engine that determines whether user requests
    should route to Sonarr (TV), Radarr (Movies), or Lidarr (Music).
    
    Classification strategy:
    1. Query TMDb for movies and TV shows
    2. Query Spotify/MusicBrainz for music
    3. Score results based on relevance, popularity, and metadata quality
    4. Return ranked matches with confidence scores
    """

    def __init__(self):
        config = Config()
        self.tmdb_api_key = config.TMDB_API_KEY
        self.spotify_client_id = config.SPOTIFY_CLIENT_ID
        self.spotify_client_secret = config.SPOTIFY_CLIENT_SECRET
        
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.musicbrainz_base_url = "https://musicbrainz.org/ws/2"
        self.spotify_token = None
        
        if not self.tmdb_api_key:
            logging.warning("TMDb API key not configured. Movie/TV classification will fail.")
        
        if not self.spotify_client_id or not self.spotify_client_secret:
            logging.warning("Spotify credentials not configured. Music classification via Spotify will be limited.")

    def classify(self, query: str, limit: int = 10) -> List[MediaMatch]:
        """
        Classify a user's media request and return ranked potential matches.
        
        Args:
            query: User's search query (e.g., "Dexter", "Breaking Bad", "Taylor Swift")
            limit: Maximum number of results to return
            
        Returns:
            List of MediaMatch objects sorted by confidence score (highest first)
        """
        logging.info(f"Classifying media request: '{query}'")
        
        all_matches = []
        
        # Parallel search across all services
        all_matches.extend(self._search_tmdb_movies(query))
        all_matches.extend(self._search_tmdb_tv(query))
        all_matches.extend(self._search_music(query))
        
        # Sort by confidence score (descending)
        all_matches.sort(key=lambda m: m.confidence, reverse=True)
        
        # Log classification results
        if all_matches:
            logging.info(f"Found {len(all_matches)} potential matches for '{query}'")
            for i, match in enumerate(all_matches[:3]):
                logging.info(f"  {i+1}. {match}")
        else:
            logging.warning(f"No matches found for '{query}'")
        
        return all_matches[:limit]

    def get_best_match(self, query: str) -> Optional[MediaMatch]:
        """
        Get the single best match for a query.
        Returns None if no confident match is found.
        """
        matches = self.classify(query, limit=1)
        if matches and matches[0].confidence >= 0.5:  # Minimum confidence threshold
            return matches[0]
        return None

    def has_ambiguity(self, query: str, threshold: float = 0.15) -> bool:
        """
        Determine if a query has multiple plausible matches across different services.
        
        Args:
            query: Search query
            threshold: Maximum confidence difference to consider results ambiguous
            
        Returns:
            True if disambiguation is needed
        """
        matches = self.classify(query, limit=5)
        
        if len(matches) < 2:
            return False
        
        # Check if top results have similar confidence across different services
        top_confidence = matches[0].confidence
        different_services = set()
        
        for match in matches[1:3]:  # Check next 2 matches
            confidence_diff = top_confidence - match.confidence
            if confidence_diff <= threshold and match.service != matches[0].service:
                different_services.add(match.service)
        
        return len(different_services) > 0

    def _search_tmdb_movies(self, query: str) -> List[MediaMatch]:
        """Search TMDb for movies."""
        if not self.tmdb_api_key:
            return []
        
        try:
            url = f"{self.tmdb_base_url}/search/movie"
            params = {
                "api_key": self.tmdb_api_key,
                "query": query,
                "include_adult": "false",
                "language": "en-US"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            matches = []
            for result in data.get("results", [])[:5]:  # Top 5 movie results
                confidence = self._calculate_movie_confidence(result, query)
                
                matches.append(MediaMatch(
                    title=result.get("title", "Unknown"),
                    media_type=MediaType.MOVIE,
                    service=MediaService.RADARR,
                    confidence=confidence,
                    external_id=str(result.get("id")),
                    year=self._extract_year(result.get("release_date")),
                    description=result.get("overview"),
                    poster_url=self._build_tmdb_poster_url(result.get("poster_path")),
                    additional_data={"popularity": result.get("popularity", 0)}
                ))
            
            return matches
            
        except Exception as e:
            logging.error(f"Error searching TMDb movies: {e}")
            return []

    def _search_tmdb_tv(self, query: str) -> List[MediaMatch]:
        """Search TMDb for TV shows."""
        if not self.tmdb_api_key:
            return []
        
        try:
            url = f"{self.tmdb_base_url}/search/tv"
            params = {
                "api_key": self.tmdb_api_key,
                "query": query,
                "include_adult": "false",
                "language": "en-US"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            matches = []
            for result in data.get("results", [])[:5]:  # Top 5 TV results
                confidence = self._calculate_tv_confidence(result, query)
                
                # Fetch external IDs (TVDB) for TV shows
                tvdb_id = self._get_tvdb_id(result.get("id"))
                
                matches.append(MediaMatch(
                    title=result.get("name", "Unknown"),
                    media_type=MediaType.TV_SERIES,
                    service=MediaService.SONARR,
                    confidence=confidence,
                    external_id=tvdb_id or str(result.get("id")),  # Prefer TVDB, fallback to TMDB
                    year=self._extract_year(result.get("first_air_date")),
                    description=result.get("overview"),
                    poster_url=self._build_tmdb_poster_url(result.get("poster_path")),
                    additional_data={
                        "popularity": result.get("popularity", 0),
                        "tmdb_id": str(result.get("id"))
                    }
                ))
            
            return matches
            
        except Exception as e:
            logging.error(f"Error searching TMDb TV shows: {e}")
            return []

    def _search_music(self, query: str) -> List[MediaMatch]:
        """Search for music via Spotify and MusicBrainz."""
        matches = []
        
        # Try Spotify first (faster, better metadata)
        matches.extend(self._search_spotify(query))
        
        # Fallback to MusicBrainz if Spotify fails or limited results
        if len(matches) < 2:
            matches.extend(self._search_musicbrainz(query))
        
        return matches

    def _search_spotify(self, query: str) -> List[MediaMatch]:
        """Search Spotify for artists and albums."""
        if not self.spotify_client_id or not self.spotify_client_secret:
            return []
        
        try:
            # Get Spotify access token
            if not self.spotify_token:
                self.spotify_token = self._get_spotify_token()
            
            if not self.spotify_token:
                return []
            
            url = "https://api.spotify.com/v1/search"
            headers = {"Authorization": f"Bearer {self.spotify_token}"}
            params = {
                "q": query,
                "type": "artist,album",
                "limit": 5
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Token expired - retry with new token
            if response.status_code == 401:
                self.spotify_token = self._get_spotify_token()
                headers = {"Authorization": f"Bearer {self.spotify_token}"}
                response = requests.get(url, headers=headers, params=params, timeout=10)
            
            response.raise_for_status()
            data = response.json()
            
            matches = []
            
            # Process artist results
            for artist in data.get("artists", {}).get("items", [])[:3]:
                confidence = self._calculate_music_confidence(artist, query, "artist")
                
                matches.append(MediaMatch(
                    title=artist.get("name", "Unknown"),
                    media_type=MediaType.MUSIC,
                    service=MediaService.LIDARR,
                    confidence=confidence,
                    external_id=None,  # Would need MusicBrainz ID for Lidarr
                    description=f"Artist with {artist.get('followers', {}).get('total', 0):,} followers",
                    poster_url=artist.get("images", [{}])[0].get("url") if artist.get("images") else None,
                    additional_data={
                        "spotify_id": artist.get("id"),
                        "type": "artist",
                        "popularity": artist.get("popularity", 0)
                    }
                ))
            
            # Process album results
            for album in data.get("albums", {}).get("items", [])[:2]:
                confidence = self._calculate_music_confidence(album, query, "album")
                
                matches.append(MediaMatch(
                    title=f"{album.get('name')} - {album.get('artists', [{}])[0].get('name', 'Unknown')}",
                    media_type=MediaType.MUSIC,
                    service=MediaService.LIDARR,
                    confidence=confidence * 0.95,  # Slight penalty for albums vs artists
                    external_id=None,
                    year=self._extract_year(album.get("release_date")),
                    description=f"Album by {album.get('artists', [{}])[0].get('name', 'Unknown')}",
                    poster_url=album.get("images", [{}])[0].get("url") if album.get("images") else None,
                    additional_data={
                        "spotify_id": album.get("id"),
                        "type": "album",
                        "artist": album.get('artists', [{}])[0].get('name')
                    }
                ))
            
            return matches
            
        except Exception as e:
            logging.error(f"Error searching Spotify: {e}")
            return []

    def _search_musicbrainz(self, query: str) -> List[MediaMatch]:
        """Search MusicBrainz for artists (provides MusicBrainz IDs needed by Lidarr)."""
        try:
            url = f"{self.musicbrainz_base_url}/artist"
            headers = {"User-Agent": "MediaManagementSystem/1.0 (https://github.com/zy538324/Media_management)"}
            params = {
                "query": query,
                "fmt": "json",
                "limit": 3
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            matches = []
            for artist in data.get("artists", []):
                confidence = self._calculate_musicbrainz_confidence(artist, query)
                
                matches.append(MediaMatch(
                    title=artist.get("name", "Unknown"),
                    media_type=MediaType.MUSIC,
                    service=MediaService.LIDARR,
                    confidence=confidence,
                    external_id=artist.get("id"),  # MusicBrainz ID - critical for Lidarr
                    description=f"{artist.get('type', 'Artist')} - {artist.get('disambiguation', '')}".strip(" -"),
                    additional_data={
                        "country": artist.get("country"),
                        "type": artist.get("type"),
                        "score": artist.get("score", 0)
                    }
                ))
            
            return matches
            
        except Exception as e:
            logging.error(f"Error searching MusicBrainz: {e}")
            return []

    def _get_spotify_token(self) -> Optional[str]:
        """Get Spotify API access token via client credentials flow."""
        try:
            url = "https://accounts.spotify.com/api/token"
            data = {"grant_type": "client_credentials"}
            auth = (self.spotify_client_id, self.spotify_client_secret)
            
            response = requests.post(url, data=data, auth=auth, timeout=10)
            response.raise_for_status()
            
            return response.json().get("access_token")
        except Exception as e:
            logging.error(f"Error getting Spotify token: {e}")
            return None

    def _get_tvdb_id(self, tmdb_id: int) -> Optional[str]:
        """Fetch TVDB ID from TMDb external IDs endpoint."""
        if not self.tmdb_api_key or not tmdb_id:
            return None
        
        try:
            url = f"{self.tmdb_base_url}/tv/{tmdb_id}/external_ids"
            params = {"api_key": self.tmdb_api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            tvdb_id = data.get("tvdb_id")
            return str(tvdb_id) if tvdb_id else None
            
        except Exception as e:
            logging.error(f"Error fetching TVDB ID for TMDB ID {tmdb_id}: {e}")
            return None

    def _calculate_movie_confidence(self, result: Dict, query: str) -> float:
        """Calculate confidence score for a movie result."""
        score = 0.0
        query_lower = query.lower()
        title_lower = result.get("title", "").lower()
        
        # Exact title match: +0.5
        if query_lower == title_lower:
            score += 0.5
        elif query_lower in title_lower or title_lower in query_lower:
            score += 0.3
        
        # Popularity score (normalize to 0-0.3)
        popularity = result.get("popularity", 0)
        score += min(0.3, popularity / 1000)
        
        # Has poster: +0.1
        if result.get("poster_path"):
            score += 0.1
        
        # Recent release: +0.1
        release_year = self._extract_year(result.get("release_date"))
        if release_year and release_year >= 2010:
            score += 0.1
        
        return min(1.0, score)

    def _calculate_tv_confidence(self, result: Dict, query: str) -> float:
        """Calculate confidence score for a TV show result."""
        score = 0.0
        query_lower = query.lower()
        name_lower = result.get("name", "").lower()
        
        # Exact name match: +0.5
        if query_lower == name_lower:
            score += 0.5
        elif query_lower in name_lower or name_lower in query_lower:
            score += 0.3
        
        # Popularity score (normalize to 0-0.3)
        popularity = result.get("popularity", 0)
        score += min(0.3, popularity / 1000)
        
        # Has poster: +0.1
        if result.get("poster_path"):
            score += 0.1
        
        # Recent series: +0.1
        first_air_year = self._extract_year(result.get("first_air_date"))
        if first_air_year and first_air_year >= 2010:
            score += 0.1
        
        return min(1.0, score)

    def _calculate_music_confidence(self, result: Dict, query: str, result_type: str) -> float:
        """Calculate confidence score for Spotify music results."""
        score = 0.0
        query_lower = query.lower()
        name_lower = result.get("name", "").lower()
        
        # Exact match: +0.5
        if query_lower == name_lower:
            score += 0.5
        elif query_lower in name_lower or name_lower in query_lower:
            score += 0.3
        
        # Popularity score (Spotify 0-100, normalize to 0-0.3)
        popularity = result.get("popularity", 0)
        score += min(0.3, popularity / 300)
        
        # Artist type bonus: +0.1 (artists are primary targets for Lidarr)
        if result_type == "artist":
            score += 0.1
        
        # Has images: +0.1
        if result.get("images"):
            score += 0.1
        
        return min(1.0, score)

    def _calculate_musicbrainz_confidence(self, result: Dict, query: str) -> float:
        """Calculate confidence score for MusicBrainz results."""
        score = 0.0
        query_lower = query.lower()
        name_lower = result.get("name", "").lower()
        
        # MusicBrainz provides a score field (0-100)
        mb_score = result.get("score", 0)
        score += min(0.6, mb_score / 150)
        
        # Exact match: +0.3
        if query_lower == name_lower:
            score += 0.3
        elif query_lower in name_lower or name_lower in query_lower:
            score += 0.15
        
        # Has disambiguation info: +0.1
        if result.get("disambiguation"):
            score += 0.1
        
        return min(1.0, score)

    def _build_tmdb_poster_url(self, poster_path: Optional[str]) -> Optional[str]:
        """Build full poster URL from TMDb poster path."""
        if not poster_path:
            return None
        return f"https://image.tmdb.org/t/p/w500{poster_path}"

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string (YYYY-MM-DD format)."""
        if not date_str:
            return None
        try:
            return int(date_str.split("-")[0])
        except (ValueError, IndexError):
            return None
