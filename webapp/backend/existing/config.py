"""
config.py - AI Job Alert Bot Configuration (Legacy)
"""

import os

# ============================================================
# Email Configuration
# ============================================================
EMAIL_CONFIG = {
    "sender_email": os.environ.get("ALERT_SENDER_EMAIL", ""),
    "sender_password": os.environ.get("ALERT_SENDER_PASSWORD", ""),
    "recipient_email": os.environ.get("ALERT_RECIPIENT_EMAIL", ""),
    "smtp_server": "smtp-mail.outlook.com",
    "smtp_port": 587,
}

# ============================================================
# API Keys
# ============================================================
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
REED_API_KEY = os.environ.get("REED_API_KEY", "")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# ============================================================
# Search Queries
# ============================================================
SEARCH_QUERIES = [
    "product manager London",
    "product analyst London",
    "data analyst London",
    "growth analyst London",
    "senior product manager London",
    "senior product analyst London",
    "senior data analyst London",
    "product manager AI",
    "product analyst GenAI",
    "data analyst machine learning",
]

LOCATION = "London"
COUNTRY = "gb"
MAX_RESULTS_PER_QUERY = 50
MAX_DAILY_JOBS = 25

# ============================================================
# Title Filters
# ============================================================

TITLE_MUST_CONTAIN = [
    "product", "analyst", "analytics", "data", "insight",
    "strategy", "research", "growth", "UX", "delivery",
    "operations", "success manager",
]

TOO_SENIOR_KEYWORDS = [
    "director", "VP", "vice president", "head of", "chief",
    "principal", "staff", "distinguished", "partner",
    "10+ years", "10 years", "15 years", "12 years",
]

TOO_JUNIOR_KEYWORDS = [
    "intern", "internship", "graduate programme", "graduate program",
    "graduate scheme", "entry level trainee",
    "apprentice", "apprenticeship", "placement year",
]

IRRELEVANT_KEYWORDS = [
    "C++ developer", "Java developer", "DevOps engineer",
    "backend engineer", "frontend engineer",
    "iOS developer", "Android developer",
    "QA engineer", "test engineer", "accountant",
    "solicitor", "nurse", "warehouse", "driver",
]

TITLE_EXCLUDE = TOO_SENIOR_KEYWORDS + TOO_JUNIOR_KEYWORDS + IRRELEVANT_KEYWORDS

# ============================================================
# Description Filters
# ============================================================

DESCRIPTION_WARNING_KEYWORDS = [
    "6+ years", "7+ years", "8+ years", "10+ years",
    "12+ years", "15+ years",
    "senior leadership", "P&L responsibility",
    "managing a team of 10+",
]

DESCRIPTION_BOOST_KEYWORDS = [
    "1-3 years", "1+ years", "2+ years", "2-3 years",
    "3-5 years", "3+ years", "4+ years", "2-5 years",
    "product analytics", "user research", "KPI",
    "Power BI", "Tableau", "SQL", "Python",
    "data-driven", "insight", "A/B test",
    "cross-functional", "agile", "scrum",
    "AI", "GenAI", "LLM", "machine learning",
    "generative AI", "NLP", "deep learning", "agentic",
    "GPT", "large language model", "computer vision",
    "Alteryx", "dashboard", "go-to-market",
]

# ============================================================
# Salary
# ============================================================
MIN_SALARY = 0
MAX_SALARY = 0

# ============================================================
# Files
# ============================================================
SEEN_JOBS_FILE = "seen_jobs.json"
LOG_FILE = "job_alert.log"
