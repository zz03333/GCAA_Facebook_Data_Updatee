# Further Folder Organization Plan

**Current Status**: 19 files in root (too cluttered)
**Goal**: Clean, professional structure

---

## 📊 Current Root Directory (Cluttered)

```
API_Parser/
├── .DS_Store                    (system file)
├── .gitignore                   ✅ keep in root
├── CLAUDE.md                    📄 documentation
├── Dockerfile                   ✅ keep in root (deployment)
├── MARKDOWN_FILES_GUIDE.md      📄 documentation
├── PROJECT_STATUS.md            📄 documentation
├── SYSTEM_ARCHITECTURE.md       📄 documentation
├── claude code prompt.md        📄 documentation
├── daily_run.sh                 🔧 deployment script
├── dashboard.html               ❌ old file
├── deploy.sh                    🔧 deployment script
├── engagement_data.db           💾 database
├── engagement_data.db.backup    💾 old backup
├── main.py                      ✅ keep in root (entry point)
├── plan.md                      📄 documentation
├── requirements.txt             ✅ keep in root (Python deps)
├── run_pipeline.py              ✅ keep in root (entry point)
├── setup-scheduler.sh           🔧 deployment script
├── 合併文章總集.md               📄 documentation
└── (directories: utils/, collectors/, analytics/, etc.)
```

---

## 🎯 Proposed Clean Structure

```
API_Parser/
│
├── 📌 Core Files (Keep in Root - 5 files)
│   ├── .gitignore
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── run_pipeline.py
│
├── 📂 docs/                     (All Documentation)
│   ├── CLAUDE.md
│   ├── PROJECT_STATUS.md        ⭐ Main guide
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── MARKDOWN_FILES_GUIDE.md
│   ├── claude-code-prompt.md
│   ├── plan.md
│   ├── 合併文章總集.md
│   └── archive/                 (Old summaries)
│       └── (11 old .md files)
│
├── 📂 scripts/                  (Deployment & Utility Scripts)
│   ├── daily_run.sh
│   ├── deploy.sh
│   └── setup-scheduler.sh
│
├── 📂 data/                     (Database Files)
│   ├── engagement_data.db       ⭐ Current database
│   └── backups/
│       └── engagement_data.db.backup
│
├── 📂 archive/                  (Old/Deprecated Files)
│   └── dashboard.html           (old standalone dashboard)
│
├── 📂 Python Packages (Already Clean)
│   ├── utils/
│   ├── collectors/
│   ├── analytics/
│   ├── exporters/
│   ├── tests/
│   └── notebooks/
│
└── 📂 fb-dashboard/             (React Dashboard - Keep as is)
    └── (backup of old dashboard)
```

---

## 📋 Reorganization Steps

### Step 1: Organize Documentation
```bash
# Move all markdown files to docs/
mv CLAUDE.md PROJECT_STATUS.md SYSTEM_ARCHITECTURE.md \
   MARKDOWN_FILES_GUIDE.md "claude code prompt.md" plan.md \
   合併文章總集.md docs/

# Create quick README in root that points to docs/
```

### Step 2: Organize Scripts
```bash
# Create scripts directory
mkdir -p scripts

# Move deployment scripts
mv daily_run.sh deploy.sh setup-scheduler.sh scripts/
```

### Step 3: Organize Database Files
```bash
# Create data directory with backups folder
mkdir -p data/backups

# Move database files
mv engagement_data.db data/
mv engagement_data.db.backup data/backups/
```

### Step 4: Archive Old Files
```bash
# Create archive directory
mkdir -p archive

# Move old dashboard
mv dashboard.html archive/
```

### Step 5: Update Import Paths (if needed)
```python
# In main.py and run_pipeline.py, update DB path if hardcoded
# Change: 'engagement_data.db'
# To:     'data/engagement_data.db'
```

### Step 6: Create Root README
```bash
# Create simple README.md in root pointing to docs/
```

---

## ✅ Benefits of This Structure

1. **Cleaner Root**
   - Only 5 core files in root
   - Easy to find entry points (main.py, run_pipeline.py)
   - Deployment files clearly visible (Dockerfile, requirements.txt)

2. **Better Organization**
   - All docs in `docs/` folder
   - All scripts in `scripts/` folder
   - All data in `data/` folder
   - Old files in `archive/` folder

3. **Professional Structure**
   - Follows standard project conventions
   - Easy for new developers to understand
   - Clear separation of concerns

4. **Easier Maintenance**
   - Know exactly where to find things
   - Documentation centralized
   - Scripts organized together

---

## ⚠️ Files That Need Path Updates

After moving files, these may need updates:

### 1. **utils/config.py**
```python
# Update DB_PATH
DB_PATH = 'data/engagement_data.db'  # was: 'engagement_data.db'
```

### 2. **deployment scripts** (in scripts/)
```bash
# Update relative paths if they reference files
# Example: scripts/deploy.sh may need '../Dockerfile'
```

### 3. **Dockerfile**
```dockerfile
# May need to update COPY commands if paths change
COPY data/engagement_data.db /app/data/
```

### 4. **.gitignore**
```
# Update paths
data/*.db
data/backups/
```

---

## 🚀 Quick Commands to Execute

Want me to run all these commands for you? I can:

1. ✅ Create new directories (docs/, scripts/, data/, archive/)
2. ✅ Move files to proper locations
3. ✅ Update path references in code
4. ✅ Create a simple README.md in root
5. ✅ Update .gitignore

**Ready to proceed?** Say "yes" and I'll execute the reorganization!

---

## 📝 Alternative: Minimal Reorganization

If full reorganization is too much, here's a minimal version:

**Just move documentation:**
```bash
# Only organize docs, keep everything else as is
mkdir -p docs
mv *.md docs/
# Keep CLAUDE.md in root for Claude Code
cp docs/CLAUDE.md ./
```

This gives you:
- Clean root (fewer .md files)
- All documentation centralized
- Minimal code changes needed

**Which approach do you prefer?**
1. Full reorganization (cleaner but needs path updates)
2. Minimal reorganization (just organize docs)
3. Custom (tell me what you want)
