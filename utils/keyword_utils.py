# utils/keyword_utils.py

import mysql.connector as MySQLdb  # Changed from import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

def get_keywords():
    """
    Fetch keywords from MySQL database
    Returns: List of keywords
    """
    connection = MySQLdb.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'ncb_projectv3')
    )
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT keyword FROM keywords")
        keywords = [row['keyword'] for row in cursor.fetchall()]
        return keywords
    finally:
        cursor.close()
        connection.close()