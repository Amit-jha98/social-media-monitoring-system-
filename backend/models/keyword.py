# backend/models/keyword.py
from sqlalchemy import Column, Integer, String
from database.db_connection import Base


class Keyword(Base):
    __tablename__ = 'keywords'

    id = Column(Integer, primary_key=True)
    keyword = Column(String(500), nullable=True)
    added_by = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}')>"


