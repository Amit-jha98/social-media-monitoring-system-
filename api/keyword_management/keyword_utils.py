# api/keyword_management/keyword_utils.py

from api.keyword_management.keyword_service import KeywordService

def get_keywords():
    keywords = KeywordService.get_all_keywords()
    return [k.keyword for k in keywords]
