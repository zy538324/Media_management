# Quick Start: Intelligent *arr Routing

## What This Does

Transforms your media management system into an **intelligent unified request portal**:

```
BEFORE: User must know if "Dexter" is a movie, TV show, or music
AFTER:  User types "Dexter" → System automatically routes to Sonarr (TV)
```

## 5-Minute Setup

### 1. Run Setup Script

```bash
chmod +x setup_intelligent_routing.sh
./setup_intelligent_routing.sh
```

This will:
- ✅ Install dependencies (musicbrainzngs)
- ✅ Backup your database
- ✅ Run database migration
- ✅ Verify configuration

### 2. Update `app/__init__.py`

Add these two lines:

```python
from app.routes.unified_requests import unified_requests_bp
app.register_blueprint(unified_requests_bp)
```

### 3. Verify API Keys in `config.yaml`

Ensure you have:

```yaml
TMDb:
  api_key: your_tmdb_key_here  # Required

Spotify:
  client_id: your_spotify_id       # Recommended for music
  client_secret: your_spotify_secret

Sonarr:
  api_url: http://localhost:8989
  api_key: your_sonarr_key

Radarr:
  api_url: http://localhost:7878
  api_key: your_radarr_key

Lidarr:
  api_url: http://localhost:8686
  api_key: your_lidarr_key
```

### 4. Test

```bash
python test_classifier.py
```

Should show:
```
✓ Configuration
✓ TMDb Connection
✓ Spotify Connection
✓ Classification
✓ ALL TESTS PASSED!
```

### 5. Restart App

```bash
python run.py
```

## Usage Examples

### Python API

```python
from app.helpers.media_classifier import MediaClassifier

classifier = MediaClassifier()

# Auto-classify
match = classifier.get_best_match("Breaking Bad")
print(f"{match.title} → {match.service.value} (confidence: {match.confidence:.0%})")
# Output: Breaking Bad → sonarr (confidence: 95%)

# Get all matches for disambiguation
matches = classifier.classify("Dexter")
for m in matches:
    print(f"  {m.title} ({m.year}) - {m.service.value}")
# Output:
#   Dexter (2006) - sonarr
#   Dexter Soundtrack - lidarr
```

### REST API

**Classify media:**
```bash
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "The Matrix"}'
```

**Create request:**
```bash
curl -X POST http://localhost:5000/api/request/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Interstellar"}'
```

### Process Existing Requests

Backfill classification for existing pending requests:

```python
from app.helpers.request_processor import RequestProcessor

RequestProcessor.process_pending_requests()
```

## How It Works

### Classification Flow

```
1. User enters: "Dexter"
   ↓
2. System queries:
   - TMDb Movies → No strong match
   - TMDb TV → "Dexter" (2006) TV series [confidence: 0.92]
   - Spotify → "Dexter" artist [confidence: 0.35]
   - MusicBrainz → Various artists [confidence: 0.28]
   ↓
3. Best match selected:
   "Dexter" (2006) → Sonarr [confidence: 0.92]
   ↓
4. Request created with metadata:
   - arr_service: "sonarr"
   - external_id: "12345" (TVDB ID)
   - confidence_score: 0.92
   ↓
5. RequestProcessor routes to Sonarr
   ↓
6. Status: "SentToSonarr"
```

### Confidence Scoring

| Score | Meaning | Action |
|-------|---------|--------|
| 0.8-1.0 | High confidence | Auto-route |
| 0.5-0.79 | Medium confidence | Route with logging |
| 0.35-0.49 | Low confidence | Suggest disambiguation |
| < 0.35 | Very low | Require disambiguation |

### Disambiguation Example

When "Blade Runner" is searched:

```json
{
  "results": [
    {
      "title": "Blade Runner",
      "year": 1982,
      "service": "radarr",
      "confidence": 0.89
    },
    {
      "title": "Blade Runner 2049 Soundtrack",
      "service": "lidarr",
      "confidence": 0.76
    }
  ],
  "has_ambiguity": true
}
```

User sees both options and selects the correct one.

## Files Created/Modified

### New Files
- `app/helpers/media_classifier.py` - Core classification engine (600+ lines)
- `app/routes/unified_requests.py` - API endpoints
- `migrations/add_classification_fields.sql` - Database schema
- `INTELLIGENT_ROUTING.md` - Full documentation
- `test_classifier.py` - Test suite
- `setup_intelligent_routing.sh` - Installation script

### Modified Files
- `app/helpers/request_processor.py` - Now uses MediaClassifier
- `app/models.py` - Added classification fields to Request model
- `config.py` - Already had *arr configs

### Database Changes

Added to `requests` table:
```sql
arr_service TEXT          -- 'sonarr', 'radarr', or 'lidarr'
external_id TEXT          -- TMDB/TVDB/MusicBrainz ID
confidence_score REAL     -- 0.0 to 1.0
classification_data TEXT  -- Full metadata JSON
```

## Troubleshooting

### "No matches found"

**Check TMDb API key:**
```python
from config import Config
print(Config().TMDB_API_KEY)
```

### "Music classification not working"

**Spotify credentials required:**
```yaml
Spotify:
  client_id: your_id_here
  client_secret: your_secret_here
```

### "Wrong service selected"

**Manually reclassify:**
```python
from app.models import Request, db
req = Request.query.get(42)
req.arr_service = 'radarr'  # Force to Radarr
req.status = 'Pending'
db.session.commit()
```

### "Request stuck in 'Pending'"

**Check *arr service status:**
```bash
# Test Sonarr
curl http://localhost:8989/api/v3/system/status?apikey=YOUR_KEY

# Test Radarr
curl http://localhost:7878/api/v3/system/status?apikey=YOUR_KEY

# Test Lidarr
curl http://localhost:8686/api/v1/system/status?apikey=YOUR_KEY
```

## Performance

- **Classification speed**: 500-800ms (parallel API calls)
- **Cache recommendations**: Results stored in `classification_data`
- **API rate limits**: Respects TMDb (40/10s), MusicBrainz (1/s)
- **Database indexes**: Added for `arr_service`, `status`, `confidence_score`

## Next Steps

1. **Read full docs**: `INTELLIGENT_ROUTING.md`
2. **Run tests**: `python test_classifier.py`
3. **Create UI templates** (optional - API is functional)
4. **Configure scheduled processing**:
   ```python
   from apscheduler.schedulers.background import BackgroundScheduler
   scheduler = BackgroundScheduler()
   scheduler.add_job(
       RequestProcessor.process_pending_requests,
       'interval',
       minutes=5
   )
   scheduler.start()
   ```

## Support

- **Documentation**: [`INTELLIGENT_ROUTING.md`](INTELLIGENT_ROUTING.md)
- **Issues**: [GitHub Issues](https://github.com/zy538324/Media_management/issues)
- **Test suite**: `python test_classifier.py`

## Credits

Built using:
- **TMDb API** - Movie/TV metadata
- **Spotify API** - Music search
- **MusicBrainz** - Music identification
- **Sonarr/Radarr/Lidarr** - Media automation

---

**Status**: ✅ Production-ready

**Tested with**: Python 3.8+, SQLite, Flask 3.0+
