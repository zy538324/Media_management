import logging
import json
from app.models import Request, db
from app.helpers.tmdb_helper import TMDbHelper
from app.helpers.sonarr_helper import SonarrHelper
from app.helpers.radarr_helper import RadarrHelper
from app.helpers.lidarr_helper import LidarrHelper
from app.helpers.media_classifier import MediaClassifier, MediaService, MediaType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RequestProcessor:
    @staticmethod
    def process_pending_requests():
        """Process pending requests using intelligent media classification and appropriate *Arr service."""
        logging.info("Starting intelligent request processing with *Arr services.")

        classifier = MediaClassifier()
        tmdb_helper = TMDbHelper()
        sonarr_helper = SonarrHelper()
        radarr_helper = RadarrHelper()
        lidarr_helper = LidarrHelper()

        pending_requests = Request.query.filter_by(status='Pending').all()
        if not pending_requests:
            logging.info("No pending requests to process.")
            return
        
        logging.info(f"Found {len(pending_requests)} pending requests.")

        for req in pending_requests:
            try:
                logging.info(f"Processing request ID {req.id}: Title='{req.title}', Type='{req.media_type}'")

                # If request already has classification data, use it
                if req.is_classified() and req.arr_service:
                    logging.info(f"Request ID {req.id} already classified as {req.arr_service} (confidence: {req.confidence_score:.2f})")
                    best_match = type('obj', (object,), {
                        'service': MediaService(req.arr_service),
                        'media_type': MediaType(req.media_type.lower()),
                        'external_id': req.external_id,
                        'title': req.title
                    })()
                else:
                    # Use intelligent classifier to determine media type and service
                    best_match = classifier.get_best_match(req.title)
                    
                    if not best_match:
                        logging.warning(f"Classification failed for request ID {req.id}: '{req.title}'. Setting status to Failed (Classification).")
                        req.status = 'Failed (Classification)'
                        db.session.commit()
                        continue

                    # Store classification metadata
                    req.arr_service = best_match.service.value
                    req.external_id = best_match.external_id
                    req.confidence_score = best_match.confidence
                    req.media_type = best_match.media_type.value
                    
                    # Store full classification data as JSON for debugging
                    classification_metadata = {
                        'title': best_match.title,
                        'year': best_match.year,
                        'description': best_match.description,
                        'poster_url': best_match.poster_url,
                        'additional_data': best_match.additional_data
                    }
                    req.classification_data = json.dumps(classification_metadata)
                    
                    db.session.commit()
                    
                    logging.info(f"Classified request ID {req.id} as '{best_match.title}' → {best_match.service.value} (confidence: {best_match.confidence:.2f})")

                # Route to appropriate service based on classification
                success = False
                new_status = req.status

                if best_match.service == MediaService.RADARR:
                    # Process movie with Radarr
                    if not best_match.external_id:
                        logging.warning(f"Missing TMDB ID for movie: {req.title} (Request ID: {req.id})")
                        new_status = 'Failed (Missing TMDB ID)'
                    else:
                        logging.info(f"Adding movie to Radarr: '{req.title}' (TMDB ID: {best_match.external_id})")
                        if radarr_helper.add_movie(tmdb_id=best_match.external_id, title=req.title):
                            new_status = 'SentToRadarr'
                            success = True
                            logging.info(f"Successfully added to Radarr: {req.title}")
                        else:
                            logging.error(f"Radarr failed to add movie: {req.title} (Request ID: {req.id})")
                            new_status = 'Failed (Radarr)'

                elif best_match.service == MediaService.SONARR:
                    # Process TV show with Sonarr
                    tvdb_id = best_match.external_id
                    
                    # If we have TMDB ID but no TVDB ID, try to get TVDB ID
                    if not tvdb_id and best_match.additional_data and best_match.additional_data.get('tmdb_id'):
                        tmdb_id = best_match.additional_data['tmdb_id']
                        tvdb_id = classifier._get_tvdb_id(int(tmdb_id))
                        if tvdb_id:
                            req.external_id = tvdb_id
                            db.session.commit()
                    
                    if not tvdb_id:
                        logging.warning(f"Missing TVDB ID for series: {req.title} (Request ID: {req.id})")
                        new_status = 'Failed (Missing TVDB ID)'
                    else:
                        logging.info(f"Adding series to Sonarr: '{req.title}' (TVDB ID: {tvdb_id})")
                        if sonarr_helper.add_series(tvdb_id=tvdb_id, title=req.title):
                            new_status = 'SentToSonarr'
                            success = True
                            logging.info(f"Successfully added to Sonarr: {req.title}")
                        else:
                            logging.error(f"Sonarr failed to add series: {req.title} (Request ID: {req.id})")
                            new_status = 'Failed (Sonarr)'

                elif best_match.service == MediaService.LIDARR:
                    # Process music with Lidarr
                    musicbrainz_id = best_match.external_id
                    artist_name = req.title
                    
                    # Extract artist name from additional data if available
                    if best_match.additional_data:
                        if best_match.additional_data.get('type') == 'album' and best_match.additional_data.get('artist'):
                            artist_name = best_match.additional_data['artist']
                    
                    logging.info(f"Adding artist to Lidarr: '{artist_name}' (MusicBrainz ID: {musicbrainz_id or 'None'})")
                    if lidarr_helper.add_artist(artist_name=artist_name, musicbrainz_id=musicbrainz_id):
                        new_status = 'SentToLidarr'
                        success = True
                        logging.info(f"Successfully added to Lidarr: {artist_name}")
                    else:
                        logging.error(f"Lidarr failed to add music: {req.title} (Request ID: {req.id})")
                        new_status = 'Failed (Lidarr)'

                else:
                    logging.warning(f"Unknown service: {best_match.service} for request ID {req.id}")
                    new_status = 'Failed (Unknown Service)'

                req.status = new_status
                db.session.commit()

                if success:
                    logging.info(f"✓ Request ID {req.id} processed successfully: '{req.title}' → {best_match.service.value}")
                else:
                    logging.info(f"✗ Request ID {req.id} failed with status: {new_status}")

            except Exception as e:
                db.session.rollback()
                logging.error(f"Unhandled exception processing request ID {req.id} ({req.title}): {e}", exc_info=True)
                req.status = 'Failed (Exception)'
                db.session.commit()

        logging.info("Request processing cycle completed.")

    @staticmethod
    def classify_request(title: str):
        """
        Classify a media request and return all potential matches.
        Useful for disambiguation UI.
        
        Args:
            title: Media title to classify
            
        Returns:
            List of MediaMatch objects with classification results
        """
        classifier = MediaClassifier()
        return classifier.classify(title, limit=10)

    @staticmethod
    def check_ambiguity(title: str) -> bool:
        """
        Check if a title has ambiguous classification across multiple services.
        
        Args:
            title: Media title to check
            
        Returns:
            True if disambiguation is needed
        """
        classifier = MediaClassifier()
        return classifier.has_ambiguity(title)
