"""
dedup.py - 去重模块（JSON记录，30天自动清理）
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Set

import config
from scrapers import Job

logger = logging.getLogger(__name__)


def _load_seen() -> dict:
    if not os.path.exists(config.SEEN_JOBS_FILE):
        return {"jobs": {}, "last_cleanup": ""}
    try:
        with open(config.SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"jobs": {}, "last_cleanup": ""}


def _save_seen(data: dict):
    with open(config.SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _cleanup(data: dict) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    if data.get("last_cleanup") == today:
        return data
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    old = len(data["jobs"])
    data["jobs"] = {k: v for k, v in data["jobs"].items() if v.get("date", "") >= cutoff}
    removed = old - len(data["jobs"])
    if removed > 0:
        logger.info(f"🧹 清理 {removed} 条旧记录")
    data["last_cleanup"] = today
    return data


def deduplicate(jobs: List[Job]) -> List[Job]:
    data = _load_seen()
    data = _cleanup(data)

    seen: Set[str] = set(data["jobs"].keys())
    batch: Set[str] = set()
    new_jobs: List[Job] = []

    for job in jobs:
        key = job.unique_key
        if key in seen or key in batch:
            continue
        batch.add(key)
        new_jobs.append(job)

    today = datetime.now().strftime("%Y-%m-%d")
    for job in new_jobs:
        data["jobs"][job.unique_key] = {
            "title": job.title, "company": job.company, "date": today,
        }
    _save_seen(data)

    logger.info(f"📊 去重: {len(jobs)} → {len(new_jobs)} 新职位")
    return new_jobs
