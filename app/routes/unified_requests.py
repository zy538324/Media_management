from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Request as MediaRequest, db
from app.helpers.media_classifier import MediaClassifier, MediaService, MediaType
from app.helpers.request_processor import RequestProcessor
import logging
import json

logging.basicConfig(level=logging.INFO)

unified_requests_bp = Blueprint('unified_requests', __name__)


@unified_requests_bp.route('/request/unified', methods=['GET'])
@login_required
def unified_request_page():
    """Unified request page where users can search and request any media type."""
    return render_template('unified_request.html')


@unified_requests_bp.route('/api/classify', methods=['POST'])
@login_required
def classify_media():
    """
    API endpoint to classify media and return potential matches.
    Used for real-time search suggestions.
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Query must be at least 2 characters'
            }), 400
        
        classifier = MediaClassifier()
        matches = classifier.classify(query, limit=10)
        
        # Convert matches to JSON-serializable format
        results = []
        for match in matches:
            results.append({
                'title': match.title,
                'media_type': match.media_type.value,
                'service': match.service.value,
                'service_display': _get_service_display_name(match.service.value),
                'confidence': round(match.confidence, 2),
                'year': match.year,
                'description': match.description,
                'poster_url': match.poster_url,
                'external_id': match.external_id,
                'additional_data': match.additional_data
            })
        
        # Check if disambiguation is needed
        has_ambiguity = classifier.has_ambiguity(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'has_ambiguity': has_ambiguity,
            'result_count': len(results)
        })
        
    except Exception as e:
        logging.error(f"Classification API error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Classification failed. Please try again.'
        }), 500


@unified_requests_bp.route('/api/request/create', methods=['POST'])
@login_required
def create_unified_request():
    """
    Create a new media request with intelligent classification.
    Handles both auto-classified and manually selected requests.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        title = data.get('title', '').strip()
        if not title:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        # Check for manual selection (from disambiguation)
        selected_match = data.get('selected_match')
        
        if selected_match:
            # User manually selected from disambiguation options
            media_type = selected_match.get('media_type')
            arr_service = selected_match.get('service')
            external_id = selected_match.get('external_id')
            confidence = selected_match.get('confidence', 1.0)
            classification_data = json.dumps(selected_match)
        else:
            # Auto-classify
            classifier = MediaClassifier()
            best_match = classifier.get_best_match(title)
            
            if not best_match:
                return jsonify({
                    'success': False,
                    'error': 'Could not classify media. Please try a more specific title.',
                    'requires_disambiguation': True
                }), 400
            
            # Check if disambiguation is needed
            if classifier.has_ambiguity(title) and not data.get('skip_disambiguation'):
                return jsonify({
                    'success': False,
                    'requires_disambiguation': True,
                    'message': 'Multiple matches found. Please select the correct one.'
                }), 200
            
            media_type = best_match.media_type.value
            arr_service = best_match.service.value
            external_id = best_match.external_id
            confidence = best_match.confidence
            classification_data = json.dumps({
                'title': best_match.title,
                'year': best_match.year,
                'description': best_match.description,
                'poster_url': best_match.poster_url,
                'additional_data': best_match.additional_data
            })
        
        # Create the request
        new_request = MediaRequest(
            user_id=current_user.id,
            title=title,
            media_type=media_type,
            status='Pending',
            priority=data.get('priority', 'Medium'),
            arr_service=arr_service,
            external_id=external_id,
            confidence_score=confidence,
            classification_data=classification_data
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        logging.info(f"User {current_user.username} created request: {title} → {arr_service} (confidence: {confidence:.2f})")
        
        return jsonify({
            'success': True,
            'message': f'Request created successfully! {title} will be added to {_get_service_display_name(arr_service)}.',
            'request_id': new_request.id,
            'service': arr_service,
            'confidence': round(confidence, 2)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Request creation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to create request. Please try again.'
        }), 500


@unified_requests_bp.route('/api/request/<int:request_id>/reclassify', methods=['POST'])
@login_required
def reclassify_request(request_id):
    """
    Reclassify an existing request.
    Useful if classification was incorrect.
    """
    try:
        media_request = MediaRequest.query.get_or_404(request_id)
        
        # Check ownership (admins can reclassify anyone's requests)
        if media_request.user_id != current_user.id and current_user.role != 'Admin':
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        force_service = data.get('force_service')  # 'sonarr', 'radarr', or 'lidarr'
        
        if force_service:
            # Manual override
            media_request.arr_service = force_service
            media_request.confidence_score = 1.0  # Manual selection = 100% confidence
            media_request.status = 'Pending'  # Reset to pending for reprocessing
            
            service_to_type = {
                'sonarr': 'tv',
                'radarr': 'movie',
                'lidarr': 'music'
            }
            media_request.media_type = service_to_type.get(force_service, media_request.media_type)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Request reclassified to {_get_service_display_name(force_service)}',
                'service': force_service
            })
        else:
            # Auto-reclassify
            classifier = MediaClassifier()
            best_match = classifier.get_best_match(media_request.title)
            
            if not best_match:
                return jsonify({
                    'success': False,
                    'error': 'Reclassification failed'
                }), 400
            
            media_request.arr_service = best_match.service.value
            media_request.external_id = best_match.external_id
            media_request.confidence_score = best_match.confidence
            media_request.media_type = best_match.media_type.value
            media_request.status = 'Pending'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Request reclassified successfully',
                'service': best_match.service.value,
                'confidence': round(best_match.confidence, 2)
            })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Reclassification error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Reclassification failed'
        }), 500


@unified_requests_bp.route('/requests/my', methods=['GET'])
@login_required
def my_requests():
    """View current user's requests with classification details."""
    requests = MediaRequest.query.filter_by(user_id=current_user.id).order_by(MediaRequest.requested_at.desc()).all()
    return render_template('my_requests.html', requests=requests)


@unified_requests_bp.route('/requests/all', methods=['GET'])
@login_required
def all_requests():
    """View all requests (admin only)."""
    if current_user.role != 'Admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('unified_requests.my_requests'))
    
    requests = MediaRequest.query.order_by(MediaRequest.requested_at.desc()).all()
    return render_template('all_requests.html', requests=requests)


def _get_service_display_name(service):
    """Get user-friendly service name."""
    service_names = {
        'sonarr': 'Sonarr (TV Shows)',
        'radarr': 'Radarr (Movies)',
        'lidarr': 'Lidarr (Music)'
    }
    return service_names.get(service, 'Unknown')
