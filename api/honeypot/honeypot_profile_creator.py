import os
import sys
from flask import Flask, jsonify, request
from celery import Celery

# Ensure that the project directory is included in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))  # Adjust to reach the project root
sys.path.append(project_root)

# Now you can import your modules without issues
from api.scraping.scraper_manager import ScraperManager
from api.honeypot.honeypot_profile_setup import HoneypotProfileSetup

# Initialize the Flask app
app = Flask(__name__)

# Configure Celery to use Redis as a broker
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

# Initialize the scraper manager
scraper_manager = ScraperManager(batch_size=100)

# Initialize the honeypot profile setup manager
honeypot_profile_setup = HoneypotProfileSetup()

# Celery Task for Scraping
@celery.task
def start_scraping():
    scraper_manager.scrape_all_platforms()

# Route to Start Scraping
@app.route('/start_scraping', methods=['GET'])
def start_scraping_route():
    task = start_scraping.apply_async()
    return jsonify({"message": "Scraping started", "task_id": task.id})

# Route to Create a Honeypot Profile
@app.route('/api/create_honeypot_profile', methods=['POST'])
def create_honeypot_profile():
    data = request.json
    platform = data.get('platform')
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not all([platform, username, password, email]):
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
    
    result = honeypot_profile_setup.create_profile(platform, username, password, email)
    return jsonify(result)

# Route to Manage (View/Update/Delete) a Honeypot Profile
@app.route('/api/manage_honeypot_profile', methods=['POST'])
def manage_honeypot_profile():
    data = request.json
    action = data.get('action')  # Example: 'view', 'update', 'delete'
    profile_id = data.get('profile_id')
    updates = data.get('updates', {})  # If updating, pass the new data
    
    if not action or not profile_id:
        return jsonify({'status': 'error', 'message': 'Action and Profile ID are required'}), 400
    
    result = honeypot_profile_setup.manage_profile(action, profile_id, updates)
    return jsonify(result)

# Main Application Entry
if __name__ == '__main__':
    app.run(debug=True)
