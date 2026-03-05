import sys
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Add the project root to sys.path to fix module import issues
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

# Import utility functions
from utils.encryption_utils import EncryptionUtils

# Load environment variables from the .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("dummy_data_insertion.log"), logging.StreamHandler()]
)

# Database credentials and configuration
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB = os.getenv("MYSQL_DB")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Create database engine
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
engine = create_engine(DATABASE_URL, echo=False)  # Disable echo for cleaner logs

# Initialize EncryptionUtils
encryption_utils = EncryptionUtils(ENCRYPTION_KEY)

def insert_dummy_data_into_clean_data():
    """
    Insert dummy data into the clean_data table for testing purposes.
    """
    dummy_entries = [
        {
            "keyword": "beerlover",
            "platform": "Telegram",
            "channel_id": "user123",
            "channel_name": "drug_dealer",
            "link": "https://t.me/quick_sale",
            "caption": "Quick sale on white powder, DM for more queries",
            "tags": "#drugs, #sale",
            "comments": "Contact for details",
            "likes": 25,
            "post_time": datetime(2024, 11, 18, 12, 0, 0),  
            "content": encryption_utils.encrypt("Quick sale for white powder, DM for more infotmation")
        },
        {
            "keyword": "movies",
            "platform": "Instagram",
            "channel_id": "user456",
            "channel_name": "movie_lover",
            "link": "https://instagram.com/movies_fanpage",
            "caption": "Just added a stuff, DM for rates!",
            "tags": "#movies, #bollywood", 
            "comments": "Loved the storyline!",
            "likes": 150,
            "post_time": datetime(2024, 11, 18, 14, 0, 0),  
            "content": encryption_utils.encrypt("Kuch green chahiye, DM for rates!")
        },
        {
            "keyword": "party",
            "platform": "Telegram",
            "channel_id": "user789",
            "channel_name": "party_enthusiast",
            "link": "https://t.me/party_stuff",
            "caption": "Party stuff ready, interested people DM here",
            "tags": "#party, #fun",
            "comments": "DM for more details",
            "likes": 45,
            "post_time": datetime(2024, 11, 18, 16, 0, 0),  
            "content": encryption_utils.encrypt("Party stuff ready, interested he to DM me")
        },
        {
            "keyword": "chitta",
            "platform": "WhatsApp",
            "channel_id": "user999",
            "channel_name": "family_person",
            "link": "https://wa.me/family_chat",
            "caption": "Sasta chitta aa gya he, DM me fast",
            "tags": "#family, #love",
            "comments": "Great time with loved ones",
            "likes": 60,
            "post_time": datetime(2024, 11, 18, 18, 0, 0),  
            "content": encryption_utils.encrypt("Sasta chitta aa gya he, DM me  fast")
        }
    ]



    try:
        insert_query = """
            INSERT INTO clean_data (keyword, platform, channel_id, channel_name, link, caption, tags, comments, likes, post_time, content)
            VALUES (:keyword, :platform, :channel_id, :channel_name, :link, :caption, :tags, :comments, :likes, :post_time, :content)
            ON DUPLICATE KEY UPDATE
            channel_name = VALUES(channel_name), caption = VALUES(caption), tags = VALUES(tags), comments = VALUES(comments),
            likes = VALUES(likes), post_time = VALUES(post_time), content = VALUES(content)
        """
        with engine.begin() as connection:
            connection.execute(text(insert_query), dummy_entries)
        logging.info("Dummy data inserted successfully into clean_data.")
    except IntegrityError as e:
        logging.error(f"Integrity error during dummy data insert into clean_data: {e}", exc_info=True)
    except SQLAlchemyError as e:
        logging.error(f"SQLAlchemy error during dummy data insert into clean_data: {e}", exc_info=True)

if __name__ == "__main__":
    # Call the function to insert dummy data
    insert_dummy_data_into_clean_data()
