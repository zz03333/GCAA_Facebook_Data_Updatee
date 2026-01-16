# Onboarding Document - Facebook 社群數據分析框架

**Created**: 2026-01-15
**Project**: Facebook Community Data Analysis Framework for GCAA (綠色公民行動聯盟)
**Status**: Production-ready, actively running
**Onboarded By**: Claude (Sonnet 4.5)

---

## Executive Summary

This is a production-ready Facebook social media analytics system for GCAA (Green Citizens' Action Alliance), a Taiwanese civic organization. The system automates what previously took 2.75 hours of manual work down to 35 seconds, collecting Facebook page and post data, analyzing content, calculating KPIs, and generating reports.

**Key Stats** (as of latest run):
- 18 posts analyzed
- Average engagement rate: 2.06%
- Total reach: 279,990
- Pipeline execution: 33 seconds
- Efficiency gain: 280x faster than manual

---

## 1. Project Overview

### Purpose & Context
Automated Facebook analytics system that:
- Collects Facebook page and post data automatically
- Analyzes content (topics, timing, performance)
- Calculates KPIs and performance benchmarks
- Generates reports and exports to Google Sheets
- Provides REST API for automation

### Stakeholders
- **Organization**: GCAA (綠色公民行動聯盟 - Green Citizens' Action Alliance)
- **Use Case**: Replace manual social media analytics
- **Team Access**: Via Google Colab notebooks and Google Sheets

### Tech Stack
- Python 3.12, Flask 3.1.0, SQLite, Docker
- Facebook Graph API v23.0
- Google Sheets API
- Google Cloud Run deployment
- GitHub Actions CI/CD

---

## 2. Project Evolution

### Timeline
1. **Phase 1** (2025-09-30): Post-level data collection
2. **Phase 2** (2025-10-02): Page-level data collection
3. **Phase 3** (2025-12-12): Analytics engine
4. **Phase 4** (2025-12-13): Flexible query system
5. **Current** (2026-01): Cloud Run production deployment

### Original Goal
- Create Jupyter notebooks (.ipynb) for Google Colab
- Enable non-technical team members to run data collection
- Call Facebook API → Process → Write to Google Sheets

### Current State
- Evolved from notebooks to production Python scripts
- Full Flask API with multiple endpoints
- Automated Cloud Run deployment
- Comprehensive analytics and reporting

---

## 3. Architecture

### High-Level Data Flow
```
Facebook API
    ↓
Data Collection (collector_*.py)
    ↓
SQLite Database (engagement_data.db)
    ↓
Analytics Processing (analytics_processor.py)
    ↓
Reports (analytics_reports.py, query_analytics.py)
    ↓
Export (Google Sheets, API responses)
```

### Core Modules
- **Collection**: [main.py](main.py), [collector_page.py](collector_page.py), [run_pipeline.py](run_pipeline.py)
- **Database**: [setup_database.py](setup_database.py), [analytics_schema.py](analytics_schema.py), [db_utils.py](db_utils.py)
- **Analytics**: [analytics_processor.py](analytics_processor.py), [analytics_reports.py](analytics_reports.py), [query_analytics.py](query_analytics.py)
- **Export**: [export_to_sheets.py](export_to_sheets.py)
- **Config**: [config.py](config.py), [requirements.txt](requirements.txt), [Dockerfile](Dockerfile)

---

## 4. Database Schema

### Core Tables (7 total)

#### 1. `posts` - Post Basic Info
Primary key: `post_id`
Fields: post_id, page_id, created_time, message, permalink_url

#### 2. `post_insights_snapshots` - Metrics Snapshots
Primary key: `(post_id, fetch_date)`
Fields: likes_count, comments_count, shares_count, post_clicks, post_impressions_unique (reach), post_reactions_*, post_video_views_*

**Important**: Originally included impression breakdown metrics but Facebook deprecated them (2025-11-01). Now uses `post_impressions_unique` as primary reach metric.

#### 3. `posts_classification` - Content Classification
Primary key: `post_id`
Fields: media_type, message_length_tier, topic_primary, topic_secondary, time_slot, day_of_week, has_cta, is_weekend

#### 4. `posts_performance` - KPIs
Primary key: `(post_id, snapshot_date)`
Fields: engagement_rate, click_through_rate, share_rate, performance_tier (viral/high/average/low), percentile_rank, virality_score

#### 5. `benchmarks` - Performance Benchmarks
Primary key: `(benchmark_type, benchmark_key, period)`
Stores avg metrics by topic, time_slot, media_type, etc.

#### 6. `pages` - Page Information
Primary key: `page_id`

#### 7. `page_daily_metrics` - Daily Page Metrics
Primary key: `(page_id, date)`
Fields: fan_count, followers_count, page_impressions_unique, page_post_engagements, reactions

---

## 5. Facebook API Integration

### Configuration
- **Page ID**: 103640919705348
- **App ID**: 1085898272974442
- **API Version**: v23.0
- **Access Token**: Long-lived Page Access Token (~60 day validity)

### Valid Metrics (Updated 2025-12-12)

**Post Metrics** (11 metrics):
```python
POST_METRICS = [
    'post_clicks',              # ✓
    'post_impressions_unique',  # ✓ (reach)
    # post_impressions deprecated ✗
    # post_impressions_organic deprecated ✗
    # post_impressions_paid deprecated ✗
    'post_video_views',         # ✓
    'post_video_views_organic', # ✓
    'post_video_views_paid',    # ✓
    'post_reactions_like_total',  # ✓
    'post_reactions_love_total',  # ✓
    'post_reactions_wow_total',   # ✓
    'post_reactions_haha_total',  # ✓
    'post_reactions_sorry_total', # ✓
    'post_reactions_anger_total', # ✓
]
```

**Page Metrics** (4 daily + 1 lifetime):
- page_impressions_unique, page_post_engagements, page_video_views, page_actions_post_reactions_total
- fan_count (lifetime)

### Critical Issue: Deprecated Metrics
- **Date**: 2025-11-01
- **Impact**: Many impression metrics deprecated by Facebook
- **Solution**: Removed from [config.py](config.py), updated SQL queries, use `post_impressions_unique` instead
- **Validation**: Run `python3 test_metrics.py` to verify valid metrics

---

## 6. Analytics System

### Content Classification

**Topics** (7 types, Chinese keyword matching):
- `climate` - 氣候變遷 (climate change)
- `energy` - 能源政策 (energy policy)
- `event` - 活動宣傳 (event promotion)
- `edu` - 教育科普 (education)
- `news` - 時事評論 (news)
- `action` - 行動呼籲 (call to action)
- `org` - 組織動態 (org updates)

**Time Slots** (5 types, Taiwan timezone):
- `morning`: 06:00-11:59
- `noon`: 12:00-14:59
- `afternoon`: 15:00-17:59
- `evening`: 18:00-22:59
- `night`: 23:00-05:59

**Media Types**: text, photo, video, link

### KPI Definitions

| KPI | Formula | Purpose |
|-----|---------|---------|
| Engagement Rate | (reactions + comments + shares) / reach × 100 | Overall interaction |
| Click-Through Rate | clicks / reach × 100 | Content attraction |
| Share Rate | shares / reach × 100 | Virality |
| Comment Rate | comments / reach × 100 | Discussion |
| Virality Score | shares / reactions | Spread potential |

### Performance Tiers
Based on engagement rate percentiles:
- `viral` - Top 5% (≥ P95)
- `high` - Top 25% (≥ P75)
- `average` - Middle 50%
- `low` - Bottom 25% (< P25)

---

## 7. API Endpoints

Base URL (Cloud Run): `https://your-app.run.app`
Base URL (local): `http://localhost:8080`

### Main Endpoints

#### `POST /` - Complete Pipeline
Runs collection + analysis + export to Google Sheets

#### `POST /analytics` - Run Analytics Only
Process classification, KPIs, benchmarks

#### `GET /reports/weekly` - Weekly Report
Returns text report for last 7 days

#### `GET /reports/custom?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&granularity=weekly`
Custom date range report

#### `GET /query?type=trends&start_date=...&end_date=...&granularity=weekly`
Flexible queries with parameters:
- `type`: trends/topics/time_slots/top_posts
- `granularity`: daily/weekly/monthly
- `topic`: filter by topic
- `time_slot`: filter by time slot
- `limit`: number of results

#### `POST /export-sheets` - Export to Google Sheets
Exports 5 analysis worksheets

#### `GET /health` - Health Check
Returns `{"status": "healthy"}`

---

## 8. Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 setup_database.py
python3 analytics_schema.py

# Set environment variables
export FACEBOOK_ACCESS_TOKEN_BASE64="your_base64_token"
export GCP_SA_CREDENTIALS_BASE64="your_base64_credentials"

# Run pipeline
python3 run_pipeline.py

# Run Flask API
python3 main.py
```

### Cloud Run (Production)

**Deployment**: Automated via GitHub Actions on push to `main` branch

**Environment Variables**:
- `FACEBOOK_ACCESS_TOKEN_BASE64` - Base64-encoded Facebook token
- `GCP_SA_CREDENTIALS_BASE64` - Base64-encoded service account JSON
- `PORT` - 8080 (auto-set)

**Manual Deploy**:
```bash
gcloud run deploy facebook-analytics \
  --image gcr.io/gemini-api-reports/facebook-analytics \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated
```

### Scheduled Execution

**Cloud Scheduler** (recommended):
```bash
gcloud scheduler jobs create http facebook-daily-collection \
  --schedule="0 9 * * *" \
  --time-zone="Asia/Taipei" \
  --uri="https://your-app.run.app/" \
  --http-method=POST
```

**Cron** (local):
```bash
0 9 * * * cd /path/to/API_Parser && python3 run_pipeline.py >> logs/pipeline.log 2>&1
```

---

## 9. Common Tasks

### Run Complete Pipeline
```bash
python3 run_pipeline.py
```

### Query Data
```bash
# Weekly trends (last 30 days)
python3 query_analytics.py --days 30 --granularity weekly

# Top 10 posts
python3 query_analytics.py --top 10

# Energy topic analysis
python3 query_analytics.py --topic energy --top 20

# Custom date range
python3 query_analytics.py --start 2025-11-01 --end 2025-11-30

# JSON output
python3 query_analytics.py --days 7 --format json
```

### Export to Google Sheets
```bash
python3 export_to_sheets.py
```

### Test & Diagnose
```bash
# Test API connection
python3 -c "from run_pipeline import test_api_connection; test_api_connection()"

# Test valid metrics
python3 test_metrics.py

# Diagnose insights
python3 diagnose_insights.py
```

### Database Inspection
```bash
# Check row counts
python3 -c "
import sqlite3
conn = sqlite3.connect('engagement_data.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
for (table,) in cursor.fetchall():
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    print(f'{table}: {cursor.fetchone()[0]} rows')
conn.close()
"
```

---

## 10. Documentation Files

### Must-Read
1. **[plan.md](plan.md)** - Complete development plan and evolution
2. **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Phase 2-4 completion report
3. **[FLEXIBLE_QUERY_COMPLETE.md](FLEXIBLE_QUERY_COMPLETE.md)** - Query feature docs
4. **[README_ANALYTICS.md](README_ANALYTICS.md)** - User guide
5. **[QUERY_GUIDE.md](QUERY_GUIDE.md)** - Query usage guide
6. **[claude code prompt.md](claude%20code%20prompt.md)** - Original requirements

### Reference
- **[合併文章總集.md](合併文章總集.md)** - Official Facebook API docs (Chinese, 63k tokens)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[LOOKER_STUDIO_GUIDE.md](LOOKER_STUDIO_GUIDE.md)** - Dashboard setup

---

## 11. Known Issues & Workarounds

### 1. Facebook API Deprecated Metrics
**Issue**: Many impression metrics deprecated (2025-11-01)
**Workaround**: Use `post_impressions_unique` (reach), removed deprecated metrics from config

### 2. Access Token Expiration
**Issue**: Long-lived tokens expire ~60 days
**Workaround**: Manual renewal via Facebook Graph API Explorer, set calendar reminder

### 3. Database Size
**Current**: 2.7 MB (SQLite)
**Future**: Consider PostgreSQL for scale

### 4. Google Sheets Rate Limits
**Current**: Within free tier
**Workaround**: Batch operations, export only when needed

---

## 12. Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| All insights return 0 | Deprecated metrics | Check [config.py](config.py), run `test_metrics.py` |
| API 400 error | Invalid token | Renew Access Token |
| Sheets export fails | Missing credentials | Set `GCP_SA_CREDENTIALS_BASE64`, share sheet |
| Database locked | Concurrent access | Close connections, use `db_utils.get_connection()` |
| No data in range | Wrong date format | Use YYYY-MM-DD |
| Import errors | Missing deps | Run `pip install -r requirements.txt` |

---

## 13. Quick Reference

### Environment Variables
```bash
# Required
FACEBOOK_ACCESS_TOKEN_BASE64   # Base64 Facebook token
GCP_SA_CREDENTIALS_BASE64      # Base64 service account JSON

# Alternative (plain)
FACEBOOK_ACCESS_TOKEN
GCP_SA_CREDENTIALS

# Auto-set
PORT=8080  # Cloud Run
```

### Key Commands
```bash
python3 run_pipeline.py              # Complete pipeline
python3 query_analytics.py --days 30  # Query data
python3 export_to_sheets.py          # Export to Sheets
python3 test_metrics.py              # Test API
python3 main.py                      # Run Flask
```

### Important URLs
- Facebook Graph API Explorer: https://developers.facebook.com/tools/explorer
- Google Cloud Console: https://console.cloud.google.com/
- Project Spreadsheet: https://docs.google.com/spreadsheets/d/1HJXQrlB0eYJsHmioLMNfCKV_OXHqqgwtwRtO9s5qbB0/

---

## 14. File Structure

```
API_Parser/
├── main.py                         # Flask API entry point
├── run_pipeline.py                 # Pipeline orchestrator
├── config.py                       # Configuration
├── requirements.txt                # Dependencies
├── Dockerfile                      # Container
│
├── collector_page.py               # Page data collection
├── collector_ads.py                # Ad data collection
│
├── analytics_processor.py          # Classification + KPIs
├── analytics_reports.py            # Reports generation
├── analytics_trends.py             # Trends analysis
├── analytics_schema.py             # Analytics schema
├── query_analytics.py              # Flexible queries
│
├── export_to_sheets.py             # Google Sheets export
├── export_to_docs.py               # Google Docs export
│
├── setup_database.py               # Database init
├── db_utils.py                     # Database utilities
│
├── test_metrics.py                 # Test valid metrics
├── test_api_metrics.py             # Test API connection
├── diagnose_insights.py            # Diagnose insights
├── backfill_insights.py            # Backfill data
│
├── engagement_data.db              # SQLite database (2.7 MB)
│
├── *.ipynb                         # Jupyter notebooks (Colab)
├── *.md                            # Documentation
└── .github/workflows/              # CI/CD
```

---

## 15. Performance Metrics

**Current Performance** (2025-12-12 test):
- Pipeline execution: 33.1 seconds
- Posts processed: 18
- API requests: ~40
- Database operations: ~100
- Memory usage: < 100 MB
- Database size: 2.7 MB

**Efficiency**:
- Before (manual): 2.75 hours
- After (automated): 35 seconds
- Improvement: **280x faster**

---

## 16. Security

### Sensitive Data
- Facebook Access Token: Never commit, use env vars
- Service Account JSON: Never commit, base64 encode in env
- Database: Public FB data, but store securely
- API: Currently unauthenticated (internal use)

### Best Practices
- Rotate tokens regularly
- Separate dev/prod service accounts
- Monitor Cloud Run logs
- Consider API auth for production

---

## 17. Next Steps After Onboarding

1. **Verify Setup**
   ```bash
   python3 test_metrics.py
   python3 -c "from run_pipeline import test_api_connection; test_api_connection()"
   ```

2. **Run Test Pipeline**
   ```bash
   python3 -c "from run_pipeline import collect_post_data; collect_post_data(limit=5)"
   ```

3. **Explore Data**
   ```bash
   python3 query_analytics.py --days 7
   ```

4. **Review Recent Changes**
   ```bash
   git log --oneline -10
   git diff HEAD~1
   ```

5. **Check Current Status**
   - Review [plan.md](plan.md) for roadmap
   - Check GitHub Actions for deployment status
   - Verify Cloud Run service is running

---

## 18. Getting Help

### When Stuck
1. Check error logs (Cloud Run or local console)
2. Run diagnostics (`test_metrics.py`, `diagnose_insights.py`)
3. Validate config (env vars, database schema)
4. Review docs (this file, [plan.md](plan.md), implementation docs)
5. Check Facebook API status: developers.facebook.com/status
6. Inspect database with SQL queries

### Common Errors
- "Invalid metric" → Check [config.py](config.py), metric may be deprecated
- "Token expired" → Renew via Graph API Explorer
- "Permission denied" → Check service account has Sheets access
- "Table not found" → Run `setup_database.py` and `analytics_schema.py`

---

**Document Version**: 1.0
**Last Updated**: 2026-01-15
**Onboarding Complete**: ✅

---

## Appendix: Data Flow Example

### Complete Daily Run
1. Cloud Scheduler triggers `POST /`
2. `main.py` calls `run_pipeline.run_full_pipeline()`
3. Pipeline executes:
   - Test API connection
   - Collect page metrics (7 days)
   - Collect posts (30 days, max 50)
   - For each post: fetch info + insights
   - Store in database
   - Run `analytics_processor`:
     * Classify posts (topic, time_slot, media_type)
     * Calculate KPIs (ER, CTR, etc.)
     * Update benchmarks
   - Generate reports
4. `main.py` calls `export_to_sheets.main()`
5. Export 5 worksheets to Google Sheets
6. Return success response

### Query Flow
1. `GET /query?type=top_posts&limit=10`
2. Routes to `query_analytics.query_top_posts()`
3. SQL joins: posts + classification + performance + insights
4. Format as JSON
5. Return to client

---

**You are now onboarded!** 🎉

For questions or clarifications on specific components, refer to the detailed documentation files listed in section 10.
