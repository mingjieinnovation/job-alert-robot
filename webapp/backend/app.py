import os
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS
from models import db

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

def create_app():
    app = Flask(__name__)
    CORS(app)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'database.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    from api_resume import resume_bp
    from api_keywords import keywords_bp
    from api_jobs import jobs_bp
    from api_applications import applications_bp
    from api_analytics import analytics_bp
    from api_filters import filters_bp
    from api_jd_analysis import jd_bp

    app.register_blueprint(resume_bp)
    app.register_blueprint(keywords_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(filters_bp)
    app.register_blueprint(jd_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
