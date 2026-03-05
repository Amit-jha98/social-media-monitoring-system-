from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.db_config import Config

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,      # Verify connections before use
    pool_recycle=3600,        # Recycle connections every hour
    pool_size=10,
    max_overflow=20,
)
Session = sessionmaker(bind=engine)

# Shared Base for all models - import this in all model files
Base = declarative_base()


def get_session():
    """Create and return a new database session. Always close after use."""
    return Session()


@contextmanager
def get_db_session():
    """Context manager for safe database session handling.
    
    Usage:
        with get_db_session() as session:
            session.query(Model).all()
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
