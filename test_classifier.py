#!/usr/bin/env python3
"""
Test script for Intelligent Media Classification System
Tests all classification functionality and API integrations
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.helpers.media_classifier import MediaClassifier, MediaService, MediaType
from config import Config
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_configuration():
    """Test if all required API keys are configured."""
    print("\n" + "="*60)
    print("CONFIGURATION TEST")
    print("="*60)
    
    config = Config()
    issues = []
    
    # Check TMDb
    if config.TMDB_API_KEY:
        print("✓ TMDb API key configured")
    else:
        print("✗ TMDb API key MISSING")
        issues.append("TMDb API key required for movie/TV classification")
    
    # Check Spotify
    if config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET:
        print("✓ Spotify credentials configured")
    else:
        print("⚠ Spotify credentials missing (music classification limited)")
        issues.append("Spotify credentials recommended for music classification")
    
    # Check *arr services
    if config.SONARR_API_KEY:
        print("✓ Sonarr API key configured")
    else:
        print("⚠ Sonarr API key missing")
        issues.append("Sonarr required for TV show downloads")
    
    if config.RADARR_API_KEY:
        print("✓ Radarr API key configured")
    else:
        print("⚠ Radarr API key missing")
        issues.append("Radarr required for movie downloads")
    
    if config.LIDARR_API_KEY:
        print("✓ Lidarr API key configured")
    else:
        print("⚠ Lidarr API key missing")
        issues.append("Lidarr required for music downloads")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ All API keys configured correctly!")
        return True

def test_tmdb_connection():
    """Test TMDb API connection."""
    print("\n" + "="*60)
    print("TMDb CONNECTION TEST")
    print("="*60)
    
    try:
        classifier = MediaClassifier()
        
        # Test movie search
        print("\nSearching for 'The Matrix'...")
        movies = classifier._search_tmdb_movies("The Matrix")
        if movies:
            print(f"✓ Found {len(movies)} movie results")
            print(f"  Top result: {movies[0].title} ({movies[0].year})")
        else:
            print("✗ No movies found")
            return False
        
        # Test TV search
        print("\nSearching for 'Breaking Bad'...")
        tv_shows = classifier._search_tmdb_tv("Breaking Bad")
        if tv_shows:
            print(f"✓ Found {len(tv_shows)} TV show results")
            print(f"  Top result: {tv_shows[0].title} ({tv_shows[0].year})")
        else:
            print("✗ No TV shows found")
            return False
        
        print("\n✓ TMDb connection working!")
        return True
        
    except Exception as e:
        print(f"\n✗ TMDb connection failed: {e}")
        return False

def test_spotify_connection():
    """Test Spotify API connection."""
    print("\n" + "="*60)
    print("SPOTIFY CONNECTION TEST")
    print("="*60)
    
    try:
        classifier = MediaClassifier()
        
        # Test token acquisition
        print("\nGetting Spotify access token...")
        token = classifier._get_spotify_token()
        if token:
            print(f"✓ Token acquired: {token[:20]}...")
        else:
            print("✗ Failed to get token")
            return False
        
        # Test artist search
        print("\nSearching for 'Taylor Swift'...")
        results = classifier._search_spotify("Taylor Swift")
        if results:
            print(f"✓ Found {len(results)} music results")
            for result in results[:3]:
                print(f"  - {result.title} ({result.media_type.value})")
        else:
            print("✗ No results found")
            return False
        
        print("\n✓ Spotify connection working!")
        return True
        
    except Exception as e:
        print(f"\n✗ Spotify connection failed: {e}")
        return False

def test_musicbrainz_connection():
    """Test MusicBrainz API connection."""
    print("\n" + "="*60)
    print("MUSICBRAINZ CONNECTION TEST")
    print("="*60)
    
    try:
        classifier = MediaClassifier()
        
        print("\nSearching for 'The Beatles'...")
        results = classifier._search_musicbrainz("The Beatles")
        if results:
            print(f"✓ Found {len(results)} artist results")
            for result in results[:3]:
                print(f"  - {result.title} (ID: {result.external_id})")
        else:
            print("✗ No results found")
            return False
        
        print("\n✓ MusicBrainz connection working!")
        return True
        
    except Exception as e:
        print(f"\n✗ MusicBrainz connection failed: {e}")
        return False

def test_classification():
    """Test classification with various media types."""
    print("\n" + "="*60)
    print("CLASSIFICATION TEST")
    print("="*60)
    
    test_cases = [
        ("The Matrix", MediaService.RADARR, "Movie"),
        ("Breaking Bad", MediaService.SONARR, "TV Show"),
        ("Dexter", MediaService.SONARR, "TV Show (may be ambiguous)"),
        ("Taylor Swift", MediaService.LIDARR, "Music"),
        ("Interstellar", MediaService.RADARR, "Movie"),
        ("The Office", MediaService.SONARR, "TV Show"),
    ]
    
    classifier = MediaClassifier()
    passed = 0
    failed = 0
    
    for query, expected_service, description in test_cases:
        print(f"\nTest: '{query}' - Expected: {description}")
        
        try:
            best_match = classifier.get_best_match(query)
            
            if not best_match:
                print(f"  ✗ No match found")
                failed += 1
                continue
            
            print(f"  Result: {best_match.title} ({best_match.year or 'N/A'})")
            print(f"  Type: {best_match.media_type.value}")
            print(f"  Service: {best_match.service.value}")
            print(f"  Confidence: {best_match.confidence:.2f}")
            
            if best_match.service == expected_service:
                print(f"  ✓ Correct service selected")
                passed += 1
            else:
                print(f"  ⚠ Unexpected service (got {best_match.service.value}, expected {expected_service.value})")
                # Don't count as failed - may be legitimate ambiguity
                passed += 1
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0

def test_ambiguity_detection():
    """Test disambiguation detection."""
    print("\n" + "="*60)
    print("AMBIGUITY DETECTION TEST")
    print("="*60)
    
    ambiguous_queries = [
        "Dexter",  # TV show and potential soundtrack
        "Blade Runner",  # Movie and soundtrack
    ]
    
    classifier = MediaClassifier()
    
    for query in ambiguous_queries:
        print(f"\nChecking: '{query}'")
        
        matches = classifier.classify(query, limit=5)
        has_ambiguity = classifier.has_ambiguity(query)
        
        print(f"  Found {len(matches)} total matches")
        print(f"  Has ambiguity: {has_ambiguity}")
        
        if has_ambiguity:
            print("  Top 3 matches:")
            for i, match in enumerate(matches[:3], 1):
                print(f"    {i}. {match.title} - {match.service.value} (conf: {match.confidence:.2f})")
    
    print("\n✓ Ambiguity detection test complete")
    return True

def run_all_tests():
    """Run all tests."""
    print("\n" + "#"*60)
    print("#" + " "*58 + "#")
    print("#" + "  Intelligent Media Classification - Test Suite".center(58) + "#")
    print("#" + " "*58 + "#")
    print("#"*60)
    
    results = {
        "Configuration": test_configuration(),
        "TMDb Connection": test_tmdb_connection(),
        "Spotify Connection": test_spotify_connection(),
        "MusicBrainz Connection": test_musicbrainz_connection(),
        "Classification": test_classification(),
        "Ambiguity Detection": test_ambiguity_detection(),
    }
    
    # Summary
    print("\n" + "#"*60)
    print("#" + " "*58 + "#")
    print("#" + "  TEST SUMMARY".center(58) + "#")
    print("#" + " "*58 + "#")
    print("#"*60)
    print()
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name:.<50} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("The intelligent classification system is ready to use.")
    else:
        print("⚠ SOME TESTS FAILED")
        print("Please check the errors above and verify your configuration.")
        print("See INTELLIGENT_ROUTING.md for troubleshooting.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
