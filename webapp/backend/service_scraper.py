"""Job scraper service - calls real APIs directly using user keywords."""

import os
import re
import json
import logging
import time
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timezone
from base64 import b64encode

from models import db, JobRecord, SearchSession

logger = logging.getLogger(__name__)

# API keys from environment variables
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

LOCATION = "London"
COUNTRY = "gb"
MAX_RESULTS_PER_QUERY = 50
MIN_SALARY = 45000  # Minimum annual salary £45,000

# Title filters - target roles
TITLE_MUST_CONTAIN = [
    "analyst",  # any role containing analyst
    "product manager",  # includes associate/junior/senior product manager
]

TITLE_EXCLUDE = [
    "scientist", "data scientist", "research scientist",
    "engineer", "software engineer", "backend engineer", "frontend engineer",
    "DevOps engineer", "QA engineer", "test engineer",
    "director", "VP", "vice president", "head of", "chief",
    "principal", "staff", "distinguished", "partner",
    "6+ years", "7+ years", "8+ years", "10+ years",
    "6 years", "7 years", "8 years", "10 years", "12 years", "15 years",
    "intern", "internship", "graduate programme", "graduate program",
    "graduate scheme", "entry level trainee",
    "apprentice", "apprenticeship", "placement year",
    "C++ developer", "Java developer",
    "iOS developer", "Android developer",
    "accountant", "solicitor", "nurse", "warehouse", "driver",
    "IT ", "IT analyst", "summer",
    # Training / bootcamp posts (not real jobs)
    "job guarantee", "bootcamp", "training programme", "course",
    # Analyst roles: exclude associate/junior/intern prefix
    "associate analyst", "junior analyst", "intern analyst",
    "associate data analyst", "junior data analyst",
    "associate product analyst", "junior product analyst",
    "associate business analyst", "junior business analyst",
    "associate insight analyst", "junior insight analyst",
]

# Contract job keywords
CONTRACT_KEYWORDS = [
    "contract", "contractor", "freelance", "freelancer",
    "fixed term", "fixed-term", "temp ",
    "FTC", "ftc", " month ftc", "month contract",
    "6 month", "12 month", "3 month", "9 month",
    "maternity cover", "paternity cover", "temporary",
    "interim", "inside ir35", "outside ir35", "day rate", "ir35",
]

# Language requirements to exclude (keep only Chinese/English roles)
LANGUAGE_EXCLUDE = [
    "french", "german", "spanish", "italian", "portuguese",
    "dutch", "japanese", "korean", "arabic", "russian",
    "turkish", "polish", "hindi", "swedish", "norwegian",
    "danish", "finnish", "greek", "hebrew", "czech",
    "hungarian", "romanian", "thai", "vietnamese",
    "mandarin speaker", "cantonese speaker",
]


def _clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or "")


def _passes_title_filter(title: str) -> bool:
    t = title.lower()
    if TITLE_MUST_CONTAIN:
        if not any(kw.lower() in t for kw in TITLE_MUST_CONTAIN):
            return False
    if TITLE_EXCLUDE:
        if any(kw.lower() in t for kw in TITLE_EXCLUDE):
            return False
    # Exclude contract jobs from title
    for kw in CONTRACT_KEYWORDS:
        if kw.lower() in t:
            return False
    # Exclude jobs requiring non-Chinese/English languages in title
    for lang in LANGUAGE_EXCLUDE:
        if lang.lower() in t:
            return False
    return True


def _is_contract_job(text: str) -> bool:
    """Check if text indicates a contract role."""
    t = f" {text.lower()} "
    for kw in CONTRACT_KEYWORDS:
        if kw.lower() in t:
            return True
    if re.search(r'\b(contract|contractor|ftc)\b', t):
        return True
    if re.search(r'\d+[\s-]?months?\s*(contract|ftc|fixed)', t):
        return True
    # "Duration: 6 months"
    if re.search(r'duration[:\s]+\d+\s*months?', t):
        return True
    # "X month role/position/assignment"
    if re.search(r'\d+[\s-]?months?\s*(role|position|assignment|placement|engagement)', t):
        return True
    return False


def _requires_other_language(text: str) -> bool:
    """Check if job requires a language other than Chinese/English."""
    t = text.lower()
    for lang in LANGUAGE_EXCLUDE:
        if lang.lower() in t:
            return True
    return False


# Default job-title search queries (always used as the base)
# NOTE: First 5 are sent to LinkedIn (rate-limited) - keep the most important ones here
DEFAULT_SEARCH_QUERIES = [
    "product manager London",
    "analyst London",
    "data analyst London",
    "product analyst London",
    "business analyst London",
    "associate product manager London",
    "insight analyst London",
    "junior product manager London",
    "senior analyst London",
]

# Keywords that represent job roles (worth combining into search queries)
ROLE_KEYWORDS = {
    "analyst", "data analyst", "product analyst",
    "business analyst", "insight analyst",
    "product manager", "associate product manager",
    "junior product manager",
}


def _build_search_queries(keywords: list[dict]) -> list[str]:
    """Build search queries using default job-title queries + role keywords from user.

    Resume skill keywords (sql, python, tableau etc.) are NOT used as search queries
    — they're only used for scoring. Only job-role keywords get added as queries.
    """
    queries = list(DEFAULT_SEARCH_QUERIES)

    # Check if user has any role-type keywords worth adding as extra queries
    boost_kws = [k["keyword"] for k in keywords if k.get("category") == "boost"]
    for kw in boost_kws:
        if kw.lower() in ROLE_KEYWORDS:
            q = f"{kw} London"
            if q not in queries:
                queries.append(q)

    return queries[:12]  # Cap at 12 queries


def _make_unique_key(source: str, job_id: str, title: str, company: str) -> str:
    if job_id:
        return f"{source}_{job_id}"
    clean_title = re.sub(r'[^a-z0-9]', '', title.lower())
    clean_company = re.sub(r'[^a-z0-9]', '', company.lower())
    return f"{source}_{clean_company}_{clean_title}"


# ============================================================
# Adzuna API
# ============================================================

def fetch_adzuna(queries: list[str]) -> list[dict]:
    """Fetch jobs from Adzuna API."""
    all_jobs = []
    base_url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"

    for query in queries:
        try:
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "what": query,
                "where": LOCATION,
                "results_per_page": min(MAX_RESULTS_PER_QUERY, 50),
                "max_days_old": 7,
                "sort_by": "date",
                "content-type": "application/json",
            }
            if MIN_SALARY > 0:
                params["salary_min"] = MIN_SALARY

            resp = requests.get(base_url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            count = 0
            for item in data.get("results", []):
                title = item.get("title", "")
                if not _passes_title_filter(title):
                    continue

                salary = ""
                sal_min = item.get("salary_min")
                sal_max = item.get("salary_max")
                if sal_min and sal_max:
                    salary = f"£{int(sal_min):,} - £{int(sal_max):,}"
                elif sal_min:
                    salary = f"From £{int(sal_min):,}"

                job_id = str(item.get("id", ""))
                all_jobs.append({
                    "title": title,
                    "company": item.get("company", {}).get("display_name", "Unknown"),
                    "location": item.get("location", {}).get("display_name", LOCATION),
                    "url": item.get("redirect_url", ""),
                    "source": "adzuna",
                    "salary": salary,
                    "description": _clean_html(item.get("description", ""))[:500],
                    "posted_date": item.get("created", "")[:10],
                    "job_id": job_id,
                    "unique_key": _make_unique_key("adzuna", job_id, title,
                                                    item.get("company", {}).get("display_name", "")),
                })
                count += 1

            logger.info(f"  Adzuna [{query}]: {count} jobs passed filter")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"  Adzuna [{query}] failed: {e}")

    return all_jobs


# ============================================================
# LinkedIn (public job listings)
# ============================================================

def fetch_linkedin(queries: list[str]) -> list[dict]:
    """Fetch jobs from LinkedIn public listings."""
    all_jobs = []
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    # Use fewer queries for LinkedIn (rate sensitive)
    linkedin_queries = queries[:7]

    for query in linkedin_queries:
        try:
            params = {
                "keywords": query,
                "location": "London, United Kingdom",
                "f_TPR": "r604800",
                "start": 0,
                "count": min(MAX_RESULTS_PER_QUERY, 50),
            }

            resp = requests.get(base_url, params=params, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"  LinkedIn [{query}]: HTTP {resp.status_code}")
                continue

            html = resp.text
            count = 0

            title_pattern = re.compile(
                r'<h3[^>]*class="[^"]*base-search-card__title[^"]*"[^>]*>\s*(.*?)\s*</h3>', re.DOTALL)
            company_pattern = re.compile(
                r'<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>\s*(.*?)\s*</h4>', re.DOTALL)
            location_pattern = re.compile(
                r'<span[^>]*class="[^"]*job-search-card__location[^"]*"[^>]*>\s*(.*?)\s*</span>', re.DOTALL)
            link_pattern = re.compile(
                r'<a[^>]*class="[^"]*base-card__full-link[^"]*"[^>]*href="([^"]*)"', re.DOTALL)
            date_pattern = re.compile(r'<time[^>]*datetime="([^"]*)"', re.DOTALL)

            titles = title_pattern.findall(html)
            companies = company_pattern.findall(html)
            locations = location_pattern.findall(html)
            links = link_pattern.findall(html)
            dates = date_pattern.findall(html)

            num_jobs = min(len(titles), len(companies), len(links))

            for i in range(num_jobs):
                title = _clean_html(titles[i]).strip()
                if not _passes_title_filter(title):
                    continue

                company = _clean_html(companies[i]).strip() if i < len(companies) else "Unknown"
                location = _clean_html(locations[i]).strip() if i < len(locations) else "London"
                url = links[i].split("?")[0] if i < len(links) else ""
                posted = dates[i][:10] if i < len(dates) else ""

                job_id_match = re.search(r'/view/[^/]*-(\d+)', url)
                jid = job_id_match.group(1) if job_id_match else ""

                all_jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "source": "linkedin",
                    "salary": "",
                    "description": "",
                    "posted_date": posted,
                    "job_id": jid,
                    "unique_key": _make_unique_key("linkedin", jid, title, company),
                })
                count += 1

            logger.info(f"  LinkedIn [{query}]: {count} jobs passed filter")
            time.sleep(2)

        except Exception as e:
            logger.error(f"  LinkedIn [{query}] failed: {e}")

    return all_jobs


# ============================================================
# Google Jobs (via SerpAPI)
# ============================================================

def fetch_google_jobs(queries: list[str]) -> list[dict]:
    """Fetch jobs from Google Jobs via SerpAPI."""
    if SERPAPI_KEY == "YOUR_SERPAPI_KEY":
        logger.warning("  SerpAPI not configured, skipping Google Jobs")
        return []

    all_jobs = []
    base_url = "https://serpapi.com/search.json"

    # Limit queries to save API quota
    google_queries = queries[:3]

    for query in google_queries:
        try:
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": "London, United Kingdom",
                "api_key": SERPAPI_KEY,
                "chips": "date_posted:week",
                "num": min(MAX_RESULTS_PER_QUERY, 50),
            }

            resp = requests.get(base_url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            count = 0
            for item in data.get("jobs_results", []):
                title = item.get("title", "")
                if not _passes_title_filter(title):
                    continue

                desc = item.get("description", "")[:500]
                salary = ""
                detected = item.get("detected_extensions", {})
                if detected.get("salary"):
                    salary = detected["salary"]

                url = ""
                apply_options = item.get("apply_options", [])
                if apply_options:
                    url = apply_options[0].get("link", "")

                posted = detected.get("posted_at", "")
                job_id = item.get("job_id", "")
                company = item.get("company_name", "Unknown")

                all_jobs.append({
                    "title": title,
                    "company": company,
                    "location": item.get("location", "London"),
                    "url": url,
                    "source": "google_jobs",
                    "salary": salary,
                    "description": desc,
                    "posted_date": posted,
                    "job_id": job_id,
                    "unique_key": _make_unique_key("google_jobs", job_id, title, company),
                })
                count += 1

            logger.info(f"  Google Jobs [{query}]: {count} jobs passed filter")
            time.sleep(1)

        except Exception as e:
            logger.error(f"  Google Jobs [{query}] failed: {e}")

    return all_jobs


# ============================================================
# X/Twitter (RSS Bridge)
# ============================================================

def fetch_x_twitter() -> list[dict]:
    """Fetch job posts from X/Twitter via RSS Bridge."""
    all_jobs = []

    x_queries = [
        '"hiring" "London" (analyst OR "product manager")',
        '"data analyst" "London" hiring',
        '"product manager" "London" hiring',
        'from:AIJobAlert analyst London',
    ]

    rss_bridges = [
        "https://rss-bridge.org/bridge01",
        "https://rss-bridge.bb8.fun",
    ]

    for query in x_queries:
        fetched = False
        for bridge in rss_bridges:
            if fetched:
                break
            try:
                params = {
                    "action": "display",
                    "bridge": "TwitterBridge",
                    "context": "By+keyword",
                    "q": query,
                    "format": "Mrss",
                }
                resp = requests.get(f"{bridge}/", params=params, timeout=15,
                                    headers={"User-Agent": "JobAlertBot/1.0"})
                if resp.status_code != 200:
                    continue

                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:5]:
                    title_el = item.find('title')
                    link_el = item.find('link')
                    desc_el = item.find('description')

                    if title_el is None or link_el is None:
                        continue

                    text = title_el.text or ""
                    if not any(kw in text.lower() for kw in
                               ['hiring', 'job', 'role', 'position', 'vacancy', 'looking for']):
                        continue
                    if any(kw in text.lower() for kw in ['intern', 'director', 'vp', 'head of']):
                        continue

                    link = link_el.text or ""
                    desc = _clean_html(desc_el.text if desc_el is not None else "")[:300]

                    all_jobs.append({
                        "title": f"[X] {text[:120]}",
                        "company": "(via X/Twitter)",
                        "location": "London",
                        "url": link,
                        "source": "x_twitter",
                        "salary": "",
                        "description": desc,
                        "posted_date": "",
                        "job_id": link,
                        "unique_key": _make_unique_key("x_twitter", link, text[:120], "x_twitter"),
                    })

                fetched = True
                logger.info(f"  X [{query[:35]}...]: success")
            except Exception:
                continue

        if not fetched:
            logger.debug(f"  X [{query[:35]}...]: unavailable")
        time.sleep(1)

    return all_jobs


# ============================================================
# Jungle (formerly Otta / Welcome to the Jungle)
# ============================================================

JUNGLE_ALGOLIA_APP_ID = os.environ.get("JUNGLE_ALGOLIA_APP_ID", "")
JUNGLE_ALGOLIA_API_KEY = os.environ.get("JUNGLE_ALGOLIA_API_KEY", "")
JUNGLE_ALGOLIA_INDEX = os.environ.get("JUNGLE_ALGOLIA_INDEX", "wttj_jobs_production_en")


def fetch_jungle() -> list[dict]:
    """Fetch jobs from Jungle (Welcome to the Jungle) via Algolia search."""
    all_jobs = []

    jungle_queries = ["data analyst", "product analyst", "business analyst",
                      "product manager", "insight analyst"]

    for query in jungle_queries:
        try:
            url = f"https://{JUNGLE_ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{JUNGLE_ALGOLIA_INDEX}/query"
            headers = {
                "x-algolia-application-id": JUNGLE_ALGOLIA_APP_ID,
                "x-algolia-api-key": JUNGLE_ALGOLIA_API_KEY,
                "Content-Type": "application/json",
                "Referer": "https://www.welcometothejungle.com/",
            }
            payload = {
                "query": query,
                "hitsPerPage": 20,
                "filters": "offices.country_code:GB",
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"  Jungle [{query}]: HTTP {resp.status_code}")
                continue

            data = resp.json()
            count = 0
            for hit in data.get("hits", []):
                title = hit.get("name", "")
                if not _passes_title_filter(title):
                    continue

                # Check for London office
                offices = hit.get("offices", [])
                location_parts = []
                has_london = False
                for office in offices:
                    city = office.get("city", "")
                    if "london" in city.lower():
                        has_london = True
                    location_parts.append(city)
                if not has_london:
                    continue

                location = ", ".join(location_parts) if location_parts else "London"
                org = hit.get("organization", {})
                company_name = org.get("name", "Unknown")
                slug = hit.get("slug", "")
                org_slug = org.get("slug", "")
                job_id = hit.get("reference", hit.get("objectID", ""))
                job_url = f"https://www.welcometothejungle.com/en/companies/{org_slug}/jobs/{slug}" if org_slug and slug else ""

                salary = ""
                sal_min = hit.get("salary_minimum") or hit.get("salary_yearly_minimum")
                sal_max = hit.get("salary_maximum")
                sal_currency = hit.get("salary_currency", "")
                if sal_min:
                    sym = "£" if sal_currency == "GBP" else ("€" if sal_currency == "EUR" else sal_currency)
                    if sal_max:
                        salary = f"{sym}{int(sal_min):,} - {sym}{int(sal_max):,}"
                    else:
                        salary = f"From {sym}{int(sal_min):,}"

                desc = (hit.get("summary", "") or "")[:500]
                posted = hit.get("published_at_date", "")

                all_jobs.append({
                    "title": title,
                    "company": company_name,
                    "location": location,
                    "url": job_url,
                    "source": "jungle",
                    "salary": salary,
                    "description": desc,
                    "posted_date": posted,
                    "job_id": job_id,
                    "unique_key": _make_unique_key("jungle", job_id, title, company_name),
                })
                count += 1

            logger.info(f"  Jungle [{query}]: {count} jobs passed filter")
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"  Jungle [{query}] failed: {e}")

    return all_jobs


# ============================================================
# Main entry point
# ============================================================

def fetch_and_store_jobs(keywords: list[dict]) -> dict:
    """Fetch jobs from all sources, score with user keywords, and store in DB."""
    from service_scoring import score_job

    queries = _build_search_queries(keywords)
    logger.info(f"Starting job search with queries: {queries}")

    # Fetch from all sources
    all_raw_jobs = []

    logger.info("--- Fetching from Adzuna ---")
    try:
        adzuna_jobs = fetch_adzuna(queries)
        all_raw_jobs.extend(adzuna_jobs)
        logger.info(f"  Adzuna total: {len(adzuna_jobs)}")
    except Exception as e:
        logger.error(f"  Adzuna source failed: {e}")

    logger.info("--- Fetching from LinkedIn ---")
    try:
        linkedin_jobs = fetch_linkedin(queries)
        all_raw_jobs.extend(linkedin_jobs)
        logger.info(f"  LinkedIn total: {len(linkedin_jobs)}")
    except Exception as e:
        logger.error(f"  LinkedIn source failed: {e}")

    logger.info("--- Fetching from Google Jobs ---")
    try:
        google_jobs = fetch_google_jobs(queries)
        all_raw_jobs.extend(google_jobs)
        logger.info(f"  Google Jobs total: {len(google_jobs)}")
    except Exception as e:
        logger.error(f"  Google Jobs source failed: {e}")

    logger.info("--- Fetching from X/Twitter ---")
    try:
        x_jobs = fetch_x_twitter()
        all_raw_jobs.extend(x_jobs)
        logger.info(f"  X/Twitter total: {len(x_jobs)}")
    except Exception as e:
        logger.error(f"  X/Twitter source failed: {e}")

    logger.info("--- Fetching from Jungle ---")
    try:
        jungle_jobs = fetch_jungle()
        all_raw_jobs.extend(jungle_jobs)
        logger.info(f"  Jungle total: {len(jungle_jobs)}")
    except Exception as e:
        logger.error(f"  Jungle source failed: {e}")

    logger.info(f"Total fetched from all sources: {len(all_raw_jobs)}")

    # Cross-source deduplication: same title+company OR same description = same job
    def _dedup_key(title: str, company: str) -> str:
        t = re.sub(r'[^a-z0-9]', '', title.lower())
        c = re.sub(r'[^a-z0-9]', '', company.lower())
        return f"{c}_{t}"

    def _desc_fingerprint(description: str) -> str | None:
        """First 200 chars of description, normalised. None if description too short."""
        fp = re.sub(r'\s+', ' ', (description or "").lower().strip())[:200]
        return fp if len(fp) >= 50 else None  # ignore very short/empty descriptions

    seen_dedup = {}   # title+company key -> job_data
    seen_desc = {}    # description fingerprint -> job_data
    dedup_count = 0
    for job_data in all_raw_jobs:
        dk = _dedup_key(job_data["title"], job_data["company"])
        fp = _desc_fingerprint(job_data.get("description", ""))

        # Check duplicate by title+company
        if dk in seen_dedup:
            existing = seen_dedup[dk]
            if (not existing.get("salary") and job_data.get("salary")) or \
               (not existing.get("description") and job_data.get("description")):
                seen_dedup[dk] = job_data
                if fp:
                    seen_desc[fp] = job_data
            dedup_count += 1
            continue

        # Check duplicate by description fingerprint (same job, different title)
        if fp and fp in seen_desc:
            dedup_count += 1
            continue

        seen_dedup[dk] = job_data
        if fp:
            seen_desc[fp] = job_data

    all_raw_jobs = list(seen_dedup.values())
    if dedup_count:
        logger.info(f"  Cross-source dedup removed {dedup_count} duplicates, {len(all_raw_jobs)} unique jobs remain")

    # Create search session
    boost_kws = [k["keyword"] for k in keywords if k.get("category") == "boost"]
    sources_used = ",".join(set(j["source"] for j in all_raw_jobs)) if all_raw_jobs else ""
    session = SearchSession(
        query_text=json.dumps(boost_kws),
        total_results=0,
        sources=sources_used,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(session)
    db.session.flush()

    # Score and store
    boost_keywords = [{"keyword": k["keyword"], "weight": k.get("weight", 1.0)}
                      for k in keywords if k.get("category") == "boost"]
    exclude_keywords = [{"keyword": k["keyword"], "weight": k.get("weight", 2.0)}
                        for k in keywords if k.get("category") == "exclude"]

    # Pre-load existing dedup keys and description fingerprints from DB
    existing_dedup_keys = set()
    existing_desc_fps = set()
    for row in JobRecord.query.with_entities(JobRecord.title, JobRecord.company, JobRecord.description).all():
        dk = _dedup_key(row.title or "", row.company or "")
        existing_dedup_keys.add(dk)
        fp = _desc_fingerprint(row.description or "")
        if fp:
            existing_desc_fps.add(fp)

    new_count = 0
    seen_keys = set()
    for job_data in all_raw_jobs:
        unique_key = job_data["unique_key"]

        # Skip duplicates within batch (same source/id)
        if unique_key in seen_keys:
            continue
        seen_keys.add(unique_key)

        # Skip if already in DB by unique_key (exact match)
        existing = JobRecord.query.filter_by(unique_key=unique_key).first()
        if existing:
            continue

        # Skip cross-source duplicates: same title+company already stored from another source
        dk = _dedup_key(job_data["title"], job_data["company"])
        if dk in existing_dedup_keys:
            continue

        # Skip description duplicates: same job listed twice with different titles
        fp = _desc_fingerprint(job_data.get("description", ""))
        if fp and fp in existing_desc_fps:
            continue

        existing_dedup_keys.add(dk)
        if fp:
            existing_desc_fps.add(fp)

        # Score (include salary in the text for salary filtering)
        scored = score_job(
            {"title": job_data["title"],
             "description": job_data.get("description", ""),
             "salary": job_data.get("salary", "")},
            boost_keywords,
            exclude_keywords,
        )

        # Skip jobs that fail hard filters (no AI mention or >5yr experience)
        if scored["match_score"] <= -99:
            continue

        record = JobRecord(
            job_id=job_data["job_id"],
            source=job_data["source"],
            unique_key=unique_key,
            title=job_data["title"],
            company=job_data["company"],
            location=job_data["location"],
            salary=job_data.get("salary", ""),
            url=job_data["url"],
            description=job_data.get("description", ""),
            posted_date=job_data.get("posted_date", ""),
            match_score=scored["match_score"],
            match_tags=scored["match_tags"],
            experience_ok=scored["experience_ok"],
            search_session_id=session.id,
            first_seen_at=datetime.now(timezone.utc),
        )
        db.session.add(record)
        new_count += 1

    session.total_results = new_count
    db.session.commit()

    logger.info(f"Stored {new_count} new jobs (out of {len(all_raw_jobs)} fetched)")

    return {
        "session_id": session.id,
        "new_count": new_count,
        "total_fetched": len(all_raw_jobs),
    }
