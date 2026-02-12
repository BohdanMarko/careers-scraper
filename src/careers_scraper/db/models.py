"""SQLAlchemy ORM models for careers scraper."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Job(Base):
    """Job posting model."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True)
    title = Column(String, index=True)
    location = Column(String, nullable=True)
    department = Column(String, nullable=True)
    url = Column(String, unique=True)
    description = Column(Text, nullable=True)
    posted_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    matches_keywords = Column(Boolean, default=False)


class CompanyCareerPage(Base):
    """Company career page configuration model."""

    __tablename__ = "company_career_pages"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    url = Column(String, unique=True)
    scraper_type = Column(String, default="dynamic")  # 'static' or 'dynamic'
    is_active = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
