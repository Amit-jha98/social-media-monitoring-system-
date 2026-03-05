import os
from database.db_connection import Session
from backend.models import RawData
from utils.encryption_utils import EncryptionUtils


def get_decrypted_data():
    """Fetch and decrypt all raw data records."""
    session = Session()
    encryption_utils = EncryptionUtils(key=os.getenv('ENCRYPTION_KEY'))
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
                    'timestamp': record.timestamp
                })
            except Exception as e:
                print(f"Error decrypting record {record.id}: {str(e)}")
                continue
    finally:
        session.close()

    return decrypted_data
