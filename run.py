#!/usr/bin/env python3
"""
Hexaware Question Builder Application
Main application entry point
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from config import config
from models import db, User
from auth import auth_bp
from routes import main_bp, dashboard_bp, curriculum_bp, questions_bp, assessments_bp, reports_bp, api_bp

def create_app(config_name=None):
    """Create and configure the Flask application"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize Flask-Mail
    mail = Mail(app)
    
    # Initialize CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(curriculum_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            from werkzeug.security import generate_password_hash
            from models import UserRole
            
            admin_user = User(
                username='admin',
                email='admin@hexaware.com',
                password_hash=generate_password_hash('admin123'),
                role=UserRole.ADMIN,
                department='IT Administration',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: admin/admin123")
    
    return app

def main():
    """Main function to run the application"""
    app = create_app()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting Hexaware Question Builder on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Access the application at: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
