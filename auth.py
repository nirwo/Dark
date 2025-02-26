from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
import json
import requests
import os
from datetime import datetime

from models import db, User

# Create auth blueprint
auth = Blueprint('auth', __name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


def get_google_provider_cfg():
    """Get Google provider configuration"""
    try:
        return requests.get(GOOGLE_DISCOVERY_URL).json()
    except:
        return None


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        # Check if the user exists and password is correct
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))
            
        # Log the user in
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # If the user was trying to access a protected page, redirect there
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
            
        return redirect(next_page)
        
    return render_template('login.html')


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Email address already exists')
            return redirect(url_for('auth.signup'))
            
        # Create a new user
        new_user = User(email=email, name=name)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))
        
    return render_template('signup.html')


@auth.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    return redirect(url_for('index'))


@auth.route('/login/google')
def google_login():
    """Google OAuth login route"""
    # Get Google provider configuration
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash("Error connecting to Google OAuth service.")
        return redirect(url_for('auth.login'))
    
    # Get the authorization endpoint
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Create OAuth client
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
    
    # Construct authorization URL
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    
    return redirect(request_uri)


@auth.route('/login/google/callback')
def google_callback():
    """Google OAuth callback route"""
    # Get Google provider configuration
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash("Error connecting to Google OAuth service.")
        return redirect(url_for('auth.login'))
    
    # Get authorization code from response
    code = request.args.get("code")
    if not code:
        flash("Error with Google login, please try again.")
        return redirect(url_for('auth.login'))
    
    # Get token endpoint
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Create OAuth client
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
    
    # Prepare token request
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    
    # Request tokens
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    
    # Parse the token response
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    # Get userinfo endpoint
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    
    # Request user info
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    # Parse user info
    if userinfo_response.json().get("email_verified"):
        google_id = userinfo_response.json()["sub"]
        email = userinfo_response.json()["email"]
        name = userinfo_response.json().get("name", "")
        picture = userinfo_response.json().get("picture", "")
    else:
        flash("User email not verified by Google.")
        return redirect(url_for('auth.login'))
    
    # Check if user exists
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        # Try to find by email
        user = User.query.filter_by(email=email).first()
        if user:
            # Link existing account to Google
            user.google_id = google_id
            user.profile_pic = picture
        else:
            # Create a new user
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                profile_pic=picture
            )
        
        db.session.add(user)
        db.session.commit()
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Log in the user
    login_user(user)
    
    return redirect(url_for('index'))


@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)


@auth.route('/admin')
@login_required
def admin_panel():
    """Admin panel (only for admins)"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)


@auth.route('/admin/make_admin/<int:user_id>')
@login_required
def make_admin(user_id):
    """Make a user an admin (only for admins)"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    
    flash(f'{user.name} is now an admin.')
    return redirect(url_for('auth.admin_panel'))


@auth.route('/admin/logs')
@login_required
def view_logs():
    """View application logs (only for admins)"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    try:
        log_path = os.path.join(current_app.root_path, 'darkweb.log')
        if os.path.exists(log_path):
            with open(log_path, 'r') as log_file:
                log_content = log_file.read()
        else:
            log_content = "Log file not found."
    except Exception as e:
        log_content = f"Error reading log file: {str(e)}"
    
    return render_template('log.html', log_content=log_content)
