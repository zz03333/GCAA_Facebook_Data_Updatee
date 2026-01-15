"""
使用 run_pipeline.py 架構抓取 2025 全年資料
"""
import sys
sys.path.insert(0, '/Users/jinsoon/Desktop/GCAA/社群宣傳/API_Parser')

# 直接呼叫 run_pipeline 的函數
from run_pipeline import collect_post_data, run_analytics, test_api_connection

if __name__ == '__main__':
    print("=== 抓取 2025 全年資料 ===\n")
    
    if not test_api_connection():
        print("API 連線失敗")
        sys.exit(1)
    
    # 收集 2025 全年貼文 (limit 最大值為 100，會自動分頁)
    success = collect_post_data(
        since_date='2025-01-01',
        until_date='2025-12-15',
        limit=100
    )
    
    if success:
        print("\n=== 執行分析處理 ===\n")
        run_analytics()
        print("\n✓ 完成")
    else:
        print("\n✗ 收集失敗")
