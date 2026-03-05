import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Database configuration loaded from environment variables."""
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', '')}"
        f"@{os.getenv('MYSQL_HOST', 'localhost')}/{os.getenv('MYSQL_DB', 'ncb_projectv3')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())

# IMPORTANT: Create a .env file with your database credentials.
# See .env.example for required variables.
