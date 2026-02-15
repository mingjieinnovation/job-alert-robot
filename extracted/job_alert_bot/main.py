"""
main.py - AI Job Alert Bot 主程序

用法：
    python main.py          # 正式运行（抓取 + 发邮件）
    python main.py --test   # 测试（不发邮件）
    python main.py --dry    # 干跑（不记录，不发邮件）
"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from scrapers import fetch_all_jobs
from dedup import deduplicate
from emailer import send_email


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        ]
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    test_mode = "--test" in sys.argv
    dry_mode = "--dry" in sys.argv

    logger.info(f"🤖 AI Job Alert Bot | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"   模式: {'测试' if test_mode else '干跑' if dry_mode else '正式'}")
    logger.info(f"   过滤: 必须提及AI · ≤5年经验 · 排除 Director/VP/Principal/Intern/Graduate")

    # 1. 抓取
    all_jobs = fetch_all_jobs()

    if not all_jobs:
        logger.warning("⚠️ 未抓取到职位，检查 API 配置")
        if not test_mode:
            send_email([], {"sources": 0, "duplicates": 0})
        return

    # 2. 去重
    if dry_mode:
        new_jobs = all_jobs
    else:
        new_jobs = deduplicate(all_jobs)

    # 3. 截取
    if len(new_jobs) > config.MAX_DAILY_JOBS:
        new_jobs = new_jobs[:config.MAX_DAILY_JOBS]

    stats = {
        "sources": len(set(j.source for j in all_jobs)),
        "duplicates": len(all_jobs) - len(new_jobs),
    }

    # 4. 输出
    if test_mode or dry_mode:
        logger.info(f"\n{'='*55}")
        logger.info(f"📋 {len(new_jobs)} 个职位:")
        logger.info(f"{'='*55}")
        for i, j in enumerate(new_jobs, 1):
            exp = "⚠️偏资深" if not j.experience_ok else "✅"
            score = f"[分数:{j.match_score}]"
            logger.info(f"  #{i} {j.title}")
            logger.info(f"     🏢 {j.company} | 📍 {j.location} | {exp} {score}")
            if j.salary:
                logger.info(f"     💰 {j.salary}")
            if j.match_tags:
                logger.info(f"     标签: {' '.join(j.match_tags[:4])}")
            logger.info(f"     🔗 {j.url}")
        logger.info(f"{'='*55}")
        logger.info("✅ 测试完成（未发邮件）")
    else:
        if send_email(new_jobs, stats):
            logger.info(f"🎉 推送 {len(new_jobs)} 个职位")
        else:
            logger.error("💥 发送失败")


if __name__ == "__main__":
    main()
