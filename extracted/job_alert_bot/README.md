# 🤖 AI Job Alert Bot v2

每天自动推送20+伦敦AI产品/分析职位到邮箱，**严格按4年经验级别过滤**。

## 核心改进：经验级别智能过滤

```
原始结果 (300+)
    ↓ 标题过滤：排除 Director/VP/Principal/Head/Intern/Graduate
    ↓ 描述评分：检测经验年限要求，标记⚠️偏资深
    ↓ 匹配加分：命中 KPI/SQL/Python/user research/AI/1-3 years 等加⭐
    ↓ 去重：对比历史推送记录
最终推送 (20-25个，按匹配分排序)
```

数据来源（5个）：
- **Adzuna API** — 聚合 Indeed, CV-Library, Totaljobs 等
- **Reed API** — 英国本土求职网站
- **LinkedIn** — 公开职位页面解析（无需登录）
- **Google Jobs** — 通过 SerpAPI，聚合所有平台
- **X/Twitter** — RSS Bridge 抓取招聘帖

邮件中每个职位会显示：
- **🎯 强匹配** — 多个技能关键词命中，经验要求3-5年
- **👍 匹配** — 部分关键词命中
- **⚠️ 可能偏资深** — 描述中要求6+年经验（但标题不含Director等才会保留）

## 快速设置（15分钟）

### 1. 获取 API 密钥

| API | 注册链接 | 费用 | 用途 |
|-----|---------|------|------|
| Adzuna | https://developer.adzuna.com/signup | 免费 250次/天 | 聚合 Indeed/CV-Library |
| Reed | https://www.reed.co.uk/developers/jobseeker | 免费 | 英国本土职位 |
| SerpAPI | https://serpapi.com/manage-api-key | 免费 100次/月 | Google Jobs 数据 |

> LinkedIn 和 X/Twitter 不需要 API 密钥，自动从公开页面抓取。

### 2. 生成 Outlook App Password

https://account.live.com/proofs/manage/additional → App passwords → Create

### 3. 编辑 config.py

```python
ADZUNA_APP_ID = "你的ID"
ADZUNA_APP_KEY = "你的Key"
REED_API_KEY = "你的Key"
SERPAPI_KEY = "你的SerpAPI Key"
EMAIL_CONFIG = {
    "sender_password": "你的App密码",
    ...
}
```

### 4. 测试

```bash
pip install requests
python main.py --test    # 测试，不发邮件
python main.py           # 正式运行
```

### 5. 每日定时运行

**PythonAnywhere（推荐，免费，不用开电脑）：**
1. https://www.pythonanywhere.com 注册
2. 上传文件 → Tasks → 添加 `cd ~/job_alert_bot && python main.py`
3. 设置时间 08:00 UTC

**Windows:** 任务计划程序 → 每天8:00 → 启动 python main.py

**Mac/Linux:** `crontab -e` → `0 8 * * * cd ~/job_alert_bot && python3 main.py`

## 文件说明

| 文件 | 作用 |
|------|------|
| config.py | 所有配置：API密钥、邮箱、搜索词、**过滤规则** |
| scrapers.py | 抓取 Adzuna + Reed + X/Twitter，**经验级别评分** |
| dedup.py | JSON去重，30天自动清理 |
| emailer.py | HTML邮件，显示匹配分数和⚠️标记 |
| main.py | 主程序 |

## 自定义过滤

在 `config.py` 中修改：

```python
# 加搜索词
SEARCH_QUERIES.append("new keyword")

# 排除更多资深职位
TOO_SENIOR_KEYWORDS.append("executive")

# 调整薪资范围
MIN_SALARY = 50000
```
