"""
emailer.py - HTML邮件发送，显示匹配分数和经验级别标记
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List

import config
from scrapers import Job

logger = logging.getLogger(__name__)


def _build_html(jobs: List[Job], stats: dict) -> str:
    job_cards = ""
    for i, job in enumerate(jobs, 1):
        # 匹配分数颜色
        if job.match_score >= 3:
            score_color, score_bg, score_label = "#1b5e20", "#e8f5e9", "🎯 强匹配"
        elif job.match_score >= 1:
            score_color, score_bg, score_label = "#e65100", "#fff3e0", "👍 匹配"
        else:
            score_color, score_bg, score_label = "#616161", "#f5f5f5", "📋 一般"

        # 经验级别警告
        exp_warning = ""
        if not job.experience_ok:
            exp_warning = """<span style="background:#fff3e0;color:#e65100;padding:2px 6px;
                border-radius:3px;font-size:11px;margin-left:6px;">⚠️ 可能偏资深</span>"""

        # 薪资
        salary_html = ""
        if job.salary:
            salary_html = f"""<span style="background:#e8f5e9;color:#2e7d32;padding:2px 6px;
                border-radius:3px;font-size:11px;margin-left:6px;">💰 {job.salary}</span>"""

        # 匹配标签
        tags_html = ""
        if job.match_tags:
            tags = " ".join(job.match_tags[:4])
            tags_html = f'<div style="font-size:11px;color:#888;margin-top:4px;">{tags}</div>'

        # 描述
        desc = job.description_snippet
        if len(desc) > 250:
            desc = desc[:250] + "..."

        job_cards += f"""
        <div style="border:1px solid #e0e0e0;border-radius:8px;padding:14px;
                    margin:8px 0;background:#fff;border-left:4px solid {score_color};">
            <div style="margin-bottom:4px;">
                <span style="background:{score_bg};color:{score_color};padding:2px 8px;
                    border-radius:3px;font-size:11px;font-weight:bold;">{score_label}</span>
                {salary_html}{exp_warning}
                <span style="color:#bbb;font-size:11px;float:right;">#{i} · {job.source}</span>
            </div>
            <div style="margin:6px 0;">
                <a href="{job.url}" style="color:#1a73e8;font-size:14px;font-weight:bold;
                   text-decoration:none;" target="_blank">{job.title}</a>
            </div>
            <div style="color:#333;font-size:12px;">
                🏢 {job.company} &nbsp;|&nbsp; 📍 {job.location}
                {f' &nbsp;|&nbsp; 📅 {job.posted_date}' if job.posted_date else ''}
            </div>
            {tags_html}
            <div style="color:#666;font-size:12px;line-height:1.5;margin-top:6px;">{desc}</div>
            <div style="margin-top:8px;">
                <a href="{job.url}" style="background:#1a73e8;color:white;padding:5px 14px;
                   border-radius:4px;text-decoration:none;font-size:12px;" target="_blank">
                    查看详情 →</a>
            </div>
        </div>"""

    # 统计
    strong = sum(1 for j in jobs if j.match_score >= 3)
    good = sum(1 for j in jobs if 1 <= j.match_score < 3)
    risky = sum(1 for j in jobs if not j.experience_ok)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
                 background:#f5f5f5;margin:0;padding:20px;">
    <div style="max-width:650px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);color:white;
                    padding:25px;border-radius:10px 10px 0 0;text-align:center;">
            <h1 style="margin:0;font-size:20px;">🤖 AI Job Alert</h1>
            <p style="margin:6px 0 0;opacity:0.9;font-size:13px;">
                {datetime.now().strftime('%Y年%m月%d日')} · ≤5年经验 · 必须提及AI</p>
        </div>
        <div style="background:#fff;padding:12px 20px;border-bottom:1px solid #eee;font-size:12px;color:#666;">
            📊 新职位: <strong>{len(jobs)}</strong> &nbsp;|&nbsp;
            🎯 强匹配: <strong style="color:#1b5e20;">{strong}</strong> &nbsp;|&nbsp;
            👍 匹配: <strong>{good}</strong> &nbsp;|&nbsp;
            ⚠️ 偏资深: <strong style="color:#e65100;">{risky}</strong> &nbsp;|&nbsp;
            🚫 过滤重复: {stats.get('duplicates', 0)}
        </div>
        <div style="background:#fafafa;padding:8px 16px 16px;">{job_cards}</div>
        <div style="background:#fff;padding:12px 20px;border-radius:0 0 10px 10px;
                    border-top:1px solid #eee;text-align:center;">
            <p style="color:#999;font-size:10px;margin:0;">
                AI Job Alert Bot · 必须提及AI · ≤5年经验 · 排除: Director/VP/Principal/Intern/Graduate
                <br>修改过滤条件: config.py</p>
        </div>
    </div></body></html>"""


def send_email(jobs: List[Job], stats: dict) -> bool:
    cfg = config.EMAIL_CONFIG
    if cfg["sender_password"] == "YOUR_APP_PASSWORD_HERE":
        logger.error("❌ 邮箱密码未配置")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = cfg["sender_email"]
    msg["To"] = cfg["recipient_email"]

    if jobs:
        msg["Subject"] = f"🤖 AI Jobs | {len(jobs)}个新职位 | {datetime.now().strftime('%m/%d')}"
        html = _build_html(jobs, stats)
    else:
        msg["Subject"] = f"😴 AI Jobs | 今天没有新职位 | {datetime.now().strftime('%m/%d')}"
        html = f"""<!DOCTYPE html><html><body style="font-family:sans-serif;background:#f5f5f5;padding:20px;">
            <div style="max-width:600px;margin:0 auto;background:white;border-radius:10px;
                        padding:40px;text-align:center;">
                <h2 style="color:#666;">😴 今天没有新职位</h2>
                <p style="color:#999;">所有结果和之前重复，明天继续！</p>
            </div></body></html>"""

    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        logger.info(f"📧 发送到 {cfg['recipient_email']}...")
        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(cfg["sender_email"], cfg["sender_password"])
            server.send_message(msg)
        logger.info("✅ 发送成功！")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ 认证失败！需要 App Password，不是登录密码")
        logger.error("   Outlook: https://account.live.com/proofs/manage/additional")
        return False
    except Exception as e:
        logger.error(f"❌ 发送失败: {e}")
        return False
