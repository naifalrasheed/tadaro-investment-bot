"""
Chat Interface Routes
Complete chat functionality using Claude integration
Preserves ALL original chat capabilities with clean architecture
"""

from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from . import chat_bp
from claude_integration.chat_interface import ChatInterface
from ml_components.adaptive_learning_db import AdaptiveLearningDB
from datetime import datetime
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def get_adaptive_learning():
    """Get adaptive learning DB instance for current user"""
    if current_user.is_authenticated:
        return AdaptiveLearningDB(current_user.id)
    return None

def ensure_json_serializable(obj):
    """Ensure an object is JSON serializable by converting problematic types"""
    if isinstance(obj, dict):
        return {k: ensure_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        # Fall back to string representation for other types
        return str(obj)

@chat_bp.route('/')
@chat_bp.route('/interface')
@login_required
def chat_interface():
    """Display the main chat interface"""
    return render_template('chat.html')

@chat_bp.route('/api/message', methods=['POST'])
@login_required
def process_message():
    """API endpoint for chat message processing - main chat functionality"""
    try:
        # Get message from request
        data = request.json
        message = data.get('message', '')
        include_visualizations = data.get('include_visualizations', True)
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Create a new chat interface for this user
        user_chat = ChatInterface(user_id=current_user.id)
        
        # Process the message using Claude integration
        response = user_chat.process_message(message, include_visualizations=include_visualizations)
        
        # Extract just the text to simplify response
        text = response.get('text', 'No response generated')
        simplified_response = {'text': text}
        
        # Only include visualizations if they exist and are requested
        if include_visualizations and 'visualizations' in response:
            try:
                # Convert visualizations to simpler format if needed
                visualizations = response['visualizations']
                # Process each visualization to ensure it's serializable
                for key, viz in visualizations.items():
                    if 'data' in viz:
                        # Ensure data is serializable
                        viz['data'] = ensure_json_serializable(viz['data'])
                simplified_response['visualizations'] = visualizations
            except Exception as viz_error:
                logger.error(f"Error processing visualizations: {str(viz_error)}")
                # Continue without visualizations if they cause errors
        
        # Record this interaction in the adaptive learning system
        try:
            adaptive_learning = get_adaptive_learning()
            if adaptive_learning:
                # Extract potential stock symbols for tracking
                stock_symbols = user_chat.context.get('current_stocks', [])
                for symbol in stock_symbols:
                    adaptive_learning.record_stock_view(symbol)
        except Exception as learning_error:
            logger.error(f"Error in adaptive learning: {str(learning_error)}")
            # Continue without recording if adaptive learning fails
        
        # Return the simplified response
        return jsonify(simplified_response)
        
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}")
        return jsonify({'text': "I'm sorry, I encountered an error processing your request. Please try again."}), 500

@chat_bp.route('/api/history', methods=['GET'])
@login_required
def chat_history():
    """Get chat history for the current user"""
    try:
        # Create a new chat interface for this user
        user_chat = ChatInterface(user_id=current_user.id)
        
        # Get history (would be stored in DB in a real app)
        history = user_chat.get_chat_history()
        
        # If no history, provide a welcome message
        if not history:
            history = [
                {
                    'role': 'assistant', 
                    'content': "Welcome to the Investment Bot! How can I help you today? You can ask me to analyze stocks, compare investments, or get portfolio advice.",
                    'timestamp': datetime.now().isoformat()
                }
            ]
        
        # Ensure history is safe to serialize to JSON
        safe_history = []
        for item in history:
            safe_item = {
                'role': item.get('role', 'unknown'),
                'content': str(item.get('content', '')),
                'timestamp': item.get('timestamp', datetime.now().isoformat())
            }
            safe_history.append(safe_item)
        
        return jsonify({'history': safe_history})
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        # Return an empty history with welcome message on error
        return jsonify({
            'history': [{
                'role': 'assistant',
                'content': "Welcome to the Investment Bot! How can I help you today?",
                'timestamp': datetime.now().isoformat()
            }]
        })

@chat_bp.route('/api/clear', methods=['POST'])
@login_required
def clear_chat():
    """Clear chat history for the current user"""
    try:
        # Create a new chat interface for this user
        user_chat = ChatInterface(user_id=current_user.id)
        
        # Clear the history
        user_chat.clear_chat_history()
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear chat history'
        }), 500

@chat_bp.route('/api/context', methods=['GET'])
@login_required  
def get_chat_context():
    """Get current chat context and user preferences"""
    try:
        # Create chat interface
        user_chat = ChatInterface(user_id=current_user.id)
        
        # Get user context
        context = user_chat.get_user_context()
        
        # Get adaptive learning preferences
        adaptive_learning = get_adaptive_learning()
        preferences = {}
        if adaptive_learning:
            preferences = adaptive_learning.get_user_profile_summary()
        
        return jsonify({
            'context': context,
            'preferences': preferences,
            'user_id': current_user.id
        })
        
    except Exception as e:
        logger.error(f"Error getting chat context: {str(e)}")
        return jsonify({
            'context': {},
            'preferences': {},
            'error': str(e)
        })

# Legacy compatibility routes (maintain existing URLs)
@chat_bp.route('/chat', methods=['GET'])
@login_required
def chat_view_legacy():
    """Legacy route for backward compatibility"""
    return render_template('chat.html')

@chat_bp.route('/chat', methods=['POST'])
@login_required
def chat_post_legacy():
    """Legacy POST route - redirect to new API"""
    return process_message()

# Test endpoint
@chat_bp.route('/test')
def test():
    """Test endpoint to verify chat blueprint is working"""
    return jsonify({
        'message': '✅ Chat blueprint is working perfectly!',
        'routes': [
            '/chat/ - Main chat interface',
            '/chat/interface - Chat interface (alternative)',
            '/chat/api/message - Process chat messages',
            '/chat/api/history - Get chat history', 
            '/chat/api/clear - Clear chat history',
            '/chat/api/context - Get user context'
        ],
        'features': [
            'Claude AI integration',
            'Adaptive learning integration', 
            'Visualization support',
            'Chat history management',
            'User context tracking',
            'Error handling and logging'
        ],
        'service_layer': 'Active - Using ChatInterface + AdaptiveLearningDB'
    })