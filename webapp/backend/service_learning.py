"""Learn from user feedback to adjust keyword weights."""

import json
import logging
from collections import Counter
from datetime import datetime, timezone

from models import db, UserKeyword, JobRecord, JobApplication, ApplicationFeedback

logger = logging.getLogger(__name__)


def analyze_and_retrain() -> dict:
    """Analyze applied/interviewed jobs vs ignored ones to update keyword weights.

    Returns insights dict with updated keywords and statistics.
    """
    # Get jobs the user showed interest in (applied, interview, offer)
    positive_apps = JobApplication.query.filter(
        JobApplication.status.in_(["applied", "interview", "offer"])
    ).all()
    positive_job_ids = [a.job_id for a in positive_apps]

    # Get jobs explicitly marked as "not interested" (strong negative signal)
    not_interested_apps = JobApplication.query.filter(
        JobApplication.status == "not_interested"
    ).all()
    not_interested_job_ids = [a.job_id for a in not_interested_apps]
    not_interested_jobs = JobRecord.query.filter(
        JobRecord.id.in_(not_interested_job_ids)
    ).all() if not_interested_job_ids else []

    # Also get high-score jobs with no action (weaker negative signal)
    all_actioned_ids = positive_job_ids + not_interested_job_ids
    ignored_jobs = JobRecord.query.filter(
        JobRecord.match_score >= 3,
        ~JobRecord.id.in_(all_actioned_ids) if all_actioned_ids else True,
    ).all()

    positive_jobs = JobRecord.query.filter(JobRecord.id.in_(positive_job_ids)).all() if positive_job_ids else []

    # Extract keyword frequencies from positive jobs
    positive_keywords = Counter()
    for job in positive_jobs:
        text = (job.title + " " + (job.description or "")).lower()
        for kw in UserKeyword.query.filter_by(category="boost").all():
            if kw.keyword.lower() in text:
                positive_keywords[kw.keyword.lower()] += 1

    # Extract keyword frequencies from "not interested" jobs (strong negative)
    not_interested_keywords = Counter()
    for job in not_interested_jobs:
        text = (job.title + " " + (job.description or "")).lower()
        for kw in UserKeyword.query.filter_by(category="boost").all():
            if kw.keyword.lower() in text:
                not_interested_keywords[kw.keyword.lower()] += 1

    # Extract keyword frequencies from ignored jobs (weak negative)
    ignored_keywords = Counter()
    for job in ignored_jobs:
        text = (job.title + " " + (job.description or "")).lower()
        for kw in UserKeyword.query.filter_by(category="boost").all():
            if kw.keyword.lower() in text:
                ignored_keywords[kw.keyword.lower()] += 1

    # Collect keywords mentioned in feedback
    feedback_keywords = Counter()
    feedbacks = ApplicationFeedback.query.all()
    for fb in feedbacks:
        if fb.keywords_mentioned:
            try:
                kws = json.loads(fb.keywords_mentioned)
                for k in kws:
                    feedback_keywords[k.lower()] += 1
            except (json.JSONDecodeError, TypeError):
                pass

    # Update weights
    updates = []
    all_keywords = UserKeyword.query.filter_by(category="boost").all()
    for kw in all_keywords:
        kw_lower = kw.keyword.lower()
        pos_count = positive_keywords.get(kw_lower, 0)
        ni_count = not_interested_keywords.get(kw_lower, 0)
        ign_count = ignored_keywords.get(kw_lower, 0)
        fb_count = feedback_keywords.get(kw_lower, 0)

        # Increase weight for keywords in applied jobs and feedback
        new_weight = 1.0
        if pos_count > 0:
            new_weight += 0.3 * pos_count
        if fb_count > 0:
            new_weight += 0.5 * fb_count
        # Strong decrease for keywords in "not interested" jobs
        if ni_count > 0:
            new_weight -= 0.4 * ni_count
        # Weaker decrease for keywords only found in ignored jobs
        if ign_count > 0 and pos_count == 0:
            new_weight -= 0.2 * ign_count

        new_weight = max(0.1, min(5.0, new_weight))

        if abs(new_weight - kw.weight) > 0.01:
            old_weight = kw.weight
            kw.weight = round(new_weight, 2)
            kw.source = "learned"
            updates.append({
                "keyword": kw.keyword,
                "old_weight": old_weight,
                "new_weight": kw.weight,
            })

    # Add new keywords from feedback that aren't tracked yet
    new_keywords = []
    existing_kws = {kw.keyword.lower() for kw in UserKeyword.query.all()}
    for kw_text, count in feedback_keywords.most_common(10):
        if kw_text not in existing_kws and count >= 2:
            new_kw = UserKeyword(
                keyword=kw_text,
                category="boost",
                weight=1.5,
                source="learned",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(new_kw)
            new_keywords.append(kw_text)

    db.session.commit()

    return {
        "positive_jobs_count": len(positive_jobs),
        "not_interested_count": len(not_interested_jobs),
        "ignored_jobs_count": len(ignored_jobs),
        "weight_updates": updates,
        "new_keywords": new_keywords,
        "total_feedbacks_analyzed": len(feedbacks),
    }


def get_insights() -> dict:
    """Get keyword performance insights."""
    keywords = UserKeyword.query.filter_by(category="boost").order_by(UserKeyword.weight.desc()).all()

    # Count how many applied jobs contain each keyword
    applications = JobApplication.query.filter(
        JobApplication.status.in_(["applied", "interview", "offer"])
    ).all()
    applied_job_ids = [a.job_id for a in applications]
    applied_jobs = JobRecord.query.filter(JobRecord.id.in_(applied_job_ids)).all() if applied_job_ids else []

    keyword_stats = []
    for kw in keywords:
        hit_count = 0
        for job in applied_jobs:
            text = (job.title + " " + (job.description or "")).lower()
            if kw.keyword.lower() in text:
                hit_count += 1

        keyword_stats.append({
            "keyword": kw.keyword,
            "weight": kw.weight,
            "source": kw.source,
            "applied_job_hits": hit_count,
        })

    total_jobs = JobRecord.query.count()
    total_applications = JobApplication.query.count()
    total_feedbacks = ApplicationFeedback.query.count()

    return {
        "keyword_stats": keyword_stats,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "total_feedbacks": total_feedbacks,
        "application_rate": round(total_applications / total_jobs * 100, 1) if total_jobs > 0 else 0,
    }
