"""API endpoints for job description analysis."""

from flask import Blueprint, request, jsonify
from models import db, UserKeyword
from service_jd_analysis import analyze_job_description

jd_bp = Blueprint("jd", __name__)


@jd_bp.route("/api/jd/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    # Get current user keywords
    existing = [kw.to_dict() for kw in UserKeyword.query.all()]

    result = analyze_job_description(text, existing)
    return jsonify(result)


@jd_bp.route("/api/jd/apply", methods=["POST"])
def apply_suggestions():
    data = request.get_json()
    add_boost = data.get("add_boost", [])
    remove_exclude = data.get("remove_exclude", [])

    added = 0
    removed = 0

    # Add new boost keywords
    for kw in add_boost:
        kw_lower = kw.strip().lower()
        if not kw_lower:
            continue
        existing = UserKeyword.query.filter(
            db.func.lower(UserKeyword.keyword) == kw_lower,
            UserKeyword.category == "boost"
        ).first()
        if not existing:
            db.session.add(UserKeyword(
                keyword=kw_lower,
                category="boost",
                weight=1.0,
                source="jd_analysis",
            ))
            added += 1

    # Remove from exclude list (conflicts the user wants to resolve)
    for kw in remove_exclude:
        kw_lower = kw.strip().lower()
        if not kw_lower:
            continue
        exclude_kw = UserKeyword.query.filter(
            db.func.lower(UserKeyword.keyword) == kw_lower,
            UserKeyword.category == "exclude"
        ).first()
        if exclude_kw:
            db.session.delete(exclude_kw)
            removed += 1

    db.session.commit()
    return jsonify({"added": added, "removed": removed})
