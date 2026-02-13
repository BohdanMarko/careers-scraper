-- Initial database schema for careers-scraper
-- Run this manually if needed: sqlite3 careers.db < scripts/migrations/001_initial_schema.sql

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    location VARCHAR,
    department VARCHAR,
    url VARCHAR NOT NULL UNIQUE,
    description TEXT,
    posted_date DATETIME,
    scraped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN NOT NULL DEFAULT 0,
    matches_keywords BOOLEAN NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);

-- Company career pages table
CREATE TABLE IF NOT EXISTS company_career_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name VARCHAR NOT NULL,
    url VARCHAR NOT NULL UNIQUE,
    scraper_type VARCHAR NOT NULL DEFAULT 'dynamic',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    last_scraped DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_company_career_pages_company_name ON company_career_pages(company_name);
