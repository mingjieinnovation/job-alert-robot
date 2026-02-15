from flask import Blueprint, jsonify
from service_learning import analyze_and_retrain, get_insights

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/retrain", methods=["POST"])
def retrain():
    """Analyze feedback and update keyword weights."""
    result = analyze_and_retrain()
    return jsonify(result)


@analytics_bp.route("/api/analytics/insights", methods=["GET"])
def insights():
    """Get keyword performance insights."""
    result = get_insights()
    return jsonify(result)
