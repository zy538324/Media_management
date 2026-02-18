# Intelligent Media Classification System

This document describes the intelligent media classification engine that automatically routes media requests to the appropriate *arr service (Sonarr, Radarr, or Lidarr).

## Overview

The Media Management System now features an **intelligent classification engine** that automatically determines whether a user's media request should be routed to:

- **Radarr** (Movies)
- **Sonarr** (TV Shows)
- **Lidarr** (Music)

Users simply request "Dexter" and the system intelligently determines whether they want the TV show (Sonarr), the movie, or the soundtrack (Lidarr).

## How It Works

### 1. Multi-Source Classification

When a user submits a media request, the classifier:

1. **Searches TMDb** for movies and TV shows
2. **Searches Spotify** for music (artists and albums)
3. **Searches MusicBrainz** as fallback for music metadata
4. **Scores all results** based on:
   - Title/name match accuracy
   - Popularity metrics
   - Metadata completeness (posters, descriptions)
   - Release recency

### 2. Confidence Scoring

Each potential match receives a confidence score (0.0 to 1.0):

- **0.9-1.0**: Highly confident (exact match + high popularity)
- **0.7-0.9**: Very confident (partial match + good metadata)
- **0.5-0.7**: Moderately confident (acceptable match)
- **<0.5**: Low confidence (disambiguation recommended)

### 3. Automatic Routing

The system automatically routes requests to the appropriate service based on the highest confidence match:

```
User Request: "Breaking Bad"
  → Classifier searches all sources
  → Finds TV show (confidence: 0.95)
  → Finds soundtrack (confidence: 0.42)
  → Routes to Sonarr (highest confidence)
  → Adds to download queue
```

## Key Features

### Ambiguity Detection

When multiple services have similar confidence scores (within 15%), the system:

- Logs a warning about ambiguity
- Proceeds with the highest confidence match
- Stores all classification data for review

Example ambiguous case:
```
User Request: "Blade Runner"
  → Movie (1982) - confidence: 0.88 [Radarr]
  → TV Series (2024) - confidence: 0.81 [Sonarr]
  → Soundtrack - confidence: 0.74 [Lidarr]
  → System routes to Radarr (highest)
  → Logs ambiguity warning
```

### Classification Metadata Storage

Every request stores:

- `arr_service`: Target service (sonarr/radarr/lidarr)
- `external_id`: External API ID (TMDB/TVDB/MusicBrainz)
- `confidence_score`: Classifier confidence (0.0-1.0)
- `classification_data`: Full JSON metadata for debugging

### User Type Hints

Users can provide type hints to filter results:

- If user specifies "Movie", only movie results are considered
- If user specifies "TV Show", only TV results are considered
- If no type specified, automatic classification is used

## Configuration

Ensure your `config.yaml` includes:

```yaml
# TMDb (required for movie/TV classification)
TMDb:
  api_key: your_tmdb_api_key_here

# Spotify (optional but recommended for music)
Spotify:
  client_id: your_spotify_client_id
  client_secret: your_spotify_client_secret

# *arr Services
Sonarr:
  api_url: http://localhost:8989
  api_key: your_sonarr_api_key

Radarr:
  api_url: http://localhost:7878
  api_key: your_radarr_api_key

Lidarr:
  api_url: http://localhost:8686
  api_key: your_lidarr_api_key
```

## Database Migration

To enable classification features on existing installations:

```bash
# Apply the migration
sqlite3 media_management.db < migrations/add_classification_fields.sql
```

This adds the following fields to the `requests` table:
- `arr_service` - Target *arr service
- `arr_id` - ID in target service
- `external_id` - External API ID
- `confidence_score` - Classification confidence
- `classification_data` - Full metadata JSON

## API Usage

### Classify a Title

```python
from app.helpers.media_classifier import MediaClassifier

classifier = MediaClassifier()
matches = classifier.classify("Dexter", limit=5)

for match in matches:
    print(f"{match.title} - {match.service.value} ({match.confidence:.2f})")
```

Output:
```
Dexter - sonarr (0.92)
Dexter (2024) - radarr (0.65)
Dexter Gordon - lidarr (0.58)
```

### Check for Ambiguity

```python
if classifier.has_ambiguity("The Matrix"):
    print("Multiple plausible matches detected")
    matches = classifier.classify("The Matrix")
    # Present disambiguation UI to user
```

### Get Best Match

```python
best = classifier.get_best_match("Breaking Bad")
if best:
    print(f"Best match: {best.title} ({best.service.value})")
    print(f"Confidence: {best.confidence:.0%}")
```

## Classification Algorithm

### Movie Scoring

```python
score = 0.0

# Exact title match: +0.5
if query.lower() == title.lower():
    score += 0.5

# Popularity (normalized): +0.3 max
score += min(0.3, popularity / 1000)

# Has poster: +0.1
if has_poster:
    score += 0.1

# Recent release (2010+): +0.1
if year >= 2010:
    score += 0.1
```

### TV Show Scoring

Similar to movies, with additional TVDB ID retrieval for Sonarr compatibility.

### Music Scoring

```python
score = 0.0

# Exact match: +0.5
if query.lower() == name.lower():
    score += 0.5

# Spotify popularity: +0.3 max
score += min(0.3, popularity / 300)

# Artist type bonus: +0.1
if type == "artist":
    score += 0.1

# Has images: +0.1
if has_images:
    score += 0.1
```

## Troubleshooting

### "Classification failed" Errors

**Cause**: No matches found across any service

**Solutions**:
1. Check API keys are configured correctly
2. Verify network connectivity to TMDb/Spotify/MusicBrainz
3. Try a more specific search term
4. Check application logs for API errors

### Low Confidence Scores

**Cause**: Ambiguous or obscure titles

**Solutions**:
1. Include year in search (e.g., "Dune 2021")
2. Provide type hint ("Dune movie" vs "Dune soundtrack")
3. Review `classification_data` JSON for alternatives

### Wrong Service Routing

**Cause**: Classifier chose incorrect highest confidence match

**Solutions**:
1. Review logs for ambiguity warnings
2. Check confidence scores of all matches
3. Use user type hints to filter results
4. Adjust confidence thresholds in code if needed

## Performance Considerations

### API Rate Limits

- **TMDb**: 40 requests per 10 seconds
- **Spotify**: No strict limit with client credentials
- **MusicBrainz**: 1 request per second (auto-throttled)

### Caching Strategy

The classifier makes real-time API calls. For production:

1. **Cache results** in database for repeated searches
2. **Background processing** for batch requests
3. **Redis caching** for frequently searched titles

### Optimization Tips

```python
# Limit results per source
matches = classifier.classify(query, limit=5)  # Returns top 5

# Single best match (faster)
best = classifier.get_best_match(query)  # Single API round-trip
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**
   - Train on user correction patterns
   - Personalized classification per user
   - Confidence threshold auto-adjustment

2. **Advanced Disambiguation UI**
   - Show multiple matches with posters
   - User selection stored as preference
   - "Did you mean?" suggestions

3. **Multi-Version Support**
   - Handle remakes (e.g., "Dune 1984" vs "Dune 2021")
   - Detect sequels and prequels
   - Franchise grouping

4. **Quality Profile Routing**
   - Route based on user quality preferences
   - Automatic 4K vs HD decisions
   - Storage space considerations

## Architecture Diagram

```
┌─────────────────┐
│   User Request  │
│   "Dexter"      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│   MediaClassifier       │
│   ┌─────────────────┐   │
│   │ TMDb Search     │◄──┼── Movies & TV
│   │ Spotify Search  │◄──┼── Music (Artist/Album)
│   │ MusicBrainz     │◄──┼── Music (Fallback)
│   └─────────────────┘   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Confidence Scoring     │
│  ┌─────────────────┐    │
│  │ Title Match     │    │
│  │ Popularity      │    │
│  │ Metadata        │    │
│  │ Recency         │    │
│  └─────────────────┘    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Best Match Selection   │
│  Dexter (TV) - 0.92     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Route to Service      │
├─────────────────────────┤
│  Sonarr  │ Radarr │ Lidarr
└─────────────────────────┘
```

## Credits

- **TMDb API**: Movie and TV show metadata
- **Spotify API**: Music artist and album data
- **MusicBrainz API**: Open music encyclopedia
- **pyarr**: Python library for *arr services

## Support

For issues related to classification:

1. Check logs in `app/logs/` for detailed error messages
2. Review `classification_data` field in database for debug info
3. Open issue on GitHub with:
   - Search query that failed
   - Expected vs actual routing
   - Relevant log excerpts

---

**Version**: 1.0.0  
**Last Updated**: February 18, 2026  
**Author**: Media Management System Contributors
