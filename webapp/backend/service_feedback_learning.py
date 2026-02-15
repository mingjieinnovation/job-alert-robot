"""Learn from user feedback (dismiss/apply) to suggest keywords."""

import logging
import re
from models import db, UserKeyword
from service_resume import TECH_SKILLS, DOMAIN_SKILLS

logger = logging.getLogger(__name__)

STOPWORDS = {
    "i", "me", "my", "the", "a", "an", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall", "to", "of",
    "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out", "off",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "don", "don't",
    "that", "this", "it", "its", "and", "but", "or", "if", "because",
    "about", "up", "down", "job", "role", "position", "work", "want",
    "like", "think", "look", "looking", "really", "much", "also", "get",
}


def _existing_keywords():
    """Return set of lowercase existing keyword strings."""
    return {kw.keyword.lower() for kw in UserKeyword.query.all()}


def _extract_phrases_from_notes(notes):
    """Extract meaningful phrases/words from user notes."""
    if not notes:
        return []
    text = notes.lower().strip()
    parts = re.split(r'[,;.\n]+', text)
    phrases = []
    for part in parts:
        part = part.strip()
        words = part.split()
        meaningful = [w for w in words if w not in STOPWORDS and len(w) > 2]
        if meaningful:
            if 2 <= len(meaningful) <= 4:
                phrases.append(" ".join(meaningful))
            for w in meaningful:
                if len(w) > 3:
                    phrases.append(w)
    return list(set(phrases))


def suggest_from_dismissal(job, notes):
    """Suggest exclude keywords from a 'not interested' action with notes.

    Returns list of suggested keyword strings (does NOT save them).
    All meaningful phrases from the notes are returned as suggestions
    so the user can pick which ones to keep.
    """
    if not notes:
        return []

    existing = _existing_keywords()

    # Return all meaningful phrases extracted from notes
    phrases = _extract_phrases_from_notes(notes)
    suggestions = [p for p in phrases if p not in existing]

    logger.info("Suggested %d exclude keywords from dismissal: %s", len(suggestions), suggestions)
    return list(set(suggestions))


def suggest_from_application(job):
    """Suggest boost keywords from an 'applied' action.

    Returns list of suggested keyword strings (does NOT save them).
    """
    suggestions = []
    job_title = (job.title or "").lower()
    job_desc = (job.description or "").lower()
    job_text = f"{job_title} {job_desc}"

    existing = _existing_keywords()

    # Check tech skills present in this job
    for skill in TECH_SKILLS:
        if skill.lower() in job_text and skill.lower() not in existing:
            suggestions.append(skill.lower())

    # Check domain skills present in this job
    for skill in DOMAIN_SKILLS:
        if skill.lower() in job_text and skill.lower() not in existing:
            suggestions.append(skill.lower())

    # Check match_tags if available
    if job.match_tags:
        tags = job.match_tags if isinstance(job.match_tags, list) else []
        for tag in tags:
            tag_lower = tag.lower().strip()
            if len(tag_lower) > 2 and tag_lower not in existing:
                suggestions.append(tag_lower)

    logger.info("Suggested %d boost keywords from application: %s", len(suggestions), suggestions)
    return list(set(suggestions))


def save_learned_keywords(keywords_list, category, weight=0.5):
    """Save user-confirmed keywords.

    Args:
        keywords_list: list of keyword strings
        category: 'boost' or 'exclude'
        weight: keyword weight (default 0.5 for learned)

    Returns list of actually saved keyword strings.
    """
    existing = _existing_keywords()
    saved = []
    for kw_str in keywords_list:
        kw_str = kw_str.strip().lower()
        if len(kw_str) < 2 or kw_str in existing:
            continue
        kw = UserKeyword(
            keyword=kw_str,
            category=category,
            weight=weight,
            source="learned",
        )
        db.session.add(kw)
        existing.add(kw_str)
        saved.append(kw_str)
    db.session.commit()
    logger.info("Saved %d learned %s keywords: %s", len(saved), category, saved)
    return saved
