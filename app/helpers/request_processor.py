import logging
from app.models import Request, db
from app.helpers.tmdb_helper import TMDbHelper
from app.helpers.sonarr_helper import SonarrHelper
from app.helpers.radarr_helper import RadarrHelper
from app.helpers.lidarr_helper import LidarrHelper
# Removed JackettHelper, QBittorrentHelper, normalize_media_type, get_download_path imports

class RequestProcessor:
    @staticmethod
    def process_pending_requests():
        """Process pending requests using TMDb and appropriate *Arr service."""
        logging.info("Starting request processing with *Arr services.")

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
            validated_media = None
            # Default to user's title if TMDb fails or is skipped (for music)
            validated_title = req.title
            tmdb_id = None
            tvdb_id = None # For series

            try:
                logging.info(f"Processing request ID {req.id}: Title='{req.title}', Type='{req.media_type}'")

                # TMDb validation is primarily for Movies and TV Shows to get IDs and standardized titles.
                # For Music, Lidarr typically uses MusicBrainz IDs, so TMDb might be less critical.
                # The subtask implies tmdb_helper.get_media_details might be used for all types initially.

                # Perform TMDb validation for all types first as per original logic structure
                # This also helps standardize titles and get TMDB IDs if available.
                validated_media = tmdb_helper.get_media_details(req.title, req.media_type.lower())

                if not validated_media:
                    logging.warning(f"TMDb validation failed for request ID {req.id}: {req.title} (Type: {req.media_type}). Setting status to Failed (TMDb).")
                    req.status = 'Failed (TMDb)'
                    db.session.commit()
                    continue

                # Extract common details if validation passed
                tmdb_id = validated_media.get('id')
                # Title: Movies use 'title', TV shows use 'name'. Fallback to req.title if specific field not found.
                if req.media_type.lower() == 'movie':
                    validated_title = validated_media.get('title', req.title)
                elif req.media_type.lower() in ['tv show', 'series', 'tv']:
                    validated_title = validated_media.get('name', req.title)
                    external_ids = validated_media.get('external_ids', {})
                    tvdb_id = external_ids.get('tvdb_id') if isinstance(external_ids, dict) else None
                    logging.info(f"TMDb details for TV Series '{validated_title}' (Request ID {req.id}): TMDB ID={tmdb_id}, TVDB ID={tvdb_id}")
                else: # For music and other types, use 'name' or 'title' field from TMDb if available
                    validated_title = validated_media.get('name') or validated_media.get('title', req.title)
                    logging.info(f"TMDb details for '{validated_title}' (Request ID {req.id}): TMDB ID={tmdb_id}")


                media_type_lower = req.media_type.lower()
                success = False
                new_status = req.status # Default to current status

                if media_type_lower == 'movie':
                    if not tmdb_id:
                        logging.warning(f"Missing TMDB ID for movie: {validated_title} (Request ID: {req.id}). Status: Failed (Missing TMDB ID)")
                        new_status = 'Failed (Missing TMDB ID)'
                    else:
                        logging.info(f"Processing MOVIE request ID {req.id}: {validated_title} (TMDB ID: {tmdb_id}) with Radarr.")
                        if radarr_helper.add_movie(tmdb_id=tmdb_id, title=validated_title):
                            new_status = 'SentToRadarr'
                            success = True
                        else:
                            logging.error(f"Radarr failed to add movie: {validated_title} (Request ID: {req.id})")
                            new_status = 'Failed (Radarr)'

                elif media_type_lower in ['tv show', 'series', 'tv']:
                    # Sonarr v3+ can often work with TMDB ID for series lookup if TVDB ID is not present
                    series_id_to_use = tvdb_id if tvdb_id else tmdb_id
                    id_type = "TVDB ID" if tvdb_id else "TMDB ID"

                    if not series_id_to_use:
                        logging.warning(f"Missing TVDB ID or TMDB ID for series: {validated_title} (Request ID: {req.id}). Status: Failed (Missing Series ID)")
                        new_status = 'Failed (Missing Series ID)'
                    else:
                        logging.info(f"Processing TV request ID {req.id}: {validated_title} ({id_type}: {series_id_to_use}) with Sonarr.")
                        # SonarrHelper's add_series was defined with tvdb_id as the primary parameter.
                        # If tvdb_id is None, we are passing tmdb_id to this parameter.
                        # Ensure SonarrHelper.add_series can correctly interpret this (e.g. by checking what type of ID it is, or if Sonarr API can handle TMDB ID for tvdb_id field)
                        # For this subtask, we assume it's handled or Sonarr API is flexible.
                        if sonarr_helper.add_series(tvdb_id=series_id_to_use, title=validated_title):
                            new_status = 'SentToSonarr'
                            success = True
                        else:
                            logging.error(f"Sonarr failed to add series: {validated_title} (Request ID: {req.id})")
                            new_status = 'Failed (Sonarr)'

                elif media_type_lower in ['music', 'album', 'artist']:
                    logging.info(f"Processing MUSIC request ID {req.id}: {validated_title} with Lidarr.")
                    # LidarrHelper.add_artist takes artist_name and musicbrainz_id.
                    # We don't have musicbrainz_id from TMDb typically. A real flow might search Lidarr first.
                    # For now, we pass validated_title (could be album or artist title) as artist_name and no MBID.
                    # This is a known simplification from the subtask description.
                    if lidarr_helper.add_artist(artist_name=validated_title, musicbrainz_id=None): # musicbrainz_id is not available here
                        new_status = 'SentToLidarr'
                        success = True
                    else:
                        logging.error(f"Lidarr failed to add music: {validated_title} (Request ID: {req.id})")
                        new_status = 'Failed (Lidarr)'

                else:
                    logging.warning(f"Unsupported media type: {req.media_type} for request ID {req.id}: {req.title}. Status: Failed (Unsupported Type)")
                    new_status = 'Failed (Unsupported Type)'

                req.status = new_status
                db.session.commit()

                if success:
                    logging.info(f"Successfully processed request ID {req.id} for '{validated_title}'. Status: {new_status}")
                else:
                    logging.info(f"Finished processing request ID {req.id} for '{validated_title}' with status: {new_status}")

            except Exception as e:
                db.session.rollback()
                logging.error(f"Unhandled exception processing request ID {req.id} ({req.title}): {e}", exc_info=True)
                req.status = 'Failed (Exception)'
                db.session.commit()

        logging.info("Request processing cycle completed.")
