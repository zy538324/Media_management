#!/usr/bin/env python3
"""
Reclassify Failed Requests
Resets failed classification requests to Pending for retry
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import Request, db
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def reclassify_failed():
    """Reset failed classification requests for retry."""
    app = create_app()
    
    with app.app_context():
        # Find requests with classification failures
        failed = Request.query.filter(
            Request.status == 'Failed (Classification)'
        ).all()
        
        if not failed:
            logging.info("No failed classification requests found")
            return 0
        
        logging.info(f"Found {len(failed)} failed classification requests")
        
        for req in failed:
            logging.info(f"  Resetting request {req.id}: {req.title}")
            req.status = 'Pending'
            req.arr_service = None
            req.confidence_score = None
        
        db.session.commit()
        logging.info(f"✓ Reset {len(failed)} requests for reclassification")
        logging.info("Run the request processor to reclassify them")
        
        return len(failed)

if __name__ == "__main__":
    count = reclassify_failed()
    sys.exit(0 if count >= 0 else 1)
