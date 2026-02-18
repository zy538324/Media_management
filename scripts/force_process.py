#!/usr/bin/env python3
"""
Force Request Processing
Manually trigger request processing without waiting for scheduler
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.helpers.request_processor import RequestProcessor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def force_process():
    """Force immediate processing of pending requests."""
    app = create_app()
    
    with app.app_context():
        logging.info("Forcing request processing...")
        RequestProcessor.process_pending_requests()
        logging.info("Processing complete")

if __name__ == "__main__":
    force_process()
