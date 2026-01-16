#!/bin/bash
# =============================================================
# Facebook 社群數據分析 - 每日排程腳本
# 每日 08:00 GMT+8 執行
# =============================================================

# 設定路徑
SCRIPT_DIR="/Users/jinsoon/Desktop/GCAA/社群宣傳/API_Parser"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_$(date +%Y%m%d).log"
CREDENTIALS_FILE="/Users/jinsoon/Desktop/GCAA/社群宣傳/esg-reports-collection-bced6b2269b5.json"

# 建立 logs 資料夾
mkdir -p "$LOG_DIR"

# 開始記錄
echo "========================================" >> "$LOG_FILE"
echo "開始執行: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 切換到腳本目錄
cd "$SCRIPT_DIR" || exit 1

# 設定環境變數
export GCP_SA_CREDENTIALS=$(cat "$CREDENTIALS_FILE")

# 啟動虛擬環境 (如果有的話)
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 執行完整流程
echo "[$(date '+%H:%M:%S')] 執行 run_pipeline.py..." >> "$LOG_FILE"
python3 run_pipeline.py >> "$LOG_FILE" 2>&1
PIPELINE_STATUS=$?

if [ $PIPELINE_STATUS -eq 0 ]; then
    echo "[$(date '+%H:%M:%S')] ✓ run_pipeline.py 完成" >> "$LOG_FILE"
else
    echo "[$(date '+%H:%M:%S')] ✗ run_pipeline.py 失敗 (exit code: $PIPELINE_STATUS)" >> "$LOG_FILE"
fi

# 匯出到 Google Sheets
echo "[$(date '+%H:%M:%S')] 執行 export_to_sheets.py..." >> "$LOG_FILE"
python3 export_to_sheets.py >> "$LOG_FILE" 2>&1
EXPORT_STATUS=$?

if [ $EXPORT_STATUS -eq 0 ]; then
    echo "[$(date '+%H:%M:%S')] ✓ export_to_sheets.py 完成" >> "$LOG_FILE"
else
    echo "[$(date '+%H:%M:%S')] ✗ export_to_sheets.py 失敗 (exit code: $EXPORT_STATUS)" >> "$LOG_FILE"
fi

# 結束記錄
echo "" >> "$LOG_FILE"
echo "執行完成: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 清理 14 天以上的舊 log
find "$LOG_DIR" -name "daily_*.log" -mtime +14 -delete

exit 0
