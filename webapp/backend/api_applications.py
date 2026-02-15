import json
from flask import Blueprint, request, jsonify
from models import db, JobApplication, ApplicationFeedback, JobRecord
from datetime import datetime, timezone
from service_feedback_learning import suggest_from_dismissal, suggest_from_application, save_learned_keywords

applications_bp = Blueprint("applications", __name__)


@applications_bp.route("/api/applications", methods=["GET"])
def list_applications():
    status = request.args.get("status")
    exclude_status = request.args.get("exclude_status")
    query = JobApplication.query
    if status:
        query = query.filter_by(status=status)
    if exclude_status:
        query = query.filter(JobApplication.status != exclude_status)

    apps = query.order_by(JobApplication.updated_at.desc()).all()
    result = []
    for app in apps:
        app_dict = app.to_dict()
        job = JobRecord.query.get(app.job_id)
        if job:
            app_dict["job"] = job.to_dict()
        result.append(app_dict)

    return jsonify(result)


@applications_bp.route("/api/applications", methods=["POST"])
def create_application():
    data = request.get_json()
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    existing = JobApplication.query.filter_by(job_id=job_id).first()
    if existing:
        return jsonify({"error": "Application already exists", "application": existing.to_dict()}), 409

    app = JobApplication(
        job_id=job_id,
        status=data.get("status", "interested"),
        notes=data.get("notes", ""),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    if data.get("status") == "applied":
        app.applied_date = datetime.now(timezone.utc)

    db.session.add(app)
    db.session.commit()

    # Suggest keywords from feedback
    suggested_keywords = []
    job = JobRecord.query.get(job_id)
    if job:
        if data.get("status") == "not_interested" and data.get("notes"):
            suggested_keywords = suggest_from_dismissal(job, data["notes"])
        elif data.get("status") == "applied":
            suggested_keywords = suggest_from_application(job)

    result = app.to_dict()
    result["suggested_keywords"] = suggested_keywords
    result["keyword_category"] = "exclude" if data.get("status") == "not_interested" else "boost"
    return jsonify(result), 201


@applications_bp.route("/api/applications/<int:app_id>", methods=["PUT"])
def update_application(app_id):
    app = JobApplication.query.get_or_404(app_id)
    data = request.get_json()

    if "status" in data:
        app.status = data["status"]
        if data["status"] == "applied" and not app.applied_date:
            app.applied_date = datetime.now(timezone.utc)
    if "notes" in data:
        app.notes = data["notes"]

    app.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    # Suggest keywords from feedback
    suggested_keywords = []
    keyword_category = None
    job = JobRecord.query.get(app.job_id)
    if job and "status" in data:
        if data["status"] == "not_interested" and (data.get("notes") or app.notes):
            suggested_keywords = suggest_from_dismissal(job, data.get("notes") or app.notes)
            keyword_category = "exclude"
        elif data["status"] == "applied":
            suggested_keywords = suggest_from_application(job)
            keyword_category = "boost"

    result = app.to_dict()
    result["suggested_keywords"] = suggested_keywords
    if keyword_category:
        result["keyword_category"] = keyword_category
    return jsonify(result)


@applications_bp.route("/api/applications/save-keywords", methods=["POST"])
def save_keywords_from_feedback():
    """Save user-confirmed keywords from feedback learning."""
    data = request.get_json()
    keywords = data.get("keywords", [])
    category = data.get("category", "boost")
    if category not in ("boost", "exclude"):
        return jsonify({"error": "category must be 'boost' or 'exclude'"}), 400
    saved = save_learned_keywords(keywords, category)
    return jsonify({"saved": saved})


@applications_bp.route("/api/applications/<int:app_id>", methods=["DELETE"])
def delete_application(app_id):
    app = JobApplication.query.get_or_404(app_id)
    ApplicationFeedback.query.filter_by(application_id=app_id).delete()
    db.session.delete(app)
    db.session.commit()
    return jsonify({"message": "Deleted"})


@applications_bp.route("/api/applications/<int:app_id>/feedback", methods=["POST"])
def add_feedback(app_id):
    app = JobApplication.query.get_or_404(app_id)
    data = request.get_json()

    feedback = ApplicationFeedback(
        application_id=app_id,
        feedback_type=data.get("feedback_type", "general"),
        feedback_text=data.get("feedback_text", ""),
        keywords_mentioned=json.dumps(data.get("keywords_mentioned", [])),
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(feedback)
    db.session.commit()
    return jsonify(feedback.to_dict()), 201
