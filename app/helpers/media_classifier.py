import logging
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
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
    media_type: str
    service: str
    confidence: float
    external_id: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    additional_data: Optional[Dict] = None

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'title': self.title,
            'media_type': self.media_type,
            'service': self.service,
            'confidence': self.confidence,
            'external_id': self.external_id,
            'year': self.year,
            'description': self.description,
            'poster_url': self.poster_url,
            'additional_data': self.additional_data
        }


class MediaClassifier:
    """Intelligent media classification engine for routing to Sonarr/Radarr/Lidarr."""

    def __init__(self):
        config = Config()
        self.tmdb_api_key = config.TMDB_API_KEY
        self.spotify_client_id = config.SPOTIFY_CLIENT_ID
        self.spotify_client_secret = config.SPOTIFY_CLIENT_SECRET
        
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.musicbrainz_base_url = "https://musicbrainz.org/ws/2"
        self.spotify_token = None

    def classify(self, query: str, limit: int = 10) -> List[MediaMatch]:
        """Classify media request and return ranked matches."""
        logging.info(f"Classifying: '{query}'")
        
        all_matches = []
        all_matches.extend(self._search_tmdb_movies(query))
        all_matches.extend(self._search_tmdb_tv(query))
        all_matches.extend(self._search_music(query))
        
        all_matches.sort(key=lambda m: m.confidence, reverse=True)
        
        if all_matches:
            logging.info(f"Found {len(all_matches)} matches")
            for i, match in enumerate(all_matches[:3]):
                logging.info(f"  {i+1}. {match.title} → {match.service} ({match.confidence:.2f})")
        
        return all_matches[:limit]

    def get_best_match(self, query: str) -> Optional[MediaMatch]:
        """Get single best match."""
        matches = self.classify(query, limit=1)
        return matches[0] if matches and matches[0].confidence >= 0.5 else None

    def has_ambiguity(self, query: str, threshold: float = 0.15) -> bool:
        """Check if disambiguation needed."""
        matches = self.classify(query, limit=5)
        if len(matches) < 2:
            return False
        
        top_conf = matches[0].confidence
        services = set()
        
        for match in matches[1:3]:
            if (top_conf - match.confidence) <= threshold and match.service != matches[0].service:
                services.add(match.service)
        
        return len(services) > 0

    def _search_tmdb_movies(self, query: str) -> List[MediaMatch]:
        """Search TMDb for movies."""
        if not self.tmdb_api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.tmdb_base_url}/search/movie",
                params={"api_key": self.tmdb_api_key, "query": query, "include_adult": "false"},
                timeout=10
            )
            response.raise_for_status()
            
            matches = []
            for r in response.json().get("results", [])[:5]:
                matches.append(MediaMatch(
                    title=r.get("title", "Unknown"),
                    media_type=MediaType.MOVIE.value,
                    service=MediaService.RADARR.value,
                    confidence=self._calc_movie_conf(r, query),
                    external_id=str(r.get("id")),
                    year=self._extract_year(r.get("release_date")),
                    description=r.get("overview"),
                    poster_url=self._build_poster_url(r.get("poster_path")),
                    additional_data={"popularity": r.get("popularity", 0)}
                ))
            return matches
        except Exception as e:
            logging.error(f"TMDb movie search error: {e}")
            return []

    def _search_tmdb_tv(self, query: str) -> List[MediaMatch]:
        """Search TMDb for TV shows."""
        if not self.tmdb_api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.tmdb_base_url}/search/tv",
                params={"api_key": self.tmdb_api_key, "query": query, "include_adult": "false"},
                timeout=10
            )
            response.raise_for_status()
            
            matches = []
            for r in response.json().get("results", [])[:5]:
                tvdb_id = self._get_tvdb_id(r.get("id"))
                matches.append(MediaMatch(
                    title=r.get("name", "Unknown"),
                    media_type=MediaType.TV_SERIES.value,
                    service=MediaService.SONARR.value,
                    confidence=self._calc_tv_conf(r, query),
                    external_id=tvdb_id or str(r.get("id")),
                    year=self._extract_year(r.get("first_air_date")),
                    description=r.get("overview"),
                    poster_url=self._build_poster_url(r.get("poster_path")),
                    additional_data={"popularity": r.get("popularity", 0), "tmdb_id": str(r.get("id"))}
                ))
            return matches
        except Exception as e:
            logging.error(f"TMDb TV search error: {e}")
            return []

    def _search_music(self, query: str) -> List[MediaMatch]:
        """Search music via Spotify and MusicBrainz."""
        matches = self._search_spotify(query)
        if len(matches) < 2:
            matches.extend(self._search_musicbrainz(query))
        return matches

    def _search_spotify(self, query: str) -> List[MediaMatch]:
        """Search Spotify."""
        if not self.spotify_client_id or not self.spotify_client_secret:
            return []
        
        try:
            if not self.spotify_token:
                self.spotify_token = self._get_spotify_token()
            if not self.spotify_token:
                return []
            
            response = requests.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {self.spotify_token}"},
                params={"q": query, "type": "artist,album", "limit": 5},
                timeout=10
            )
            
            if response.status_code == 401:
                self.spotify_token = self._get_spotify_token()
                response = requests.get(
                    "https://api.spotify.com/v1/search",
                    headers={"Authorization": f"Bearer {self.spotify_token}"},
                    params={"q": query, "type": "artist,album", "limit": 5},
                    timeout=10
                )
            
            response.raise_for_status()
            data = response.json()
            matches = []
            
            for artist in data.get("artists", {}).get("items", [])[:3]:
                matches.append(MediaMatch(
                    title=artist.get("name", "Unknown"),
                    media_type=MediaType.MUSIC.value,
                    service=MediaService.LIDARR.value,
                    confidence=self._calc_music_conf(artist, query, "artist"),
                    external_id=None,
                    description=f"Artist with {artist.get('followers', {}).get('total', 0):,} followers",
                    poster_url=artist.get("images", [{}])[0].get("url") if artist.get("images") else None,
                    additional_data={"spotify_id": artist.get("id"), "type": "artist"}
                ))
            
            return matches
        except Exception as e:
            logging.error(f"Spotify search error: {e}")
            return []

    def _search_musicbrainz(self, query: str) -> List[MediaMatch]:
        """Search MusicBrainz."""
        try:
            response = requests.get(
                f"{self.musicbrainz_base_url}/artist",
                headers={"User-Agent": "MediaManagementSystem/1.0"},
                params={"query": query, "fmt": "json", "limit": 3},
                timeout=10
            )
            response.raise_for_status()
            
            matches = []
            for artist in response.json().get("artists", []):
                matches.append(MediaMatch(
                    title=artist.get("name", "Unknown"),
                    media_type=MediaType.MUSIC.value,
                    service=MediaService.LIDARR.value,
                    confidence=self._calc_mb_conf(artist, query),
                    external_id=artist.get("id"),
                    description=f"{artist.get('type', 'Artist')} - {artist.get('disambiguation', '')}".strip(" -"),
                    additional_data={"country": artist.get("country"), "score": artist.get("score", 0)}
                ))
            return matches
        except Exception as e:
            logging.error(f"MusicBrainz search error: {e}")
            return []

    def _get_spotify_token(self) -> Optional[str]:
        """Get Spotify token."""
        try:
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(self.spotify_client_id, self.spotify_client_secret),
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            logging.error(f"Spotify token error: {e}")
            return None

    def _get_tvdb_id(self, tmdb_id: int) -> Optional[str]:
        """Get TVDB ID."""
        if not self.tmdb_api_key or not tmdb_id:
            return None
        try:
            response = requests.get(
                f"{self.tmdb_base_url}/tv/{tmdb_id}/external_ids",
                params={"api_key": self.tmdb_api_key},
                timeout=10
            )
            response.raise_for_status()
            tvdb_id = response.json().get("tvdb_id")
            return str(tvdb_id) if tvdb_id else None
        except:
            return None

    def _calc_movie_conf(self, r: Dict, query: str) -> float:
        score = 0.0
        q, t = query.lower(), r.get("title", "").lower()
        if q == t: score += 0.5
        elif q in t or t in q: score += 0.3
        score += min(0.3, r.get("popularity", 0) / 1000)
        if r.get("poster_path"): score += 0.1
        year = self._extract_year(r.get("release_date"))
        if year and year >= 2010: score += 0.1
        return min(1.0, score)

    def _calc_tv_conf(self, r: Dict, query: str) -> float:
        score = 0.0
        q, n = query.lower(), r.get("name", "").lower()
        if q == n: score += 0.5
        elif q in n or n in q: score += 0.3
        score += min(0.3, r.get("popularity", 0) / 1000)
        if r.get("poster_path"): score += 0.1
        year = self._extract_year(r.get("first_air_date"))
        if year and year >= 2010: score += 0.1
        return min(1.0, score)

    def _calc_music_conf(self, r: Dict, query: str, rtype: str) -> float:
        score = 0.0
        q, n = query.lower(), r.get("name", "").lower()
        if q == n: score += 0.5
        elif q in n or n in q: score += 0.3
        score += min(0.3, r.get("popularity", 0) / 300)
        if rtype == "artist": score += 0.1
        if r.get("images"): score += 0.1
        return min(1.0, score)

    def _calc_mb_conf(self, r: Dict, query: str) -> float:
        score = min(0.6, r.get("score", 0) / 150)
        q, n = query.lower(), r.get("name", "").lower()
        if q == n: score += 0.3
        elif q in n or n in q: score += 0.15
        if r.get("disambiguation"): score += 0.1
        return min(1.0, score)

    def _build_poster_url(self, path: Optional[str]) -> Optional[str]:
        return f"https://image.tmdb.org/t/p/w500{path}" if path else None

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        if not date_str: return None
        try:
            return int(date_str.split("-")[0])
        except:
            return None
