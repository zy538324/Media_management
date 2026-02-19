from flask import Blueprint, request, jsonify
from app.models import db, Request
from flask_login import login_required, current_user
from app.helpers.qbittorrent_helper import QBittorrentHelper
from app.helpers.tmdb_helper import TMDbHelper
from app.helpers.jackett_helper import JackettHelper
from app.helpers.radarr_helper import RadarrHelper
from app.helpers.sonarr_helper import SonarrHelper
from app.helpers.lidarr_helper import LidarrHelper
from config import Config
import logging

bp = Blueprint('request_routes', __name__)

# Initialize the configuration
config = Config()

@bp.route('/create-request', methods=['POST'])
@login_required
def create_request():
    data = request.get_json()
    title = data.get('title')
    media_type = data.get('media_type')

    logging.info(f"[CREATE-REQUEST] Received request for title='{title}', media_type='{media_type}'")

    if not title or not media_type:
        return jsonify({'error': 'Title and media type are required'}), 400

    # Check if the media exists using TMDb and classify it
    tmdb_helper = TMDbHelper()
    logging.info(f"[CREATE-REQUEST] Classifying title with TMDb: {title}")
    classification = tmdb_helper.classify_title(title)
    logging.info(f"[CREATE-REQUEST] Classification result: {classification}")
    
    if not classification:
        return jsonify({'message': f"Failed to classify the title: {title}"}), 404

    # Get TMDb details for the media
    logging.info(f"[CREATE-REQUEST] Getting TMDb details for {title} (type: {classification})")
    media_details = tmdb_helper.get_media_details(title, classification.lower())
    tmdb_id = media_details.get('id') if media_details else None
    logging.info(f"[CREATE-REQUEST] TMDb ID: {tmdb_id}, Media Details: {media_details}")

    # Add request to the database
    new_request = Request(
        user_id=current_user.id,
        media_type=classification,
        title=title
    )
    db.session.add(new_request)
    db.session.commit()
    logging.info(f"[CREATE-REQUEST] Request saved to database with ID: {new_request.id}")
    
    # Send to appropriate *arr service
    try:
        logging.info(f"[CREATE-REQUEST] Attempting to send to *arr services. Classification: {classification}, TMDb ID: {tmdb_id}")
        
        if classification == 'Movie' and tmdb_id:
            logging.info(f"[CREATE-REQUEST] Sending to Radarr...")
            radarr = RadarrHelper()
            logging.info(f"[CREATE-REQUEST] Radarr configured - API URL: {radarr.api_url}, Has API Key: {bool(radarr.api_key)}")
            
            if radarr.api_url and radarr.api_key:
                success = radarr.add_movie(tmdb_id, title)
                logging.info(f"[CREATE-REQUEST] Sent movie request to Radarr: {title} (ID: {tmdb_id}) - Success: {success}")
            else:
                logging.warning(f"[CREATE-REQUEST] Radarr not configured, request created but not sent to Radarr")
                
        elif classification == 'TV' and tmdb_id:
            logging.info(f"[CREATE-REQUEST] Sending to Sonarr...")
            sonarr = SonarrHelper()
            logging.info(f"[CREATE-REQUEST] Sonarr configured - API URL: {sonarr.api_url}, Has API Key: {bool(sonarr.api_key)}")
            
            if sonarr.api_url and sonarr.api_key:
                success = sonarr.add_series(tmdb_id, title)
                logging.info(f"[CREATE-REQUEST] Sent TV request to Sonarr: {title} (ID: {tmdb_id}) - Success: {success}")
            else:
                logging.warning(f"[CREATE-REQUEST] Sonarr not configured, request created but not sent to Sonarr")
                
        elif classification == 'Music' and tmdb_id:
            logging.info(f"[CREATE-REQUEST] Sending to Lidarr...")
            lidarr = LidarrHelper()
            logging.info(f"[CREATE-REQUEST] Lidarr configured - API URL: {lidarr.api_url}, Has API Key: {bool(lidarr.api_key)}")
            
            if lidarr.api_url and lidarr.api_key:
                success = lidarr.add_artist(tmdb_id, title)
                logging.info(f"[CREATE-REQUEST] Sent music request to Lidarr: {title} (ID: {tmdb_id}) - Success: {success}")
            else:
                logging.warning(f"[CREATE-REQUEST] Lidarr not configured, request created but not sent to Lidarr")
        else:
            logging.warning(f"[CREATE-REQUEST] No TMDb ID or unrecognized classification. Classification: {classification}, TMDb ID: {tmdb_id}")
            
    except Exception as e:
        logging.error(f"[CREATE-REQUEST] Error sending request to *arr service: {e}", exc_info=True)
    
    return jsonify({'message': f"Request for {title} created successfully"}), 201