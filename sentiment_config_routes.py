from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models import db, SentimentConfig, SENTIMENT_PRESETS

# Create blueprint
sentiment_bp = Blueprint('sentiment', __name__, url_prefix='/sentiment')

@sentiment_bp.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    """View and manage sentiment analysis configurations"""
    # Get all user's configurations
    configs = SentimentConfig.query.filter_by(user_id=current_user.id).all()
    
    # Get presets from models
    presets = SENTIMENT_PRESETS
    
    # Get symbol from query parameter if it exists
    symbol = request.args.get('symbol')
    
    if request.method == 'POST':
        # Create or update a config
        config_id = request.form.get('config_id')
        name = request.form.get('name')
        is_default = 'is_default' in request.form
        
        # Get weights from form
        price_momentum = int(request.form.get('price_momentum_weight', 40))
        week_52_range = int(request.form.get('week_52_range_weight', 20))
        ytd_performance = int(request.form.get('ytd_performance_weight', 20))
        news_sentiment = int(request.form.get('news_sentiment_weight', 10))
        rotc = int(request.form.get('rotc_weight', 10))
        
        # Validate total equals 100
        total = price_momentum + week_52_range + ytd_performance + news_sentiment + rotc
        if total != 100:
            flash(f"Weights must sum to 100%. Current sum: {total}%", "error")
            return redirect(url_for('sentiment.config', symbol=symbol))
        
        if config_id:
            # Update existing config
            config = SentimentConfig.query.get(config_id)
            if config and config.user_id == current_user.id:
                config.name = name
                config.price_momentum_weight = price_momentum
                config.week_52_range_weight = week_52_range
                config.ytd_performance_weight = ytd_performance
                config.news_sentiment_weight = news_sentiment
                config.rotc_weight = rotc
                
                # If setting as default, unset others
                if is_default:
                    SentimentConfig.query.filter_by(
                        user_id=current_user.id, 
                        is_default=True
                    ).update({'is_default': False})
                config.is_default = is_default
                
                db.session.commit()
                flash(f"Updated sentiment configuration: {name}", "success")
            else:
                flash("Invalid configuration ID", "error")
        else:
            # Create new config
            config = SentimentConfig(
                user_id=current_user.id,
                name=name,
                price_momentum_weight=price_momentum,
                week_52_range_weight=week_52_range,
                ytd_performance_weight=ytd_performance,
                news_sentiment_weight=news_sentiment,
                rotc_weight=rotc
            )
            
            # If setting as default, unset others
            if is_default:
                SentimentConfig.query.filter_by(
                    user_id=current_user.id, 
                    is_default=True
                ).update({'is_default': False})
            config.is_default = is_default
            
            db.session.add(config)
            db.session.commit()
            flash(f"Created new sentiment configuration: {name}", "success")
            
            # Set this config as active in session
            session['active_sentiment_config'] = config.as_dict()
        
        # If symbol is provided, redirect to reanalyze route
        if symbol:
            return redirect(url_for('reanalyze', symbol=symbol))
        else:
            return redirect(url_for('sentiment.config'))
    
    return render_template(
        'sentiment_config.html',
        configs=configs,
        presets=presets,
        symbol=symbol
    )

@sentiment_bp.route('/config/delete/<int:config_id>', methods=['POST'])
@login_required
def delete_config(config_id):
    """Delete a sentiment configuration"""
    config = SentimentConfig.query.get(config_id)
    
    if config and config.user_id == current_user.id:
        # Don't allow deleting the default config
        if config.is_default:
            flash("Cannot delete the default configuration", "error")
            return redirect(url_for('sentiment.config'))
            
        db.session.delete(config)
        db.session.commit()
        flash("Sentiment configuration deleted", "success")
    else:
        flash("Invalid configuration ID", "error")
        
    return redirect(url_for('sentiment.config'))

@sentiment_bp.route('/config/apply/<int:config_id>', methods=['POST'])
@login_required
def apply_config(config_id):
    """Apply a sentiment configuration to current analysis"""
    config = SentimentConfig.query.get(config_id)
    
    # Get symbol from form or query parameter
    symbol = request.form.get('symbol') or request.args.get('symbol')
    
    if config and config.user_id == current_user.id:
        # Store in session for use in analysis
        session['active_sentiment_config'] = config.as_dict()
        print(f"SETTING SENTIMENT CONFIG IN SESSION: {config.as_dict()}")
        
        # If symbol is provided, redirect to reanalyze route
        if symbol:
            flash(f"Applied sentiment configuration: {config.name}", "success")
            return redirect(url_for('reanalyze', symbol=symbol))
        else:
            flash(f"Applied sentiment configuration: {config.name}", "success")
    else:
        flash("Invalid configuration ID", "error")
        
    return redirect(url_for('sentiment.config', symbol=symbol))

@sentiment_bp.route('/config/preset/<preset_name>', methods=['POST'])
@login_required
def apply_preset(preset_name):
    """Apply a preset sentiment configuration"""
    # Find the preset by name
    preset = None
    for p in SENTIMENT_PRESETS:
        if p['name'] == preset_name:
            preset = p
            break
            
    if not preset:
        flash("Invalid preset name", "error")
        return redirect(url_for('sentiment.config'))
    
    # Store in session
    preset['id'] = 0  # Indicate it's a preset, not a saved config
    session['active_sentiment_config'] = preset
    
    # Check for symbol in form or query parameter
    symbol = request.form.get('symbol') or request.args.get('symbol')
    
    # If symbol is provided, redirect to reanalyze route
    if symbol:
        flash(f"Applied preset configuration: {preset_name}", "success")
        return redirect(url_for('reanalyze', symbol=symbol))
        
    flash(f"Applied preset configuration: {preset_name}", "success")
    return redirect(url_for('sentiment.config'))

@sentiment_bp.route('/api/configs', methods=['GET'])
@login_required
def get_configs():
    """API endpoint to get all user configurations"""
    configs = SentimentConfig.query.filter_by(user_id=current_user.id).all()
    return jsonify([config.as_dict() for config in configs])

@sentiment_bp.route('/api/config/default', methods=['GET'])
@login_required
def get_default_config():
    """API endpoint to get the default configuration"""
    config = SentimentConfig.get_default_for_user(current_user.id)
    return jsonify(config.as_dict())

@sentiment_bp.route('/api/config/validate', methods=['POST'])
def validate_weights():
    """API endpoint to validate that weights sum to 100%"""
    data = request.get_json()
    
    # Get weights from request
    price_momentum = int(data.get('price_momentum_weight', 0))
    week_52_range = int(data.get('week_52_range_weight', 0))
    ytd_performance = int(data.get('ytd_performance_weight', 0))
    news_sentiment = int(data.get('news_sentiment_weight', 0))
    rotc = int(data.get('rotc_weight', 0))
    
    # Calculate total
    total = price_momentum + week_52_range + ytd_performance + news_sentiment + rotc
    
    return jsonify({
        'valid': total == 100,
        'total': total,
        'difference': 100 - total
    })