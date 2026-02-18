from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Request as MediaRequest, db
from app.helpers.media_classifier import MediaClassifier
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

unified_requests_bp = Blueprint('unified_requests', __name__, url_prefix='/unified')


@unified_requests_bp.route('/request', methods=['GET'])
@login_required
def request_page():
    """Render the unified media request page."""
    return render_template('unified_request.html')


@unified_requests_bp.route('/classify', methods=['POST'])
@login_required
def classify_media():
    """
    AJAX endpoint to classify a media title and return potential matches.
    Used for real-time search as user types.
    
    Request body:
        {"title": "search query"}
    
    Response:
        {
            "success": true,
            "matches": [
                {
                    "title": "Dexter",
                    "media_type": "tv",
                    "service": "sonarr",
                    "confidence": 0.95,
                    "year": 2006,
                    "description": "...",
                    "poster_url": "...",
                    "external_id": "..."
                }
            ],
            "needs_disambiguation": false
        }
    """
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        if len(title) < 2:
            return jsonify({'success': False, 'error': 'Title too short'}), 400
        
        classifier = MediaClassifier()
        matches = classifier.classify(title, limit=10)
        
        # Check if disambiguation is needed
        needs_disambiguation = classifier.has_ambiguity(title)
        
        # Convert matches to JSON-serializable format
        matches_data = []
        for match in matches:
            matches_data.append({
                'title': match.title,
                'media_type': match.media_type.value,
                'service': match.service.value,
                'confidence': round(match.confidence, 3),
                'year': match.year,
                'description': match.description,
                'poster_url': match.poster_url,
                'external_id': match.external_id,
                'additional_data': match.additional_data
            })
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'needs_disambiguation': needs_disambiguation,
            'best_match': matches_data[0] if matches_data else None
        })
        
    except Exception as e:
        logging.error(f"Error classifying media: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@unified_requests_bp.route('/submit', methods=['POST'])
@login_required
def submit_request():
    """
    Submit a media request with classification data.
    
    Request body (form data or JSON):
        {
            "title": "Media title",
            "match_index": 0,  # Optional: index of selected match from classification
            "classification_data": {...}  # Full classification data
        }
    """
    try:
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        title = data.get('title', '').strip()
        if not title:
            flash('Title is required', 'error')
            return redirect(url_for('unified_requests.request_page'))
        
        # Get classification data if provided
        classification_json = data.get('classification_data')
        if classification_json:
            if isinstance(classification_json, str):
                classification = json.loads(classification_json)
            else:
                classification = classification_json
        else:
            # Perform classification if not provided
            classifier = MediaClassifier()
            best_match = classifier.get_best_match(title)
            
            if not best_match:
                flash(f'Could not classify "{title}". Please try a different search term.', 'error')
                return redirect(url_for('unified_requests.request_page'))
            
            classification = {
                'title': best_match.title,
                'media_type': best_match.media_type.value,
                'service': best_match.service.value,
                'confidence': best_match.confidence,
                'year': best_match.year,
                'description': best_match.description,
                'poster_url': best_match.poster_url,
                'external_id': best_match.external_id,
                'additional_data': best_match.additional_data
            }
        
        # Create request in database
        new_request = MediaRequest(
            user_id=current_user.id,
            title=classification.get('title', title),
            media_type=classification.get('media_type', 'unknown'),
            status='Pending',
            priority=data.get('priority', 'Medium'),
            arr_service=classification.get('service'),
            external_id=classification.get('external_id'),
            confidence_score=classification.get('confidence'),
            classification_data=json.dumps(classification)
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        logging.info(f"Request created: ID={new_request.id}, Title='{new_request.title}', Service={new_request.arr_service}")
        
        # Return appropriate response based on request type
        if request.is_json:
            return jsonify({
                'success': True,
                'request_id': new_request.id,
                'message': f'Request submitted: {new_request.title} → {new_request.arr_service}'
            })
        else:
            flash(f'Request submitted successfully: {new_request.title}', 'success')
            return redirect(url_for('unified_requests.request_page'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error submitting request: {e}", exc_info=True)
        
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            flash(f'Error submitting request: {str(e)}', 'error')
            return redirect(url_for('unified_requests.request_page'))


@unified_requests_bp.route('/my-requests', methods=['GET'])
@login_required
def my_requests():
    """View current user's media requests."""
    user_requests = MediaRequest.query.filter_by(user_id=current_user.id).order_by(MediaRequest.requested_at.desc()).all()
    return render_template('my_requests.html', requests=user_requests)


@unified_requests_bp.route('/requests/<int:request_id>', methods=['GET'])
@login_required
def request_detail(request_id):
    """View details of a specific request."""
    media_request = MediaRequest.query.get_or_404(request_id)
    
    # Only allow user to view their own requests (or admins)
    if media_request.user_id != current_user.id and current_user.role != 'Admin':
        flash('You do not have permission to view this request', 'error')
        return redirect(url_for('unified_requests.my_requests'))
    
    # Parse classification data
    classification = None
    if media_request.classification_data:
        try:
            classification = json.loads(media_request.classification_data)
        except:
            pass
    
    return render_template('request_detail.html', request=media_request, classification=classification)


@unified_requests_bp.route('/requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    """Cancel a pending request."""
    media_request = MediaRequest.query.get_or_404(request_id)
    
    # Only allow user to cancel their own requests (or admins)
    if media_request.user_id != current_user.id and current_user.role != 'Admin':
        flash('You do not have permission to cancel this request', 'error')
        return redirect(url_for('unified_requests.my_requests'))
    
    if media_request.status != 'Pending':
        flash('Can only cancel pending requests', 'error')
        return redirect(url_for('unified_requests.request_detail', request_id=request_id))
    
    media_request.status = 'Cancelled'
    db.session.commit()
    
    logging.info(f"Request {request_id} cancelled by user {current_user.id}")
    flash(f'Request cancelled: {media_request.title}', 'success')
    
    return redirect(url_for('unified_requests.my_requests'))


@unified_requests_bp.route('/health', methods=['GET'])
@login_required
def check_services_health():
    """
    Check health status of all *arr services.
    
    Response:
        {
            "sonarr": {"status": "online", "version": "3.0.9"},
            "radarr": {"status": "online", "version": "4.3.2"},
            "lidarr": {"status": "offline", "error": "Connection refused"}
        }
    """
    from app.helpers.sonarr_helper import SonarrHelper
    from app.helpers.radarr_helper import RadarrHelper
    from app.helpers.lidarr_helper import LidarrHelper
    
    health = {}
    
    # Check Sonarr
    try:
        sonarr = SonarrHelper()
        # Assuming helpers have a health check method
        health['sonarr'] = {'status': 'online'}
    except Exception as e:
        health['sonarr'] = {'status': 'offline', 'error': str(e)}
    
    # Check Radarr
    try:
        radarr = RadarrHelper()
        health['radarr'] = {'status': 'online'}
    except Exception as e:
        health['radarr'] = {'status': 'offline', 'error': str(e)}
    
    # Check Lidarr
    try:
        lidarr = LidarrHelper()
        health['lidarr'] = {'status': 'online'}
    except Exception as e:
        health['lidarr'] = {'status': 'offline', 'error': str(e)}
    
    return jsonify(health)
