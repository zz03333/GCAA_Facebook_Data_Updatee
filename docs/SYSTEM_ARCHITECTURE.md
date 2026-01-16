# GCAA Facebook Analytics System - Architecture & Data Flow

**Last Updated**: 2026-01-15
**System Status**: Production (Deployed to Cloud Run)

---

## 📊 System Overview

This is a **fully automated Facebook analytics pipeline** that:
1. Collects Facebook post data via Graph API
2. Analyzes engagement metrics and classifies content
3. Exports insights to Google Sheets
4. Visualizes data in a React dashboard

**Performance**: 280x faster than manual process (33s vs 2.75 hours)

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Facebook Graph API (v23.0)                                          │
│       │                                                               │
│       ├──> collector_page.py    (Page-level metrics)                 │
│       └──> collector_ads.py     (Post-level insights)                │
│                      │                                                │
│                      ▼                                                │
│           Google Sheets API                                           │
│           (Raw Data Storage)                                          │
│                      │                                                │
└──────────────────────┼──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ANALYTICS LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  run_pipeline.py (Orchestrator)                                      │
│       │                                                               │
│       ├──> analytics_processor.py                                    │
│       │    ├── Topic Classification (7 topics)                       │
│       │    ├── KPI Calculation (ER, Share Rate, etc.)                │
│       │    └── Performance Tier Assignment                           │
│       │                                                               │
│       ├──> analytics_trends.py                                       │
│       │    └── Trend analysis & predictions                          │
│       │                                                               │
│       └──> analytics_reports.py                                      │
│            └── Weekly/custom report generation                       │
│                      │                                                │
│                      ▼                                                │
│        SQLite Database                                                │
│        facebook_data_warehouse.db                                    │
│        (7 tables, 18 posts currently)                                │
│                      │                                                │
└──────────────────────┼──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXPORT LAYER                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  export_to_sheets.py                                                 │
│       │                                                               │
│       ├──> Google Sheets (Analytics Output)                          │
│       │    ├── Summary Dashboard                                     │
│       │    ├── Topic Performance                                     │
│       │    ├── Time Slot Analysis                                    │
│       │    └── Top Posts                                             │
│       │                                                               │
│       └──> export_to_docs.py (Optional)                              │
│            └── Google Docs report generation                         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      VISUALIZATION LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  fb-dashboard/ (React + Vite)                                        │
│       │                                                               │
│       ├──> Data Sync:                                                │
│       │    └── sync/data_sync.py                                     │
│       │        ├── Reads: Google Sheets (raw_posts + raw_insights)  │
│       │        └── Generates: dist/data/*.json                       │
│       │                                                               │
│       └──> Frontend (3 tabs):                                        │
│            ├── Dashboard - KPIs, trends, heatmaps                    │
│            ├── Explorer - Post table with filters                    │
│            └── Analytics - Scatter plot analysis                     │
│                      │                                                │
│                      ▼                                                │
│        Firebase Hosting                                               │
│        https://[your-project].web.app                                │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Data Flow

### Step 1: Data Collection (Daily/On-Demand)

**Trigger**: Cloud Scheduler → Cloud Run endpoint (`/` or POST)

```python
# main.py orchestrates:
1. run_pipeline.run_full_pipeline()
   ├── Calls Facebook Graph API
   ├── Fetches posts (last 90 days by default)
   ├── Fetches post insights (14 metrics per post)
   └── Stores raw data → Google Sheets

2. export_to_sheets.main()
   └── Exports analytics → Google Sheets
```

**Data Sources**:
- **Facebook Graph API v23.0** (`/{page-id}/posts`, `/{post-id}/insights`)
- **Page ID**: `103640919705348` (GCAA 粉絲專頁)
- **Access Token**: Long-lived token (expires ~60 days)

**Metrics Collected** (14 metrics):
```python
POST_INSIGHTS_METRICS = [
    'post_clicks',
    'post_impressions_unique',
    'post_reactions_like_total',
    'post_reactions_love_total',
    'post_reactions_wow_total',
    'post_reactions_haha_total',
    'post_reactions_sorry_total',
    'post_reactions_anger_total',
    'post_video_views',
    'post_video_views_organic',
    'post_video_views_paid',
]
```

### Step 2: Analytics Processing

**Processor**: `analytics_processor.py`

**Operations**:
1. **Topic Classification** (7 topics):
   - Climate (氣候), Energy (能源), Nuclear (核能)
   - Event (活動), Advocate (倡議), Education (教育), Other (其他)

2. **KPI Calculation**:
   - Engagement Rate (ER) = (Reactions + Comments + Shares) / Reach × 100
   - Share Rate = Shares / Reach × 100
   - Click Rate = Clicks / Reach × 100

3. **Performance Tier Assignment** (4 tiers):
   - 🔥 Viral: ER > 5%
   - ⬆️ High: ER > 3%
   - ➡️ Average: ER > 1%
   - ⬇️ Low: ER ≤ 1%

4. **Benchmark Updates**: Rolling averages per topic

**Output**: SQLite database (`facebook_data_warehouse.db`)

### Step 3: Export to Google Sheets

**Exporter**: `export_to_sheets.py`

**Google Sheets Structure**:
```
Spreadsheet: "Faceboook Insights Metrics_Data Warehouse"
├── raw_data (raw posts + insights)
├── raw_page_data (page-level metrics)
├── summary_dashboard (aggregated KPIs)
├── topic_performance (topic breakdown)
├── time_slot_analysis (hourly/weekday patterns)
└── top_posts (best performers)
```

### Step 4: Dashboard Visualization

**Dashboard**: `fb-dashboard/` (React + Vite)

**Data Sync Process**:
```bash
# Manual sync (when needed):
cd fb-dashboard/sync
python data_sync.py

# This reads:
- Google Sheets → raw_posts + raw_post_insights

# And generates:
- fb-dashboard/dist/data/posts.json (all posts)
- fb-dashboard/dist/data/daily.json (daily aggregates)
- fb-dashboard/dist/data/stats.json (statistics)
```

**Frontend Features**:
- **Dashboard Tab**: KPI cards, trend chart, topic/action type charts, heatmap
- **Explorer Tab**: Searchable/filterable post table
- **Analytics Tab**: Scatter plot (reach vs engagement)

**Deployment**:
```bash
cd fb-dashboard
npm run build
firebase deploy
```

---

## 🌐 Connected Services

### 1. Facebook Graph API
- **Endpoint**: `https://graph.facebook.com/v23.0/`
- **Authentication**: Long-lived Page Access Token
- **Permissions**: `pages_read_engagement`, `read_insights`
- **Rate Limit**: 200 calls/hour/user (handled with 0.2s delays)
- **Token Expiry**: ~60 days (manual renewal required)

### 2. Google Sheets API
- **Spreadsheet ID**: `1HJXQrlB0eYJsHmioLMNfCKV_OXHqqgwtwRtO9s5qbB0`
- **Authentication**: GCP Service Account (JSON key)
- **Permissions**: Editor access to spreadsheet
- **Usage**:
  - Raw data storage (input)
  - Analytics output (export)

### 3. Google Cloud Run
- **Service**: Flask API (`main.py`)
- **Region**: (To be confirmed)
- **Container**: Docker image built from `Dockerfile`
- **Endpoints**:
  ```
  GET/POST /              → Full pipeline (collection + export)
  GET     /health         → Health check
  POST    /analytics      → Run analytics only
  GET     /reports/weekly → Generate weekly report
  GET     /query          → Custom query API
  GET     /reports/custom → Custom report
  POST    /export-sheets  → Export to Sheets only
  ```
- **Trigger**: Cloud Scheduler (daily at configured time)
- **Environment Variables**:
  ```bash
  FACEBOOK_ACCESS_TOKEN_BASE64  # Base64-encoded token
  GCP_SA_CREDENTIALS_BASE64     # Base64-encoded service account JSON
  PORT                          # Default: 8080
  ```

### 4. Firebase Hosting
- **Project**: `esg-reports-collection` (or similar)
- **Deployed Site**: `https://[project-id].web.app`
- **Content**: React dashboard (`fb-dashboard/dist/`)
- **Configuration**: `fb-dashboard/firebase.json`

### 5. Firestore (Optional/Legacy)
- **Status**: Currently NOT actively used
- **Reason**: Dashboard uses static JSON files instead
- **Potential**: Could be used for real-time data sync in future

---

## 🔐 Credentials & Secrets

### Required Credentials

1. **Facebook Access Token**
   - Location: Environment variable `FACEBOOK_ACCESS_TOKEN_BASE64`
   - Type: Long-lived Page Access Token
   - Renewal: Every ~60 days via Facebook Graph API Explorer
   - Permissions: `pages_read_engagement`, `read_insights`

2. **Google Service Account**
   - Location: Environment variable `GCP_SA_CREDENTIALS_BASE64`
   - Type: JSON key file (base64-encoded)
   - Permissions: Editor access to Google Sheets
   - Used by: `main.py`, `export_to_sheets.py`, `fb-dashboard/sync/`

3. **Firebase Config** (for dashboard)
   - Location: `fb-dashboard/src/` (if needed)
   - Type: Firebase web app config
   - Note: Current setup uses static JSON files, not Firestore

---

## 📅 Deployment & Scheduling

### Current Deployment

**Cloud Run Service**:
```bash
# Build and deploy
docker build -t gcr.io/[PROJECT_ID]/facebook-analytics .
docker push gcr.io/[PROJECT_ID]/facebook-analytics
gcloud run deploy facebook-analytics \
  --image gcr.io/[PROJECT_ID]/facebook-analytics \
  --platform managed \
  --region [REGION] \
  --set-env-vars FACEBOOK_ACCESS_TOKEN_BASE64=[TOKEN],GCP_SA_CREDENTIALS_BASE64=[CREDS]
```

**Cloud Scheduler**:
```bash
# Daily trigger at 8:00 AM
gcloud scheduler jobs create http facebook-daily-sync \
  --schedule="0 8 * * *" \
  --uri="https://[CLOUD_RUN_URL]/" \
  --http-method=POST
```

### Dashboard Deployment

```bash
# Build React app
cd fb-dashboard
npm run build

# Deploy to Firebase
firebase deploy
```

### Data Sync (Manual)

**When to run**:
- After new Facebook data is collected
- Before updating the dashboard

**How to run**:
```bash
cd fb-dashboard/sync
python data_sync.py

# Then rebuild and redeploy dashboard
cd ..
npm run build
firebase deploy
```

---

## 🗄️ Database Schema

**Database**: `facebook_data_warehouse.db` (SQLite)

**Tables** (7 total):

1. **raw_posts** - Raw Facebook post data
   - Columns: post_id, page_id, page_name, message, created_time, permalink_url, etc.

2. **raw_post_insights** - Raw insights metrics
   - Columns: post_id, post_clicks, post_impressions_unique, reactions, etc.

3. **posts_classified** - Posts with topic classification
   - Columns: post_id, topic, confidence_score, classified_at

4. **post_kpis** - Calculated KPIs
   - Columns: post_id, engagement_rate, share_rate, click_rate, performance_tier

5. **benchmarks** - Rolling average benchmarks per topic
   - Columns: topic, avg_engagement_rate, avg_share_rate, updated_at

6. **trends** - Trend analysis data
   - Columns: date, metric, value, trend_direction

7. **reports** - Generated reports
   - Columns: report_id, report_type, generated_at, content

**Current Stats**:
- Total posts: 18
- Average ER: 2.06%
- Date range: Recent 90 days

---

## 🔧 Maintenance Tasks

### Regular Maintenance

**Every 60 days**:
- [ ] Renew Facebook Access Token
  - Go to Facebook Graph API Explorer
  - Generate new long-lived token
  - Update `FACEBOOK_ACCESS_TOKEN_BASE64` in Cloud Run

**Every week**:
- [ ] Check Cloud Run logs for errors
- [ ] Verify Google Sheets data is updating
- [ ] Review dashboard for data freshness

**As needed**:
- [ ] Update metric definitions if Facebook API changes
- [ ] Sync dashboard data (`fb-dashboard/sync/data_sync.py`)
- [ ] Rebuild and redeploy dashboard

### Troubleshooting

**Issue**: No new data in Google Sheets
- Check Cloud Scheduler is running
- Check Cloud Run logs for errors
- Verify Facebook token is valid: `curl "https://graph.facebook.com/v23.0/me?access_token=TOKEN"`

**Issue**: Dashboard shows old data
- Run `fb-dashboard/sync/data_sync.py`
- Rebuild and redeploy dashboard

**Issue**: API rate limit errors
- Increase delay in `main.py` (currently 0.2s between requests)
- Reduce batch size

---

## 🚀 Quick Commands

### Run Full Pipeline Locally
```bash
python main.py
# Or test individual components:
python run_pipeline.py
python export_to_sheets.py
```

### Query Analytics
```bash
# Weekly report
curl https://[CLOUD_RUN_URL]/reports/weekly

# Custom query
curl "https://[CLOUD_RUN_URL]/query?start_date=2025-11-01&end_date=2025-11-30&type=trends"
```

### Deploy Dashboard
```bash
cd fb-dashboard
npm install
npm run build
firebase deploy
```

### Sync Dashboard Data
```bash
cd fb-dashboard/sync
python data_sync.py
```

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Pipeline runtime | 33 seconds |
| Manual process time | 2.75 hours |
| **Speedup** | **280x faster** |
| Posts analyzed | 18 (current) |
| Metrics per post | 14 |
| Average engagement rate | 2.06% |
| Database size | ~50 KB |

---

## 🔮 Future Improvements

- [ ] Real-time dashboard updates (use Firestore instead of JSON)
- [ ] Automated token renewal
- [ ] Email/Slack notifications for weekly reports
- [ ] Predictive analytics (trending topics, optimal post times)
- [ ] A/B testing framework for content strategies
- [ ] Integration with other platforms (Instagram, Twitter)
- [ ] Mobile app for on-the-go analytics

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| [main.py](main.py) | Flask API orchestrator |
| [run_pipeline.py](run_pipeline.py) | Pipeline orchestrator |
| [analytics_processor.py](analytics_processor.py) | Topic classification & KPIs |
| [export_to_sheets.py](export_to_sheets.py) | Google Sheets exporter |
| [query_analytics.py](query_analytics.py) | Flexible query API |
| [fb-dashboard/src/App.jsx](fb-dashboard/src/App.jsx) | React dashboard |
| [fb-dashboard/sync/data_sync.py](fb-dashboard/sync/data_sync.py) | Dashboard data sync |
| [Dockerfile](Dockerfile) | Cloud Run container |
| [plan.md](plan.md) | Original development plan |

---

**Questions?** Check the onboarding doc at `.claude/tasks/onboard-20260115/onboarding.md`
