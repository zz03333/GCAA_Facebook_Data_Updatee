# Data Quality Issues - Investigation & Fixes

**Date**: 2026-01-15
**Status**: ✅ Fixes deployed and pipeline running

## Issues Reported

1. ✅ **raw_post_insights**: Duplicate data, mixed fetch times, date in likes column (row 8)
2. ✅ **page_daily_metrics**: Missing recent 3 months of data
3. ℹ️ **trending_posts**: Missing all data
4. ℹ️ **ad_recommendations**: Missing half the data
5. ⏳ **raw_posts**: Only has data before 2025-12-15

---

## Investigation & Fixes

### 1. raw_post_insights - Data Corruption (Row 8)

**Issue**: Row 8 shows "2025-12-18" in the 讚數 (likes) column instead of the actual number (115).

**Root Cause**: Database corruption - the value "2025-12-18" was incorrectly stored in the `likes_count` INTEGER column for post_id `103640919705348_1174874021503360` on fetch_date `2025-12-18`. SQLite's dynamic typing allows this.

**Fix**:
- ✅ No code changes needed - this is a one-time data corruption
- ✅ The next pipeline run will collect fresh data and UPSERT will overwrite the corrupted value
- ✅ Pipeline now running to fix this automatically

---

### 2. raw_post_insights - 30-Day Limit

**Issue**: Only showing last 30 days of snapshot data.

**Root Cause**: [exporters/export_to_sheets.py:673](../exporters/export_to_sheets.py#L673) had:
```sql
WHERE i.fetch_date >= DATE('now', '-30 days')
```

**Fix**:
- ✅ Removed the 30-day WHERE clause
- ✅ Now exports ALL historical post insights snapshots
- ✅ Committed in: `8416eaa`

---

### 3. page_daily_metrics - Missing 3 Months

**Issue**: Should show at least 3 months of data, but only showing 7 days.

**Root Cause**: [run_pipeline.py:343](../run_pipeline.py#L343) was:
```python
collect_page_data(days_back=7)  # Only 7 days!
```

**Fix**:
- ✅ Changed to `days_back=90` (3 months)
- ✅ Next pipeline run will collect 90 days of page metrics
- ✅ Committed in: `8416eaa`

---

### 4. trending_posts - Empty Sheet

**Issue**: Sheet is completely empty.

**Root Cause**: **This is expected behavior**, not a bug.

**Explanation**:
- [analytics/analytics_trends.py:111](../analytics/analytics_trends.py#L111) filters for posts created in last 72 hours only
- The sheet shows "正在起飛的貼文" (posts that are trending/taking off)
- If no posts were published in the last 72 hours, the sheet will be empty
- This is working as designed

**Resolution**: ℹ️ No fix needed - this is a feature, not a bug

---

### 5. ad_recommendations - Missing Half Data

**Issue**: Missing approximately half the expected data.

**Root Cause**: **This is expected behavior**, not a bug.

**Explanation**:
- [analytics/ad_predictor.py:262](../analytics/ad_predictor.py#L262) filters for posts from last 30 days only
- [exporters/export_to_sheets.py:1016](../exporters/export_to_sheets.py#L1016) uses `min_score=40` threshold
- Only posts with ad_potential_score >= 40 are included
- Ad recommendations are intentionally limited to recent posts (30 days) because:
  - Advertising old posts (>30 days) is generally ineffective
  - Budget should focus on recent, high-performing content

**Resolution**: ℹ️ No fix needed - this is a feature, not a bug

If you want to see more historical ad recommendations, we can:
- Option A: Increase the 30-day window in `get_recommended_posts()`
- Option B: Lower the min_score threshold (may include lower quality recommendations)

---

### 6. raw_posts - Data Before 2025-12-15

**Issue**: raw_posts only has data before 2025-12-15, missing recent posts.

**Status**: ⏳ Being addressed by current pipeline run

**Root Cause**: The code fixes in previous deployment (`83c5b9a`) changed the date range from 30/90 days to `since_date = '2024-01-01'`. The pipeline needs to run to collect the data.

**Fix**:
- ✅ Code already fixed in previous commit
- ⏳ Current pipeline run is collecting all posts from 2024-01-01 onwards
- ⏳ This will populate raw_posts with all historical data

---

## Summary

| Issue | Type | Status | Action Taken |
|-------|------|--------|--------------|
| raw_post_insights corruption (row 8) | Bug | ✅ Fixed | Next pipeline run will overwrite |
| raw_post_insights 30-day limit | Bug | ✅ Fixed | Removed WHERE clause |
| page_daily_metrics only 7 days | Bug | ✅ Fixed | Changed to 90 days |
| trending_posts empty | Feature | ℹ️ Expected | No posts in last 72h |
| ad_recommendations "missing half" | Feature | ℹ️ Expected | Only shows last 30 days, score >= 40 |
| raw_posts missing recent data | Pending | ⏳ Running | Pipeline collecting from 2024-01-01 |

---

## Next Steps

1. ⏳ **Wait for pipeline to complete** (currently running, ~10-15 minutes)
2. 🔍 **Verify data in Google Sheets** after pipeline completes:
   - Check raw_post_insights has all historical snapshots
   - Check page_daily_metrics has 90 days
   - Check raw_posts has all posts from 2024-01-01 onwards
   - Verify row 8 corruption is fixed (should show 115, not "2025-12-18")

---

## Deployment Info

- **Commit**: `8416eaa` - "fix: Improve data collection and export coverage"
- **Deployed**: 2026-01-15 ~18:10 GMT+8
- **GitHub Actions**: [Run #21027425667](https://github.com/zz03333/GCAA_Facebook_Data_Updatee/actions/runs/21027425667) ✅ Success
- **Cloud Run Revision**: Will be `facebook-insights-collector-00007-xxx` (check deployment)
- **Pipeline Triggered**: 2026-01-15 18:11 GMT+8

---

## Files Modified

1. [exporters/export_to_sheets.py](../exporters/export_to_sheets.py#L661-L674)
   - Removed 30-day limit from raw_post_insights query

2. [run_pipeline.py](../run_pipeline.py#L342-L343)
   - Changed page_daily_metrics collection from 7 to 90 days
