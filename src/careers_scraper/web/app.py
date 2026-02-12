"""FastAPI web dashboard for careers scraper."""

import logging
from pathlib import Path
from fastapi import FastAPI, Depends, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from careers_scraper.db import get_db, Job, CompanyCareerPage
from careers_scraper.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Careers Scraper Dashboard")

# Get static files directory
static_dir = Path(__file__).parent / "static"
logger.debug(f"Static files directory: {static_dir}")

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class JobResponse(BaseModel):
    """Response model for job listings."""

    id: int
    company: str
    title: str
    location: Optional[str]
    department: Optional[str]
    url: str
    description: Optional[str]
    scraped_at: datetime
    matches_keywords: bool

    class Config:
        from_attributes = True


class CompanyResponse(BaseModel):
    """Response model for company career pages."""

    id: int
    company_name: str
    url: str
    is_active: bool
    last_scraped: Optional[datetime]

    class Config:
        from_attributes = True


@app.get("/")
async def home():
    """Serve the main dashboard page."""
    index_file = static_dir / "index.html"
    logger.debug(f"Serving index.html from {index_file}")
    return FileResponse(index_file)


@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs(
    matching_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get all jobs, optionally filtered by keyword matches.

    Args:
        matching_only: If True, return only jobs matching search keywords
        db: Database session

    Returns:
        List of job listings
    """
    query = db.query(Job)

    if matching_only:
        query = query.filter(Job.matches_keywords == True)

    jobs = query.order_by(Job.scraped_at.desc()).all()
    logger.debug(f"Retrieved {len(jobs)} jobs (matching_only={matching_only})")
    return jobs


@app.get("/api/companies", response_model=List[CompanyResponse])
async def get_companies(db: Session = Depends(get_db)):
    """
    Get all company career pages.

    Args:
        db: Database session

    Returns:
        List of company career pages
    """
    companies = db.query(CompanyCareerPage).all()
    logger.debug(f"Retrieved {len(companies)} companies")
    return companies


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics.

    Args:
        db: Database session

    Returns:
        Dictionary with total jobs, matching jobs, and total companies
    """
    total_jobs = db.query(Job).count()
    matching_jobs = db.query(Job).filter(Job.matches_keywords == True).count()
    total_companies = db.query(CompanyCareerPage).count()

    logger.debug(
        f"Stats: {total_jobs} jobs, {matching_jobs} matching, {total_companies} companies"
    )

    return {
        "total_jobs": total_jobs,
        "matching_jobs": matching_jobs,
        "total_companies": total_companies
    }
