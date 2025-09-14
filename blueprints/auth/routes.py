"""
Authentication Routes
Handles user registration, login, logout, and profile management
"""

from flask import render_template, request, redirect, url_for, flash, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import requests
import os
from . import auth_bp
from models import db, User, FeatureWeight
from user_profiling.profile_analyzer import ProfileAnalyzer
from ml_components.adaptive_learning_db import AdaptiveLearningDB


def get_adaptive_learning():
    """Get adaptive learning DB instance for current user"""
    if current_user.is_authenticated:
        return AdaptiveLearningDB(current_user.id)
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            # Redirect to profiling if not yet completed
            if not user.has_completed_profiling:
                return redirect(url_for('user_profiling'))
                
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email address already in use. Please use a different email or reset your password.', 'danger')
            return redirect(url_for('auth.register'))
            
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            # Ensure has_completed_profiling is set to False
            user.has_completed_profiling = False
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during user registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Initialize feature weights for new user
        feature_weights = FeatureWeight(user_id=user.id)
        db.session.add(feature_weights)
        
        try:
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error initializing user features: {str(e)}")
            flash('Registration successful, but there was an error setting up your profile. Please contact support.', 'warning')
            return redirect(url_for('auth.login'))
    
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('index'))


@auth_bp.route('/create-profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    """Handle user profile creation with CFA risk profiling"""
    if request.method == 'POST':
        # Get form data
        profile_data = {
            'time_horizon': {
                'withdrawal_start': int(request.form.get('withdrawal_start')),
                'withdrawal_duration': int(request.form.get('withdrawal_duration'))
            },
            'risk_tolerance': {
                'risk_attitude': int(request.form.get('risk_attitude')),
                'loss_response': int(request.form.get('loss_response'))
            },
            'knowledge_level': int(request.form.get('knowledge_level')),
            'sectors': request.form.getlist('sectors')
        }
        
        # Use existing profile analyzer
        profile_analyzer = ProfileAnalyzer()
        recommendations = profile_analyzer.analyze_profile()
        
        # Save profile to session
        session['user_profile'] = recommendations
        
        # Update sector preferences based on selected sectors
        adaptive_learning = get_adaptive_learning()
        if adaptive_learning:
            for sector in profile_data.get('sectors', []):
                adaptive_learning._update_sector_preference(sector, 2)  # +2 score for selected sectors
        
        # Mark profiling as completed
        current_user.has_completed_profiling = True
        db.session.commit()
        
        return render_template('profile_results.html', profile=recommendations)
        
    return render_template('profile.html')


@auth_bp.route('/view-profile')
@login_required
def view_profile():
    """View current user profile"""
    profile = session.get('user_profile')
    
    # Add adaptive learning data if available
    adaptive_learning = get_adaptive_learning()
    user_preferences = None
    if adaptive_learning:
        user_preferences = adaptive_learning.get_user_profile_summary()
    
    return render_template('view_profile.html', 
                         profile=profile, 
                         user_preferences=user_preferences)


@auth_bp.route('/profile_results')
@login_required
def profile_results():
    """Display profile analysis results"""
    profile = session.get('user_profile')
    if not profile:
        flash('No profile data found. Please complete your profile first.', 'warning')
        return redirect(url_for('auth.create_profile'))

    return render_template('profile_results.html', profile=profile)


# ==========================================
# GOOGLE OAUTH ROUTES
# ==========================================

@auth_bp.route('/auth/google')
def google_auth():
    """Redirect to Google OAuth"""
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', url_for('auth.google_callback', _external=True))

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={google_client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid email profile&"
        f"response_type=code&"
        f"state=security_token"
    )

    return redirect(google_auth_url)


@auth_bp.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    if not code:
        flash('Google authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Exchange code for access token
        token_data = {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', url_for('auth.google_callback', _external=True))
        }

        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_json = token_response.json()

        if 'access_token' not in token_json:
            flash('Failed to get access token from Google.', 'error')
            return redirect(url_for('auth.login'))

        # Get user info from Google
        headers = {'Authorization': f"Bearer {token_json['access_token']}"}
        user_response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
        user_info = user_response.json()

        # Check if user exists or create new user
        user = User.query.filter_by(email=user_info['email']).first()

        if not user:
            # Create new user with Google info
            user = User(
                username=user_info['email'].split('@')[0],  # Use email prefix as username
                email=user_info['email'],
                full_name=user_info.get('name', ''),
                google_id=user_info['id']
            )
            # Set a random password for Google users (they won't use it)
            user.set_password('google_auth_' + user_info['id'])

            db.session.add(user)

            # Initialize default feature weights
            default_weights = FeatureWeight.get_default_weights()
            for feature, weight in default_weights.items():
                feature_weight = FeatureWeight(
                    user_id=user.id,
                    feature_name=feature,
                    weight=weight
                )
                db.session.add(feature_weight)

            try:
                db.session.commit()
                current_app.logger.info(f"New Google user created: {user.email}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating Google user: {str(e)}")
                flash('Error creating your account. Please try again.', 'error')
                return redirect(url_for('auth.login'))

        # Log the user in
        login_user(user)
        flash(f'Welcome, {user.full_name or user.username}!', 'success')

        # Redirect to profiling if not completed
        if not user.has_completed_profiling:
            return redirect(url_for('auth.create_profile'))

        return redirect(url_for('index'))

    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        flash('Authentication error occurred. Please try again.', 'error')
        return redirect(url_for('auth.login'))