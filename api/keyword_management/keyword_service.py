# api/keyword_management/keyword_service.py

import sys
import os

# Ensure project root is in path before imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from database.db_connection import Session
from backend.models import Keyword


class KeywordService:
    @staticmethod
    def add_keyword(keyword):
        session = Session()
        try:
            existing_keyword = session.query(Keyword).filter_by(keyword=keyword).first()
            if existing_keyword:
                return {"success": False, "error": "Keyword already exists."}

            new_keyword = Keyword(keyword=keyword)
            session.add(new_keyword)
            session.commit()
            return {"success": True, "message": "Keyword added successfully."}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    @staticmethod
    def update_keyword(keyword_id, new_keyword_name):
        session = Session()
        try:
            keyword = session.get(Keyword, keyword_id)
            if not keyword:
                return {"success": False, "error": "Keyword not found."}

            keyword.keyword = new_keyword_name
            session.commit()
            return {"success": True, "message": "Keyword updated successfully."}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    @staticmethod
    def delete_keyword(keyword_id):
        session = Session()
        try:
            keyword = session.get(Keyword, keyword_id)
            if not keyword:
                return {"success": False, "error": "Keyword not found."}

            session.delete(keyword)
            session.commit()
            return {"success": True, "message": "Keyword deleted successfully."}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_all_keywords():
        session = Session()
        try:
            return session.query(Keyword).all()
        finally:
            session.close()
