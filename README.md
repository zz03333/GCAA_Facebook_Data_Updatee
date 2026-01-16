# Facebook Analytics System

**Automated Facebook data collection, analysis, and reporting pipeline**

---

## 🚀 Quick Start

### Run the pipeline
```bash
python run_pipeline.py
```

### Start the API server
```bash
python main.py
```

### Export to Google Sheets
```bash
python exporters/export_to_sheets.py
```

---

## 📚 Documentation

All documentation is in the **[docs/](docs/)** folder:

- **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** - 📍 **START HERE** - Complete project guide
- **[docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)** - Technical architecture & deployment
- **[docs/claude-code-prompt.md](docs/claude-code-prompt.md)** - Original project requirements
- **[docs/plan.md](docs/plan.md)** - Development history
- **[docs/合併文章總集.md](docs/合併文章總集.md)** - Facebook API reference (Chinese)

---

## 📁 Project Structure

```
API_Parser/
├── main.py                  # Flask API server (Cloud Run entry point)
├── run_pipeline.py          # Pipeline orchestrator
├── requirements.txt         # Python dependencies
├── Dockerfile              # Cloud Run deployment config
│
├── data/                   # Database files
│   ├── engagement_data.db  # SQLite database
│   └── backups/           # Database backups
│
├── docs/                   # All documentation
│   ├── PROJECT_STATUS.md  # 📍 Main guide
│   └── ...
│
├── scripts/                # Deployment scripts
│   ├── deploy.sh
│   ├── daily_run.sh
│   └── setup-scheduler.sh
│
├── utils/                  # Configuration & utilities
├── collectors/             # Facebook data collection
├── analytics/              # Data processing & analysis
├── exporters/              # Google Sheets export
├── tests/                  # Testing scripts
├── notebooks/              # Jupyter analysis
└── fb-dashboard/           # React dashboard (backup)
```

---

## 🎯 What This System Does

1. **Collects** data from Facebook Graph API daily
2. **Analyzes** posts: topic classification, KPI calculation, trends
3. **Exports** 21+ analytics tabs to Google Sheets with timestamps
4. **Visualizes** data in React dashboard

**Performance**: 280x faster than manual process (33s vs 2.75 hours)

---

## 🔧 Key Features

- ✅ Automated daily data collection via Cloud Run
- ✅ 14 Facebook metrics per post tracked
- ✅ Topic classification (Climate, Energy, Nuclear, etc.)
- ✅ KPI calculation (Engagement Rate, Share Rate, etc.)
- ✅ 21+ Google Sheets tabs with auto-timestamps
- ✅ Flexible query API for custom reports
- ✅ React dashboard for visualization

---

## 📊 Google Sheets Output

The system exports to **"Facebook Insights Metrics_Data Warehouse"** with:

- **Raw Data** (3 tabs): Posts, insights, page metrics
- **Analytics** (9 tabs): Best times, performance, trends
- **Ad Analytics** (5 tabs): Recommendations, campaigns, ROI
- **Reports** (2 tabs): Yearly analysis, pipeline logs
- **Documentation** (1 tab): Tab descriptions

Check the `data_updated_at` column to see when data was last refreshed.

---

## 🌐 Deployment

### Cloud Run (Production)
```bash
docker build -t gcr.io/[PROJECT_ID]/facebook-analytics .
gcloud run deploy facebook-analytics --image gcr.io/[PROJECT_ID]/facebook-analytics
```

### Environment Variables
```bash
FACEBOOK_ACCESS_TOKEN_BASE64  # Facebook API token (base64)
GCP_SA_CREDENTIALS_BASE64     # Google service account (base64)
PORT=8080                      # Server port
```

See [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) for detailed deployment instructions.

---

## 🔐 Credentials

Required credentials:
- Facebook Page Access Token (renew every 60 days)
- Google Cloud Service Account JSON key

See [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md#-credentials--secrets) for details.

---

## 📖 Need Help?

**Start here**: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)

**Common tasks**:
- Understanding project structure → [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- Deploying to Cloud Run → [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)
- Adding new Google Sheets tabs → [docs/PROJECT_STATUS.md#-how-to-add-new-tabs-to-google-sheets](docs/PROJECT_STATUS.md)
- API reference → [docs/合併文章總集.md](docs/合併文章總集.md)

---

**Last Updated**: 2026-01-15
**Status**: ✅ Production Ready
