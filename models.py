import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    google_id = db.Column(db.String(100), nullable=True, unique=True)
    profile_pic = db.Column(db.String(200), nullable=True)
    
    # Relationship with SearchHistory
    searches = db.relationship('SearchHistory', backref='user', lazy=True)
    
    def set_password(self, password):
        """Create hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class SearchHistory(db.Model):
    """Search history model"""
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    search_query = db.Column(db.String(100), nullable=False)
    search_type = db.Column(db.String(20), default='email', nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    result_count = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), default='low')
    results_json = db.Column(db.Text, nullable=True)
    search_duration = db.Column(db.Float, default=0.0)  # in seconds
    
    def get_results(self):
        """Get results as a Python dictionary"""
        if not self.results_json:
            return {}
        try:
            return json.loads(self.results_json)
        except:
            return {}
    
    def set_results(self, results_dict):
        """Set results from a Python dictionary"""
        self.results_json = json.dumps(results_dict)
    
    def __repr__(self):
        return f'<SearchHistory {self.search_type}:{self.search_query} ({self.timestamp})>'


def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Create admin user if none exists
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                email='admin@example.com',
                name='Administrator',
                is_admin=True
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
