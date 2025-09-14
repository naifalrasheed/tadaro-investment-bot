from flask import Flask, request, jsonify
from ml_components.improved_ml_engine import ImprovedMLEngine
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ML engine once at startup
ml_engine = ImprovedMLEngine()

@app.route('/analyze', methods=['POST'])
def analyze_stock():
    """API endpoint for stock analysis"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate input data
        if not all(key in data for key in ['stock_data', 'symbol']):
            return jsonify({"error": "Missing required fields: stock_data and symbol"}), 400
            
        stock_data = data.get('stock_data')
        symbol = data.get('symbol')
        
        # Process the data
        features, targets = ml_engine.prepare_features(stock_data, symbol)
        
        # Use existing trained model rather than training on each request
        prediction, confidence = ml_engine.predict(features.iloc[-1:])
        
        return jsonify({
            "prediction": float(prediction),
            "confidence": float(confidence),
            "symbol": symbol,
            "timestamp": request.json.get('timestamp', '')
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == "__main__":
    # In production, use a proper WSGI server and set debug=False
    app.run(host='0.0.0.0', port=5000, debug=False)