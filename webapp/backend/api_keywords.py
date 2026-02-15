from flask import Blueprint, request, jsonify
from models import db, UserKeyword
from datetime import datetime, timezone

keywords_bp = Blueprint("keywords", __name__)


@keywords_bp.route("/api/keywords", methods=["GET"])
def get_keywords():
    keywords = UserKeyword.query.order_by(UserKeyword.category, UserKeyword.weight.desc()).all()
    return jsonify([kw.to_dict() for kw in keywords])


@keywords_bp.route("/api/keywords", methods=["POST"])
def add_keyword():
    data = request.get_json()
    if not data or not data.get("keyword"):
        return jsonify({"error": "Keyword is required"}), 400

    kw = UserKeyword(
        keyword=data["keyword"].strip(),
        category=data.get("category", "boost"),
        weight=data.get("weight", 1.0),
        source=data.get("source", "manual"),
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(kw)
    db.session.commit()
    return jsonify(kw.to_dict()), 201


@keywords_bp.route("/api/keywords/<int:keyword_id>", methods=["PUT"])
def update_keyword(keyword_id):
    kw = UserKeyword.query.get_or_404(keyword_id)
    data = request.get_json()

    if "keyword" in data:
        kw.keyword = data["keyword"].strip()
    if "category" in data:
        kw.category = data["category"]
    if "weight" in data:
        kw.weight = data["weight"]

    db.session.commit()
    return jsonify(kw.to_dict())


@keywords_bp.route("/api/keywords/<int:keyword_id>", methods=["DELETE"])
def delete_keyword(keyword_id):
    kw = UserKeyword.query.get_or_404(keyword_id)
    db.session.delete(kw)
    db.session.commit()
    return jsonify({"message": "Deleted"})
