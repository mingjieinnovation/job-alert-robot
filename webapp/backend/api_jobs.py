from flask import Blueprint, request, jsonify
from models import db, JobRecord, JobApplication, UserKeyword
from service_scraper import fetch_and_store_jobs
from service_scoring import score_job
from sqlalchemy import func, and_, or_
import json

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/api/jobs/search", methods=["POST"])
def search_jobs():
    """Trigger a new job search using current keywords."""
    keywords = UserKeyword.query.all()
    kw_list = [kw.to_dict() for kw in keywords]

    try:
        result = fetch_and_store_jobs(kw_list)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@jobs_bp.route("/api/jobs", methods=["GET"])
def list_jobs():
    """List jobs with optional filters."""
    # Always exclude hard-filtered jobs (score = -99: contract, wrong title, excluded keyword in title, etc.)
    query = JobRecord.query.filter(JobRecord.match_score > -99)

    min_score = request.args.get("min_score", type=float)
    if min_score is not None:
        query = query.filter(JobRecord.match_score >= min_score)

    source = request.args.get("source")
    if source:
        query = query.filter(JobRecord.source == source)

    experience_ok = request.args.get("experience_ok")
    if experience_ok is not None:
        query = query.filter(JobRecord.experience_ok == (experience_ok.lower() == "true"))

    session_id = request.args.get("session_id", type=int)
    if session_id:
        query = query.filter(JobRecord.search_session_id == session_id)

    # Hide jobs marked as "not_interested"
    hide_dismissed = request.args.get("hide_dismissed")
    if hide_dismissed and hide_dismissed.lower() == "true":
        dismissed_job_ids = db.session.query(JobApplication.job_id).filter(
            JobApplication.status == "not_interested"
        ).subquery()
        query = query.filter(~JobRecord.id.in_(dismissed_job_ids))

    # Hide ALL jobs that have been processed (any application status),
    # including cross-source duplicates of processed jobs already in the DB
    hide_processed = request.args.get("hide_processed")
    if hide_processed and hide_processed.lower() == "true":
        # Step 1: exclude jobs with a direct application record
        processed_job_ids_sq = db.session.query(JobApplication.job_id)
        query = query.filter(~JobRecord.id.in_(processed_job_ids_sq))

        # Step 2: also exclude same-title+company duplicates from other sources
        # (handles pre-existing duplicates before the insert-level dedup was added)
        processed_tc = db.session.query(
            func.lower(JobRecord.title),
            func.lower(JobRecord.company)
        ).join(JobApplication, JobRecord.id == JobApplication.job_id).all()

        if processed_tc:
            conditions = [
                and_(
                    func.lower(JobRecord.title) == tc[0],
                    func.lower(JobRecord.company) == tc[1]
                )
                for tc in processed_tc
            ]
            query = query.filter(~or_(*conditions))

    sort = request.args.get("sort", "score")
    if sort == "date":
        query = query.order_by(JobRecord.first_seen_at.desc())
    else:
        query = query.order_by(JobRecord.match_score.desc())

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "jobs": [job.to_dict() for job in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@jobs_bp.route("/api/jobs/<int:job_id>", methods=["GET"])
def get_job(job_id):
    job = JobRecord.query.get_or_404(job_id)
    return jsonify(job.to_dict())


@jobs_bp.route("/api/jobs/rescore", methods=["POST"])
def rescore_jobs():
    """Re-score all jobs with current keyword weights."""
    keywords = UserKeyword.query.all()
    boost_kws = [{"keyword": kw.keyword, "weight": kw.weight}
                 for kw in keywords if kw.category == "boost"]
    exclude_kws = [{"keyword": kw.keyword, "weight": kw.weight}
                   for kw in keywords if kw.category == "exclude"]

    jobs = JobRecord.query.all()
    updated = 0
    for job in jobs:
        job_data = {"title": job.title, "description": job.description or ""}
        scored = score_job(job_data, boost_kws, exclude_kws)
        job.match_score = scored["match_score"]
        job.match_tags = scored["match_tags"]
        job.experience_ok = scored["experience_ok"]
        updated += 1

    db.session.commit()
    return jsonify({"updated": updated})
