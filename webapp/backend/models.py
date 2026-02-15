from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class FilterSettings(db.Model):
    __tablename__ = "filter_settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)  # JSON
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        import json
        try:
            val = json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            val = self.value
        return {"key": self.key, "value": val}


class ResumeRecord(db.Model):
    __tablename__ = "resume_records"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500))
    keywords_count = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "keywords_count": self.keywords_count,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


class UserKeyword(db.Model):
    __tablename__ = "user_keywords"
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(20), nullable=False, default="boost")  # boost / exclude
    weight = db.Column(db.Float, default=1.0)
    source = db.Column(db.String(20), default="manual")  # resume / manual / learned
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "keyword": self.keyword,
            "category": self.category,
            "weight": self.weight,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SearchSession(db.Model):
    __tablename__ = "search_sessions"
    id = db.Column(db.Integer, primary_key=True)
    query_text = db.Column(db.Text)  # JSON
    total_results = db.Column(db.Integer, default=0)
    sources = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    jobs = db.relationship("JobRecord", backref="search_session", lazy=True)


class JobRecord(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(200))
    source = db.Column(db.String(50))
    unique_key = db.Column(db.String(500), unique=True)
    title = db.Column(db.String(500))
    company = db.Column(db.String(300))
    location = db.Column(db.String(300))
    salary = db.Column(db.String(200))
    url = db.Column(db.Text)
    description = db.Column(db.Text)
    posted_date = db.Column(db.String(50))
    match_score = db.Column(db.Float, default=0)
    match_tags = db.Column(db.Text)  # JSON
    experience_ok = db.Column(db.Boolean, default=True)
    search_session_id = db.Column(db.Integer, db.ForeignKey("search_sessions.id"))
    first_seen_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    application = db.relationship("JobApplication", backref="job", uselist=False, lazy=True)

    def to_dict(self):
        import json
        tags = []
        if self.match_tags:
            try:
                tags = json.loads(self.match_tags)
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "id": self.id,
            "job_id": self.job_id,
            "source": self.source,
            "unique_key": self.unique_key,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "salary": self.salary,
            "url": self.url,
            "description": self.description,
            "posted_date": self.posted_date,
            "match_score": self.match_score,
            "match_tags": tags,
            "experience_ok": self.experience_ok,
            "search_session_id": self.search_session_id,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "application": self.application.to_dict() if self.application else None,
        }


class JobApplication(db.Model):
    __tablename__ = "job_applications"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    status = db.Column(db.String(20), default="interested")  # interested/applied/interview/offer/rejected
    applied_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    feedbacks = db.relationship("ApplicationFeedback", backref="application", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "status": self.status,
            "applied_date": self.applied_date.isoformat() if self.applied_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "feedbacks": [f.to_dict() for f in self.feedbacks],
        }


class ApplicationFeedback(db.Model):
    __tablename__ = "application_feedback"
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("job_applications.id"), nullable=False)
    feedback_type = db.Column(db.String(50))
    feedback_text = db.Column(db.Text)
    keywords_mentioned = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        import json
        kw = []
        if self.keywords_mentioned:
            try:
                kw = json.loads(self.keywords_mentioned)
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "id": self.id,
            "application_id": self.application_id,
            "feedback_type": self.feedback_type,
            "feedback_text": self.feedback_text,
            "keywords_mentioned": kw,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
