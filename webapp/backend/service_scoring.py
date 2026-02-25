"""Adaptive job scoring using user keywords and learned weights.

Hard filters:
- Exclude jobs requiring more than 5 years experience
- Exclude contract/freelance jobs
"""

import re
import json
import logging

logger = logging.getLogger(__name__)

# Experience keywords that indicate >5 years required
EXPERIENCE_EXCLUDE = [
    "6+ years", "7+ years", "8+ years", "10+ years",
    "12+ years", "15+ years",
    "6 years experience", "7 years experience",
    "8 years experience", "10 years experience",
]

# Contract keywords
CONTRACT_KEYWORDS = [
    "contract", "contractor", "freelance", "freelancer",
    "fixed term", "fixed-term", "temporary",
    "ftc", " month ftc", "month contract",
    "6 month", "12 month", "3 month", "9 month",
    "maternity cover", "paternity cover",
    "interim", "inside ir35", "outside ir35", "day rate", "ir35",
]

# Language requirements to exclude
LANGUAGE_EXCLUDE = [
    "french", "german", "spanish", "italian", "portuguese",
    "dutch", "japanese", "korean", "arabic", "russian",
    "turkish", "polish", "hindi", "swedish", "norwegian",
    "danish", "finnish", "greek", "hebrew", "czech",
    "hungarian", "romanian", "thai", "vietnamese",
]


def _exceeds_max_experience(text: str, max_years: int = 5) -> bool:
    """Check if description requires more than max_years experience."""
    for kw in EXPERIENCE_EXCLUDE:
        if kw in text:
            return True
    years_match = re.findall(r'(\d+)\+?\s*years?', text)
    for y in years_match:
        if int(y) > max_years:
            return True
    return False


def _is_contract_job(text: str) -> bool:
    """Check if text indicates a contract role."""
    for kw in CONTRACT_KEYWORDS:
        if kw in text:
            return True
    if re.search(r'\b(contract|contractor|ftc)\b', text):
        return True
    # "6 month contract/ftc/fixed"
    if re.search(r'\d+[\s-]?months?\s*(contract|ftc|fixed)', text):
        return True
    # "Duration: 6 months" or "duration: 12 months"
    if re.search(r'duration[:\s]+\d+\s*months?', text):
        return True
    # "X month role/position/assignment/placement"
    if re.search(r'\d+[\s-]?months?\s*(role|position|assignment|placement|engagement)', text):
        return True
    return False


def _requires_other_language(text: str) -> bool:
    """Check if job requires a language other than Chinese/English."""
    for lang in LANGUAGE_EXCLUDE:
        if lang in text:
            return True
    return False


def _get_filters():
    """Load filter settings from DB (with fallback to defaults)."""
    try:
        from api_filters import get_all_filters
        return get_all_filters()
    except Exception:
        return {
            "min_salary": 45000,
            "max_experience_years": 5,
            "contract_keywords": CONTRACT_KEYWORDS,
            "language_exclude": LANGUAGE_EXCLUDE,
        }


def _salary_below_minimum(text: str, min_salary: int = 45000) -> bool:
    """Check if a stated salary is below the minimum threshold.

    For salary ranges like '£24,000 - £35,000', filters if the highest
    value in the range is still below the minimum.
    """
    # Match patterns like £30,000, £30000, £30k
    matches = re.findall(r'£\s*([\d,]+)\s*(?:k|K)?', text)
    if not matches:
        return False

    # Parse all salary values found
    salaries = []
    for m in matches:
        val = int(m.replace(',', ''))
        if val < 1000:
            val *= 1000
        # Only consider values that look like annual salaries
        if 15000 <= val <= 500000:
            salaries.append(val)

    if not salaries:
        return False

    # If the highest salary in the text is below minimum, filter it out
    max_salary = max(salaries)
    return max_salary < min_salary


def score_job(job_dict: dict, boost_keywords: list, exclude_keywords: list) -> dict:
    """Score a job using user-defined keywords with weights.

    Hard filters applied first:
    - Must not require >5 years experience -> score -99 if exceeds
    - Must not be a contract role -> score -99 if contract
    - Salary must be >= £45,000 if stated

    Args:
        job_dict: dict with title, description, etc.
        boost_keywords: list of {"keyword": str, "weight": float}
        exclude_keywords: list of {"keyword": str, "weight": float}

    Returns:
        Updated job_dict with match_score, match_tags, experience_ok.
    """
    text = (job_dict.get("title", "") + " " + job_dict.get("description", "") + " " + job_dict.get("salary", "")).lower()
    score = 0.0
    tags = []
    experience_ok = True

    # Load dynamic filters from DB
    filters = _get_filters()

    # Hard filter: salary below minimum
    if _salary_below_minimum(text, filters.get("min_salary", 45000)):
        job_dict["match_score"] = -99
        job_dict["match_tags"] = json.dumps(["❌salary <£45k"])
        job_dict["experience_ok"] = False
        return job_dict

    # Hard filter: no contract jobs
    if _is_contract_job(text):
        job_dict["match_score"] = -99
        job_dict["match_tags"] = json.dumps(["❌contract"])
        job_dict["experience_ok"] = False
        return job_dict

    # Hard filter: no non-Chinese/English language requirements
    if _requires_other_language(text):
        job_dict["match_score"] = -99
        job_dict["match_tags"] = json.dumps(["❌language requirement"])
        job_dict["experience_ok"] = False
        return job_dict

    # Hard filter: no more than 5 years experience required
    if _exceeds_max_experience(text):
        job_dict["match_score"] = -99
        job_dict["match_tags"] = json.dumps(["❌>5yr experience"])
        job_dict["experience_ok"] = False
        return job_dict

    # Boost keywords
    for kw_data in boost_keywords:
        kw = kw_data["keyword"].lower()
        weight = kw_data.get("weight", 1.0)
        if kw in text:
            score += weight
            tags.append(f"⭐{kw_data['keyword']}")

    # Exclude / warning keywords
    for kw_data in exclude_keywords:
        kw = kw_data["keyword"].lower()
        weight = kw_data.get("weight", 2.0)
        if kw in text:
            score -= weight
            tags.append(f"⚠️{kw_data['keyword']}")
            experience_ok = False

    # AI bonus (not required, but still a positive signal)
    if any(kw in text for kw in ["genai", "generative ai", "llm", "agentic"]):
        score += 2
        tags.append("🤖AI")
    elif " ai " in f" {text} " or "artificial intelligence" in text:
        score += 1
        tags.append("🤖AI")

    # Experience year detection (bonus for <=5 years)
    years_match = re.findall(r'(\d+)\+?\s*years?', text)
    for y in years_match:
        yr = int(y)
        if yr <= 5:
            score += 1

    job_dict["match_score"] = round(score, 2)
    job_dict["match_tags"] = json.dumps(tags)
    job_dict["experience_ok"] = experience_ok
    return job_dict
