"""
ML & Adaptive Learning Routes
Machine learning and adaptive learning functionality for personalized recommendations
"""

from flask import render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required, current_user
from . import ml_bp
from ml_components.adaptive_learning_db import AdaptiveLearningDB
from models import db, StockAnalysis, PredictionRecord
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger(__name__)

def get_adaptive_learning():
    """Get adaptive learning DB instance for current user"""
    if current_user.is_authenticated:
        return AdaptiveLearningDB(current_user.id)
    return None

@ml_bp.route('/preferences')
@login_required
def user_preferences():
    """View a summary of the user's preferences and learning profile"""
    try:
        adaptive_learning = get_adaptive_learning()
        if not adaptive_learning:
            flash('Please log in to view your preferences')
            return redirect(url_for('auth.login'))
        
        profile = adaptive_learning.get_user_profile_summary()
        
        # Get recent predictions for tracking
        predictions = PredictionRecord.query.filter_by(
            user_id=current_user.id
        ).order_by(PredictionRecord.prediction_date.desc()).limit(10).all()
        
        return render_template(
            'preferences.html', 
            profile=profile, 
            predictions=predictions
        )
        
    except Exception as e:
        logger.error(f"Error in user_preferences: {str(e)}")
        flash('Error loading preferences', 'error')
        return redirect(url_for('main.index'))

@ml_bp.route('/api/feedback', methods=['POST'])
@login_required
def stock_feedback():
    """Handle feedback on stock analysis (like, dislike, purchase)"""
    try:
        symbol = request.form.get('symbol') or request.json.get('symbol') if request.is_json else None
        reaction = request.form.get('reaction') or request.json.get('reaction') if request.is_json else None
        
        if not symbol or not reaction:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
        # Get the most recent analysis data for this stock
        analysis = StockAnalysis.query.filter_by(
            user_id=current_user.id,
            symbol=symbol
        ).order_by(StockAnalysis.date.desc()).first()
        
        # Record user feedback
        adaptive_learning = get_adaptive_learning()
        if adaptive_learning:
            # Get the stock data from analysis if available
            stock_data = analysis.analysis_data if analysis else None
            adaptive_learning.record_stock_feedback(symbol, reaction, stock_data)
        
        # Record view time
        view_duration = None
        if request.form.get('view_start_time'):
            view_duration = time.time() - float(request.form.get('view_start_time'))
        elif request.is_json and request.json.get('view_start_time'):
            view_duration = time.time() - float(request.json.get('view_start_time'))
            
        if adaptive_learning and view_duration and view_duration > 0:
            adaptive_learning.record_stock_view(
                symbol, 
                sector=stock_data.get('sector') if stock_data else None, 
                view_duration=view_duration
            )
        
        return jsonify({
            'success': True, 
            'message': f'Recorded {reaction} feedback for {symbol}'
        })
        
    except Exception as e:
        logger.error(f"Error in stock_feedback: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_bp.route('/api/prediction/<int:prediction_id>', methods=['POST'])
@login_required
def update_prediction(prediction_id):
    """Update a prediction with actual results"""
    try:
        actual_value = request.form.get('actual_value') or request.json.get('actual_value') if request.is_json else None
        
        if not actual_value:
            return jsonify({'success': False, 'error': 'Missing actual value'}), 400
        
        actual_value = float(actual_value)
        adaptive_learning = get_adaptive_learning()
        if adaptive_learning:
            adaptive_learning.update_prediction_outcome(prediction_id, actual_value)
        
        return jsonify({'success': True, 'message': f'Updated prediction {prediction_id}'})
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid actual value - must be numeric'}), 400
    except Exception as e:
        logger.error(f"Error in update_prediction: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_bp.route('/api/predictions/batch-update', methods=['POST'])
@login_required
def update_all_predictions():
    """Update all predictions with actual outcomes (for admin use)"""
    try:
        from services.stock_service import StockService
        from services.api_client import UnifiedAPIClient
        
        # Initialize services
        api_client = UnifiedAPIClient()
        stock_service = StockService(api_client)
        
        # Get predictions that are at least 7 days old and have no actual value
        week_ago = datetime.utcnow() - timedelta(days=7)
        predictions = PredictionRecord.query.filter(
            PredictionRecord.prediction_date < week_ago,
            PredictionRecord.actual_value.is_(None),
            PredictionRecord.user_id == current_user.id  # Only user's own predictions
        ).all()
        
        updated_count = 0
        errors = []
        
        for prediction in predictions:
            try:
                # Get current data for the stock using service layer
                data = stock_service.analyze_stock(prediction.symbol, current_user.id)
                if data and 'current_price' in data:
                    # Update the prediction with actual price
                    prediction.actual_value = data['current_price']
                    prediction.error = abs(prediction.predicted_value - data['current_price'])
                    db.session.add(prediction)
                    updated_count += 1
            except Exception as e:
                error_msg = f"Error updating prediction for {prediction.symbol}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if updated_count > 0:
            db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'total_predictions': len(predictions),
            'errors': errors[:5]  # Return first 5 errors only
        })
        
    except Exception as e:
        logger.error(f"Error in update_all_predictions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_bp.route('/profile-summary')
@login_required
def profile_summary():
    """Get user's ML profile summary as JSON"""
    try:
        adaptive_learning = get_adaptive_learning()
        if not adaptive_learning:
            return jsonify({'error': 'Adaptive learning not available'}), 400
        
        profile = adaptive_learning.get_user_profile_summary()
        return jsonify({
            'success': True,
            'profile': profile,
            'user_id': current_user.id
        })
        
    except Exception as e:
        logger.error(f"Error in profile_summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_bp.route('/recommendations')
@login_required  
def get_recommendations():
    """Get personalized stock recommendations"""
    try:
        adaptive_learning = get_adaptive_learning()
        if not adaptive_learning:
            return jsonify({'error': 'Adaptive learning not available'}), 400
        
        # Get recommended stocks (this would typically be from the recommendations route)
        recommendations = adaptive_learning.get_user_profile_summary()
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'user_id': current_user.id
        })
        
    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ml_bp.route('/api/record-view', methods=['POST'])
@login_required
def record_stock_view():
    """Record that a user viewed a specific stock"""
    try:
        symbol = request.form.get('symbol') or request.json.get('symbol') if request.is_json else None
        sector = request.form.get('sector') or request.json.get('sector') if request.is_json else None
        view_duration = request.form.get('view_duration') or request.json.get('view_duration') if request.is_json else None
        
        if not symbol:
            return jsonify({'success': False, 'error': 'Missing symbol parameter'}), 400
        
        adaptive_learning = get_adaptive_learning()
        if adaptive_learning:
            duration = float(view_duration) if view_duration else None
            adaptive_learning.record_stock_view(symbol, sector=sector, view_duration=duration)
        
        return jsonify({
            'success': True,
            'message': f'Recorded view for {symbol}'
        })
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid view duration'}), 400
    except Exception as e:
        logger.error(f"Error in record_stock_view: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Legacy compatibility route for stock-feedback
@ml_bp.route('/stock-feedback', methods=['POST'])
@login_required
def stock_feedback_legacy():
    """Legacy route for backward compatibility"""
    return stock_feedback()

# Test endpoint
@ml_bp.route('/test')
def test():
    """Test endpoint to verify ML blueprint is working"""
    return jsonify({
        'message': '✅ ML blueprint is working perfectly!',
        'routes': [
            '/ml/preferences - User preferences and learning profile',
            '/ml/api/feedback - Record stock feedback (like/dislike/purchase)', 
            '/ml/api/prediction/<id> - Update prediction with actual results',
            '/ml/api/predictions/batch-update - Batch update all predictions',
            '/ml/profile-summary - Get ML profile as JSON',
            '/ml/recommendations - Get personalized recommendations',
            '/ml/api/record-view - Record stock view for learning',
            '/ml/stock-feedback - Legacy feedback route'
        ],
        'features': [
            'Adaptive learning integration',
            'Stock feedback recording', 
            'Prediction tracking and updates',
            'User preference learning',
            'Personalized recommendations',
            'Stock view analytics',
            'Batch prediction updates',
            'Error handling and logging'
        ],
        'service_integration': 'Uses AdaptiveLearningDB and service layer'
    })