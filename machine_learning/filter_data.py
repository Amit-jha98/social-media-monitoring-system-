import sys
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import torch
import hashlib
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from celery import Celery
from utils.encryption_utils import EncryptionUtils

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("filter_data.log"), logging.StreamHandler()]
)

# Database credentials
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB = os.getenv("MYSQL_DB")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Load tokenizer and model
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
tokenizer = RobertaTokenizer.from_pretrained(os.path.join(project_root, "machine_learning/saved_model"))
model = RobertaForSequenceClassification.from_pretrained(os.path.join(project_root, "machine_learning/saved_model"))
encryption_utils = EncryptionUtils(ENCRYPTION_KEY)

# Initialize Celery
celery_app = Celery("filter_data", broker='redis://localhost:6379/0')


def hash_text(text):
    """Generate a SHA-256 hash for the given text."""
    return hashlib.sha256(text.encode()).hexdigest()


def add_or_update_monitored_channel(platform_id, channel_name, channel_id):
    """Insert or update monitored channel data."""
    try:
        insert_query = """
            INSERT INTO monitored_channels (platform_id, channel_name, channel_id)
            VALUES (:platform_id, :channel_name, :channel_id)
            ON DUPLICATE KEY UPDATE last_checked = CURRENT_TIMESTAMP;
        """
        with engine.begin() as connection:
            connection.execute(text(insert_query), {
                "platform_id": platform_id,
                "channel_name": channel_name,
                "channel_id": channel_id
            })
        logging.info(f"Monitored channel '{channel_name}' (ID: {channel_id}) added/updated successfully.")
    except SQLAlchemyError as e:
        logging.error(f"Error inserting/updating monitored channel '{channel_name}': {e}")


def process_suspicious_entries(suspicious_entries):
    """Insert suspicious entries into the database, avoiding duplicates."""
    if not suspicious_entries:
        logging.info("No suspicious entries to process.")
        return

    try:
        with engine.begin() as connection:
            for entry in suspicious_entries:
                # Check for duplicate using text hash
                check_duplicate_query = text("""
                    SELECT id FROM suspicious_activity
                    WHERE text_hash = :text_hash
                """)
                duplicate_result = connection.execute(check_duplicate_query, {"text_hash": entry["text_hash"]}).fetchone()

                if duplicate_result:
                    logging.info(f"Duplicate entry detected, skipping insertion for hash {entry['text_hash']}.")
                    continue

                # Insert the suspicious activity entry
                insert_query = text("""
                    INSERT INTO suspicious_activity (
                        keyword_id, keyword_text, platform_id, channel_id, detected_text, text_hash, detected_at
                    )
                    VALUES (
                        :keyword_id, :keyword_text, :platform_id, :channel_id, :detected_text, :text_hash, :detected_at
                    )
                """)
                connection.execute(insert_query, entry)

        logging.info(f"Successfully processed {len(suspicious_entries)} suspicious entries.")
    except SQLAlchemyError as e:
        logging.error(f"Transaction failed. Error inserting suspicious entries: {e}")


def filter_suspicious_data_task():
    """Filter suspicious data from the clean_data table and store results."""
    logging.info("Starting the filter_suspicious_data_task.")
    suspicious_entries = []
    total_positive = 0

    session = SessionLocal()

    try:
        query = "SELECT id, keyword, platform, caption, channel_name FROM clean_data"
        result = session.execute(text(query))
        clean_data = result.fetchall()
        logging.info(f"Fetched {len(clean_data)} rows from clean_data table.")
    except SQLAlchemyError as e:
        logging.error(f"Database fetch error: {e}")
        session.close()
        return {"status": "error", "message": str(e)}

    for row in clean_data:
        try:
            id_, keyword, platform, caption, channel_name = row
            content = caption or ""
            logging.debug(f"Processing ID {id_}: {content[:30]}...")

            # Determine keyword ID and text
            keyword_id = keyword if isinstance(keyword, int) else None
            keyword_text = keyword if not isinstance(keyword, int) else None

            # Fetch platform ID
            platform_id = None
            if platform:
                platform_query = text("SELECT id FROM platforms WHERE name = :name")
                platform_result = session.execute(platform_query, {"name": platform}).fetchone()
                if platform_result:
                    platform_id = platform_result[0]
                else:
                    logging.error(f"Platform '{platform}' not found.")
                    continue

            # Ensure channel is monitored
            channel_name = channel_name or "Unknown Channel"
            channel_id = str(id_)
            add_or_update_monitored_channel(platform_id, channel_name, channel_id)

            # Predict using the model
            inputs = tokenizer(content, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
                prediction = torch.argmax(outputs.logits, dim=1).item()

            # Store only positive (suspicious) predictions
            if prediction == 1:
                total_positive += 1
                encrypted_text = encryption_utils.encrypt(content)
                text_hash = hash_text(content)
                suspicious_entries.append({
                    "keyword_id": keyword_id,
                    "keyword_text": keyword_text,
                    "platform_id": platform_id,
                    "channel_id": channel_id,
                    "detected_text": encrypted_text,
                    "text_hash": text_hash,
                    "detected_at": datetime.now()
                })
                logging.info(f"Suspicious content detected for ID {id_}.")

        except Exception as e:
            logging.error(f"Error processing row ID {id_}: {e}")

    if suspicious_entries:
        process_suspicious_entries(suspicious_entries)

    session.close()
    logging.info(f"Task completed. Total positive entries: {total_positive}.")
    return {"status": "success", "message": f"Processed {len(clean_data)} rows with {total_positive} positive detections."}


if __name__ == "__main__":
    try:
        result = filter_suspicious_data_task()
        logging.info("Task executed synchronously.")
        print(result)
    except Exception as e:
        logging.error(f"Execution error: {e}")
        print({"status": "error", "message": str(e)})

