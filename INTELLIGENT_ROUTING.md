# Intelligent Media Classification & *arr Routing

## Overview

This system provides **intelligent automatic routing** of media requests to the appropriate service:
- **Movies** → Radarr
- **TV Shows** → Sonarr  
- **Music** → Lidarr

Users simply type a title like "Dexter" and the system automatically determines whether it's a movie, TV show, or music, then routes it to the correct *arr service for download.

## Features

### ✅ Automatic Classification
- Multi-source intelligence engine queries TMDb (movies/TV), Spotify (music), and MusicBrainz (music IDs)
- Confidence scoring ranks all potential matches
- Automatically selects the best match when confidence is high

### ✅ Disambiguation UI
- When multiple media types match the same title (e.g., "Blade Runner" movie vs soundtrack)
- User is presented with options showing:
  - Title and year
  - Media type (Movie/TV Show/Music)
  - Target service (Radarr/Sonarr/Lidarr)
  - Description/overview
  - Poster artwork

### ✅ External ID Resolution
- Movies: TMDB ID
- TV Shows: TVDB ID (with TMDB fallback)
- Music: MusicBrainz ID (critical for Lidarr)

### ✅ Comprehensive Logging
- All classification decisions logged with confidence scores
- Audit trail for debugging and improvement
- Request status tracking through entire pipeline

## Architecture

### Core Components

```
User Request "Dexter"
         ↓
  MediaClassifier
    ├─→ TMDb Movies API
    ├─→ TMDb TV API
    ├─→ Spotify API
    └─→ MusicBrainz API
         ↓
  Confidence Scoring
         ↓
  Best Match Selected
         ↓
  RequestProcessor
    ├─→ Radarr (if movie)
    ├─→ Sonarr (if TV)
    └─→ Lidarr (if music)
```

### File Structure

- **`app/helpers/media_classifier.py`** - Core intelligence engine
  - `MediaClassifier` class with multi-source search
  - `MediaMatch` dataclass for results
  - Confidence scoring algorithms
  - External ID resolution

- **`app/helpers/request_processor.py`** - Enhanced request processor
  - Uses `MediaClassifier` for automatic routing
  - Handles pre-classified requests from disambiguation
  - Error handling and fallback logic

- **`app/routes/unified_requests.py`** - API endpoints
  - `/api/classify` - Real-time classification for search
  - `/api/request/create` - Create classified request
  - `/api/request/<id>/reclassify` - Manual override

- **`app/models.py`** - Enhanced Request model
  - `arr_service` - Target service (sonarr/radarr/lidarr)
  - `external_id` - TMDB/TVDB/MusicBrainz ID
  - `confidence_score` - Classification confidence (0.0-1.0)
  - `classification_data` - Full metadata JSON

## Installation

### 1. Run Database Migration

```bash
sqlite3 media_management.db < migrations/add_classification_fields.sql
```

This adds the required classification fields to the `requests` table.

### 2. Configure *arr Services

Ensure your `config.yaml` has all three services configured:

```yaml
Sonarr:
  api_url: http://localhost:8989
  api_key: your_sonarr_api_key_here

Radarr:
  api_url: http://localhost:7878
  api_key: your_radarr_api_key_here

Lidarr:
  api_url: http://localhost:8686
  api_key: your_lidarr_api_key_here

TMDb:
  api_key: your_tmdb_api_key  # Required for classification

Spotify:
  client_id: your_spotify_client_id  # Required for music classification
  client_secret: your_spotify_client_secret
```

### 3. Register Blueprint

In your `app/__init__.py`, register the unified requests blueprint:

```python
from app.routes.unified_requests import unified_requests_bp

app.register_blueprint(unified_requests_bp)
```

### 4. Restart Application

```bash
python run.py
```

## Usage

### API Usage

#### Classify Media (Real-time Search)

```bash
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "Breaking Bad"}'
```

Response:
```json
{
  "success": true,
  "results": [
    {
      "title": "Breaking Bad",
      "media_type": "tv",
      "service": "sonarr",
      "service_display": "Sonarr (TV Shows)",
      "confidence": 0.95,
      "year": 2008,
      "description": "A high school chemistry teacher...",
      "external_id": "1396",
      "poster_url": "https://image.tmdb.org/..."
    }
  ],
  "has_ambiguity": false
}
```

#### Create Request

```bash
curl -X POST http://localhost:5000/api/request/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Dexter"}'
```

Response:
```json
{
  "success": true,
  "message": "Request created successfully! Dexter will be added to Sonarr (TV Shows).",
  "request_id": 42,
  "service": "sonarr",
  "confidence": 0.92
}
```

#### Manual Override (Reclassify)

```bash
curl -X POST http://localhost:5000/api/request/42/reclassify \
  -H "Content-Type: application/json" \
  -d '{"force_service": "radarr"}'
```

### Python Usage

```python
from app.helpers.media_classifier import MediaClassifier

# Initialize classifier
classifier = MediaClassifier()

# Get best match
best_match = classifier.get_best_match("The Matrix")
if best_match:
    print(f"{best_match.title} → {best_match.service.value}")
    print(f"Confidence: {best_match.confidence:.2%}")

# Get all matches
matches = classifier.classify("Dexter", limit=5)
for match in matches:
    print(f"{match.title} ({match.year}) - {match.media_type.value} - {match.confidence:.2f}")

# Check for ambiguity
if classifier.has_ambiguity("Blade Runner"):
    print("Multiple matches found - disambiguation needed")
```

### Request Processing

```python
from app.helpers.request_processor import RequestProcessor

# Process all pending requests with intelligent classification
RequestProcessor.process_pending_requests()

# Classify a specific title
matches = RequestProcessor.classify_request("Interstellar")

# Check if disambiguation needed
needs_disambiguation = RequestProcessor.check_ambiguity("Dune")
```

## Confidence Scoring

The classifier uses a weighted scoring system (0.0 to 1.0):

### Movie Confidence Factors:
- **+0.5** - Exact title match
- **+0.3** - Partial title match
- **+0.3** - High popularity (normalized)
- **+0.1** - Has poster artwork
- **+0.1** - Recent release (2010+)

### TV Show Confidence Factors:
- **+0.5** - Exact name match
- **+0.3** - Partial name match
- **+0.3** - High popularity (normalized)
- **+0.1** - Has poster artwork
- **+0.1** - Recent series (2010+)

### Music Confidence Factors:
- **+0.5** - Exact artist/album match
- **+0.3** - High popularity (Spotify)
- **+0.1** - Artist type (vs album)
- **+0.1** - Has cover artwork

### Thresholds
- **≥ 0.5** - Auto-approve (high confidence)
- **0.35-0.49** - Review recommended
- **< 0.35** - Low confidence (disambiguation suggested)

## Disambiguation Logic

Disambiguation is triggered when:

1. Multiple results from **different services** have similar confidence scores
2. Confidence difference between top 2 results ≤ 0.15
3. At least one result from a different service category

Example: "Dexter"
- Dexter (TV Series) - 0.92 confidence → Sonarr
- Dexter Soundtrack - 0.81 confidence → Lidarr
- Difference: 0.11 (< 0.15) → **Disambiguation UI shown**

## Status Codes

Request status values after intelligent processing:

- **`Pending`** - Awaiting classification/processing
- **`SentToSonarr`** - Successfully added to Sonarr
- **`SentToRadarr`** - Successfully added to Radarr
- **`SentToLidarr`** - Successfully added to Lidarr
- **`Failed (Classification)`** - No confident match found
- **`Failed (Missing TMDB ID)`** - Movie without TMDB ID
- **`Failed (Missing TVDB ID)`** - TV show without TVDB ID
- **`Failed (Sonarr)`** - Sonarr API error
- **`Failed (Radarr)`** - Radarr API error
- **`Failed (Lidarr)`** - Lidarr API error
- **`Failed (Exception)`** - Unhandled error

## Troubleshooting

### Classification Always Fails

**Check API keys:**
```python
from config import Config
config = Config()
print(f"TMDb: {bool(config.TMDB_API_KEY)}")
print(f"Spotify ID: {bool(config.SPOTIFY_CLIENT_ID)}")
print(f"Spotify Secret: {bool(config.SPOTIFY_CLIENT_SECRET)}")
```

**Test TMDb connection:**
```python
from app.helpers.media_classifier import MediaClassifier
classifier = MediaClassifier()
results = classifier._search_tmdb_movies("The Matrix")
print(f"Found {len(results)} movies")
```

### Music Classification Not Working

**Spotify API requires both client_id and client_secret:**
```yaml
Spotify:
  client_id: your_actual_client_id_here
  client_secret: your_actual_client_secret_here
```

**Test Spotify connection:**
```python
classifier = MediaClassifier()
token = classifier._get_spotify_token()
print(f"Spotify token: {token[:20]}..." if token else "Failed")
```

### Wrong Service Selected

**Check confidence scores in logs:**
```bash
grep "Classified request" app/logs/app.log | tail -20
```

**Manually override:**
```python
from app.models import Request, db
request = Request.query.get(42)
request.arr_service = 'radarr'  # Force to Radarr
request.confidence_score = 1.0
request.status = 'Pending'
db.session.commit()
```

### TVDB ID Not Found

Some TV shows don't have TVDB IDs in TMDb. The system will:
1. Try to fetch TVDB ID via TMDb external_ids endpoint
2. Fall back to TMDB ID (Sonarr v3+ accepts TMDB IDs)
3. If both fail, status = `Failed (Missing TVDB ID)`

**Manual TVDB lookup:**
```python
from app.helpers.media_classifier import MediaClassifier
classifier = MediaClassifier()
tvdb_id = classifier._get_tvdb_id(tmdb_id=12345)
print(f"TVDB ID: {tvdb_id}")
```

## Performance

### API Rate Limits

- **TMDb**: 40 requests per 10 seconds
- **Spotify**: No strict limit for client credentials flow
- **MusicBrainz**: 1 request per second (automatically respected)

### Caching Strategy

Classification results are stored in `classification_data` field. Reclassify only when:
- User manually requests it
- Original classification failed
- Confidence was below threshold

### Optimization Tips

1. **Cache Spotify token** - Reused across requests (automatically handled)
2. **Batch process requests** - Use scheduled job instead of real-time
3. **Index database fields** - Already created in migration

## Security Considerations

### API Key Storage
- All keys stored in `config.yaml` (should be gitignored)
- Never commit actual API keys to repository
- Use environment variables in production

### User Input Sanitization
- All search queries sanitized before API calls
- SQL injection prevented via SQLAlchemy ORM
- XSS protection via Jinja2 auto-escaping

### Rate Limiting
- Implement user-level rate limiting for `/api/classify` endpoint
- Prevent abuse via request throttling

## Future Enhancements

- [ ] Machine learning model to improve confidence scoring over time
- [ ] User preference learning ("User always wants TV shows, not movies")
- [ ] Fuzzy matching for typos and alternate spellings
- [ ] Support for anime-specific databases (AniDB, AniList)
- [ ] Bulk request classification
- [ ] Classification result caching (Redis)
- [ ] WebSocket real-time classification updates
- [ ] A/B testing different confidence scoring algorithms

## Credits

- **TMDb** - Movie and TV show metadata
- **Spotify** - Music search and metadata
- **MusicBrainz** - Music identification (MusicBrainz IDs)
- **Sonarr/Radarr/Lidarr** - Media automation

## License

Same as parent project (MIT License).
