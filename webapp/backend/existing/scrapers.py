"""
scrapers.py - 5个来源抓取 + 经验级别智能过滤

来源：
1. Adzuna API（聚合 Indeed/CV-Library 等）
2. Reed API（英国本土）
3. LinkedIn（公开职位页面解析）
4. Google Jobs（通过 SerpAPI）
5. X/Twitter（RSS Bridge）
"""

import requests
import logging
import time
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List
from base64 import b64encode
from html.parser import HTMLParser

import config

logger = logging.getLogger(__name__)


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    salary: str = ""
    description_snippet: str = ""
    posted_date: str = ""
    job_id: str = ""
    match_score: int = 0
    match_tags: List[str] = field(default_factory=list)
    experience_ok: bool = True

    def to_dict(self):
        d = asdict(self)
        d["match_tags"] = self.match_tags
        return d

    @property
    def unique_key(self) -> str:
        if self.job_id:
            return f"{self.source}_{self.job_id}"
        clean_title = re.sub(r'[^a-z0-9]', '', self.title.lower())
        clean_company = re.sub(r'[^a-z0-9]', '', self.company.lower())
        return f"{self.source}_{clean_company}_{clean_title}"


# ============================================================
# 过滤 & 评分
# ============================================================

def _passes_title_filter(title: str) -> bool:
    t = title.lower()
    if config.TITLE_MUST_CONTAIN:
        if not any(kw.lower() in t for kw in config.TITLE_MUST_CONTAIN):
            return False
    if config.TITLE_EXCLUDE:
        if any(kw.lower() in t for kw in config.TITLE_EXCLUDE):
            return False
    return True


def _score_job(job: Job) -> Job:
    """评分：Boost关键词加分，Warning关键词扣分，经验年限检测"""
    text = (job.title + " " + job.description_snippet).lower()
    score = 0
    tags = []

    for kw in config.DESCRIPTION_BOOST_KEYWORDS:
        if kw.lower() in text:
            score += 1
            if kw.lower() in ["product analytics", "user research", "kpi",
                               "power bi", "sql", "python", "data-driven",
                               "1-3 years", "2-3 years"]:
                tags.append(f"⭐{kw}")

    for kw in config.DESCRIPTION_WARNING_KEYWORDS:
        if kw.lower() in text:
            score -= 2
            tags.append(f"⚠️{kw}")
            job.experience_ok = False

    if any(kw in text for kw in ["genai", "generative ai", "llm", "agentic"]):
        score += 2
        tags.append("🤖AI")
    elif " ai " in f" {text} " or "artificial intelligence" in text:
        score += 1

    years_match = re.findall(r'(\d+)\+?\s*years?', text)
    for y in years_match:
        yr = int(y)
        if yr <= 5:
            score += 1
        elif yr >= 7:
            score -= 2
            job.experience_ok = False
            tags.append(f"⚠️需{yr}年经验")

    job.match_score = score
    job.match_tags = tags
    return job


def _clean_html(text: str) -> str:
    """去除HTML标签"""
    return re.sub(r'<[^>]+>', '', text or "")


# ============================================================
# 1. Adzuna API
# ============================================================

def fetch_adzuna_jobs() -> List[Job]:
    """
    Adzuna 聚合了 Indeed, CV-Library, Totaljobs 等来源
    文档: https://developer.adzuna.com/docs/search
    免费: 250次/天
    """
    if config.ADZUNA_APP_ID == "YOUR_ADZUNA_APP_ID":
        logger.warning("  ⚠️ Adzuna 未配置，跳过")
        return []

    all_jobs = []
    base_url = f"https://api.adzuna.com/v1/api/jobs/{config.COUNTRY}/search/1"

    for query in config.SEARCH_QUERIES:
        try:
            params = {
                "app_id": config.ADZUNA_APP_ID,
                "app_key": config.ADZUNA_APP_KEY,
                "what": query,
                "where": config.LOCATION,
                "results_per_page": min(config.MAX_RESULTS_PER_QUERY, 50),  # Adzuna最大50
                "max_days_old": 7,
                "sort_by": "date",
                "content-type": "application/json",
            }
            if config.MIN_SALARY > 0:
                params["salary_min"] = config.MIN_SALARY

            resp = requests.get(base_url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            count = 0
            for item in data.get("results", []):
                title = item.get("title", "")
                if not _passes_title_filter(title):
                    continue

                salary = ""
                sal_min = item.get("salary_min")
                sal_max = item.get("salary_max")
                if sal_min and sal_max:
                    salary = f"£{int(sal_min):,} - £{int(sal_max):,}"
                elif sal_min:
                    salary = f"From £{int(sal_min):,}"

                job = Job(
                    title=title,
                    company=item.get("company", {}).get("display_name", "Unknown"),
                    location=item.get("location", {}).get("display_name", config.LOCATION),
                    url=item.get("redirect_url", ""),
                    source="adzuna",
                    salary=salary,
                    description_snippet=_clean_html(item.get("description", ""))[:500],
                    posted_date=item.get("created", "")[:10],
                    job_id=str(item.get("id", "")),
                )
                job = _score_job(job)
                all_jobs.append(job)
                count += 1

            logger.info(f"  Adzuna [{query}]: {count} 个通过")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"  Adzuna [{query}] 失败: {e}")

    return all_jobs


# ============================================================
# 2. Reed API
# ============================================================

def fetch_reed_jobs() -> List[Job]:
    """
    英国本土求职网站
    文档: https://www.reed.co.uk/developers/jobseeker
    免费，无限制
    """
    if config.REED_API_KEY == "YOUR_REED_API_KEY":
        logger.warning("  ⚠️ Reed 未配置，跳过")
        return []

    all_jobs = []
    base_url = "https://www.reed.co.uk/api/1.0/search"
    auth = b64encode(f"{config.REED_API_KEY}:".encode()).decode()

    for query in config.SEARCH_QUERIES:
        try:
            params = {
                "keywords": query,
                "locationName": config.LOCATION,
                "distancefromlocation": 15,
                "resultsToTake": min(config.MAX_RESULTS_PER_QUERY, 100),  # Reed最大100
            }
            if config.MIN_SALARY > 0:
                params["minimumSalary"] = config.MIN_SALARY

            resp = requests.get(base_url, params=params, timeout=15,
                                headers={"Authorization": f"Basic {auth}"})
            resp.raise_for_status()
            data = resp.json()

            count = 0
            for item in data.get("results", []):
                title = item.get("jobTitle", "")
                if not _passes_title_filter(title):
                    continue

                salary = ""
                sal_min = item.get("minimumSalary")
                sal_max = item.get("maximumSalary")
                if sal_min and sal_max:
                    salary = f"£{int(sal_min):,} - £{int(sal_max):,}"
                elif sal_min:
                    salary = f"From £{int(sal_min):,}"

                job = Job(
                    title=title,
                    company=item.get("employerName", "Unknown"),
                    location=item.get("locationName", config.LOCATION),
                    url=f"https://www.reed.co.uk/jobs/{item.get('jobId', '')}",
                    source="reed",
                    salary=salary,
                    description_snippet=item.get("jobDescription", "")[:500],
                    posted_date=item.get("date", "")[:10],
                    job_id=str(item.get("jobId", "")),
                )
                job = _score_job(job)
                all_jobs.append(job)
                count += 1

            logger.info(f"  Reed [{query}]: {count} 个通过")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"  Reed [{query}] 失败: {e}")

    return all_jobs


# ============================================================
# 3. LinkedIn（公开职位页面解析）
# ============================================================

def fetch_linkedin_jobs() -> List[Job]:
    """
    LinkedIn 公开职位搜索（不需要登录）

    原理：LinkedIn 的职位搜索页有一个面向搜索引擎的公开版本，
    通过 /jobs-guest/jobs/api/seeMoreJobPostings/search 可以
    获取 HTML 格式的职位列表。我们解析这个 HTML 提取职位信息。

    注意：这不是官方 API，LinkedIn 可能随时改变格式。
    如果某天突然抓不到了，不影响其他来源。
    """
    all_jobs = []
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    # LinkedIn 搜索词精简（太多会触发频率限制）
    linkedin_queries = [
        "AI product manager",
        "AI product analyst",
        "AI data analyst",
        "GenAI product",
        "product analytics AI",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    for query in linkedin_queries:
        try:
            params = {
                "keywords": query,
                "location": "London, United Kingdom",
                "f_TPR": "r604800",  # 过去7天
                "start": 0,
                "count": min(config.MAX_RESULTS_PER_QUERY, 50),
            }

            resp = requests.get(base_url, params=params, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"  LinkedIn [{query}]: HTTP {resp.status_code}")
                continue

            html = resp.text
            count = 0

            # 解析 LinkedIn HTML 职位卡片
            # 每个职位在 <div class="base-card"> 中
            card_pattern = re.compile(
                r'<div[^>]*class="[^"]*base-card[^"]*"[^>]*>.*?</div>\s*</div>\s*</div>',
                re.DOTALL
            )

            # 提取各字段的正则
            title_pattern = re.compile(
                r'<h3[^>]*class="[^"]*base-search-card__title[^"]*"[^>]*>\s*(.*?)\s*</h3>',
                re.DOTALL
            )
            company_pattern = re.compile(
                r'<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>\s*(.*?)\s*</h4>',
                re.DOTALL
            )
            location_pattern = re.compile(
                r'<span[^>]*class="[^"]*job-search-card__location[^"]*"[^>]*>\s*(.*?)\s*</span>',
                re.DOTALL
            )
            link_pattern = re.compile(
                r'<a[^>]*class="[^"]*base-card__full-link[^"]*"[^>]*href="([^"]*)"',
                re.DOTALL
            )
            date_pattern = re.compile(
                r'<time[^>]*datetime="([^"]*)"',
                re.DOTALL
            )

            titles = title_pattern.findall(html)
            companies = company_pattern.findall(html)
            locations = location_pattern.findall(html)
            links = link_pattern.findall(html)
            dates = date_pattern.findall(html)

            num_jobs = min(len(titles), len(companies), len(links))

            for i in range(num_jobs):
                title = _clean_html(titles[i]).strip()
                if not _passes_title_filter(title):
                    continue

                company = _clean_html(companies[i]).strip() if i < len(companies) else "Unknown"
                location = _clean_html(locations[i]).strip() if i < len(locations) else "London"
                url = links[i].split("?")[0] if i < len(links) else ""
                posted = dates[i][:10] if i < len(dates) else ""

                # 从 URL 提取 job ID
                job_id_match = re.search(r'/view/[^/]*-(\d+)', url)
                jid = job_id_match.group(1) if job_id_match else ""

                job = Job(
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    source="linkedin",
                    posted_date=posted,
                    job_id=jid,
                )
                job = _score_job(job)
                all_jobs.append(job)
                count += 1

            logger.info(f"  LinkedIn [{query}]: {count} 个通过")
            time.sleep(2)  # LinkedIn 对频率敏感，间隔长一些

        except Exception as e:
            logger.error(f"  LinkedIn [{query}] 失败: {e}")

    return all_jobs


# ============================================================
# 4. Google Jobs（通过 SerpAPI）
# ============================================================

def fetch_google_jobs() -> List[Job]:
    """
    Google Jobs 聚合了 LinkedIn, Indeed, Glassdoor 等所有来源。

    原理：Google 没有公开的 Jobs API，但 SerpAPI.com 提供了一个
    代理服务，可以结构化地获取 Google Jobs 的搜索结果。

    免费额度：100次搜索/月。我们每天用3-5次，一个月约100-150次，
    刚好在免费边界。如果超了可以只用前几个关键词。

    注册：https://serpapi.com/manage-api-key
    """
    if config.SERPAPI_KEY == "YOUR_SERPAPI_KEY":
        logger.warning("  ⚠️ SerpAPI 未配置，跳过 Google Jobs")
        return []

    all_jobs = []
    base_url = "https://serpapi.com/search.json"

    # Google Jobs 搜索词精简（节省 API 额度）
    google_queries = [
        "AI product manager London",
        "AI product analyst London",
        "AI data analyst London",
    ]

    for query in google_queries:
        try:
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": "London, United Kingdom",
                "api_key": config.SERPAPI_KEY,
                "chips": "date_posted:week",  # 仅过去一周
                "num": min(config.MAX_RESULTS_PER_QUERY, 50),
            }

            resp = requests.get(base_url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            count = 0
            for item in data.get("jobs_results", []):
                title = item.get("title", "")
                if not _passes_title_filter(title):
                    continue

                # Google Jobs 的描述比较完整，有利于评分
                desc = item.get("description", "")[:500]

                # 提取薪资（如果有）
                salary = ""
                detected = item.get("detected_extensions", {})
                if detected.get("salary"):
                    salary = detected["salary"]

                # 提取申请链接
                url = ""
                apply_options = item.get("apply_options", [])
                if apply_options:
                    url = apply_options[0].get("link", "")

                # 提取发布时间
                posted = detected.get("posted_at", "")

                job = Job(
                    title=title,
                    company=item.get("company_name", "Unknown"),
                    location=item.get("location", "London"),
                    url=url,
                    source="google_jobs",
                    salary=salary,
                    description_snippet=desc,
                    posted_date=posted,
                    job_id=item.get("job_id", ""),
                )
                job = _score_job(job)
                all_jobs.append(job)
                count += 1

            logger.info(f"  Google Jobs [{query}]: {count} 个通过")
            time.sleep(1)

        except Exception as e:
            logger.error(f"  Google Jobs [{query}] 失败: {e}")

    return all_jobs


# ============================================================
# 5. X/Twitter（RSS Bridge）
# ============================================================

def fetch_x_jobs() -> List[Job]:
    """
    通过公开 RSS Bridge 抓取 X/Twitter 招聘帖。
    第三方服务，可能不稳定，作为补充来源。
    """
    all_jobs = []

    x_queries = [
        '"hiring" "London" "AI" (product OR analyst)',
        'from:illbeback_jobs London',
        'from:Egooshift analyst London',
        'from:AIJobAlert London',
    ]

    rss_bridges = [
        "https://rss-bridge.org/bridge01",
        "https://rss-bridge.bb8.fun",
    ]

    for query in x_queries:
        fetched = False
        for bridge in rss_bridges:
            if fetched:
                break
            try:
                params = {
                    "action": "display",
                    "bridge": "TwitterBridge",
                    "context": "By+keyword",
                    "q": query,
                    "format": "Mrss",
                }
                resp = requests.get(f"{bridge}/", params=params, timeout=15,
                                    headers={"User-Agent": "JobAlertBot/1.0"})
                if resp.status_code != 200:
                    continue

                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:5]:
                    title_el = item.find('title')
                    link_el = item.find('link')
                    desc_el = item.find('description')

                    if title_el is None or link_el is None:
                        continue

                    text = title_el.text or ""
                    if not any(kw in text.lower() for kw in
                               ['hiring', 'job', 'role', 'position', 'vacancy', 'looking for']):
                        continue
                    if any(kw in text.lower() for kw in ['intern', 'director', 'vp', 'head of']):
                        continue

                    job = Job(
                        title=f"[X] {text[:120]}",
                        company="(via X/Twitter)",
                        location="London",
                        url=link_el.text or "",
                        source="x_twitter",
                        description_snippet=_clean_html(desc_el.text if desc_el is not None else "")[:300],
                        job_id=link_el.text or "",
                    )
                    job = _score_job(job)
                    all_jobs.append(job)

                fetched = True
                logger.info(f"  X [{query[:35]}...]: 成功")
            except Exception:
                continue

        if not fetched:
            logger.debug(f"  X [{query[:35]}...]: 不可用")
        time.sleep(1)

    return all_jobs


# ============================================================
# 统一入口
# ============================================================

def fetch_all_jobs() -> List[Job]:
    all_jobs = []

    logger.info("=" * 55)
    logger.info("🔍 开始抓取（5个来源）...")

    sources = [
        ("📡 1/5 Adzuna（聚合 Indeed/CV-Library 等）", fetch_adzuna_jobs),
        ("📡 2/5 Reed（英国本土）", fetch_reed_jobs),
        ("📡 3/5 LinkedIn（公开职位）", fetch_linkedin_jobs),
        ("📡 4/5 Google Jobs（聚合所有平台）", fetch_google_jobs),
        ("📡 5/5 X/Twitter", fetch_x_jobs),
    ]

    for label, fetcher in sources:
        logger.info(f"\n{label}")
        try:
            jobs = fetcher()
            all_jobs.extend(jobs)
            logger.info(f"   → {len(jobs)} 个通过过滤")
        except Exception as e:
            logger.error(f"   → 来源失败: {e}")

    # 按匹配分数排序
    all_jobs.sort(key=lambda j: j.match_score, reverse=True)

    logger.info(f"\n🎯 5个来源总计: {len(all_jobs)} 个（未去重）")
    return all_jobs
