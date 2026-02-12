from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

Base = declarative_base()


class Job(Base):
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
    __tablename__ = "company_career_pages"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    url = Column(String, unique=True)
    scraper_type = Column(String, default="dynamic")  # 'static' or 'dynamic'
    is_active = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Database session generator"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
