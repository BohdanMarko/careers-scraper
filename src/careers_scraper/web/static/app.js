// Careers Scraper Dashboard JavaScript

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

// Initialize dashboard
loadJobs();
loadStats();
setInterval(loadJobs, 30000); // Auto-refresh every 30 seconds
