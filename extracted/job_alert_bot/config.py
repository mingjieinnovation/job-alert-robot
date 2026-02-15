"""
config.py - AI Job Alert Bot Configuration

Targets: Analyst roles + Product Manager in London
Excludes: Director+, Intern/Graduate, Contract, 6+ years experience
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
    "analyst London",
    "data analyst London",
    "product analyst London",
    "business analyst London",
    "insight analyst London",
    "product manager London",
    "associate product manager London",
    "junior product manager London",
    "senior analyst London",
]

LOCATION = "London"
COUNTRY = "gb"
MAX_RESULTS_PER_QUERY = 50
MAX_DAILY_JOBS = 25

# ============================================================
# Title Filters
# ============================================================

TITLE_MUST_CONTAIN = [
    "analyst",
    "product manager",
]

TOO_SENIOR_KEYWORDS = [
    "director", "VP", "vice president", "head of", "chief",
    "principal", "staff", "distinguished", "partner",
    "6+ years", "7+ years", "8+ years", "10+ years",
    "6 years", "7 years", "8 years", "10 years", "12 years", "15 years",
]

TOO_JUNIOR_KEYWORDS = [
    "intern", "internship", "graduate programme", "graduate program",
    "graduate scheme", "entry level trainee",
    "apprentice", "apprenticeship", "placement year",
    "IT ", "IT analyst", "summer",
]

ANALYST_EXCLUDE_PREFIXES = [
    "associate analyst", "junior analyst", "intern analyst",
    "associate data analyst", "junior data analyst",
    "associate product analyst", "junior product analyst",
    "associate business analyst", "junior business analyst",
    "associate insight analyst", "junior insight analyst",
]

IRRELEVANT_KEYWORDS = [
    "scientist", "data scientist", "research scientist",
    "engineer", "software engineer", "backend engineer", "frontend engineer",
    "DevOps engineer", "QA engineer", "test engineer",
    "C++ developer", "Java developer",
    "iOS developer", "Android developer",
    "accountant", "solicitor", "nurse", "warehouse", "driver",
]

CONTRACT_KEYWORDS = [
    "contract", "contractor", "freelance", "freelancer",
    "fixed term", "fixed-term", "temp ",
]

TITLE_EXCLUDE = TOO_SENIOR_KEYWORDS + TOO_JUNIOR_KEYWORDS + IRRELEVANT_KEYWORDS + ANALYST_EXCLUDE_PREFIXES

# ============================================================
# Description Filters
# ============================================================

DESCRIPTION_EXCLUDE_KEYWORDS = [
    "6+ years", "7+ years", "8+ years", "10+ years",
    "12+ years", "15+ years",
    "6 years experience", "7 years experience",
    "8 years experience", "10 years experience",
]

REQUIRE_AI_IN_DESCRIPTION = False

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
MIN_SALARY = 45000
MAX_SALARY = 0

# ============================================================
# Files
# ============================================================
SEEN_JOBS_FILE = "seen_jobs.json"
LOG_FILE = "job_alert.log"
