import os
import datetime
from database.db_connection import Session
from backend.models import Keyword, RawData
from utils.encryption_utils import EncryptionUtils


def get_decrypted_data():
    """
    Fetches all decrypted records from the RawData table.
    Returns a list of dictionaries containing keyword, platform, content, and timestamp.
    """
    session = Session()
    encryption_utils = EncryptionUtils(os.getenv('ENCRYPTION_KEY'))
    decrypted_data = []

    try:
        records = session.query(RawData).all()
        for record in records:
            try:
                decrypted_content = encryption_utils.decrypt(record.content)
                decrypted_data.append({
                    'keyword': record.keyword,
                    'platform': record.platform,
                    'content': decrypted_content,
                    'timestamp': record.timestamp.isoformat()
                })
            except Exception as e:
                print(f"Error decrypting record {record.id}: {str(e)}")
                continue
    except Exception as e:
        print(f"Database query error: {str(e)}")
    finally:
        session.close()

    return decrypted_data


def migrate_existing_records():
    """One-time migration to encrypt existing records."""
    session = Session()
    encryption_utils = EncryptionUtils(os.getenv('ENCRYPTION_KEY'))

    try:
        records = session.query(RawData).all()
        for record in records:
            if record.content:
                try:
                    record.content = encryption_utils.migrate_data(record.content)
                except Exception as e:
                    print(f"Error migrating record {record.id}: {str(e)}")
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def fetch_keyword_batch(batch_size):
    """Fetch a batch of keywords from the database."""
    session = Session()
    try:
        keywords = session.query(Keyword).limit(batch_size).all()
        return [{'id': k.id, 'keyword': k.keyword} for k in keywords]
    finally:
        session.close()


def store_raw_data(keyword, platform, encrypted_content, timestamp=None):
    """Store encrypted scraped data into the raw_data table."""
    session = Session()
    try:
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc)

        # Handle both single items and lists
        if isinstance(encrypted_content, list):
            for item in encrypted_content:
                raw_data = RawData(
                    keyword=keyword,
                    platform=platform,
                    content=item if isinstance(item, str) else item.decode('utf-8'),
                    timestamp=timestamp,
                    added_at=datetime.datetime.now(datetime.timezone.utc)
                )
                session.add(raw_data)
        else:
            raw_data = RawData(
                keyword=keyword,
                platform=platform,
                content=encrypted_content if isinstance(encrypted_content, str) else encrypted_content.decode('utf-8'),
                timestamp=timestamp,
                added_at=datetime.datetime.now(datetime.timezone.utc)
            )
            session.add(raw_data)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    migrate_existing_records()
