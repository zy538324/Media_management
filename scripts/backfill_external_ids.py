#!/usr/bin/env python3
"""
Backfill External IDs
Adds external IDs (TMDB/TVDB/MusicBrainz) to existing requests
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import Request, db
from app.helpers.media_classifier import MediaClassifier
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def backfill_ids(limit=None):
    """Backfill external IDs for requests missing them."""
    app = create_app()
    
    with app.app_context():
        classifier = MediaClassifier()
        
        # Get requests without external IDs
        query = Request.query.filter(
            Request.external_id.is_(None),
            Request.status != 'Failed (Classification)'
        )
        
        if limit:
            query = query.limit(limit)
        
        requests = query.all()
        
        if not requests:
            logging.info("No requests need external ID backfill")
            return 0
        
        logging.info(f"Backfilling external IDs for {len(requests)} requests...")
        
        success = 0
        failed = 0
        
        for req in requests:
            try:
                logging.info(f"Processing: {req.title}")
                match = classifier.get_best_match(req.title)
                
                if match and match.external_id:
                    req.arr_service = match.service.value
                    req.external_id = match.external_id
                    req.confidence_score = match.confidence
                    req.media_type = match.media_type.value
                    
                    logging.info(f"  ✓ {match.title} → {match.service.value} (ID: {match.external_id})")
                    success += 1
                else:
                    logging.warning(f"  ✗ No confident match found")
                    failed += 1
                    
            except Exception as e:
                logging.error(f"  ✗ Error: {e}")
                failed += 1
        
        db.session.commit()
        
        logging.info(f"\nBackfill complete: {success} success, {failed} failed")
        return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill external IDs for requests')
    parser.add_argument('--limit', type=int, help='Maximum number of requests to process')
    args = parser.parse_args()
    
    count = backfill_ids(limit=args.limit)
    sys.exit(0 if count >= 0 else 1)
