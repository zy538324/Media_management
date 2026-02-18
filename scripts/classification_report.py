#!/usr/bin/env python3
"""
Classification Report
Generates statistics and insights on classification performance
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import Request
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def generate_report(days=7):
    """Generate classification performance report."""
    app = create_app()
    
    with app.app_context():
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        print("="*70)
        print(f"Classification Performance Report (Last {days} Days)")
        print("="*70)
        print()
        
        # Total requests
        total = Request.query.filter(Request.requested_at >= cutoff).count()
        print(f"Total Requests: {total}")
        
        if total == 0:
            print("\nNo requests in this period")
            return
        
        # Classified requests
        classified = Request.query.filter(
            Request.requested_at >= cutoff,
            Request.arr_service.isnot(None)
        ).count()
        print(f"Classified: {classified} ({classified/total*100:.1f}%)")
        
        # By service
        print("\nBy Service:")
        services = Request.query.with_entities(
            Request.arr_service,
            func.count(Request.id)
        ).filter(
            Request.requested_at >= cutoff,
            Request.arr_service.isnot(None)
        ).group_by(Request.arr_service).all()
        
        for service, count in services:
            print(f"  {service:15} {count:4} ({count/classified*100:.1f}%)")
        
        # By status
        print("\nBy Status:")
        statuses = Request.query.with_entities(
            Request.status,
            func.count(Request.id)
        ).filter(
            Request.requested_at >= cutoff
        ).group_by(Request.status).all()
        
        for status, count in statuses:
            print(f"  {status:25} {count:4} ({count/total*100:.1f}%)")
        
        # Success rate
        successful = Request.query.filter(
            Request.requested_at >= cutoff,
            Request.status.like('SentTo%')
        ).count()
        print(f"\nSuccess Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        
        # Average confidence
        avg_confidence = Request.query.with_entities(
            func.avg(Request.confidence_score)
        ).filter(
            Request.requested_at >= cutoff,
            Request.confidence_score.isnot(None)
        ).scalar()
        
        if avg_confidence:
            print(f"Average Confidence: {avg_confidence:.3f}")
        
        # Low confidence requests
        low_conf = Request.query.filter(
            Request.requested_at >= cutoff,
            Request.confidence_score < 0.6,
            Request.confidence_score.isnot(None)
        ).count()
        
        if low_conf > 0:
            print(f"\nLow Confidence (<0.6): {low_conf}")
            print("\nLow Confidence Requests:")
            low_conf_reqs = Request.query.filter(
                Request.requested_at >= cutoff,
                Request.confidence_score < 0.6
            ).order_by(Request.confidence_score).limit(10).all()
            
            for req in low_conf_reqs:
                print(f"  ID {req.id:4} | {req.title:30} | {req.arr_service:7} | {req.confidence_score:.3f}")
        
        # Failed requests
        failed = Request.query.filter(
            Request.requested_at >= cutoff,
            Request.status.like('Failed%')
        ).count()
        
        if failed > 0:
            print(f"\nFailed Requests: {failed}")
            print("\nRecent Failures:")
            failed_reqs = Request.query.filter(
                Request.requested_at >= cutoff,
                Request.status.like('Failed%')
            ).order_by(Request.requested_at.desc()).limit(10).all()
            
            for req in failed_reqs:
                print(f"  ID {req.id:4} | {req.title:30} | {req.status}")
        
        print("\n" + "="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate classification report')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze (default: 7)')
    args = parser.parse_args()
    
    generate_report(days=args.days)
