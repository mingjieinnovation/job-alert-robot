# Job Alert Robot

An AI-powered job search automation system that scrapes jobs from 6 sources, scores them against your profile, learns from your feedback, and helps you track applications — all through an interactive web dashboard.

## What It Does

```
Resume Upload → Keyword Extraction → Multi-Source Job Search → Smart Scoring
     ↓                                                              ↓
Keyword Learning ← User Feedback (Apply/Dismiss) ← Job Review ← Ranked Results
```

**Data Sources**: Adzuna, Reed, LinkedIn, Google Jobs, X/Twitter, Welcome to the Jungle

**Smart Filtering**: Title rules, salary minimum, experience level, contract detection, language requirements

**Scoring**: Boost/exclude keywords with adjustable weights, AI role bonuses, experience matching

**Learning Loop**: Dismiss a job → system suggests exclude keywords. Apply to a job → system suggests boost keywords. Retrain → weights adjust based on your history.

## Project Structure

```
job-alert-robot/
├── webapp/
│   ├── backend/          # Flask REST API + SQLite
│   │   ├── app.py                    # Flask app setup
│   │   ├── models.py                 # Database schema (7 tables)
│   │   ├── service_scraper.py        # 6-source job scraper
│   │   ├── service_scoring.py        # Hard/soft scoring engine
│   │   ├── service_resume.py         # PDF parsing + keyword extraction
│   │   ├── service_learning.py       # Weight retraining from feedback
│   │   ├── service_feedback_learning.py  # Keyword suggestions on actions
│   │   ├── service_jd_analysis.py    # Job description analyzer
│   │   ├── api_jobs.py               # Search & list jobs
│   │   ├── api_applications.py       # Application tracking + learning
│   │   ├── api_keywords.py           # Keyword CRUD
│   │   ├── api_resume.py             # Resume upload
│   │   ├── api_filters.py            # Search filter management
│   │   ├── api_analytics.py          # Insights & retraining
│   │   └── api_jd_analysis.py        # JD analysis
│   └── frontend/         # React SPA
│       └── src/
│           ├── App.jsx               # Router & navigation
│           ├── api.js                # Axios API client
│           ├── pages/
│           │   ├── HomePage.jsx      # Resume + keywords + JD analyzer
│           │   ├── SearchPage.jsx    # Job search with 3 tabs
│           │   ├── JobDetailPage.jsx # Full job view + actions + keyword picker
│           │   ├── ApplicationsPage.jsx  # Kanban board
│           │   ├── FiltersPage.jsx   # Customize search filters
│           │   └── AnalyticsPage.jsx # Keyword performance & retraining
│           └── components/
│               ├── JobCard.jsx       # Job preview card
│               ├── JobList.jsx       # Job card list
│               ├── KeywordManager.jsx # Boost/exclude keyword chips
│               ├── ResumeUploader.jsx # PDF upload
│               ├── JDAnalyzer.jsx    # JD paste & analysis
│               ├── StatusBadge.jsx   # Status color badge
│               └── FeedbackForm.jsx  # Application feedback
├── extracted/
│   └── job_alert_bot/    # Standalone CLI bot (daily email alerts)
│       ├── main.py       # Orchestrator: fetch → dedup → email
│       ├── scrapers.py   # 5-source scraper + scoring
│       ├── config.py     # Search queries, filters, API keys
│       ├── dedup.py      # 30-day rolling dedup (JSON)
│       └── emailer.py    # HTML email builder + SMTP sender
├── .env.example          # Template for API keys
└── README.md
```

## Quick Start

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/lovepsycandgame/job-alert-robot.git
cd job-alert-robot

# Copy and fill in your API keys
cp .env.example .env
# Edit .env with your keys
```

### 2. Get API Keys (Free)

| API | Sign Up | Free Tier |
|-----|---------|-----------|
| [Adzuna](https://developer.adzuna.com/signup) | Developer portal | 250 calls/day |
| [Reed](https://www.reed.co.uk/developers/jobseeker) | Developer page | Unlimited |
| [SerpAPI](https://serpapi.com/manage-api-key) | Dashboard | 100 searches/month |

LinkedIn, X/Twitter, and Welcome to the Jungle scrapers don't require API keys.

### 3. Start the Web App

**Backend:**
```bash
cd webapp/backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
```

**Frontend:**
```bash
cd webapp/frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 4. Usage Flow

1. **Upload your resume** (Home page) → extracts boost keywords automatically
2. **Add/edit keywords** → fine-tune what to boost or exclude
3. **Search for jobs** (Search page) → fetches from 6 sources, scores & ranks
4. **Review jobs** → click to see details, mark as "Applied" or "Not Interested"
5. **Learn from feedback** → system suggests keywords to add based on your actions
6. **Retrain** (Analytics page) → adjusts keyword weights from your history

## Standalone Email Bot

For daily email alerts without the web app:

```bash
cd extracted/job_alert_bot
pip install requests
python main.py --test   # Test without sending email
python main.py          # Send email alert
```

Schedule with cron (Linux/Mac) or Task Scheduler (Windows) for daily runs.

## Tech Stack

- **Backend**: Flask, SQLAlchemy, SQLite, PyPDF2, spaCy
- **Frontend**: React 18, React Router, Axios, Vite
- **Scraping**: Requests, Algolia API, SerpAPI, RSS parsing

## License

MIT
