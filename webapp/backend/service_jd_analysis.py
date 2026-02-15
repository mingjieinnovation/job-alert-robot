"""Job description analysis - extract keywords and compare with user's current keywords."""

import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)

# Reuse skill dictionaries from service_resume
from service_resume import TECH_SKILLS, DOMAIN_SKILLS

ALL_KNOWN_SKILLS = TECH_SKILLS | DOMAIN_SKILLS


def analyze_job_description(text: str, existing_keywords: list[dict]) -> dict:
    """Analyze a pasted job description and compare with current user keywords.

    Args:
        text: The raw job description text
        existing_keywords: List of UserKeyword dicts with 'keyword' and 'category'

    Returns:
        dict with new_suggestions, already_tracking, conflicts
    """
    text_lower = text.lower()

    # Build sets of existing keywords by category
    boost_set = {k["keyword"].lower() for k in existing_keywords if k.get("category") == "boost"}
    exclude_set = {k["keyword"].lower() for k in existing_keywords if k.get("category") == "exclude"}

    # Find all known skills mentioned in JD
    found_skills = set()
    for skill in ALL_KNOWN_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill.lower())

    # Also extract bigrams from the text for additional discovery
    words = re.findall(r'[a-z][a-z\-]+', text_lower)
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    bigram_counts = Counter(bigrams)

    # Bigrams that appear 2+ times and look like skill phrases
    for bigram, count in bigram_counts.items():
        if count >= 2 and bigram in {s.lower() for s in ALL_KNOWN_SKILLS}:
            found_skills.add(bigram)

    # Categorize found skills
    new_suggestions = []
    already_tracking = []
    conflicts = []

    for skill in sorted(found_skills):
        if skill in boost_set:
            already_tracking.append(skill)
        elif skill in exclude_set:
            conflicts.append(skill)
        else:
            new_suggestions.append(skill)

    return {
        "new_suggestions": new_suggestions,
        "already_tracking": already_tracking,
        "conflicts": conflicts,
    }
