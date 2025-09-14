"""
REST API Routes
RESTful API endpoints including monitoring and health checks
"""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from . import api_bp
from monitoring import health_checker, system_monitor, performance_monitor, metrics_collector, alert_manager
import logging

logger = logging.getLogger(__name__)

# ============================================
# HEALTH CHECK & MONITORING ENDPOINTS
# ============================================

@api_bp.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_status = health_checker.run_all_checks()
        
        # Return appropriate HTTP status code based on health
        status_code = 200
        if health_status['overall_status'] == 'degraded':
            status_code = 503  # Service Unavailable
        elif health_status['overall_status'] == 'unhealthy':
            status_code = 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'overall_status': 'error',
            'error': str(e),
            'timestamp': health_checker.run_all_checks()['timestamp']
        }), 500

@api_bp.route('/health/quick')
def quick_health():
    """Quick health check for load balancers"""
    try:
        # Simple database connectivity test
        db_healthy = health_checker.check_database()['healthy']
        
        if db_healthy:
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'status': 'error'}), 503
            
    except Exception:
        return jsonify({'status': 'error'}), 503

@api_bp.route('/metrics')
@login_required
def system_metrics():
    """Get current system metrics"""
    try:
        metrics = system_monitor.collect_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Failed to collect metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/metrics/summary')
@login_required  
def metrics_summary():
    """Get metrics summary for specified time period"""
    hours = request.args.get('hours', default=24, type=int)
    hours = min(hours, 168)  # Limit to 1 week
    
    try:
        summary = system_monitor.get_metrics_summary(hours=hours)
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/performance')
@login_required
def performance_stats():
    """Get performance statistics"""
    hours = request.args.get('hours', default=1, type=int)
    hours = min(hours, 24)  # Limit to 24 hours
    
    try:
        performance_data = performance_monitor.get_performance_summary(hours=hours)
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Failed to get performance stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/performance/endpoints')
@login_required
def endpoint_performance():
    """Get detailed endpoint performance statistics"""
    try:
        stats = performance_monitor.get_endpoint_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Failed to get endpoint stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/performance/slow-requests')
@login_required
def slow_requests():
    """Get recent slow requests"""
    limit = request.args.get('limit', default=20, type=int)
    limit = min(limit, 100)  # Maximum 100 entries
    
    try:
        slow_queries = performance_monitor.get_slow_queries(limit=limit)
        return jsonify({'slow_requests': slow_queries})
    except Exception as e:
        logger.error(f"Failed to get slow requests: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api-usage')
@login_required
def api_usage_stats():
    """Get external API usage statistics"""
    try:
        stats = metrics_collector.get_api_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Failed to get API stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/features')
@login_required
def feature_usage_stats():
    """Get feature usage statistics"""
    try:
        stats = metrics_collector.get_feature_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Failed to get feature stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/alerts')
@login_required
def alert_history():
    """Get recent alert history"""
    hours = request.args.get('hours', default=24, type=int)
    hours = min(hours, 168)  # Limit to 1 week
    
    try:
        alerts = alert_manager.get_alert_history(hours=hours)
        return jsonify({'alerts': alerts})
    except Exception as e:
        logger.error(f"Failed to get alert history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/alerts/summary')
@login_required
def alert_summary():
    """Get alert summary"""
    try:
        summary = alert_manager.get_alert_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Failed to get alert summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================
# LEGACY & COMPATIBILITY ENDPOINTS  
# ============================================

@api_bp.route('/status')
def api_status():
    """Basic API status endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0',
        'message': 'Investment Bot API is running'
    })

@api_bp.route('/v1/status')
def api_status_v1():
    """API health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0',
        'message': 'Investment Bot API is running'
    })

# ============================================
# FUTURE API ENDPOINTS (PLACEHOLDERS)
# ============================================

@api_bp.route('/v1/stocks/<symbol>/analysis')
@login_required
def stock_analysis_api(symbol):
    """Future: Get stock analysis via API"""
    return jsonify({
        'message': 'Stock analysis API endpoint',
        'symbol': symbol,
        'status': 'not_implemented'
    }), 501

@api_bp.route('/v1/portfolio')
@login_required
def portfolio_api():
    """Future: Portfolio management API"""
    return jsonify({
        'message': 'Portfolio API endpoint',
        'status': 'not_implemented'
    }), 501

@api_bp.route('/v1/recommendations')
@login_required
def recommendations_api():
    """Future: Stock recommendations API"""
    return jsonify({
        'message': 'Recommendations API endpoint',
        'status': 'not_implemented'
    }), 501

@api_bp.route('/v1/ml/predictions')
@login_required
def ml_predictions_api():
    """Future: ML predictions API"""
    return jsonify({
        'message': 'ML predictions API endpoint', 
        'status': 'not_implemented'
    }), 501

# ============================================
# SAUDI MARKET API ENDPOINTS
# ============================================

@api_bp.route('/saudi/stock/<symbol>')
@login_required
def saudi_stock_data(symbol):
    """Get Saudi stock data via TwelveData API"""
    try:
        from services.api_client import UnifiedAPIClient
        
        # Initialize API client with TwelveData key
        api_key = current_app.config.get('TWELVEDATA_API_KEY')
        client = UnifiedAPIClient(twelvedata_api_key=api_key)
        
        data = client.get_saudi_stock_data(symbol)
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error getting Saudi stock data for {symbol}: {str(e)}")
        return jsonify({'error': str(e), 'symbol': symbol}), 500

@api_bp.route('/saudi/market-summary')
@login_required
def saudi_market_summary():
    """Get Saudi market summary including indices and movers"""
    try:
        from services.api_client import UnifiedAPIClient
        
        api_key = current_app.config.get('TWELVEDATA_API_KEY')
        client = UnifiedAPIClient(twelvedata_api_key=api_key)
        
        summary = client.get_saudi_market_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting Saudi market summary: {str(e)}")
        return jsonify({'error': str(e), 'market': 'Saudi Arabia'}), 500

@api_bp.route('/saudi/search')
@login_required
def saudi_stock_search():
    """Search for Saudi stocks"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        from services.api_client import UnifiedAPIClient
        
        api_key = current_app.config.get('TWELVEDATA_API_KEY')
        client = UnifiedAPIClient(twelvedata_api_key=api_key)
        
        results = client.search_stocks(query, market='saudi')
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error searching Saudi stocks for '{query}': {str(e)}")
        return jsonify({'error': str(e), 'query': query}), 500

@api_bp.route('/saudi/currency/convert')
@login_required
def saudi_currency_convert():
    """Convert SAR to USD"""
    sar_amount = request.args.get('amount', type=float)
    
    if sar_amount is None:
        return jsonify({'error': 'Amount parameter is required'}), 400
    
    try:
        from services.saudi_market_service import SaudiMarketService
        
        service = SaudiMarketService()
        conversion = service.convert_sar_to_usd(sar_amount)
        return jsonify(conversion)
        
    except Exception as e:
        logger.error(f"Error converting SAR to USD: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Test endpoint
@api_bp.route('/test')
def test():
    """Test endpoint to verify API blueprint is working"""
    return jsonify({
        'message': '✅ API blueprint is working perfectly!',
        'monitoring_endpoints': [
            '/api/health - Comprehensive health check',
            '/api/health/quick - Quick health check for load balancers',
            '/api/metrics - Current system metrics',
            '/api/metrics/summary - Metrics summary over time',
            '/api/performance - Performance statistics',
            '/api/performance/endpoints - Endpoint-specific performance',
            '/api/performance/slow-requests - Recent slow requests',
            '/api/api-usage - External API usage stats',
            '/api/features - Feature usage statistics',
            '/api/alerts - Recent alert history',
            '/api/alerts/summary - Alert summary'
        ],
        'saudi_market_endpoints': [
            '/api/saudi/stock/<symbol> - Get Saudi stock data',
            '/api/saudi/market-summary - Saudi market overview',
            '/api/saudi/search?q=<query> - Search Saudi stocks',
            '/api/saudi/currency/convert?amount=<sar> - Convert SAR to USD'
        ],
        'features': [
            'Comprehensive health monitoring',
            'Performance tracking',
            'Alert management',
            'API usage analytics',
            'Feature usage tracking',
            'Real-time metrics collection',
            'Saudi market integration (TwelveData)',
            'Production-ready endpoints'
        ]
    })