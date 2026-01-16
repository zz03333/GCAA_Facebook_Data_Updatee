# Project Status & Structure Guide

**Last Updated**: 2026-01-15
**Your Question**: "Where are we now? How does the system work? What files are not needed?"

---

## 📍 WHERE WE ARE NOW

### Current Status
✅ **PRODUCTION READY** - All systems are operational and organized

The system is a **fully automated Facebook analytics pipeline** that:
1. **Collects** data from Facebook Graph API
2. **Analyzes** posts and engagement metrics
3. **Exports** insights to Google Sheets (20+ tabs)
4. **Visualizes** data in a React dashboard

### What Changed Recently
- ✅ Organized 21 Python files into 5 clean directories
- ✅ Added timestamp columns to all Google Sheets tabs
- ✅ Created Tab Documentation sheet explaining all 20+ tabs
- ✅ System runs daily via Cloud Run + Cloud Scheduler

---

## 🗂️ PROJECT STRUCTURE

```
API_Parser/
├── main.py                    ⭐ Flask API server (Cloud Run entry point)
├── run_pipeline.py            ⭐ Pipeline orchestrator (data collection)
├── Dockerfile                 🚀 Cloud Run deployment config
├── requirements.txt           📦 Python dependencies
├── engagement_data.db         💾 SQLite database (analytics data)
│
├── utils/                     🔧 Core utilities (3 files)
│   ├── config.py             → Facebook/Google API configs
│   ├── db_utils.py           → Database helper functions
│   └── setup_database.py     → Database schema setup
│
├── collectors/                📥 Data collection scripts (4 files)
│   ├── collector_page.py     → Page-level metrics (daily stats)
│   ├── collector_ads.py      → Ad campaign data
│   ├── backfill_insights.py  → Historical data backfill
│   └── fetch_2025_data.py    → Date-specific fetching
│
├── analytics/                 📊 Data processing (6 files)
│   ├── analytics_processor.py → Topic classification & KPI calculation
│   ├── analytics_reports.py   → Report generation
│   ├── analytics_schema.py    → Database schema definitions
│   ├── analytics_trends.py    → Trend analysis
│   ├── ad_predictor.py        → Ad performance prediction
│   └── query_analytics.py     → Flexible query API
│
├── exporters/                 📤 Data export (3 files)
│   ├── export_to_sheets.py   ⭐ Google Sheets export (20+ tabs)
│   ├── export_to_docs.py      → Google Docs export (optional)
│   └── firestore_sync.py      → Firebase sync (optional)
│
├── tests/                     🧪 Test scripts (5 files)
│   └── (diagnostic & testing scripts)
│
├── notebooks/                 📓 Jupyter notebooks (5 files)
│   └── (data exploration & analysis)
│
└── fb-dashboard/              🌐 React dashboard (BACKUP)
    ├── src/                   → React components
    ├── dist/data/             → Static JSON data files
    ├── sync/data_sync.py      → Syncs Google Sheets → JSON
    └── (Firebase hosting configs)
```

---

## 🔄 HOW RAW DATA IS UPDATED

### Automated Daily Flow (Cloud Run)

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Cloud Scheduler triggers Cloud Run         │
│         POST request to main.py at 8:00 AM daily    │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: main.py runs the pipeline                  │
│         run_pipeline.run_full_pipeline()            │
│                                                      │
│  ├─ Connects to Facebook Graph API                  │
│  ├─ Fetches posts (last 30 days)                    │
│  ├─ Fetches post insights (14 metrics per post)     │
│  └─ Saves to engagement_data.db (SQLite)            │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: Analytics processing                       │
│         analytics_processor.py runs                 │
│                                                      │
│  ├─ Classifies posts by topic (Climate/Energy/etc) │
│  ├─ Calculates KPIs (Engagement Rate, etc.)        │
│  └─ Updates benchmarks & trends                     │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: Export to Google Sheets                    │
│         exporters/export_to_sheets.py runs          │
│                                                      │
│  └─ Creates/updates 20+ tabs in Google Sheets      │
│     with latest data + timestamp column             │
└─────────────────────────────────────────────────────┘
```

### Key Data Sources

| Data Source | What it provides | Update frequency |
|-------------|------------------|------------------|
| **Facebook Graph API** | Post metadata, insights, reactions | Daily (automated) |
| **SQLite Database** | Processed analytics, KPIs, trends | Daily (automated) |
| **Google Sheets** | Final reports & visualizations | Daily (automated) |

### Raw Data Tables (3 tabs in Google Sheets)

1. **raw_posts** - Post metadata
   - Columns: post_id, message, created_time, permalink_url, etc.
   - Source: Facebook `/{page-id}/posts` API

2. **raw_post_insights** - Engagement metrics
   - Columns: post_id, clicks, impressions, reactions, video views, etc.
   - Source: Facebook `/{post-id}/insights` API

3. **raw_page_daily** - Page-level daily stats
   - Columns: date, page_fans, post_impressions, etc.
   - Source: Facebook `/{page-id}/insights` API

---

## ➕ HOW TO ADD NEW TABS TO GOOGLE SHEETS

### Step-by-Step Process

#### 1. Create Export Function in `exporters/export_to_sheets.py`

```python
def export_your_new_tab(client, conn):
    """Export your custom analysis"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet('your_tab_name')
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title='your_tab_name',
                rows=500,
                cols=10
            )

        # Query data from database
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column1, column2, column3
            FROM your_table
            ORDER BY some_column
        """)
        rows = cursor.fetchall()

        # Prepare data for Google Sheets
        values = [
            ['Column 1', 'Column 2', 'Column 3']  # Header row
        ]

        for row in rows:
            values.append([
                row[0],  # column1
                row[1],  # column2
                row[2]   # column3
            ])

        # Export to sheet (with automatic timestamp column)
        update_with_timestamp(worksheet, 'A1', values)

        print(f"  ✓ 已導出 your_tab_name ({len(rows)} records)")
        return True

    except Exception as e:
        print(f"  ✗ 導出 your_tab_name 失敗: {e}")
        return False
```

#### 2. Register Function in `main()` function (same file)

Find the `main()` function around line 2108 and add your export:

```python
def main():
    # ... existing code ...

    # Add your export here (example location)
    print("\n📊 Custom Analysis:")
    if export_your_new_tab(client, conn):
        success_count += 1

    # Update total_count
    total_count = 22  # Increment by 1

    # ... rest of code ...
```

#### 3. Update Tab Documentation

Edit the `export_tab_documentation()` function around line 2015:

```python
def export_tab_documentation(client):
    # ... existing code ...

    docs = [
        ['Tab Name', 'Category', 'Purpose', 'Update Frequency', 'Key Columns'],

        # ... existing tabs ...

        # Add your new tab
        [
            'your_tab_name',
            'Analytics',  # or 'Raw Data', 'Reports', etc.
            'Description of what this tab shows',
            'Daily',
            'column1, column2, column3'
        ],
    ]
    # ... rest of code ...
```

#### 4. Test Locally

```bash
cd /Users/jinsoon/Desktop/GCAA/03_社群宣傳/API_Parser
python exporters/export_to_sheets.py
```

#### 5. Deploy to Cloud Run

```bash
# Rebuild Docker image
docker build -t gcr.io/[PROJECT_ID]/facebook-analytics .

# Deploy to Cloud Run
gcloud run deploy facebook-analytics \
  --image gcr.io/[PROJECT_ID]/facebook-analytics \
  --region asia-east1
```

---

## 🗑️ FILES NOT NEEDED TO RUN THE SYSTEM

### ⚠️ Can be archived/deleted (but keep fb-dashboard as backup)

#### Documentation Files (Safe to archive)
```
CLEANUP_SUMMARY.md
DEPLOYMENT_GUIDE.md
FLEXIBLE_QUERY_COMPLETE.md
IMPLEMENTATION_COMPLETE.md
LOOKER_STUDIO_GUIDE.md
PHASE_C_COMPLETE.md
Plan for Page-Level Insights Collector.md
QUERY_GUIDE.md
README_ANALYTICS.md
REORGANIZATION_SUMMARY.md
claude code prompt.md
合併文章總集.md
```

#### Old Test Data (Safe to delete)
```
engagement_data.db.backup  (old backup, can delete if current DB works)
```

#### Dashboard-related (Keep fb-dashboard as backup, others optional)
```
dashboard.html  (standalone HTML, replaced by fb-dashboard)
fb-dashboard/   (KEEP THIS - it's your old React dashboard backup)
```

#### Deployment Scripts (Optional - only needed for manual deployment)
```
deploy.sh
setup-scheduler.sh
daily_run.sh
```

### ✅ CRITICAL FILES - DO NOT DELETE

These files are essential for the system to run:

#### Core System
- `main.py` - Flask API server
- `run_pipeline.py` - Pipeline orchestrator
- `Dockerfile` - Cloud Run deployment
- `requirements.txt` - Python dependencies
- `engagement_data.db` - SQLite database

#### Directories (all files in these are needed)
- `utils/` - Configuration & DB utilities
- `collectors/` - Data collection scripts
- `analytics/` - Data processing
- `exporters/` - Google Sheets export
- `tests/` - Testing & diagnostics
- `notebooks/` - Jupyter analysis (optional but useful)

#### Keep for Reference
- `FINAL_SUMMARY.md` - Latest project summary
- `SYSTEM_ARCHITECTURE.md` - System architecture doc
- `PROJECT_STATUS.md` - This file!
- `plan.md` - Original development plan
- `CLAUDE.md` - Claude Code instructions

---

## 🎯 QUICK REFERENCE

### Run Full Pipeline Locally
```bash
python run_pipeline.py
```

### Export to Google Sheets Only
```bash
python exporters/export_to_sheets.py
```

### Check What Tabs Are Exported
Look at `exporters/export_to_sheets.py` main() function (line 2108)
Currently exports **21 tabs** total:

**Raw Data (3 tabs)**
- raw_posts
- raw_post_insights
- raw_page_daily

**Analytics - Best Times (3 tabs)**
- best_posting_times_general
- best_posting_times_by_topic
- best_posting_times_by_action

**Analytics - Performance (3 tabs)**
- format_type_performance
- issue_topic_performance
- format_issue_cross

**Analytics - Posts (3 tabs)**
- top_posts
- quadrant_analysis
- deep_dive_metrics

**Analytics - Trends (2 tabs)**
- weekly_trends
- hourly_performance

**Ad Analytics (5 tabs)**
- ad_recommendations
- trending_posts
- organic_vs_paid
- ad_campaigns
- ad_roi_analysis

**Data Export (2 tabs)**
- ad_recommendations_data
- organic_vs_paid_data

**Reports (2 tabs)**
- yearly_posting_analysis
- pipeline_logs

**Documentation (1 tab)**
- 📖 Tab Documentation

### View Google Sheets
Open: "Facebook Insights Metrics_Data Warehouse"
Check the `data_updated_at` column (last column) to see when data was last refreshed

---

## 🔧 MAINTENANCE

### Daily (Automated)
- Cloud Scheduler triggers pipeline at 8:00 AM
- Collects latest Facebook data
- Updates all Google Sheets tabs
- Logs run to `pipeline_logs` tab

### Weekly (Manual check)
- Review Google Sheets for data freshness
- Check Cloud Run logs for errors

### Every 60 Days (Manual)
- Renew Facebook Access Token
- Update `FACEBOOK_ACCESS_TOKEN_BASE64` in Cloud Run

---

## 📞 NEED HELP?

**Common Tasks:**
- Adding new tabs → See "How to Add New Tabs" section above
- Checking data freshness → Open Google Sheets, check `data_updated_at` column
- Running pipeline manually → `python run_pipeline.py`
- Viewing system architecture → Open [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)

**Files to Reference:**
- Full project details → [FINAL_SUMMARY.md](FINAL_SUMMARY.md)
- System architecture → [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
- Original goals → [claude code prompt.md](claude code prompt.md)
- Development history → [plan.md](plan.md)
