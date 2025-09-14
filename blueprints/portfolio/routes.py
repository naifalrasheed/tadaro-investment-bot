"""
Portfolio Management Routes
Clean portfolio routes using service layer architecture
Preserves ALL original functionality with better organization
"""

from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import portfolio_bp
from services.portfolio_service import PortfolioService
from services.stock_service import StockService
from services.api_client import UnifiedAPIClient
from ml_components.naif_alrasheed_model import NaifAlRasheedModel
from models import db, Portfolio
import logging
import json

logger = logging.getLogger(__name__)

def get_services():
    """Get service instances with proper configuration"""
    api_client = UnifiedAPIClient(
        alpha_vantage_key=current_app.config.get('ALPHA_VANTAGE_API_KEY'),
        news_api_key=current_app.config.get('NEWS_API_KEY')
    )
    stock_service = StockService(api_client)
    portfolio_service = PortfolioService(stock_service)
    return portfolio_service, stock_service


@portfolio_bp.route('/')
@portfolio_bp.route('/dashboard')
@login_required
def portfolio_dashboard():
    """Main portfolio dashboard - shows all user portfolios"""
    try:
        portfolio_service, stock_service = get_services()
        
        # Get user's portfolios
        portfolios = portfolio_service.get_user_portfolios(current_user.id)
        
        # Enhanced portfolio data with current values
        enhanced_portfolios = []
        for portfolio in portfolios:
            try:
                # Add current portfolio value and performance
                current_value = portfolio_service.calculate_portfolio_value(portfolio['id'])
                performance = portfolio_service.calculate_performance_metrics(portfolio['id'])
                
                enhanced_portfolios.append({
                    **portfolio,
                    'current_value': current_value,
                    'performance': performance
                })
            except Exception as e:
                logger.warning(f"Error enhancing portfolio {portfolio['id']}: {e}")
                enhanced_portfolios.append(portfolio)
        
        return render_template(
            'portfolio_dashboard.html',
            portfolios=enhanced_portfolios,
            total_portfolios=len(portfolios)
        )
        
    except Exception as e:
        logger.error(f"Error loading portfolio dashboard: {e}")
        flash('Error loading portfolios', 'danger')
        return render_template('portfolio_dashboard.html', portfolios=[], total_portfolios=0)


@portfolio_bp.route('/create', methods=['GET', 'POST'])
@portfolio_bp.route('/import', methods=['GET', 'POST'])
@login_required
def create_or_import():
    """Create new portfolio or import existing one"""
    if request.method == 'POST':
        try:
            portfolio_service, _ = get_services()
            
            # Check if this is an import or create
            is_import = 'import_file' in request.files
            
            if is_import:
                # Handle file import
                file = request.files['import_file']
                if not file or not file.filename:
                    flash('Please select a file to import', 'warning')
                    return redirect(url_for('portfolio.create_or_import'))
                
                portfolio_data = portfolio_service.import_from_file(file, current_user.id)
                flash(f'Successfully imported portfolio: {portfolio_data["name"]}', 'success')
                
            else:
                # Handle manual creation
                name = request.form.get('name', '').strip()
                if not name:
                    flash('Please enter a portfolio name', 'warning')
                    return redirect(url_for('portfolio.create_or_import'))
                
                # Process stock holdings
                stocks = []
                for i in range(1, 21):  # Support up to 20 stocks
                    symbol = request.form.get(f'symbol_{i}', '').upper().strip()
                    shares = request.form.get(f'shares_{i}', '').strip()
                    
                    if symbol and shares:
                        try:
                            stocks.append({
                                'symbol': symbol,
                                'shares': float(shares),
                                'purchase_price': float(request.form.get(f'price_{i}', 0) or 0)
                            })
                        except ValueError:
                            flash(f'Invalid data for {symbol}', 'warning')
                            continue
                
                if not stocks:
                    flash('Please add at least one stock to your portfolio', 'warning')
                    return redirect(url_for('portfolio.create_or_import'))
                
                portfolio_data = portfolio_service.create_portfolio(current_user.id, name, stocks)
                flash(f'Successfully created portfolio: {name}', 'success')
            
            return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_data['id']))
            
        except Exception as e:
            logger.error(f"Error creating/importing portfolio: {e}")
            flash(f'Error creating portfolio: {str(e)}', 'danger')
            return redirect(url_for('portfolio.create_or_import'))
    
    # GET request - show create/import form
    return render_template('portfolio_create.html')


@portfolio_bp.route('/<int:portfolio_id>')
@login_required
def view_portfolio(portfolio_id):
    """View detailed portfolio information"""
    try:
        portfolio_service, stock_service = get_services()
        
        # Get portfolio details
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            flash('Portfolio not found', 'danger')
            return redirect(url_for('portfolio.portfolio_dashboard'))
        
        # Get comprehensive portfolio analysis
        analysis = portfolio_service.analyze_portfolio(portfolio_id)
        
        return render_template(
            'portfolio_detail.html',
            portfolio=portfolio,
            analysis=analysis,
            portfolio_id=portfolio_id
        )
        
    except Exception as e:
        logger.error(f"Error viewing portfolio {portfolio_id}: {e}")
        flash('Error loading portfolio', 'danger')
        return redirect(url_for('portfolio.portfolio_dashboard'))


@portfolio_bp.route('/<int:portfolio_id>/analyze')
@login_required
def analyze_portfolio(portfolio_id):
    """Comprehensive portfolio analysis"""
    try:
        portfolio_service, stock_service = get_services()
        
        # Verify ownership
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            flash('Portfolio not found', 'danger')
            return redirect(url_for('portfolio.portfolio_dashboard'))
        
        # Perform comprehensive analysis
        analysis = portfolio_service.comprehensive_analysis(portfolio_id)
        
        return render_template(
            'portfolio_analysis.html',
            portfolio=portfolio,
            analysis=analysis,
            portfolio_id=portfolio_id
        )
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio {portfolio_id}: {e}")
        flash('Error analyzing portfolio', 'danger')
        return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))


@portfolio_bp.route('/<int:portfolio_id>/optimize', methods=['GET', 'POST'])
@login_required
def optimize_portfolio(portfolio_id):
    """Portfolio optimization using modern portfolio theory"""
    try:
        portfolio_service, _ = get_services()
        
        # Verify ownership
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            flash('Portfolio not found', 'danger')
            return redirect(url_for('portfolio.portfolio_dashboard'))
        
        if request.method == 'POST':
            # Get optimization parameters
            risk_tolerance = request.form.get('risk_tolerance', 'moderate')
            optimization_method = request.form.get('method', 'sharpe')
            
            # Perform optimization
            optimization_result = portfolio_service.optimize_portfolio(
                portfolio_id=portfolio_id,
                risk_tolerance=risk_tolerance,
                method=optimization_method
            )
            
            return render_template(
                'portfolio_optimization_results.html',
                portfolio=portfolio,
                optimization=optimization_result,
                portfolio_id=portfolio_id
            )
        
        # GET request - show optimization form
        current_analysis = portfolio_service.analyze_portfolio(portfolio_id)
        
        return render_template(
            'portfolio_optimize.html',
            portfolio=portfolio,
            current_analysis=current_analysis,
            portfolio_id=portfolio_id
        )
        
    except Exception as e:
        logger.error(f"Error optimizing portfolio {portfolio_id}: {e}")
        flash('Error optimizing portfolio', 'danger')
        return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))


@portfolio_bp.route('/delete/<int:portfolio_id>', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    """Delete a portfolio"""
    try:
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            flash('Portfolio not found', 'danger')
            return redirect(url_for('portfolio.portfolio_dashboard'))
        
        portfolio_name = portfolio.name
        db.session.delete(portfolio)
        db.session.commit()
        
        flash(f'Successfully deleted portfolio: {portfolio_name}', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting portfolio {portfolio_id}: {e}")
        flash('Error deleting portfolio', 'danger')
    
    return redirect(url_for('portfolio.portfolio_dashboard'))


# NAIF AL-RASHEED MODEL ROUTES
@portfolio_bp.route('/naif-model', methods=['GET', 'POST'])
@login_required
def naif_model():
    """Naif Al-Rasheed investment model interface"""
    try:
        if request.method == 'POST':
            market = request.form.get('market', 'US').upper()
            sector = request.form.get('sector', 'All')
            max_stocks = int(request.form.get('max_stocks', 20))
            
            # Initialize Naif model
            naif_model = NaifAlRasheedModel()
            
            # Run screening based on market
            if market == 'SAUDI':
                results = naif_model.screen_saudi_stocks(sector, max_stocks)
            else:
                results = naif_model.screen_us_stocks(sector, max_stocks)
            
            return render_template(
                'naif_model_results.html',
                results=results,
                market=market,
                sector=sector,
                screening_params={
                    'market': market,
                    'sector': sector,
                    'max_stocks': max_stocks
                }
            )
        
        # GET request - show model interface
        return render_template('naif_model.html')
        
    except Exception as e:
        logger.error(f"Error in Naif model: {e}")
        flash(f'Error running Naif model: {str(e)}', 'danger')
        return render_template('naif_model.html')


@portfolio_bp.route('/naif-model/sector-analysis')
@login_required
def naif_sector_analysis():
    """Sector analysis using Naif Al-Rasheed criteria"""
    try:
        market = request.args.get('market', 'US').upper()
        
        naif_model = NaifAlRasheedModel()
        
        if market == 'SAUDI':
            sector_analysis = naif_model.analyze_saudi_sectors()
        else:
            sector_analysis = naif_model.analyze_us_sectors()
        
        return render_template(
            'naif_sector_analysis.html',
            sector_analysis=sector_analysis,
            market=market
        )
        
    except Exception as e:
        logger.error(f"Error in sector analysis: {e}")
        flash('Error performing sector analysis', 'danger')
        return redirect(url_for('portfolio.naif_model'))


@portfolio_bp.route('/naif-model/technical/<symbol>')
@login_required 
def naif_technical(symbol):
    """Technical analysis within Naif model context"""
    try:
        symbol = symbol.upper().strip()
        market = request.args.get('market', 'US').upper()
        
        _, stock_service = get_services()
        
        # Get comprehensive analysis with Naif criteria
        analysis = stock_service.analyze_stock(
            symbol=symbol,
            user_id=current_user.id,
            market=market
        )
        
        # Apply Naif model scoring
        naif_model = NaifAlRasheedModel()
        naif_score = naif_model.score_individual_stock(analysis['stock_data'], market)
        
        return render_template(
            'naif_technical_analysis.html',
            symbol=symbol,
            market=market,
            analysis=analysis,
            naif_score=naif_score
        )
        
    except Exception as e:
        logger.error(f"Error in Naif technical analysis for {symbol}: {e}")
        flash('Error performing technical analysis', 'danger')
        return redirect(url_for('portfolio.naif_model'))


# API Endpoints
@portfolio_bp.route('/api/portfolio/<int:portfolio_id>/summary')
@login_required
def portfolio_summary_api(portfolio_id):
    """API endpoint for portfolio summary"""
    try:
        portfolio_service, _ = get_services()
        
        # Verify ownership
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first()
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        summary = portfolio_service.get_portfolio_summary(portfolio_id)
        
        return jsonify({
            'success': True,
            'portfolio_id': portfolio_id,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/test')
def test():
    """Test endpoint for portfolio blueprint"""
    return jsonify({
        'message': '✅ Portfolio blueprint is working perfectly!',
        'routes': [
            '/portfolio/ - Portfolio dashboard',
            '/portfolio/create - Create/import portfolio',
            '/portfolio/<id> - View portfolio',
            '/portfolio/<id>/analyze - Portfolio analysis', 
            '/portfolio/<id>/optimize - Portfolio optimization',
            '/portfolio/naif-model - Naif Al-Rasheed model',
            '/portfolio/naif-model/sector-analysis - Sector analysis'
        ],
        'service_layer': 'Active - Using PortfolioService + StockService',
        'features_preserved': 'ALL original functionality + improvements'
    })