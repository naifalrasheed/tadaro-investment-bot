"""
Stock Analysis Routes
Clean, modern routes using the service layer architecture
Replaces the 603-line monolithic analyze function with clean handlers
"""

from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import analysis_bp
from services.stock_service import StockService
from services.api_client import UnifiedAPIClient
from models import db
import time
import logging

# Initialize services
logger = logging.getLogger(__name__)

def get_stock_service():
    """Get StockService instance with proper API client"""
    api_client = UnifiedAPIClient(
        alpha_vantage_key=current_app.config.get('ALPHA_VANTAGE_API_KEY'),
        news_api_key=current_app.config.get('NEWS_API_KEY')
    )
    return StockService(api_client)


@analysis_bp.route('/', methods=['GET', 'POST'])
@analysis_bp.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze():
    """
    Main stock analysis route - CLEAN VERSION
    Replaces the 603-line monolithic function with service layer
    """
    start_time = time.time()
    
    if request.method == 'POST':
        try:
            symbol = request.form.get('symbol', '').upper().strip()
            if not symbol:
                flash('Please enter a stock symbol', 'warning')
                return redirect(url_for('analysis.analyze'))
            
            # Use the service layer for clean business logic
            stock_service = get_stock_service()
            
            # Perform comprehensive analysis using service layer
            analysis_result = stock_service.analyze_stock(
                symbol=symbol,
                user_id=current_user.id,
                market='US'  # Default to US market
            )
            
            # Record user interaction for adaptive learning
            view_time = time.time() - start_time
            stock_service.record_user_interaction(
                user_id=current_user.id,
                symbol=symbol,
                interaction_type='view',
                view_time=view_time
            )
            
            logger.info(f"Analysis completed for {symbol} in {view_time:.2f}s")
            
            # Render the analysis results
            return render_template(
                'analysis.html',
                results=analysis_result,
                symbol=symbol,
                analysis_time=f"{view_time:.2f}",
                user_id=current_user.id
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            flash(f'Error analyzing {symbol}: {str(e)}', 'danger')
            return redirect(url_for('analysis.analyze'))
    
    # GET request - show analysis form
    return render_template('analyze_form.html')


@analysis_bp.route('/reanalyze/<symbol>')
@login_required
def reanalyze(symbol):
    """Reanalyze a stock with fresh data"""
    try:
        symbol = symbol.upper().strip()
        stock_service = get_stock_service()
        
        # Force fresh analysis by clearing cache (if implemented)
        analysis_result = stock_service.analyze_stock(
            symbol=symbol,
            user_id=current_user.id,
            market='US'
        )
        
        # Record interaction
        stock_service.record_user_interaction(
            user_id=current_user.id,
            symbol=symbol,
            interaction_type='reanalyze'
        )
        
        return render_template(
            'analysis.html',
            results=analysis_result,
            symbol=symbol,
            is_reanalysis=True
        )
        
    except Exception as e:
        logger.error(f"Error reanalyzing {symbol}: {e}")
        flash(f'Error reanalyzing {symbol}: {str(e)}', 'danger')
        return redirect(url_for('analysis.analyze'))


@analysis_bp.route('/technical/<symbol>')
@login_required
def technical_analysis(symbol):
    """Technical analysis view for a specific stock"""
    try:
        symbol = symbol.upper().strip()
        stock_service = get_stock_service()
        
        # Get comprehensive analysis
        analysis_result = stock_service.analyze_stock(
            symbol=symbol,
            user_id=current_user.id,
            market='US'
        )
        
        # Extract technical analysis data
        technical_data = analysis_result.get('technical_analysis', {})
        
        return render_template(
            'technical_analysis.html',
            symbol=symbol,
            technical_data=technical_data,
            stock_data=analysis_result.get('stock_data', {}),
            recommendation=analysis_result.get('recommendation', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting technical analysis for {symbol}: {e}")
        flash(f'Error getting technical analysis for {symbol}: {str(e)}', 'danger')
        return redirect(url_for('analysis.analyze'))


@analysis_bp.route('/fundamental/<symbol>')
@login_required
def fundamental_analysis(symbol):
    """Fundamental analysis view for a specific stock"""
    try:
        symbol = symbol.upper().strip()
        stock_service = get_stock_service()
        
        analysis_result = stock_service.analyze_stock(
            symbol=symbol,
            user_id=current_user.id,
            market='US'
        )
        
        # Extract fundamental analysis data
        fundamental_data = analysis_result.get('fundamental_analysis', {})
        
        return render_template(
            'fundamental_analysis.html',
            symbol=symbol,
            fundamental_data=fundamental_data,
            stock_data=analysis_result.get('stock_data', {}),
            recommendation=analysis_result.get('recommendation', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting fundamental analysis for {symbol}: {e}")
        flash(f'Error getting fundamental analysis for {symbol}: {str(e)}', 'danger')
        return redirect(url_for('analysis.analyze'))


@analysis_bp.route('/sentiment/<symbol>')
@login_required
def sentiment_analysis(symbol):
    """Sentiment analysis view for a specific stock"""
    try:
        symbol = symbol.upper().strip()
        stock_service = get_stock_service()
        
        analysis_result = stock_service.analyze_stock(
            symbol=symbol,
            user_id=current_user.id,
            market='US'
        )
        
        # Extract sentiment analysis data
        sentiment_data = analysis_result.get('sentiment_analysis', {})
        
        return render_template(
            'sentiment_analysis.html',
            symbol=symbol,
            sentiment_data=sentiment_data,
            stock_data=analysis_result.get('stock_data', {}),
            recommendation=analysis_result.get('recommendation', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting sentiment analysis for {symbol}: {e}")
        flash(f'Error getting sentiment analysis for {symbol}: {str(e)}', 'danger')
        return redirect(url_for('analysis.analyze'))


@analysis_bp.route('/compare', methods=['GET', 'POST'])
@login_required
def compare_stocks():
    """Compare multiple stocks side by side"""
    if request.method == 'POST':
        try:
            symbols = []
            for i in range(1, 5):  # Support up to 4 stocks
                symbol = request.form.get(f'symbol{i}', '').upper().strip()
                if symbol:
                    symbols.append(symbol)
            
            if len(symbols) < 2:
                flash('Please enter at least 2 stock symbols to compare', 'warning')
                return redirect(url_for('analysis.compare_stocks'))
            
            stock_service = get_stock_service()
            comparisons = []
            
            for symbol in symbols:
                try:
                    analysis = stock_service.analyze_stock(
                        symbol=symbol,
                        user_id=current_user.id,
                        market='US'
                    )
                    comparisons.append(analysis)
                except Exception as e:
                    logger.warning(f"Could not analyze {symbol}: {e}")
                    continue
            
            if not comparisons:
                flash('Could not analyze any of the provided symbols', 'danger')
                return redirect(url_for('analysis.compare_stocks'))
            
            return render_template(
                'stock_comparison.html',
                comparisons=comparisons,
                symbols=symbols
            )
            
        except Exception as e:
            logger.error(f"Error comparing stocks: {e}")
            flash(f'Error comparing stocks: {str(e)}', 'danger')
            return redirect(url_for('analysis.compare_stocks'))
    
    # GET request - show comparison form
    return render_template('compare_form.html')


@analysis_bp.route('/naif/<symbol>/<market>')
@login_required
def naif_analysis(symbol, market):
    """Naif Al-Rasheed model analysis for specific market"""
    try:
        symbol = symbol.upper().strip()
        market = market.upper()
        
        if market not in ['US', 'SAUDI']:
            flash('Market must be US or SAUDI', 'warning')
            return redirect(url_for('analysis.analyze'))
        
        stock_service = get_stock_service()
        analysis_result = stock_service.analyze_stock(
            symbol=symbol,
            user_id=current_user.id,
            market=market
        )
        
        return render_template(
            'naif_analysis.html',
            symbol=symbol,
            market=market,
            analysis=analysis_result,
            recommendation=analysis_result.get('recommendation', {}),
            naif_criteria=analysis_result.get('fundamental_analysis', {}).get('thresholds', {})
        )
        
    except Exception as e:
        logger.error(f"Error in Naif analysis for {symbol} ({market}): {e}")
        flash(f'Error in Naif analysis: {str(e)}', 'danger')
        return redirect(url_for('analysis.analyze'))


# API endpoints for AJAX calls
@analysis_bp.route('/api/quick-analysis/<symbol>')
@login_required
def quick_analysis_api(symbol):
    """Quick analysis API endpoint for AJAX calls"""
    try:
        symbol = symbol.upper().strip()
        stock_service = get_stock_service()
        
        analysis_result = stock_service.analyze_stock(
            symbol=symbol,
            user_id=current_user.id,
            market='US'
        )
        
        # Return simplified data for API
        return jsonify({
            'success': True,
            'symbol': symbol,
            'price': analysis_result.get('stock_data', {}).get('price'),
            'recommendation': analysis_result.get('recommendation', {}),
            'sentiment_score': analysis_result.get('sentiment_analysis', {}).get('overall_sentiment', {}).get('score'),
            'technical_score': analysis_result.get('technical_analysis', {}).get('score'),
            'fundamental_score': analysis_result.get('fundamental_analysis', {}).get('score')
        })
        
    except Exception as e:
        logger.error(f"Error in quick analysis API for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/test')
def test():
    """Test endpoint to verify blueprint is working"""
    return jsonify({
        'message': '✅ Analysis blueprint is working perfectly!',
        'routes': [
            '/analysis/analyze - Main analysis route',
            '/analysis/reanalyze/<symbol> - Fresh analysis',
            '/analysis/technical/<symbol> - Technical analysis',
            '/analysis/fundamental/<symbol> - Fundamental analysis',
            '/analysis/sentiment/<symbol> - Sentiment analysis',
            '/analysis/compare - Compare stocks',
            '/analysis/naif/<symbol>/<market> - Naif model analysis'
        ],
        'service_layer': 'Active - Using StockService and UnifiedAPIClient'
    })