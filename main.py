"""
Facebook Post Insights 自動化數據抓取工具
從 Facebook Graph API 獲取粉絲專頁的貼文層級數據，並彙整至 Google Sheets。
"""

import requests
import pandas as pd
import gspread
from google.oauth2 import service_account
import json
import os
import base64
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any, Optional
from flask import Flask, jsonify, request

# ==================== 設定區 ====================

# Facebook API 設定
def get_facebook_token():
    """取得 Facebook Access Token（支援 base64 編碼）"""
    token = os.environ.get('FACEBOOK_ACCESS_TOKEN')
    token_base64 = os.environ.get('FACEBOOK_ACCESS_TOKEN_BASE64')

    if token_base64:
        return base64.b64decode(token_base64).decode('utf-8')
    elif token:
        return token
    else:
        return 'EAAPbnmTSpmoBQaz8PQJU8jTcLhsmMaB8cq9pYrvsHeAuzncRMgbRpWauF9vtQLNalTJd4X4idcvdTrFliXZCzxrzZCa9CvXRMCWYf8H4NFy4Fq8aay0G20ZCUxXEneQ0WGfOZBWDGfqJMC64WxwzLHAY3g3REJdmqNZCUPSC4ac6VX8Lu8SzXktQ3dERX4r1C'

FACEBOOK_CONFIG = {
    'app_id': '1085898272974442',
    'page_id': '103640919705348',
    'access_token': get_facebook_token(),
    'api_version': 'v23.0'
}

# Google Sheets 設定
GOOGLE_SHEETS_CONFIG = {
    'spreadsheet_name': 'Faceboook Insights Metrics_Data Warehouse',
    'worksheet_name': 'raw_data'
}

# 貼文層級 Insights 指標
# 更新日期: 2026-01-15 - 新增互動與觸及指標
POST_INSIGHTS_METRICS = [
    # 貼文互動指標
    'post_clicks',
    'post_engaged_users',           # 新增: 與貼文互動的不重複用戶數
    'post_negative_feedback',       # 新增: 負面回饋次數
    # 貼文觸及指標
    'post_impressions_unique',
    'post_impressions_fan_unique',  # 新增: 粉絲觸及人數
    'post_impressions_viral_unique', # 新增: 病毒式觸及人數
    # 'post_impressions',  # ✗ 已棄用
    # 'post_impressions_organic',  # ✗ 已棄用
    # 'post_impressions_paid',  # ✗ 已棄用
    # 貼文心情反應指標
    'post_reactions_like_total',
    'post_reactions_love_total',
    'post_reactions_wow_total',
    'post_reactions_haha_total',
    'post_reactions_sorry_total',
    'post_reactions_anger_total',
    # 影片相關指標
    'post_video_views',
    'post_video_views_organic',
    'post_video_views_paid',
]

# ==================== 核心功能函式 ====================

def test_facebook_api_connection(config: Dict[str, str]) -> bool:
    """測試 Facebook API 連接是否正常"""
    try:
        url = f"https://graph.facebook.com/{config['api_version']}/{config['page_id']}"
        params = {
            'access_token': config['access_token'],
            'fields': 'id,name,fan_count'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        print(f"✓ API 連接成功")
        print(f"  Page ID: {data.get('id')}")
        print(f"  Page Name: {data.get('name')}")
        print(f"  粉絲數: {data.get('fan_count', 'N/A')}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ API 連接失敗: {e}")
        return False
    except Exception as e:
        print(f"✗ 未預期的錯誤: {e}")
        return False


def fetch_page_posts(config: Dict[str, str], since: str, until: str, limit: int = 100) -> Optional[List[Dict]]:
    """從 Facebook API 獲取頁面貼文列表"""
    import calendar
    try:
        url = f"https://graph.facebook.com/{config['api_version']}/{config['page_id']}/posts"

        # 轉換日期為 Unix timestamp (UTC)
        since_dt = datetime.strptime(since, '%Y-%m-%d')
        until_dt = datetime.strptime(until, '%Y-%m-%d')
        since_ts = calendar.timegm(since_dt.timetuple())
        until_ts = calendar.timegm(until_dt.timetuple()) + 86400

        params = {
            'access_token': config['access_token'],
            'fields': 'id,message,created_time,permalink_url',
            'since': since_ts,
            'until': until_ts,
            'limit': limit
        }

        all_posts = []
        print(f"正在獲取貼文列表...")
        print(f"日期範圍: {since} 到 {until}")

        while url:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            posts = data.get('data', [])

            # 為每則貼文獲取額外資訊
            for post in posts:
                post_id = post['id']

                # 獲取反應總數
                reactions_url = f"https://graph.facebook.com/{config['api_version']}/{post_id}/reactions"
                reactions_params = {'access_token': config['access_token'], 'summary': 'total_count', 'limit': 0}
                reactions_response = requests.get(reactions_url, params=reactions_params)
                if reactions_response.status_code == 200:
                    reactions_data = reactions_response.json()
                    post['reactions'] = {'summary': {'total_count': reactions_data.get('summary', {}).get('total_count', 0)}}

                # 獲取留言總數
                comments_url = f"https://graph.facebook.com/{config['api_version']}/{post_id}/comments"
                comments_params = {'access_token': config['access_token'], 'summary': 'total_count', 'limit': 0}
                comments_response = requests.get(comments_url, params=comments_params)
                if comments_response.status_code == 200:
                    comments_data = comments_response.json()
                    post['comments'] = {'summary': {'total_count': comments_data.get('summary', {}).get('total_count', 0)}}

                # 獲取分享數
                shares_url = f"https://graph.facebook.com/{config['api_version']}/{post_id}"
                shares_params = {'access_token': config['access_token'], 'fields': 'shares'}
                shares_response = requests.get(shares_url, params=shares_params)
                if shares_response.status_code == 200:
                    shares_data = shares_response.json()
                    post['shares'] = shares_data.get('shares', {})

            all_posts.extend(posts)

            # 檢查是否有下一頁
            paging = data.get('paging', {})
            url = paging.get('next')
            params = {}

            print(f"  已獲取 {len(all_posts)} 則貼文...")

        print(f"✓ 共獲取 {len(all_posts)} 則貼文")
        return all_posts

    except requests.exceptions.RequestException as e:
        print(f"✗ API 請求失敗: {e}")
        return None
    except Exception as e:
        print(f"✗ 未預期的錯誤: {e}")
        return None


def fetch_post_insights(config: Dict[str, str], post_id: str, metrics: List[str]) -> Optional[Dict]:
    """從 Facebook API 獲取單一貼文的洞察數據"""
    try:
        url = f"https://graph.facebook.com/{config['api_version']}/{post_id}/insights"
        params = {
            'access_token': config['access_token'],
            'metric': ','.join(metrics)
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        insights_data = data.get('data', [])

        # 將 insights 數據轉換為字典格式
        insights_dict = {}
        for metric_data in insights_data:
            metric_name = metric_data.get('name')
            values = metric_data.get('values', [])
            if values:
                value = values[0].get('value', 0)
                insights_dict[metric_name] = value

        return insights_dict

    except requests.exceptions.RequestException:
        return {}
    except Exception as e:
        print(f"獲取貼文 {post_id} 的 insights 時發生錯誤: {e}")
        return {}


def process_posts_data(posts: List[Dict], page_id: str, page_name: str, fetch_date: str) -> pd.DataFrame:
    """處理貼文數據，轉換為結構化的 DataFrame"""
    processed_records = []

    for post in posts:
        record = {
            'fetch_date': fetch_date,
            'post_id': post.get('id', ''),
            'page_id': page_id,
            'page_name': page_name,
            'message': post.get('message', '')[:500],
            'created_time': post.get('created_time', ''),
            'permalink_url': post.get('permalink_url', ''),
        }

        # 處理反應數
        reactions_data = post.get('reactions', {})
        if isinstance(reactions_data, dict):
            record['reactions_count'] = reactions_data.get('summary', {}).get('total_count', 0)
        else:
            record['reactions_count'] = 0

        # 處理留言數
        comments_data = post.get('comments', {})
        if isinstance(comments_data, dict):
            record['comments_count'] = comments_data.get('summary', {}).get('total_count', 0)
        else:
            record['comments_count'] = 0

        # 處理分享數
        shares_data = post.get('shares', {})
        if isinstance(shares_data, dict):
            record['shares_count'] = shares_data.get('count', 0)
        else:
            record['shares_count'] = 0

        # 處理 insights 數據
        insights = post.get('insights', {})
        for metric_name, value in insights.items():
            record[metric_name] = value

        processed_records.append(record)

    return pd.DataFrame(processed_records)


def setup_google_sheets_client() -> Optional[gspread.Client]:
    """設定 Google Sheets 客戶端（使用環境變數中的服務帳戶金鑰）"""
    try:
        # 從環境變數讀取服務帳戶 JSON（支援 base64 編碼）
        credentials_json = os.environ.get('GCP_SA_CREDENTIALS')
        credentials_base64 = os.environ.get('GCP_SA_CREDENTIALS_BASE64')

        if credentials_base64:
            # 如果是 base64 編碼，先解碼
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
        elif not credentials_json:
            print("✗ 找不到 GCP_SA_CREDENTIALS 或 GCP_SA_CREDENTIALS_BASE64 環境變數")
            return None

        # 將 JSON 字串轉換為字典
        credentials_dict = json.loads(credentials_json)

        # 設定權限範圍
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # 建立服務帳戶憑證
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=scope)

        # 建立 gspread 客戶端
        client = gspread.authorize(credentials)

        print("✓ Google Sheets 客戶端設定成功")
        return client

    except Exception as e:
        print(f"✗ Google Sheets 客戶端設定失敗: {e}")
        return None


def write_to_google_sheets(client: gspread.Client, config: Dict[str, str], df: pd.DataFrame) -> bool:
    """將 DataFrame 寫入 Google Sheets"""
    try:
        spreadsheet = client.open(config['spreadsheet_name'])
        worksheet = spreadsheet.worksheet(config['worksheet_name'])

        # 定義欄位順序
        expected_columns = [
            'fetch_date', 'post_id', 'page_id', 'page_name', 'message', 'created_time', 'permalink_url',
            'reactions_count', 'comments_count', 'shares_count',
            'post_clicks', 'post_engaged_users', 'post_negative_feedback',
            'post_impressions_unique', 'post_impressions_fan_unique', 'post_impressions_viral_unique',
            'post_impressions', 'post_impressions_organic', 'post_impressions_paid',
            'post_reactions_like_total', 'post_reactions_love_total', 'post_reactions_wow_total',
            'post_reactions_haha_total', 'post_reactions_sorry_total', 'post_reactions_anger_total',
            'post_video_views', 'post_video_views_organic', 'post_video_views_paid'
        ]

        # 確保 DataFrame 包含所有必要欄位
        for col in expected_columns:
            if col not in df.columns:
                if col in ['fetch_date', 'post_id', 'page_id', 'page_name', 'message', 'created_time', 'permalink_url']:
                    df[col] = ''
                else:
                    df[col] = 0

        df = df[expected_columns]

        # 檢查工作表
        existing_data = worksheet.get_all_values()

        if not existing_data or not existing_data[0]:
            worksheet.append_row(expected_columns)
            print("✓ 已寫入標題列")
            existing_data = [expected_columns]
        else:
            existing_headers = existing_data[0]
            if existing_headers != expected_columns:
                worksheet.delete_rows(1)
                worksheet.insert_row(expected_columns, 1)
                print("✓ 已更新標題列")
                existing_data = worksheet.get_all_values()

        # 檢查重複記錄
        existing_records = set()
        if len(existing_data) > 1:
            headers = existing_data[0]
            try:
                post_id_idx = headers.index('post_id')
                fetch_date_idx = headers.index('fetch_date')

                for row in existing_data[1:]:
                    if len(row) > max(post_id_idx, fetch_date_idx):
                        key = f"{row[post_id_idx]}_{row[fetch_date_idx]}"
                        existing_records.add(key)

                print(f"✓ 已載入 {len(existing_records)} 筆現有記錄")
            except ValueError as e:
                print(f"⚠️  無法找到必要欄位索引: {e}")

        # 過濾新記錄
        new_rows = []
        duplicate_count = 0

        for idx, row in df.iterrows():
            key = f"{row['post_id']}_{row['fetch_date']}"
            if key not in existing_records:
                new_rows.append(row.tolist())
            else:
                duplicate_count += 1

        print(f"\n數據去重結果:")
        print(f"  總記錄數: {len(df)}")
        print(f"  新記錄: {len(new_rows)}")
        print(f"  重複記錄（已跳過）: {duplicate_count}")

        # 批次寫入
        if new_rows:
            worksheet.append_rows(new_rows)
            print(f"\n✓ 已寫入 {len(new_rows)} 筆新數據到 Google Sheets")
            return True
        else:
            print("\n⚠️  無新數據需要寫入")
            return True

    except Exception as e:
        print(f"✗ 寫入 Google Sheets 失敗: {e}")
        return False


def main_posts_collection(since_date: str = None, until_date: str = None) -> bool:
    """主要的貼文數據蒐集流程"""

    # 設定日期範圍 - 抓取所有歷史資料
    if until_date is None:
        until_date = datetime.now().strftime('%Y-%m-%d')
    if since_date is None:
        since_date = '2024-01-01'

    fetch_date = datetime.now().strftime('%Y-%m-%d')

    print(f"=== 開始貼文數據蒐集 ===")
    print(f"日期範圍: {since_date} 到 {until_date}")
    print(f"執行日期: {fetch_date}")

    # 測試 API 連接
    if not test_facebook_api_connection(FACEBOOK_CONFIG):
        return False

    # 設定 Google Sheets
    sheets_client = setup_google_sheets_client()
    if not sheets_client:
        return False

    # 獲取頁面資訊
    try:
        url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{FACEBOOK_CONFIG['page_id']}"
        params = {'access_token': FACEBOOK_CONFIG['access_token'], 'fields': 'id,name'}
        response = requests.get(url, params=params)
        response.raise_for_status()
        page_data = response.json()
        page_name = page_data.get('name', '')
        print(f"\n粉絲專頁: {page_name}")
    except Exception as e:
        print(f"✗ 無法獲取頁面資訊: {e}")
        return False

    # 獲取貼文列表
    print(f"\n步驟 1: 獲取貼文列表")
    posts = fetch_page_posts(FACEBOOK_CONFIG, since_date, until_date)

    if posts is None or not posts:
        print("⚠️ 無貼文或獲取失敗")
        return False

    print(f"✓ 成功獲取 {len(posts)} 則貼文")

    # 獲取 insights
    print(f"\n步驟 2: 獲取貼文 Insights 數據")
    success_count = 0

    for i, post in enumerate(posts, 1):
        post_id = post.get('id')
        print(f"  處理 {i}/{len(posts)}: {post_id}", end='')

        insights = fetch_post_insights(FACEBOOK_CONFIG, post_id, POST_INSIGHTS_METRICS)

        if insights:
            post['insights'] = insights
            success_count += 1
            print(f" - ✓")
        else:
            post['insights'] = {}
            print(f" - ⊘")

        time.sleep(0.2)

    print(f"\n✓ Insights 數據獲取完成 (成功: {success_count})")

    # 處理數據
    print(f"\n步驟 3: 處理數據")
    df = process_posts_data(posts, FACEBOOK_CONFIG['page_id'], page_name, fetch_date)
    print(f"✓ 已處理 {len(df)} 則貼文數據")

    # 寫入 Google Sheets
    print(f"\n步驟 4: 寫入 Google Sheets")
    success = write_to_google_sheets(sheets_client, GOOGLE_SHEETS_CONFIG, df)

    if success:
        print(f"\n🎉 貼文數據蒐集完成!")
        return True
    else:
        print(f"\n❌ 寫入失敗")
        return False


# ==================== Flask App for Cloud Run ====================

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def run_collection():
    """Cloud Scheduler 會呼叫這個端點來觸發完整數據收集流程"""
    try:
        import run_pipeline
        from exporters import export_to_sheets as exporter
        from exporters import firestore_sync

        results = {
            'pipeline': False,
            'export': False,
            'firestore': False
        }

        # Step 1: 執行 run_pipeline（抓取 Facebook 資料 + 分析）
        print("=" * 60)
        print("開始執行完整數據收集流程...")
        print("=" * 60)

        try:
            run_pipeline.run_full_pipeline()
            results['pipeline'] = True
            print("✓ run_pipeline 完成")
        except Exception as e:
            print(f"✗ run_pipeline 失敗: {e}")

        # Step 2: 執行 export_to_sheets（匯出到 Google Sheets）
        try:
            success = exporter.main()
            results['export'] = success
            print("✓ export_to_sheets 完成" if success else "✗ export_to_sheets 失敗")
        except Exception as e:
            print(f"✗ export_to_sheets 失敗: {e}")

        # Step 3: 執行 firestore_sync（同步到 Firestore for real-time dashboard）
        try:
            success = firestore_sync.sync_all()
            results['firestore'] = success
            print("✓ firestore_sync 完成" if success else "✗ firestore_sync 失敗")
        except Exception as e:
            print(f"✗ firestore_sync 失敗: {e}")
            # Firestore sync failure is not critical, don't fail the whole pipeline
            results['firestore'] = False

        # 判斷結果
        if results['pipeline'] and results['export']:
            return jsonify({
                'status': 'success',
                'message': '完整數據收集流程已完成',
                'results': results,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'partial',
                'message': '部分流程失敗',
                'results': results,
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/analytics', methods=['POST'])
def run_analytics():
    """執行數據分析處理端點"""
    try:
        from analytics import analytics_processor

        conn = analytics_processor.get_connection()

        # 執行分析流程
        classified_count = analytics_processor.process_all_posts_classification(conn)
        kpi_count = analytics_processor.calculate_post_kpis(conn)
        analytics_processor.update_benchmarks(conn)

        conn.close()

        return jsonify({
            'status': 'success',
            'message': '分析處理完成',
            'classified_count': classified_count,
            'kpi_count': kpi_count,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/reports/weekly', methods=['GET'])
def get_weekly_report():
    """取得週報端點"""
    try:
        from analytics import analytics_reports

        conn = analytics_reports.get_connection()
        report_text = analytics_reports.generate_weekly_report(conn)
        conn.close()

        return jsonify({
            'status': 'success',
            'report': report_text,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/query', methods=['GET'])
def query_custom():
    """
    自訂查詢端點

    參數:
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        granularity: 粒度 (daily/weekly/monthly, 預設: weekly)
        type: 查詢類型 (trends/topics/time_slots/top_posts/comparison)
        topic: 主題篩選 (可選)
        time_slot: 時段篩選 (可選)
        limit: 回傳筆數 (預設: 10)

    範例:
        /query?start_date=2025-11-01&end_date=2025-11-30&granularity=weekly&type=trends
        /query?start_date=2025-11-01&end_date=2025-11-30&type=topics
        /query?start_date=2025-11-01&end_date=2025-11-30&type=top_posts&limit=20
    """
    try:
        from analytics import query_analytics

        # 解析參數
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        granularity = request.args.get('granularity', 'weekly')
        query_type = request.args.get('type', 'trends')
        topic = request.args.get('topic')
        time_slot = request.args.get('time_slot')
        limit = int(request.args.get('limit', 10))

        # 驗證參數
        if not start_date or not end_date:
            # 預設最近 30 天
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        conn = query_analytics.get_connection()

        # 根據查詢類型執行不同查詢
        if query_type == 'trends':
            data = query_analytics.query_by_date_range(conn, start_date, end_date, granularity)
        elif query_type == 'topics':
            data = query_analytics.query_topic_performance(conn, start_date, end_date, topic)
        elif query_type == 'time_slots':
            data = query_analytics.query_time_slot_performance(conn, start_date, end_date)
        elif query_type == 'top_posts':
            data = query_analytics.query_top_posts(conn, start_date, end_date, limit, topic, time_slot)
        else:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': f'不支援的查詢類型: {query_type}'
            }), 400

        conn.close()

        return jsonify({
            'status': 'success',
            'query_type': query_type,
            'start_date': start_date,
            'end_date': end_date,
            'granularity': granularity if query_type == 'trends' else None,
            'data': data,
            'count': len(data),
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/reports/custom', methods=['GET'])
def get_custom_report():
    """
    取得自訂報表端點

    參數:
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        granularity: 粒度 (daily/weekly/monthly, 預設: weekly)

    範例:
        /reports/custom?start_date=2025-11-01&end_date=2025-11-30&granularity=weekly
    """
    try:
        from analytics import query_analytics

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        granularity = request.args.get('granularity', 'weekly')

        # 預設最近 30 天
        if not start_date or not end_date:
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        conn = query_analytics.get_connection()
        report_text = query_analytics.generate_custom_report(conn, start_date, end_date, granularity)
        conn.close()

        return jsonify({
            'status': 'success',
            'start_date': start_date,
            'end_date': end_date,
            'granularity': granularity,
            'report': report_text,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/export-sheets', methods=['POST'])
def export_to_sheets():
    """導出報表至 Google Sheets 端點"""
    try:
        import export_to_sheets as exporter

        success = exporter.main()

        if success:
            return jsonify({
                'status': 'success',
                'message': '報表已成功導出至 Google Sheets',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '部分報表導出失敗',
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
