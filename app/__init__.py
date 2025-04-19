from flask import Flask, current_app
from flask_migrate import Migrate  # Import Flask-Migrate for database migrations
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler  # Import APScheduler
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Config from the root directory
from config import Config

# Import db and login_manager from extensions
from app.extensions import db, login_manager

# Import routes
from app.routes.web_routes import generate_recommendations, process_requests  # Adjust import paths if needed
from app.routes.request_processing_routes import request_processing_bp
from app.routes.config_routes import config_bp  # Import the new config route
from app.routes.admin_routes import admin_bp  # Import the admin route

csrf = CSRFProtect()
migrate = Migrate()  # Initialize Flask-Migrate

def create_app():
    app = Flask(__name__)

    # Initialize CSRF protection after app creation
    csrf.init_app(app)

    # Instantiate and load the configuration
    config = Config()
    db_username = config.DB_USERNAME
    db_password = config.DB_PASSWORD
    db_host = config.DB_HOST
    db_name = config.DB_NAME
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = config.SECRET_KEY

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)  # Attach Flask-Migrate to the app
    login_manager.init_app(app)
    login_manager.login_view = 'user_routes.login'

    # Add the user_loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User  # Import User here to avoid circular import issues
        return User.query.get(int(user_id))

    # Initialize the scheduler
    scheduler = BackgroundScheduler()

    # Define the task functions
    def daily_recommendations_task():
        with app.app_context():  # Ensure the task runs within the app context
            try:
                generate_recommendations()
            except Exception as e:
                current_app.logger.error(f"Error running daily_recommendations_task: {e}")

    def process_pending_requests_task():
        with app.app_context():  # Ensure the task runs within the app context
            try:
                # Call the processing function directly (imported at the top of this file)
                from app.routes.request_processing_routes import process_requests_with_jackett_and_qbittorrent
                process_requests_with_jackett_and_qbittorrent()
            except Exception as e:
                current_app.logger.error(f"Error running process_pending_requests_task: {e}")

    # Schedule the tasks
    scheduler.add_job(daily_recommendations_task, 'interval', days=1)
    scheduler.add_job(process_pending_requests_task, 'interval', minutes=5)
    scheduler.start()

    with app.app_context():
        # Import and register your blueprints/routes here
        from .routes import media_routes, user_routes, request_routes, notification_routes, web_routes, auth_routes
        from app.routes.jellyfin_routes import jellyfin_bp
        app.register_blueprint(auth_routes.auth_bp)
        app.register_blueprint(media_routes.bp)
        app.register_blueprint(user_routes.bp)
        app.register_blueprint(request_routes.bp)
        app.register_blueprint(notification_routes.bp)
        app.register_blueprint(web_routes.bp)
        app.register_blueprint(jellyfin_bp)
        app.register_blueprint(request_processing_bp)
        app.register_blueprint(config_bp, url_prefix='/config')  # Register the new config route
        app.register_blueprint(admin_bp, url_prefix='/admin')  # Register the admin route

        # Create database tables if they don't exist
        db.create_all()

    return app

def configure_logging():
    LOG_DIR = "./logs"
    os.makedirs(LOG_DIR, exist_ok=True)

    LOG_FILE = os.path.join(LOG_DIR, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console
            RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5),  # Rotating logs
        ],
    )