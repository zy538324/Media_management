# Intelligent Routing - Operational Runbook

## Day 1: Initial Deployment

### Pre-Deployment Checklist

```bash
# 1. Pull latest code
git pull origin main

# 2. Verify installation status
python check_installation.py

# 3. Backup database (automatic in setup script, or manual)
cp media_management.db media_management.db.backup.$(date +%Y%m%d_%H%M%S)

# 4. Apply database migration
sqlite3 media_management.db < migrations/add_classification_fields.sql

# 5. Verify migration
sqlite3 media_management.db "PRAGMA table_info(requests);" | grep -E "(arr_service|external_id|confidence)"

# Expected output:
# 8|arr_service|TEXT|0||0
# 9|arr_id|TEXT|0||0
# 10|external_id|TEXT|0||0
# 11|confidence_score|REAL|0||0
# 12|classification_data|TEXT|0||0
```

### Deployment

```bash
# Start application
python run.py

# Watch logs in another terminal
tail -f logs/app.log | grep -E "(Classifying|Classified|Adding|SentTo)"
```

### Post-Deployment Verification

**Test 1: Classification API**
```bash
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "Breaking Bad"}' | jq

# Expected: JSON with results array, has_ambiguity: false, service: "sonarr"
```

**Test 2: Create Test Request**
```bash
curl -X POST http://localhost:5000/api/request/create \
  -H "Content-Type: application/json" \
  -d '{"title": "The Matrix"}' | jq

# Expected: {"success": true, "service": "radarr", "confidence": 0.XX}
```

**Test 3: Verify Request in Database**
```bash
sqlite3 media_management.db "SELECT id, title, arr_service, confidence_score, status FROM requests ORDER BY id DESC LIMIT 1;"

# Expected: 1|The Matrix|radarr|0.89|Pending
```

**Test 4: Trigger Processing**
```bash
python -c "from app.helpers.request_processor import RequestProcessor; RequestProcessor.process_pending_requests()"

# Check logs for:
# INFO: Classified request ID X as 'The Matrix' → radarr
# INFO: Adding movie to Radarr: 'The Matrix' (TMDB ID: 603)
# INFO: ✓ Request ID X processed successfully
```

**Test 5: Verify in Radarr**
```bash
curl "http://localhost:7878/api/v3/movie?apikey=YOUR_RADARR_KEY" | jq '.[] | select(.title=="The Matrix")'

# Expected: Movie object with title "The Matrix"
```

---

## Daily Operations

### Monitoring

**Check System Health**
```bash
# Classification success rate (last 24 hours)
sqlite3 media_management.db "SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN arr_service IS NOT NULL THEN 1 END) as classified,
  COUNT(CASE WHEN status LIKE 'SentTo%' THEN 1 END) as successful,
  ROUND(100.0 * COUNT(CASE WHEN status LIKE 'SentTo%' THEN 1 END) / COUNT(*), 2) as success_rate
FROM requests 
WHERE requested_at > datetime('now', '-1 day');"

# Example output:
# total|classified|successful|success_rate
# 45|43|41|91.11
```

**Check Failed Requests**
```bash
sqlite3 media_management.db "SELECT id, title, status, arr_service, confidence_score 
FROM requests 
WHERE status LIKE 'Failed%' 
ORDER BY requested_at DESC LIMIT 10;"

# Review failures and reclassify if needed
```

**Check Low Confidence Classifications**
```bash
sqlite3 media_management.db "SELECT id, title, arr_service, confidence_score, status 
FROM requests 
WHERE confidence_score < 0.6 AND confidence_score IS NOT NULL
ORDER BY confidence_score ASC LIMIT 10;"

# Review and manually verify these classifications
```

**Monitor *arr Service Connectivity**
```bash
# Test all services
for service in sonarr radarr lidarr; do
  case $service in
    sonarr) port=8989; api="/api/v3/system/status" ;;
    radarr) port=7878; api="/api/v3/system/status" ;;
    lidarr) port=8686; api="/api/v1/system/status" ;;
  esac
  
  echo -n "$service: "
  if curl -s "http://localhost:$port$api?apikey=YOUR_KEY" | jq -r '.version' 2>/dev/null; then
    echo " OK"
  else
    echo " FAILED"
  fi
done
```

### Log Analysis

**Top Classified Media Types**
```bash
grep "Classified request" logs/app.log | \
  grep -oP "(?<=\→ )\w+" | \
  sort | uniq -c | sort -rn

# Example output:
# 28 sonarr
# 15 radarr
#  3 lidarr
```

**Average Confidence Scores**
```bash
grep "confidence:" logs/app.log | \
  grep -oP "confidence: \K[0-9.]+" | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count}'

# Example output:
# Average: 0.847
```

**Recent Errors**
```bash
tail -100 logs/app.log | grep -E "(ERROR|Failed|Exception)"
```

---

## Common Maintenance Tasks

### Reclassify Failed Requests

**Option 1: Automatic Reclassification**
```python
# reclassify_failed.py
from app.models import Request, db
from app import create_app

app = create_app()
with app.app_context():
    failed = Request.query.filter(
        Request.status.like('Failed (Classification)')
    ).all()
    
    for req in failed:
        req.status = 'Pending'
        req.arr_service = None
        req.confidence_score = None
    
    db.session.commit()
    print(f"Reset {len(failed)} failed requests for reclassification")
```

Run with:
```bash
python reclassify_failed.py
```

**Option 2: Manual Override**
```python
# Force request to specific service
from app.models import Request, db
from app import create_app

app = create_app()
with app.app_context():
    req = Request.query.get(42)  # Request ID
    req.arr_service = 'radarr'  # Force to Radarr
    req.status = 'Pending'
    req.confidence_score = 1.0  # Manual = 100% confidence
    db.session.commit()
    print(f"Request {req.id} rerouted to {req.arr_service}")
```

### Bulk Import External IDs

If you have existing requests without external IDs:

```python
# backfill_ids.py
from app.models import Request, db
from app.helpers.media_classifier import MediaClassifier
from app import create_app
import logging

logging.basicConfig(level=logging.INFO)

app = create_app()
with app.app_context():
    classifier = MediaClassifier()
    
    # Get requests without external IDs
    requests = Request.query.filter(
        Request.external_id.is_(None),
        Request.status != 'Failed (Classification)'
    ).all()
    
    logging.info(f"Backfilling {len(requests)} requests...")
    
    for req in requests:
        try:
            match = classifier.get_best_match(req.title)
            if match:
                req.arr_service = match.service.value
                req.external_id = match.external_id
                req.confidence_score = match.confidence
                logging.info(f"✓ {req.title} → {match.service.value} (ID: {match.external_id})")
            else:
                logging.warning(f"✗ No match for {req.title}")
        except Exception as e:
            logging.error(f"Error processing {req.title}: {e}")
    
    db.session.commit()
    logging.info("Backfill complete")
```

### Clear Old Classification Data

```bash
# Archive requests older than 90 days
sqlite3 media_management.db "DELETE FROM requests 
WHERE status LIKE 'SentTo%' 
AND requested_at < datetime('now', '-90 days');"

# Or export to CSV first
sqlite3 media_management.db -header -csv \
  "SELECT * FROM requests WHERE requested_at < datetime('now', '-90 days');" \
  > archived_requests_$(date +%Y%m%d).csv
```

---

## Troubleshooting Guide

### Issue: High Failure Rate

**Diagnosis:**
```bash
# Check failure distribution
sqlite3 media_management.db "SELECT status, COUNT(*) 
FROM requests 
WHERE status LIKE 'Failed%' 
GROUP BY status 
ORDER BY COUNT(*) DESC;"

# Common failures:
# Failed (Sonarr) - Sonarr API issue
# Failed (Radarr) - Radarr API issue  
# Failed (Classification) - No confident match
# Failed (Missing TVDB ID) - TV show not in TVDB
```

**Solutions:**

1. **Sonarr/Radarr API Failures**
   ```bash
   # Check service status
   curl http://localhost:8989/api/v3/system/status?apikey=YOUR_KEY
   
   # Check logs
   tail -f /path/to/sonarr/logs/sonarr.txt
   
   # Restart service if needed
   systemctl restart sonarr
   ```

2. **Classification Failures**
   ```bash
   # Check TMDb API key
   python -c "from config import Config; c = Config(); print('TMDb:', bool(c.TMDB_API_KEY))"
   
   # Test TMDb directly
   curl "https://api.themoviedb.org/3/search/movie?api_key=YOUR_KEY&query=The+Matrix"
   ```

3. **Missing TVDB IDs**
   ```python
   # Some shows only have TMDB IDs
   # Update Sonarr to v3+ which accepts TMDB IDs
   # Or manually add TVDB ID:
   from app.models import Request, db
   from app import create_app
   
   app = create_app()
   with app.app_context():
       req = Request.query.get(42)
       req.external_id = '12345'  # TVDB ID from thetvdb.com
       req.status = 'Pending'
       db.session.commit()
   ```

### Issue: Slow Classification

**Diagnosis:**
```bash
# Check API response times
time python -c "from app.helpers.media_classifier import MediaClassifier; c = MediaClassifier(); c.classify('Breaking Bad')"

# Should be < 1 second
```

**Solutions:**

1. **TMDb Rate Limiting**
   - Limit: 40 requests per 10 seconds
   - Solution: Batch process requests instead of real-time

2. **Network Latency**
   - Check internet connection
   - Consider caching results (Redis)

3. **Database Locks**
   ```bash
   # Check for locks
   sqlite3 media_management.db "PRAGMA busy_timeout=5000;"
   ```

### Issue: Wrong Service Selected

**Examples:**
- "Dexter" movie instead of TV show
- "Blade Runner" soundtrack instead of movie

**Solution: Manual Override**
```bash
curl -X POST http://localhost:5000/api/request/42/reclassify \
  -H "Content-Type: application/json" \
  -d '{"force_service": "sonarr"}'
```

**Or via Python:**
```python
from app.models import Request, db
from app import create_app

app = create_app()
with app.app_context():
    req = Request.query.get(42)
    req.arr_service = 'sonarr'  # Correct service
    req.status = 'Pending'  # Reprocess
    db.session.commit()
```

### Issue: Ambiguous Classifications

**Identify:**
```bash
sqlite3 media_management.db "SELECT id, title, arr_service, confidence_score 
FROM requests 
WHERE confidence_score BETWEEN 0.35 AND 0.65 
ORDER BY confidence_score ASC;"
```

**Review:**
```python
from app.helpers.media_classifier import MediaClassifier

classifier = MediaClassifier()
matches = classifier.classify("Ambiguous Title", limit=5)

for match in matches:
    print(f"{match.title} ({match.year}) - {match.service.value} - {match.confidence:.2f}")
```

---

## Performance Optimization

### Enable Query Result Caching

```python
# app/helpers/media_classifier.py
# Add caching for repeated queries

from functools import lru_cache
import hashlib

class MediaClassifier:
    @lru_cache(maxsize=1000)
    def get_best_match(self, query: str) -> Optional[MediaMatch]:
        # Existing implementation
        pass
```

### Batch Processing

Instead of real-time classification:

```python
# Increase background processing frequency
scheduler.add_job(
    process_pending_requests_task, 
    'interval', 
    minutes=2  # Changed from 5 to 2
)
```

### Database Optimization

```bash
# Analyze and optimize
sqlite3 media_management.db "ANALYZE;"
sqlite3 media_management.db "VACUUM;"

# Add compound indexes for common queries
sqlite3 media_management.db "CREATE INDEX IF NOT EXISTS idx_requests_status_service 
ON requests(status, arr_service);"
```

---

## Backup and Recovery

### Automated Backups

```bash
# Add to crontab (daily backups at 2 AM)
0 2 * * * cd /path/to/Media_management && sqlite3 media_management.db ".backup 'backups/db_$(date +\%Y\%m\%d).db'" && find backups/ -name "db_*.db" -mtime +30 -delete
```

### Restore from Backup

```bash
# Stop application
pkill -f "python run.py"

# Restore database
cp media_management.db media_management.db.corrupted
cp backups/db_20260218.db media_management.db

# Restart application
python run.py
```

### Export Classification Data

```bash
# Export all classification metadata
sqlite3 media_management.db -header -csv \
  "SELECT id, title, arr_service, external_id, confidence_score, 
   datetime(requested_at) as requested, status 
   FROM requests 
   WHERE arr_service IS NOT NULL;" \
  > classification_export_$(date +%Y%m%d).csv
```

---

## Security Considerations

### API Key Rotation

```bash
# When rotating *arr service API keys:

# 1. Update config.yaml with new keys
vim config.yaml

# 2. Test connectivity
python test_classifier.py

# 3. Restart application (graceful)
pkill -TERM -f "python run.py"
python run.py
```

### Access Control

```python
# Add authentication to API endpoints
# In app/routes/unified_requests.py:

from flask_login import login_required

@unified_requests_bp.route('/api/classify', methods=['POST'])
@login_required  # Ensure user is authenticated
def classify_media():
    # ... existing code
```

---

## Monitoring Alerts

### Set Up Alerts

```bash
# alert_check.sh - Run every 15 minutes via cron

#!/bin/bash

# Check failure rate
FAILURE_RATE=$(sqlite3 media_management.db "SELECT 
  CAST(COUNT(CASE WHEN status LIKE 'Failed%' THEN 1 END) AS FLOAT) / COUNT(*) * 100
FROM requests 
WHERE requested_at > datetime('now', '-1 hour');")

if (( $(echo "$FAILURE_RATE > 20" | bc -l) )); then
  echo "ALERT: High failure rate: ${FAILURE_RATE}%" | mail -s "Media Management Alert" admin@example.com
fi

# Check service connectivity
for service in sonarr radarr lidarr; do
  # ... check logic ...
  if [ $? -ne 0 ]; then
    echo "ALERT: $service is down" | mail -s "Service Down: $service" admin@example.com
  fi
done
```

---

## Upgrade Path

When updating the intelligent routing system:

```bash
# 1. Backup
cp media_management.db media_management.db.backup.pre_upgrade

# 2. Pull updates
git pull origin main

# 3. Check for new migrations
ls -lt migrations/*.sql

# 4. Apply migrations
for migration in migrations/*.sql; do
  echo "Applying $migration..."
  sqlite3 media_management.db < "$migration"
done

# 5. Update dependencies
pip install -r requirements.txt --upgrade

# 6. Test
python check_installation.py
python test_classifier.py

# 7. Restart
pkill -TERM -f "python run.py"
python run.py
```

---

## Metrics to Track

```bash
# Weekly report
#!/bin/bash
echo "=== Weekly Classification Report ==="
echo ""

echo "Total Requests:"
sqlite3 media_management.db "SELECT COUNT(*) FROM requests WHERE requested_at > datetime('now', '-7 days');"

echo "\nBy Service:"
sqlite3 media_management.db "SELECT arr_service, COUNT(*) FROM requests WHERE requested_at > datetime('now', '-7 days') GROUP BY arr_service;"

echo "\nSuccess Rate:"
sqlite3 media_management.db "SELECT 
  ROUND(100.0 * COUNT(CASE WHEN status LIKE 'SentTo%' THEN 1 END) / COUNT(*), 2) || '%'
FROM requests WHERE requested_at > datetime('now', '-7 days');"

echo "\nAverage Confidence:"
sqlite3 media_management.db "SELECT ROUND(AVG(confidence_score), 3) FROM requests WHERE requested_at > datetime('now', '-7 days') AND confidence_score IS NOT NULL;"
```

---

**Runbook Version:** 1.0  
**Last Updated:** 2026-02-18  
**Owner:** Media Management System
