"""
Facebook 社群數據分析框架 - 完整執行流程
整合數據收集、分析處理、報表產出
"""

import sys
import time
from datetime import datetime
import requests

# 導入各模組
from utils import config, db_utils
from collectors import collector_page, collector_ads
from analytics import analytics_processor, analytics_reports


def test_api_connection():
    """測試 Facebook API 連接"""
    print("\n" + "="*60)
    print("Step 0: 測試 API 連接")
    print("="*60)

    try:
        url = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{config.FACEBOOK_CONFIG['page_id']}"
        params = {
            'access_token': config.FACEBOOK_CONFIG['access_token'],
            'fields': 'id,name,fan_count,followers_count'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        print(f"✓ API 連接成功")
        print(f"  粉絲專頁: {data.get('name')}")
        print(f"  Page ID: {data.get('id')}")
        print(f"  粉絲數: {data.get('fan_count', 'N/A')}")
        print(f"  追蹤者數: {data.get('followers_count', 'N/A')}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ API 連接失敗: {e}")
        return False
    except Exception as e:
        print(f"✗ 未預期的錯誤: {e}")
        return False


def collect_page_data(days_back=7):
    """收集頁面層級數據"""
    print("\n" + "="*60)
    print(f"Step 1: 收集頁面層級數據（最近 {days_back} 天）")
    print("="*60)

    try:
        collector_page.process_and_save_page_data(days_back=days_back)
        print("✓ 頁面數據收集完成")
        return True
    except Exception as e:
        print(f"✗ 頁面數據收集失敗: {e}")
        return False


def collect_post_data(since_date=None, until_date=None, limit=100):
    """
    收集貼文層級數據
    - 發布 30 天內的貼文：每日收集 insights（追蹤成長）
    - 發布超過 30 天的貼文：只收集一次（如果還沒有 snapshot）
    """
    print("\n" + "="*60)
    print("Step 2: 收集貼文層級數據")
    print("="*60)

    if until_date is None:
        until_date = datetime.now().strftime('%Y-%m-%d')
    if since_date is None:
        # 抓取所有歷史資料（從 2024 年初開始）
        since_date = '2024-01-01'

    print(f"日期範圍: {since_date} ~ {until_date}")

    try:
        from main import fetch_page_posts, fetch_post_insights, POST_INSIGHTS_METRICS

        # 獲取貼文列表
        posts = fetch_page_posts(config.FACEBOOK_CONFIG, since_date, until_date, limit)

        if not posts:
            print("⚠ 未找到新貼文")
            # 仍繼續執行，因為需要更新現有貼文
        else:
            print(f"✓ 從 API 獲取 {len(posts)} 則貼文")

        conn = db_utils.get_db_connection()
        if not conn:
            print("✗ 無法連接資料庫")
            return False

        fetch_date = datetime.now().strftime('%Y-%m-%d')
        cursor = conn.cursor()

        # 儲存新貼文的基本資訊
        if posts:
            for post in posts:
                post_data = {
                    'id': post.get('id'),
                    'page_id': config.FACEBOOK_CONFIG['page_id'],
                    'created_time': post.get('created_time'),
                    'message': post.get('message', ''),
                    'type': None,
                    'permalink_url': post.get('permalink_url')
                }
                db_utils.upsert_post(conn, post_data)

        # 找出需要收集 insights 的貼文：
        # 1. 發布 30 天內的貼文（每日追蹤）
        # 2. 發布超過 30 天但今天還沒有任何 snapshot 的貼文（補收一次）
        cursor.execute("""
            SELECT p.post_id, p.created_time,
                   julianday('now') - julianday(date(substr(p.created_time, 1, 10))) as days_since_post,
                   (SELECT COUNT(*) FROM post_insights_snapshots WHERE post_id = p.post_id) as snapshot_count
            FROM posts p
            WHERE 
                -- 30 天內的貼文
                julianday('now') - julianday(date(substr(p.created_time, 1, 10))) <= 30
                -- 或者沒有任何 snapshot 的貼文
                OR (SELECT COUNT(*) FROM post_insights_snapshots WHERE post_id = p.post_id) = 0
            ORDER BY p.created_time DESC
        """)
        posts_to_collect = cursor.fetchall()

        print(f"✓ 需要收集 insights 的貼文: {len(posts_to_collect)} 則")
        print(f"  (30天內: 每日追蹤 / 30天外: 補收一次)")

        success_count = 0
        skipped_count = 0

        for i, (post_id, created_time, days_since, snapshot_count) in enumerate(posts_to_collect, 1):
            if i % 25 == 0:
                print(f"  進度: {i}/{len(posts_to_collect)}")

            # 獲取 post insights
            insights = fetch_post_insights(config.FACEBOOK_CONFIG, post_id, POST_INSIGHTS_METRICS)

            # 獲取基本統計（reactions, comments, shares）
            basic_stats = {}
            try:
                import requests
                base_url = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{post_id}"
                access_token = config.FACEBOOK_CONFIG['access_token']

                # 獲取反應數
                resp = requests.get(f"{base_url}/reactions", params={
                    'access_token': access_token, 'summary': 'total_count', 'limit': 0
                }, timeout=10)
                if resp.ok:
                    basic_stats['likes_count'] = resp.json().get('summary', {}).get('total_count', 0)

                # 獲取留言數
                resp = requests.get(f"{base_url}/comments", params={
                    'access_token': access_token, 'summary': 'total_count', 'limit': 0
                }, timeout=10)
                if resp.ok:
                    basic_stats['comments_count'] = resp.json().get('summary', {}).get('total_count', 0)

                # 獲取分享數
                resp = requests.get(f"{base_url}", params={
                    'access_token': access_token, 'fields': 'shares'
                }, timeout=10)
                if resp.ok:
                    basic_stats['shares_count'] = resp.json().get('shares', {}).get('count', 0)

            except Exception:
                pass  # 忽略錯誤，使用預設值

            if db_utils.upsert_post_insights(conn, post_id, fetch_date, insights or {}, basic_stats):
                success_count += 1
            else:
                skipped_count += 1

            time.sleep(0.15)  # API 速率限制

        conn.close()
        print(f"\n✓ 成功收集 {success_count} 則貼文的 insights")
        if skipped_count > 0:
            print(f"  (跳過 {skipped_count} 則)")
        return True

    except Exception as e:
        print(f"✗ 貼文數據收集失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_analytics():
    """執行數據分析"""
    print("\n" + "="*60)
    print("Step 3: 執行數據分析處理")
    print("="*60)

    try:
        conn = analytics_processor.get_connection()

        # Step 3.1: 分類貼文
        print("\n[3.1] 內容分類")
        classified_count = analytics_processor.process_all_posts_classification(conn)

        if classified_count > 0:
            print(f"✓ 已分類 {classified_count} 則貼文")
        else:
            print("⚠ 無新貼文需要分類")

        # Step 3.2: 計算 KPI
        print("\n[3.2] KPI 計算")
        kpi_count = analytics_processor.calculate_post_kpis(conn)

        if kpi_count > 0:
            print(f"✓ 已計算 {kpi_count} 則貼文的 KPI")
        else:
            print("⚠ 無數據可計算 KPI")

        # Step 3.3: 更新基準
        print("\n[3.3] 基準更新")
        analytics_processor.update_benchmarks(conn)

        conn.close()
        print("\n✓ 分析處理完成")
        return True

    except Exception as e:
        print(f"✗ 分析處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_reports():
    """產出報表"""
    print("\n" + "="*60)
    print("Step 4: 產出分析報表")
    print("="*60)

    try:
        conn = analytics_reports.get_connection()

        # 週報
        print("\n" + analytics_reports.generate_weekly_report(conn))

        # 主題表現
        print("\n=== 主題表現比較 ===")
        topics = analytics_reports.get_topic_performance(conn)
        if topics:
            for t in topics[:10]:
                name = t.get('format_type_name') or t.get('format_type', '未分類')
                print(f"  {name:15s}: ER={t['avg_er']:.2f}%, Posts={t['post_count']}")
        else:
            print("  ⚠ 暫無數據")

        # 病毒貼文特徵
        print("\n=== 病毒貼文特徵 ===")
        patterns = analytics_reports.get_viral_post_patterns(conn)
        if patterns:
            for p in patterns[:5]:
                print(f"  {p['media_type']:8s} / {p['message_length_tier']:6s} / CTA={p['has_cta']}: {p['viral_count']} 則")
        else:
            print("  ⚠ 暫無病毒貼文")

        conn.close()
        print("\n✓ 報表產出完成")
        return True

    except Exception as e:
        print(f"✗ 報表產出失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def collect_ad_data():
    """收集廣告數據"""
    print("\n" + "="*60)
    print("Step 5: 收集廣告數據")
    print("="*60)

    try:
        success = collector_ads.collect_all_ad_data()
        if success:
            print("✓ 廣告數據收集完成")
        return success
    except Exception as e:
        print(f"⚠ 廣告數據收集失敗: {e}")
        return False


def show_summary():
    """顯示數據摘要"""
    print("\n" + "="*60)
    print("數據摘要")
    print("="*60)

    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        # 統計各表數據量
        tables = [
            ('posts', '貼文'),
            ('post_insights_snapshots', '貼文洞察'),
            ('posts_classification', '貼文分類'),
            ('posts_performance', '貼文表現'),
            ('page_daily_metrics', '頁面每日指標'),
            ('benchmarks', '基準值')
        ]

        for table, name in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"  {name:15s}: {count:4d} 筆")

        conn.close()

    except Exception as e:
        print(f"  ✗ 無法取得摘要: {e}")


def main():
    """主執行流程"""
    print("\n" + "="*70)
    print(" " * 15 + "Facebook 社群數據分析框架")
    print(" " * 20 + "完整執行流程")
    print("="*70)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    # Step 0: 測試 API 連接
    if not test_api_connection():
        print("\n✗ API 連接失敗，中止執行")
        return False

    # Step 1: 收集頁面數據 (至少 3 個月)
    collect_page_data(days_back=90)

    # Step 2: 收集貼文數據 (30天內每日追蹤，舊貼文補收一次)
    if not collect_post_data():
        print("\n⚠ 貼文數據收集失敗，跳過後續分析")
    else:
        # Step 3: 執行分析
        run_analytics()

        # Step 4: 產出報表
        generate_reports()

    # Step 5: 收集廣告數據 (可選，失敗不影響主流程)
    try:
        collect_ad_data()
    except Exception as e:
        print(f"\n⚠ 廣告數據收集失敗 (非致命): {e}")

    # 顯示摘要
    show_summary()

    # 執行時間
    elapsed_time = time.time() - start_time
    print("\n" + "="*70)
    print(f"✓ 完整流程執行完成 (耗時: {elapsed_time:.1f} 秒)")
    print("="*70 + "\n")

    # 記錄 Pipeline 執行紀錄
    log_pipeline_run(elapsed_time)

    return True


def log_pipeline_run(duration_seconds: float, error_message: str = None):
    """記錄 Pipeline 執行結果"""
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 確保 pipeline_runs 表存在
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                run_time TEXT NOT NULL,
                status TEXT NOT NULL,
                posts_collected INTEGER,
                posts_analyzed INTEGER,
                sheets_exported INTEGER,
                error_message TEXT,
                duration_seconds REAL
            )
        """)
        
        # 取得統計數據
        cursor.execute("SELECT COUNT(*) FROM posts")
        posts_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM posts_performance")
        perf_count = cursor.fetchone()[0]
        
        now = datetime.now()
        status = 'ERROR' if error_message else 'SUCCESS'
        
        cursor.execute("""
            INSERT INTO pipeline_runs 
            (run_date, run_time, status, posts_collected, posts_analyzed, sheets_exported, 
             error_message, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            status,
            posts_count,
            perf_count,
            20,  # 估計的報表數量
            error_message,
            round(duration_seconds, 1)
        ))
        
        conn.commit()
        conn.close()
        print("✓ Pipeline 執行紀錄已儲存")
    except Exception as e:
        print(f"⚠ 無法記錄 Pipeline 執行: {e}")



def run_full_pipeline():
    """Alias for main() - called by Cloud Run endpoint"""
    return main()


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ 使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
