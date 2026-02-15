import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, UserKeyword, ResumeRecord
from service_resume import extract_text_from_pdf, extract_keywords
from datetime import datetime, timezone

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/api/resume/status", methods=["GET"])
def resume_status():
    """Check if a resume has been uploaded before."""
    record = ResumeRecord.query.order_by(ResumeRecord.uploaded_at.desc()).first()
    if record:
        keywords = UserKeyword.query.filter_by(source="resume").all()
        return jsonify({
            "has_resume": True,
            "filename": record.filename,
            "keywords_count": len(keywords),
            "uploaded_at": record.uploaded_at.isoformat() if record.uploaded_at else None,
        })
    return jsonify({"has_resume": False})


@resume_bp.route("/api/resume/upload", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        text = extract_text_from_pdf(filepath)
        keywords = extract_keywords(text)

        # Store extracted keywords in DB (clear previous resume keywords first)
        UserKeyword.query.filter_by(source="resume").delete()

        saved = []
        for kw_data in keywords:
            kw = UserKeyword(
                keyword=kw_data["keyword"],
                category=kw_data["category"],
                weight=1.0,
                source="resume",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(kw)
            saved.append(kw_data)

        # Save resume record
        ResumeRecord.query.delete()  # Keep only latest
        record = ResumeRecord(
            filename=filename,
            keywords_count=len(saved),
            uploaded_at=datetime.now(timezone.utc),
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            "message": f"Extracted {len(saved)} keywords from resume",
            "keywords": saved,
            "text_preview": text[:500],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
