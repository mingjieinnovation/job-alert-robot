"""API for managing job search filters from the UI."""

import json
from flask import Blueprint, request, jsonify
from models import db, FilterSettings
from datetime import datetime, timezone

filters_bp = Blueprint("filters", __name__)

# Default filter values
DEFAULTS = {
    "min_salary": 45000,
    "max_experience_years": 5,
    "title_must_contain": ["analyst", "product manager"],
    "title_exclude_roles": [
        "scientist", "data scientist", "research scientist",
        "engineer", "software engineer", "backend engineer", "frontend engineer",
        "DevOps engineer", "QA engineer", "test engineer",
        "C++ developer", "Java developer",
        "iOS developer", "Android developer",
        "accountant", "solicitor", "nurse", "warehouse", "driver",
    ],
    "title_exclude_seniority": [
        "director", "VP", "vice president", "head of", "chief",
        "principal", "staff", "distinguished", "partner",
    ],
    "title_exclude_junior": [
        "intern", "internship", "graduate programme", "graduate program",
        "graduate scheme", "entry level trainee",
        "apprentice", "apprenticeship", "placement year",
    ],
    "title_exclude_analyst_prefixes": [
        "associate analyst", "junior analyst", "intern analyst",
        "associate data analyst", "junior data analyst",
        "associate product analyst", "junior product analyst",
        "associate business analyst", "junior business analyst",
        "associate insight analyst", "junior insight analyst",
    ],
    "title_exclude_other": [
        "IT ", "IT analyst", "summer",
        "job guarantee", "bootcamp", "training programme", "course",
    ],
    "contract_keywords": [
        "contract", "contractor", "freelance", "freelancer",
        "fixed term", "fixed-term", "temporary",
        "FTC", "ftc", "month ftc", "month contract",
        "6 month", "12 month", "3 month", "9 month",
        "maternity cover", "paternity cover",
    ],
    "language_exclude": [
        "french", "german", "spanish", "italian", "portuguese",
        "dutch", "japanese", "korean", "arabic", "russian",
        "turkish", "polish", "hindi", "swedish", "norwegian",
        "danish", "finnish", "greek", "hebrew", "czech",
        "hungarian", "romanian", "thai", "vietnamese",
    ],
}


def _get_setting(key: str):
    """Get a filter setting value, returning default if not set."""
    record = FilterSettings.query.filter_by(key=key).first()
    if record:
        try:
            return json.loads(record.value)
        except (json.JSONDecodeError, TypeError):
            return record.value
    return DEFAULTS.get(key)


def _set_setting(key: str, value):
    """Set a filter setting value."""
    record = FilterSettings.query.filter_by(key=key).first()
    json_val = json.dumps(value)
    if record:
        record.value = json_val
        record.updated_at = datetime.now(timezone.utc)
    else:
        record = FilterSettings(key=key, value=json_val)
        db.session.add(record)
    db.session.commit()


def get_all_filters() -> dict:
    """Get all filter settings (used by scraper/scorer)."""
    result = {}
    for key in DEFAULTS:
        result[key] = _get_setting(key)
    return result


@filters_bp.route("/api/filters", methods=["GET"])
def list_filters():
    """Get all current filter settings."""
    return jsonify(get_all_filters())


@filters_bp.route("/api/filters", methods=["PUT"])
def update_filters():
    """Update one or more filter settings."""
    data = request.get_json()
    updated = []
    for key, value in data.items():
        if key in DEFAULTS:
            _set_setting(key, value)
            updated.append(key)
    return jsonify({"updated": updated, "filters": get_all_filters()})


@filters_bp.route("/api/filters/reset", methods=["POST"])
def reset_filters():
    """Reset all filters to defaults."""
    FilterSettings.query.delete()
    db.session.commit()
    return jsonify({"message": "Reset to defaults", "filters": DEFAULTS})
