import sys
import os
from dotenv import load_dotenv
from datetime import datetime
import re
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from transformers import pipeline

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
    handlers=[logging.FileHandler("extract_clean_data.log"), logging.StreamHandler()]
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

# Load pre-trained NLP model for Named Entity Recognition
ner_pipeline = pipeline("ner", grouped_entities=True, model="dslim/bert-base-NER")

# Regex patterns for fallback extraction
FIELD_PATTERNS = {
    "link": r'(https?://\S+)',
    "channel_id": r'user_id[:=]\s*(\w+)',
    "channel_name": r'@(\w+)',
    "caption": r'caption:(.*?)(?=tags:|comments:|likes:|http|$)',
    "tags": r'#(\w+)',
    "comments": r'comments:(.*?)(?=likes:|http|$)',
    "likes": r'likes:\s*(\d+)',
    "post_time": r'(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
}

def extract_with_ai_model(text):
    """
    Extract structured fields using a pre-trained AI model (NER pipeline).
    """
    ai_extracted = {}
    try:
        entities = ner_pipeline(text)
        for entity in entities:
            entity_label = entity["entity_group"]
            entity_value = entity["word"]
            if entity_label not in ai_extracted:
                ai_extracted[entity_label] = []
            ai_extracted[entity_label].append(entity_value)

        # Flatten and join list values for simplicity
        for key in ai_extracted:
            ai_extracted[key] = ', '.join(ai_extracted[key])


        logging.debug(f"AI extracted entities: {ai_extracted}")
    except Exception as e:
        logging.error(f"Error in AI extraction: {e}", exc_info=True)
    return ai_extracted


def extract_data_from_text(decrypted_text):
    """
    Extract relevant fields from decrypted content using AI and regex as fallback.
    """
    unmatched_content = decrypted_text.strip()
    extracted_data = {}

    # Extract fields using AI
    ai_results = extract_with_ai_model(decrypted_text)

    # Map AI results to structured fields where possible
    extracted_data.update({
        "channel_id": ai_results.get("ID", None),
        "channel_name": ai_results.get("USERNAME", None),
        "link": ai_results.get("URL", None),
        "tags": ai_results.get("HASHTAG", None),
        "caption": ai_results.get("CAPTION", None),
        "comments": ai_results.get("COMMENT", None),
    })

    # Use regex as a fallback
    try:
        for field, pattern in FIELD_PATTERNS.items():
            if field not in extracted_data or not extracted_data[field]:
                match = re.search(pattern, decrypted_text, re.IGNORECASE)
                if field == "tags":
                    matches = re.findall(pattern, decrypted_text)
                    extracted_data[field] = ', '.join(matches) if matches else None
                    unmatched_content = re.sub(r'#\w+', '', unmatched_content)
                elif field == "post_time" and match:
                    extracted_data[field] = datetime.strptime(match.group(0), "%Y-%m-%d %H:%M:%S")
                    unmatched_content = unmatched_content.replace(match.group(0), '')
                elif match:
                    extracted_data[field] = match.group(1) if field != "link" else match.group(0)
                    unmatched_content = unmatched_content.replace(match.group(0), '')
                else:
                    extracted_data[field] = None

        # Remaining unmatched content
        extracted_data["content"] = unmatched_content.strip() or None
    except Exception as e:
        logging.error(f"Error extracting data: {e}", exc_info=True)

    return extracted_data


def process_and_store_clean_data():
    """
    Fetch raw data, decrypt content, extract fields using AI and regex, and store in the clean_data table.
    """
    logging.info("Starting data extraction and storage process.")
    clean_entries = []

    try:
        # Fetch encrypted content from raw_data table
        with engine.connect() as connection:
            query = "SELECT id, keyword, platform, content FROM raw_data"
            raw_data = connection.execute(text(query)).fetchall()
            logging.info(f"Fetched {len(raw_data)} rows from raw_data table.")

        # Process each row
        for row in raw_data:
            id_, keyword, platform, encrypted_content = row
            try:
                # Decrypt content from raw_data
                content = encryption_utils.decrypt(encrypted_content)
                logging.debug(f"Decrypted content for ID {id_}: {content[:50]}...")

                # Encrypt content to store in clean_data
                encrypted_clean_content = encryption_utils.encrypt(content)

                # Extract fields from decrypted content
                extracted_data = extract_data_from_text(content)

                # Prepare entry for insertion
                clean_entry = {
                    "keyword": keyword,
                    "platform": platform,
                    "channel_id": extracted_data["channel_id"],
                    "channel_name": extracted_data["channel_name"],
                    "link": extracted_data["link"],
                    "caption": extracted_data["caption"],
                    "tags": extracted_data["tags"],
                    "comments": extracted_data["comments"],
                    "likes": extracted_data["likes"],
                    "post_time": extracted_data["post_time"],
                    "content": encrypted_clean_content  # Store encrypted content
                }
                clean_entries.append(clean_entry)
            except Exception as e:
                logging.error(f"Error processing row ID {id_}: {e}", exc_info=True)

        # Bulk insert clean entries into clean_data table
        if clean_entries:
            try:
                insert_query = """
                    INSERT INTO clean_data (keyword, platform, channel_id, channel_name, link, caption, tags, comments, likes, post_time, content)
                    VALUES (:keyword, :platform, :channel_id, :channel_name, :link, :caption, :tags, :comments, :likes, :post_time, :content)
                    ON DUPLICATE KEY UPDATE
                    channel_name = VALUES(channel_name), caption = VALUES(caption), tags = VALUES(tags), comments = VALUES(comments),
                    likes = VALUES(likes), post_time = VALUES(post_time), content = VALUES(content)
                """
                with engine.begin() as connection:  # Auto-commit transactions
                    connection.execute(text(insert_query), clean_entries)
                logging.info(f"Inserted/Updated {len(clean_entries)} clean entries into clean_data table.")
            except IntegrityError as e:
                logging.error(f"Integrity error during insert: {e}", exc_info=True)
            except SQLAlchemyError as e:
                logging.error(f"SQLAlchemy error during insert: {e}", exc_info=True)

        return {"status": "success", "message": f"Processed {len(raw_data)} rows, extracted {len(clean_entries)} clean entries."}

    except SQLAlchemyError as e:
        logging.error(f"Database fetch error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    result = process_and_store_clean_data()
    print(result)
