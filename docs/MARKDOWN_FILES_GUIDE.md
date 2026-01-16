# Markdown Files - Keep vs Delete Guide

**Date**: 2026-01-15

---

## ✅ KEEP THESE (6 files) - Essential Documentation

### 1. **CLAUDE.md** (3.3K)
- **Purpose**: Claude Code instructions & development guidelines
- **Why Keep**: Tells Claude how to work on this project
- **Status**: ⭐ **CRITICAL** - Required for Claude Code

### 2. **PROJECT_STATUS.md** (13K)
- **Purpose**: Current comprehensive project guide
- **Why Keep**: Main reference for "where we are" and "how things work"
- **Status**: ⭐ **CURRENT** - Just created, replaces older summaries
- **Contains**:
  - Complete project structure
  - How raw data updates
  - How to add new tabs
  - Files to delete

### 3. **SYSTEM_ARCHITECTURE.md** (18K)
- **Purpose**: Detailed system architecture & data flow
- **Why Keep**: Technical reference for deployment & architecture
- **Status**: ✅ **USEFUL** - Detailed technical docs
- **Contains**:
  - Architecture diagrams
  - Database schema
  - API endpoints
  - Deployment instructions

### 4. **claude code prompt.md** (1.8K)
- **Purpose**: Original project requirements/prompt
- **Why Keep**: Historical reference of original goals
- **Status**: ✅ **REFERENCE** - Original vision

### 5. **plan.md** (18K)
- **Purpose**: Original development plan
- **Why Keep**: Historical reference of development process
- **Status**: ✅ **REFERENCE** - Development history

### 6. **合併文章總集.md** (226K)
- **Purpose**: Official Facebook API documentation (Chinese)
- **Why Keep**: Important reference for API usage
- **Status**: ⭐ **IMPORTANT** - API reference documentation

---

## 🗑️ ARCHIVE/DELETE THESE (10 files) - Old Summaries

These are **old progress reports** that are now outdated and redundant. All info is consolidated in **PROJECT_STATUS.md** and **SYSTEM_ARCHITECTURE.md**.

### Delete - Old Cleanup/Organization Notes
- ❌ **CLEANUP_SUMMARY.md** (5.1K) - File cleanup notes (outdated)
- ❌ **REORGANIZATION_SUMMARY.md** (2.4K) - File reorganization notes (outdated)

### Delete - Old Implementation Progress Reports
- ❌ **FINAL_SUMMARY.md** (7.1K) - Latest summary (superseded by PROJECT_STATUS.md)
- ❌ **PHASE_C_COMPLETE.md** (14K) - Phase C completion notes
- ❌ **FLEXIBLE_QUERY_COMPLETE.md** (11K) - Flexible query implementation
- ❌ **IMPLEMENTATION_COMPLETE.md** (10K) - Implementation notes
- ❌ **Plan for Page-Level Insights Collector.md** (4.0K) - Old specific plan

### Delete - Optional Usage Guides (covered in main docs)
- ❌ **DEPLOYMENT_GUIDE.md** (7.5K) - Deployment info (in SYSTEM_ARCHITECTURE.md)
- ❌ **QUERY_GUIDE.md** (9.7K) - Query usage guide (in SYSTEM_ARCHITECTURE.md)
- ❌ **README_ANALYTICS.md** (9.3K) - Analytics usage (in PROJECT_STATUS.md)
- ❌ **LOOKER_STUDIO_GUIDE.md** (3.5K) - Looker Studio guide (optional feature)

---

## 📦 Recommendation: Create Archive Folder

Instead of deleting, create an archive:

```bash
mkdir -p docs/archive

# Move old summaries to archive
mv CLEANUP_SUMMARY.md docs/archive/
mv REORGANIZATION_SUMMARY.md docs/archive/
mv FINAL_SUMMARY.md docs/archive/
mv PHASE_C_COMPLETE.md docs/archive/
mv FLEXIBLE_QUERY_COMPLETE.md docs/archive/
mv IMPLEMENTATION_COMPLETE.md docs/archive/
mv "Plan for Page-Level Insights Collector.md" docs/archive/
mv DEPLOYMENT_GUIDE.md docs/archive/
mv QUERY_GUIDE.md docs/archive/
mv README_ANALYTICS.md docs/archive/
mv LOOKER_STUDIO_GUIDE.md docs/archive/
```

---

## 📋 Final Clean Structure

After archiving, your root should have only:

```
API_Parser/
├── CLAUDE.md                    ⭐ Claude Code instructions
├── PROJECT_STATUS.md            ⭐ Current comprehensive guide
├── SYSTEM_ARCHITECTURE.md       ✅ Technical architecture
├── claude code prompt.md        ✅ Original requirements
├── plan.md                      ✅ Development history
├── 合併文章總集.md               ⭐ API documentation
│
├── docs/archive/                📦 Old summaries (archived)
│   └── (10 old .md files)
│
└── (rest of project files)
```

---

## 🎯 Quick Summary

**Keep (6 files):**
1. CLAUDE.md - Claude instructions ⭐
2. PROJECT_STATUS.md - Current guide ⭐
3. SYSTEM_ARCHITECTURE.md - Architecture docs
4. claude code prompt.md - Original goals
5. plan.md - Development history
6. 合併文章總集.md - API docs ⭐

**Archive (10 files):**
- All the "SUMMARY", "COMPLETE", "GUIDE" files
- They're old progress reports, now consolidated

**Total savings**: ~80KB of redundant docs → Cleaner project!
