from fastapi import FastAPI, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database import get_db, Job, CompanyCareerPage
from config import settings

app = FastAPI(title="Careers Scraper Dashboard")


class JobResponse(BaseModel):
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
    id: int
    company_name: str
    url: str
    is_active: bool
    last_scraped: Optional[datetime]

    class Config:
        from_attributes = True


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main dashboard page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Careers Scraper Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #333; }
            .filters { margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }
            .job-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .job-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .company { color: #666; font-weight: bold; }
            .title { font-size: 18px; margin: 5px 0; color: #0066cc; }
            .meta { color: #888; font-size: 14px; }
            .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; margin-right: 5px; }
            .badge-match { background: #4CAF50; color: white; }
            .stats { display: flex; gap: 20px; margin: 20px 0; }
            .stat-card { flex: 1; padding: 15px; background: #e3f2fd; border-radius: 5px; }
            button { padding: 8px 16px; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0052a3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Careers Scraper Dashboard</h1>

            <div class="stats" id="stats">
                <div class="stat-card">
                    <h3>Total Jobs</h3>
                    <p id="total-jobs">Loading...</p>
                </div>
                <div class="stat-card">
                    <h3>Matching Keywords</h3>
                    <p id="matching-jobs">Loading...</p>
                </div>
                <div class="stat-card">
                    <h3>Companies</h3>
                    <p id="total-companies">Loading...</p>
                </div>
            </div>

            <div class="filters">
                <label><input type="checkbox" id="matchingOnly"> Show only matching keywords</label>
                <button onclick="loadJobs()">Refresh</button>
            </div>

            <div id="jobs-container">Loading jobs...</div>
        </div>

        <script>
            async function loadJobs() {
                const matchingOnly = document.getElementById('matchingOnly').checked;
                const url = matchingOnly ? '/api/jobs?matching_only=true' : '/api/jobs';

                const response = await fetch(url);
                const jobs = await response.json();

                const container = document.getElementById('jobs-container');

                if (jobs.length === 0) {
                    container.innerHTML = '<p>No jobs found. Run a scraping cycle to populate the database.</p>';
                    return;
                }

                container.innerHTML = jobs.map(job => `
                    <div class="job-card">
                        <div class="company">${job.company}</div>
                        <div class="title"><a href="${job.url}" target="_blank">${job.title}</a></div>
                        <div class="meta">
                            ${job.location ? `📍 ${job.location}` : ''}
                            ${job.department ? `| 🏢 ${job.department}` : ''}
                            ${job.matches_keywords ? '<span class="badge badge-match">MATCH</span>' : ''}
                        </div>
                        <div class="meta">Scraped: ${new Date(job.scraped_at).toLocaleString()}</div>
                    </div>
                `).join('');
            }

            async function loadStats() {
                const [jobsRes, companiesRes] = await Promise.all([
                    fetch('/api/jobs'),
                    fetch('/api/companies')
                ]);

                const jobs = await jobsRes.json();
                const companies = await companiesRes.json();

                document.getElementById('total-jobs').textContent = jobs.length;
                document.getElementById('matching-jobs').textContent = jobs.filter(j => j.matches_keywords).length;
                document.getElementById('total-companies').textContent = companies.length;
            }

            loadJobs();
            loadStats();
            setInterval(loadJobs, 30000); // Auto-refresh every 30 seconds
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs(
    matching_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get all jobs, optionally filtered by keyword matches"""
    query = db.query(Job)

    if matching_only:
        query = query.filter(Job.matches_keywords == True)

    jobs = query.order_by(Job.scraped_at.desc()).all()
    return jobs


@app.get("/api/companies", response_model=List[CompanyResponse])
async def get_companies(db: Session = Depends(get_db)):
    """Get all company career pages"""
    companies = db.query(CompanyCareerPage).all()
    return companies


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    total_jobs = db.query(Job).count()
    matching_jobs = db.query(Job).filter(Job.matches_keywords == True).count()
    total_companies = db.query(CompanyCareerPage).count()

    return {
        "total_jobs": total_jobs,
        "matching_jobs": matching_jobs,
        "total_companies": total_companies
    }
