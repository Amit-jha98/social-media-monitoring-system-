"""Backend app module — Celery worker configuration.
Note: The main Flask entry point is main.py, not this file.
"""
import os
import sys
from flask import Flask, jsonify
from celery import Celery

# Ensure that the project directory is included in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.honeypot.honeypot_profile_setup import honeypot_blueprint
from api.scraping.scraper_manager import ScraperManager


# Initialize the Flask app for Celery context
app = Flask(__name__)

# Register the blueprint
app.register_blueprint(honeypot_blueprint, url_prefix="/api")

# Configure Celery to use Redis as a broker
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery_app = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

# Initialize the scraper manager
scraper_manager = ScraperManager(batch_size=100)


# Celery Task for Scraping
@celery_app.task
def start_scraping():
    scraper_manager.scrape_all_platforms()


# Do NOT run this file directly. Use main.py as the entry point.
if __name__ == '__main__':
    print("WARNING: Use main.py as the entry point, not backend/app.py")
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1'))
