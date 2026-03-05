from sqlalchemy import Column, Integer, String, DateTime
from database.db_connection import Base
from datetime import datetime, timezone

class RawData(Base):
    __tablename__ = 'raw_data'
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), nullable=False)
    platform = Column(String(255), nullable=False)
    content = Column(String(5000), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<RawData(id={self.id}, keyword='{self.keyword}', platform='{self.platform}', timestamp='{self.timestamp}')>"