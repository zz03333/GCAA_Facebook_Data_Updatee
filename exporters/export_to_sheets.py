"""
Facebook 社群數據分析框架 - Google Sheets 導出工具
將分析報表導出到 Google Sheets 以便視覺化與分享
"""

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import gspread
from google.oauth2 import service_account
import json
import os
import base64
import re
from datetime import datetime, timedelta
from analytics import analytics_reports, analytics_trends, ad_predictor



def add_timestamp_column(data):
    """Add 'data_updated_at' timestamp column to all rows"""
    if not data:
        return data
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add header to first row
    if data and len(data) > 0:
        data[0].append('data_updated_at')
        
        # Add timestamp to all data rows  
        for i in range(1, len(data)):
            data[i].append(timestamp)
    
    return data


# Google Sheets 設定
SPREADSHEET_NAME = 'Facebook Insights Metrics_Data Warehouse'
ANALYTICS_WORKSHEET_NAME = 'analytics_dashboard'


# ==================== 輔助函數 ====================

def update_with_timestamp(worksheet, range_name, values):
    """Wrapper to add timestamp column to all worksheet updates"""
    if not values or len(values) == 0:
        worksheet.update(range_name, values)
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Make a copy to avoid modifying original
    updated_values = [row[:] if isinstance(row, list) else list(row) for row in values]
    
    # Add header to first row if it exists
    if len(updated_values) > 0:
        updated_values[0].append('data_updated_at')
        
        # Add timestamp to all data rows
        for i in range(1, len(updated_values)):
            updated_values[i].append(timestamp)
    
    worksheet.update(range_name, updated_values)


def convert_to_gmt8(iso_time_str):
    """將 ISO 時間轉換為 GMT+8 格式字串"""
    if not iso_time_str:
        return ''
    try:
        # 解析 ISO 格式 (2024-12-01T12:00:00+0000)
        dt = datetime.fromisoformat(iso_time_str.replace('+0000', '+00:00').replace('Z', '+00:00'))
        # 轉換到 GMT+8 台灣時間
        dt_gmt8 = dt + timedelta(hours=8)
        return dt_gmt8.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_time_str[:19] if len(iso_time_str) >= 19 else iso_time_str


def hour_to_12h_format(hour):
    """將 24 小時制轉換為 12 小時制"""
    if hour == 0:
        return '12:00 AM'
    elif hour < 12:
        return f'{hour}:00 AM'
    elif hour == 12:
        return '12:00 PM'
    else:
        return f'{hour - 12}:00 PM'


def get_day_name_chinese(day_code):
    """將星期代碼轉換為中文 (週一為第一天)"""
    day_map = {
        'Mon': '週一', 'Tue': '週二', 'Wed': '週三',
        'Thu': '週四', 'Fri': '週五', 'Sat': '週六', 'Sun': '週日',
        0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'
    }
    return day_map.get(day_code, str(day_code))


def extract_hashtags(message):
    """從訊息中提取 hashtags"""
    if not message:
        return ''
    hashtags = re.findall(r'#[\w\u4e00-\u9fff]+', message)
    return ', '.join(hashtags) if hashtags else ''

# 行動類型翻譯 (原 format_type)
FORMAT_TYPE_CHINESE = {
    'event': '定期活動',
    'press': '記者會',
    'statement': '聲明稿',
    'opinion': '新聞觀點',
    'op_ed': '投書',
    'report': '報告發布',
    'booth': '擺攤資訊',
    'edu': '科普/Podcast',
    'action': '行動號召',
    '': '其他行動 (無關鍵字匹配)',
    None: '其他行動 (無關鍵字匹配)'
}

# 議題類型翻譯
ISSUE_TOPIC_CHINESE = {
    'nuclear': '核能發電',
    'climate': '氣候問題',
    'net_zero': '淨零政策',
    'industry': '產業分析',
    'renewable': '能源發展',
    'other': '其他議題',
    '': '其他議題 (無關鍵字匹配)',
    None: '其他議題 (無關鍵字匹配)'
}


# 時段翻譯
TIME_SLOT_CHINESE = {
    'morning': '早上 (6-12點)',
    'noon': '中午 (12-15點)',
    'afternoon': '下午 (15-18點)',
    'evening': '晚上 (18-23點)',
    'night': '深夜 (23-6點)',
    '': '未知',
    None: '未知'
}

# 表現等級翻譯 (含定義說明)
PERFORMANCE_TIER_CHINESE = {
    'viral': '熱門 (前5%)',
    'high': '優質 (前25%)',
    'average': '一般 (中間50%)',
    'low': '待改進 (後25%)',
    '': '未評級',
    None: '未評級'
}


def translate_format_type(code):
    """將行動代碼翻譯為中文"""
    return FORMAT_TYPE_CHINESE.get(code, code or '未分類')


def translate_issue_topic(code):
    """將議題代碼翻譯為中文"""
    return ISSUE_TOPIC_CHINESE.get(code, code or '未分類')


def translate_time_slot(code):
    """將時段代碼翻譯為中文"""
    return TIME_SLOT_CHINESE.get(code, code or '未知')


def translate_performance_tier(code):
    """將表現等級翻譯為中文"""
    return PERFORMANCE_TIER_CHINESE.get(code, code or '未評級')


# Credential file path (relative to this file)
CREDENTIALS_FILE = Path(__file__).parent.parent / 'fb-dashboard' / 'esg-reports-collection-9661012923ed.json'

def setup_google_sheets_client():
    """設定 Google Sheets 客戶端

    優先順序:
    1. 本地 JSON 憑證檔案 (CREDENTIALS_FILE)
    2. 環境變數 GCP_SA_CREDENTIALS (JSON 字串)
    3. 環境變數 GCP_SA_CREDENTIALS_BASE64 (Base64 編碼)
    """
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Priority 1: Load from local JSON file
        if CREDENTIALS_FILE.exists():
            print(f"  使用憑證檔案: {CREDENTIALS_FILE.name}")
            credentials = service_account.Credentials.from_service_account_file(
                str(CREDENTIALS_FILE), scopes=scope)
            client = gspread.authorize(credentials)
            print("✓ Google Sheets 客戶端設定成功 (檔案憑證)")
            return client

        # Priority 2 & 3: Load from environment variables
        credentials_json = os.environ.get('GCP_SA_CREDENTIALS')
        credentials_base64 = os.environ.get('GCP_SA_CREDENTIALS_BASE64')

        if credentials_base64:
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
        elif not credentials_json:
            print("⚠️  找不到 Google Sheets 憑證")
            print(f"   嘗試的憑證檔案路徑: {CREDENTIALS_FILE}")
            print("   或設定環境變數: GCP_SA_CREDENTIALS / GCP_SA_CREDENTIALS_BASE64")
            return None

        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=scope)

        client = gspread.authorize(credentials)
        print("✓ Google Sheets 客戶端設定成功 (環境變數)")
        return client

    except Exception as e:
        print(f"✗ Google Sheets 客戶端設定失敗: {e}")
        return None


def export_best_posting_times(client, conn):
    """導出最佳發文時間分析 (含 General / 按議題 / 按行動分組)"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        # 檢查工作表是否存在，不存在則建立
        try:
            worksheet = spreadsheet.worksheet('best_posting_times')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='best_posting_times', rows=200, cols=15)

        # 清空現有數據
        worksheet.clear()

        # 時段轉換對照表
        time_slot_map = {
            'morning': '6:00 AM - 12:00 PM',
            'noon': '12:00 PM - 3:00 PM',
            'afternoon': '3:00 PM - 6:00 PM',
            'evening': '6:00 PM - 11:00 PM',
            'night': '11:00 PM - 6:00 AM'
        }

        rows = []

        # === Section 1: General ===
        rows.append(['📊 整體最佳發文時間', '', '', '', ''])
        headers = ['時段', '星期', '貼文數', '平均互動率 (%)', '平均點擊率 (%)']
        rows.append(headers)

        data_general = analytics_reports.get_best_posting_times(conn, limit=20)
        for item in data_general:
            rows.append([
                time_slot_map.get(item['time_slot'], item['time_slot']),
                get_day_name_chinese(item['day_of_week']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        rows.append(['', '', '', '', ''])  # 空行

        # === Section 2: By Issue Topic ===
        rows.append(['📌 按議題分組', '', '', '', '', ''])
        headers_topic = ['議題', '時段', '星期', '貼文數', '平均互動率 (%)', '平均點擊率 (%)']
        rows.append(headers_topic)

        data_topic = analytics_reports.get_best_posting_times_by_topic(conn, limit=50)
        for item in data_topic:
            rows.append([
                translate_issue_topic(item['issue_topic']),
                time_slot_map.get(item['time_slot'], item['time_slot']),
                get_day_name_chinese(item['day_of_week']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        rows.append(['', '', '', '', '', ''])  # 空行

        # === Section 3: By Format Type ===
        rows.append(['🎯 按行動分組', '', '', '', '', ''])
        headers_format = ['行動', '時段', '星期', '貼文數', '平均互動率 (%)', '平均點擊率 (%)']
        rows.append(headers_format)

        data_format = analytics_reports.get_best_posting_times_by_format(conn, limit=50)
        for item in data_format:
            rows.append([
                translate_format_type(item['format_type']),
                time_slot_map.get(item['time_slot'], item['time_slot']),
                get_day_name_chinese(item['day_of_week']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        # 寫入數據
        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化標題列
        worksheet.format('A1:E1', {
            "backgroundColor": {"red": 0.9, "green": 0.5, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出最佳發文時間分析（General: {len(data_general)}, 議題: {len(data_topic)}, 行動: {len(data_format)}）")
        return True

    except Exception as e:
        print(f"  ✗ 導出最佳發文時間失敗: {e}")
        return False


def export_format_type_performance(client, conn):
    """導出貼文形式表現分析 (主題)"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('format_type_performance')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='format_type_performance', rows=100, cols=15)

        worksheet.clear()

        data = analytics_reports.get_format_type_performance(conn)

        headers = ['行動', '貼文數', '平均互動率 (%)', '平均分享率 (%)',
                   '平均留言率 (%)', '熱門數 (前5%)', '優質數 (前25%)']
        rows = [headers]

        for item in data:
            rows.append([
                translate_format_type(item['format_type']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_share_rate'], 2),
                round(item['avg_comment_rate'], 2),
                item['viral_count'],
                item['high_count']
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:G1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出貼文形式表現（{len(data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出貼文形式表現失敗: {e}")
        return False


def export_issue_topic_performance(client, conn):
    """導出議題表現分析"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('issue_topic_performance')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='issue_topic_performance', rows=100, cols=15)

        worksheet.clear()

        data = analytics_reports.get_issue_topic_performance(conn)

        headers = ['議題', '貼文數', '平均互動率 (%)', '平均分享率 (%)',
                   '平均留言率 (%)', '熱門數 (前5%)', '優質數 (前25%)']
        rows = [headers]

        for item in data:
            rows.append([
                translate_issue_topic(item['issue_topic']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_share_rate'], 2),
                round(item['avg_comment_rate'], 2),
                item['viral_count'],
                item['high_count']
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:G1', {
            "backgroundColor": {"red": 0.4, "green": 0.7, "blue": 0.4},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出議題表現分析（{len(data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出議題表現失敗: {e}")
        return False


def export_format_issue_cross(client, conn):
    """導出行動 × 議題交叉分析"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('format_issue_cross')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='format_issue_cross', rows=200, cols=15)

        worksheet.clear()

        data = analytics_reports.get_format_issue_cross_performance(conn)

        headers = ['行動', '議題', '貼文數', '平均互動率 (%)', '平均分享率 (%)', '高表現貼文數']
        rows = [headers]

        for item in data:
            rows.append([
                translate_format_type(item['format_type']),
                translate_issue_topic(item['issue_topic']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_share_rate'], 2),
                item['high_performer_count']
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:F1', {
            "backgroundColor": {"red": 0.6, "green": 0.4, "blue": 0.7},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出行動×議題交叉分析（{len(data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出行動×議題交叉分析失敗: {e}")
        return False


# 保留舊函數名稱相容
def export_topic_performance(client, conn):
    """導出主題表現分析 (向後相容)"""
    return export_format_type_performance(client, conn)


def export_top_posts(client, conn, days=30, limit=20):
    """導出表現最佳貼文"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('top_posts')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='top_posts', rows=100, cols=15)

        worksheet.clear()

        data = analytics_reports.get_top_posts(conn, days=days, limit=limit)

        headers = ['貼文 ID', '內容預覽', '發布時間 (GMT+8)', '行動', '議題', '時段',
                   '互動率 (%)', '表現等級', '百分位數', '觸及', '總互動數', '連結']
        rows = [headers]

        for item in data:
            rows.append([
                item['post_id'][-15:],  # 只顯示後 15 碼
                (item['message_preview'] or '')[:50],
                convert_to_gmt8(item['created_time'])[:10],  # 只顯示日期 (GMT+8)
                translate_format_type(item['topic_primary']),  # 行動中文
                translate_issue_topic(item.get('issue_topic')),  # 議題中文
                translate_time_slot(item['time_slot']),  # 時段中文
                round(item['engagement_rate'], 2),
                translate_performance_tier(item['performance_tier']),  # 等級中文
                round(item['percentile_rank'], 1),
                item['reach'],
                item['total_engagement'],
                item.get('permalink_url', '')  # 連結
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:L1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出 Top 貼文（{len(data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出 Top 貼文失敗: {e}")
        return False


def export_weekly_trends(client, conn, weeks=104):  # 預設兩年
    """導出週度趨勢"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('weekly_trends')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='weekly_trends', rows=100, cols=10)

        worksheet.clear()

        data = analytics_reports.get_weekly_trends(conn, weeks=weeks)

        # 使用日期範圍格式而非週次號
        headers = ['週次 (日期範圍)', '貼文數', '平均互動率 (%)', '總觸及', '總互動數']
        rows = [headers]

        for item in data:
            # 顯示 yyyy-mm-dd ~ yyyy-mm-dd 格式
            week_range = f"{item.get('week_start', '')} ~ {item.get('week_end', '')}"
            rows.append([
                week_range,
                item['post_count'],
                round(item['avg_er'], 2),
                item['total_reach'],
                item['total_engagement']
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:E1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出週度趨勢（{len(data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出週度趨勢失敗: {e}")
        return False


def export_hourly_performance(client, conn):
    """導出每小時表現分析"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('hourly_performance')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='hourly_performance', rows=100, cols=10)

        worksheet.clear()

        data = analytics_reports.get_hourly_performance(conn)

        headers = ['時間', '貼文數', '平均互動率 (%)', '平均點擊率 (%)']
        rows = [headers]

        for item in data:
            rows.append([
                hour_to_12h_format(item['hour_of_day']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:D1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出每小時表現（{len(data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出每小時表現失敗: {e}")
        return False


def export_raw_posts(client, conn):
    """導出 posts 表原始資料"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('raw_posts')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='raw_posts', rows=1000, cols=10)

        worksheet.clear()

        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.post_id, p.page_id, p.created_time, p.message, p.permalink_url,
                   pc.format_type, pc.issue_topic, pc.media_type
            FROM posts p
            LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
            ORDER BY p.created_time DESC
        """)
        rows_data = cursor.fetchall()

        headers = ['Post ID', 'Page ID', '發布時間 (GMT+8)', '內容', '標籤 (Hashtag)', '行動', '議題', '媒體類型', '連結']
        rows = [headers]

        # 媒體類型翻譯
        media_type_chinese = {
            'photo': '圖片',
            'photos': '多圖',
            'video': '影片',
            'link': '連結',
            'text': '純文字',
            'album': '相簿',
            None: '未分類',
            '': '未分類'
        }

        for row in rows_data:
            message = row[3] or ''
            rows.append([
                row[0],  # post_id
                row[1],  # page_id
                convert_to_gmt8(row[2]),  # created_time (GMT+8)
                message[:500],  # message (限制長度)
                extract_hashtags(message),  # hashtags
                translate_format_type(row[5]),  # format_type → 行動中文
                translate_issue_topic(row[6]),  # issue_topic → 議題中文
                media_type_chinese.get(row[7], row[7] or '未分類'),  # media_type
                row[4] or ''  # permalink_url
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:I1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出貼文原始資料（{len(rows_data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出貼文原始資料失敗: {e}")
        return False


def export_raw_post_insights(client, conn):
    """導出貼文完整資料 (合併 posts + post_insights_snapshots + posts_classification)"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('raw_post_insights')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='raw_post_insights', rows=1000, cols=25)

        worksheet.clear()

        # 合併欄位：基本資訊 + 分類 + 互動數據
        headers = [
            'Post ID', '發布時間 (GMT+8)', '內容預覽', '行動類型', '議題類型',
            '總讚數', '留言數', '分享數', '點擊數', '觸及人數',
            '影片觀看', '自然觀看', '付費觀看',
            '👍反應', '❤️反應', '😮反應', '😆反應', '😢反應', '😠反應',
            '貼文連結'
        ]

        cursor = conn.cursor()
        # 合併 posts + post_insights_snapshots + posts_classification
        cursor.execute("""
            WITH latest_snapshots AS (
                SELECT post_id, MAX(fetch_date) as latest_date
                FROM post_insights_snapshots
                GROUP BY post_id
            )
            SELECT
                p.post_id, p.created_time, SUBSTR(p.message, 1, 100) as message_preview,
                pc.format_type, pc.issue_topic,
                i.likes_count, i.comments_count, i.shares_count,
                i.post_clicks, i.post_impressions_unique,
                i.post_video_views, i.post_video_views_organic, i.post_video_views_paid,
                i.post_reactions_like_total, i.post_reactions_love_total,
                i.post_reactions_wow_total, i.post_reactions_haha_total,
                i.post_reactions_sorry_total, i.post_reactions_anger_total,
                p.permalink_url
            FROM post_insights_snapshots i
            JOIN latest_snapshots ls ON i.post_id = ls.post_id AND i.fetch_date = ls.latest_date
            JOIN posts p ON i.post_id = p.post_id
            LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
            ORDER BY p.created_time DESC
        """)
        rows_data = cursor.fetchall()

        # 行動/議題翻譯
        format_map = {
            'event': '定期活動', 'press': '記者會', 'statement': '聲明稿',
            'opinion': '新聞觀點', 'op_ed': '投書', 'report': '報告發布',
            'booth': '擺攤資訊', 'edu': '科普/Podcast', 'action': '行動號召'
        }
        issue_map = {
            'nuclear': '核能發電', 'climate': '氣候問題', 'net_zero': '淨零政策',
            'industry': '產業分析', 'renewable': '能源發展', 'other': '其他議題'
        }

        rows = [headers]
        for row in rows_data:
            rows.append([
                row[0],  # post_id
                convert_to_gmt8(row[1]),  # created_time (GMT+8)
                (row[2] or '')[:100],  # message_preview
                format_map.get(row[3], row[3] or ''),  # format_type
                issue_map.get(row[4], row[4] or ''),  # issue_topic
                row[5] or 0, row[6] or 0, row[7] or 0,  # likes, comments, shares
                row[8] or 0, row[9] or 0,  # clicks, reach
                row[10] or 0, row[11] or 0, row[12] or 0,  # video views
                row[13] or 0, row[14] or 0, row[15] or 0, row[16] or 0, row[17] or 0, row[18] or 0,  # reactions
                row[19] or ''  # permalink_url
            ])

        if rows:
            update_with_timestamp(worksheet, 'A1', rows)

        # 格式化標題 (21 columns including timestamp)
        worksheet.format('A1:U1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出貼文完整資料（{len(rows_data)} 筆，含分類與互動數據）")
        return True

    except Exception as e:
        print(f"  ✗ 導出貼文完整資料失敗: {e}")
        return False


def export_page_daily_metrics(client, conn):
    """導出 page_daily_metrics 表原始資料 (含每日貼文數)"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('page_daily_metrics')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='page_daily_metrics', rows=500, cols=15)

        # 完整重寫模式，確保資料一致
        worksheet.clear()

        # 新標題：日期、貼文數、觸及人數...
        headers = ['日期', '貼文數', '觸及人數', '互動數', '影片觀看',
                   '讚', '愛心', '哇', '哈哈', '嗚嗚', '怒', '總反應數']

        cursor = conn.cursor()
        # 結合 page_daily_metrics 與 posts 表計算每日貼文數
        cursor.execute("""
            SELECT 
                pdm.date,
                COALESCE(post_counts.post_count, 0) as post_count,
                pdm.page_impressions_unique, 
                pdm.page_post_engagements, 
                pdm.page_video_views,
                pdm.reactions_like, 
                pdm.reactions_love, 
                pdm.reactions_wow,
                pdm.reactions_haha, 
                pdm.reactions_sorry, 
                pdm.reactions_anger, 
                pdm.reactions_total
            FROM page_daily_metrics pdm
            LEFT JOIN (
                SELECT DATE(created_time) as post_date, COUNT(*) as post_count
                FROM posts
                GROUP BY DATE(created_time)
            ) post_counts ON pdm.date = post_counts.post_date
            ORDER BY pdm.date DESC
        """)
        rows_data = cursor.fetchall()

        rows = [headers]
        for row in rows_data:
            rows.append(list(row))

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化標題
        worksheet.format('A1:L1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出頁面每日指標（{len(rows_data)} 筆，含貼文數）")
        return True

    except Exception as e:
        print(f"  ✗ 導出頁面每日指標失敗: {e}")
        return False


def export_raw_ads(client, conn):
    """導出廣告原始資料（ads + ad_insights 合併）"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('raw_ads')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='raw_ads', rows=500, cols=18)

        worksheet.clear()

        cursor = conn.cursor()

        # 檢查 ads 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ads'")
        if not cursor.fetchone():
            headers = ['尚無廣告資料']
            worksheet.update([headers], 'A1')
            print("  ⊘ 廣告資料表尚未建立")
            return True

        # 合併 ads 與 ad_insights，取得最新數據
        cursor.execute("""
            WITH latest_insights AS (
                SELECT ad_id, MAX(date_stop) as latest_date
                FROM ad_insights
                GROUP BY ad_id
            )
            SELECT
                a.ad_id,
                a.name as ad_name,
                ac.name as campaign_name,
                a.status,
                a.post_id,
                DATE(a.created_time) as created_date,
                ai.date_start,
                ai.date_stop,
                COALESCE(ai.impressions, 0) as impressions,
                COALESCE(ai.reach, 0) as reach,
                COALESCE(ai.clicks, 0) as clicks,
                COALESCE(ai.spend, 0) as spend,
                COALESCE(ai.cpm, 0) as cpm,
                COALESCE(ai.cpc, 0) as cpc,
                COALESCE(ai.ctr, 0) as ctr
            FROM ads a
            LEFT JOIN ad_campaigns ac ON a.campaign_id = ac.campaign_id
            LEFT JOIN latest_insights li ON a.ad_id = li.ad_id
            LEFT JOIN ad_insights ai ON a.ad_id = ai.ad_id AND ai.date_stop = li.latest_date
            ORDER BY ai.spend DESC NULLS LAST, a.created_time DESC
        """)
        rows_data = cursor.fetchall()

        # 狀態翻譯
        status_chinese = {
            'ACTIVE': '運行中',
            'PAUSED': '已暫停',
            'DELETED': '已刪除',
            'ARCHIVED': '已封存',
            'PENDING_REVIEW': '審核中',
            'DISAPPROVED': '未通過',
        }

        headers = [
            '廣告 ID', '廣告名稱', '活動名稱', '狀態', '推廣貼文 ID', '建立日期',
            '統計起始', '統計結束', '曝光數', '觸及人數', '點擊數',
            '花費 (NT$)', 'CPM', 'CPC', 'CTR (%)'
        ]
        rows = [headers]

        for row in rows_data:
            rows.append([
                row[0][-15:] if row[0] else '',  # ad_id
                row[1] or '',  # ad_name
                row[2] or '',  # campaign_name
                status_chinese.get(row[3], row[3] or ''),  # status
                row[4][-15:] if row[4] else '',  # post_id
                row[5] or '',  # created_date
                row[6] or '',  # date_start
                row[7] or '',  # date_stop
                row[8],  # impressions
                row[9],  # reach
                row[10],  # clicks
                round(row[11], 2),  # spend
                round(row[12], 2),  # cpm
                round(row[13], 2),  # cpc
                round(row[14], 2) if row[14] else 0  # ctr
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:O1', {
            "backgroundColor": {"red": 0.8, "green": 0.4, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出廣告原始資料（{len(rows_data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出廣告原始資料失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_quadrant_analysis(client, conn):
    """導出象限分析資料（用於 Looker Studio 視覺化）"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('quadrant_analysis')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='quadrant_analysis', rows=600, cols=15)

        worksheet.clear()

        data = analytics_reports.get_quadrant_analysis(conn)

        headers = ['貼文 ID', '發布時間 (GMT+8)', '觸及人數', '互動率 (%)',
                   '中位數觸及', '中位數互動率 (%)', '象限', '議題', '行動', '內容預覽', '連結']
        rows = [headers]

        for item in data:
            rows.append([
                item['post_id'][-18:],  # 只顯示後 18 碼
                convert_to_gmt8(item['created_time'])[:10],
                item['reach'],
                round(item['engagement_rate'] * 100, 2),
                item['median_reach'],
                round(item['median_er'] * 100, 2),
                item['quadrant'],
                translate_issue_topic(item['topic_tag']),
                translate_format_type(item['format_type']),
                (item['content_short'] or '')[:40],
                item['permalink_url'] or ''
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化標題
        worksheet.format('A1:K1', {
            "backgroundColor": {"red": 0.4, "green": 0.2, "blue": 0.6},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        # 統計各象限數量
        quadrant_counts = {}
        for item in data:
            q = item['quadrant']
            quadrant_counts[q] = quadrant_counts.get(q, 0) + 1

        print(f"  ✓ 已導出象限分析（{len(data)} 筆）")
        for q, count in quadrant_counts.items():
            print(f"    - {q}: {count}")
        return True

    except Exception as e:
        print(f"  ✗ 導出象限分析失敗: {e}")
        return False


def export_deep_dive_metrics(client, conn, limit=100):
    """導出深度指標分析 - 包含所有核心 KPI"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('deep_dive_metrics')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='deep_dive_metrics', rows=200, cols=20)

        worksheet.clear()

        cursor = conn.cursor()
        # 使用 MAX 聚合（與 posts_performance KPI 計算一致，避免數據不一致）
        cursor.execute("""
            WITH max_snapshots AS (
                SELECT post_id,
                       MAX(post_impressions_unique) as post_impressions_unique,
                       MAX(likes_count) as likes_count,
                       MAX(comments_count) as comments_count,
                       MAX(shares_count) as shares_count,
                       MAX(post_clicks) as post_clicks
                FROM post_insights_snapshots
                GROUP BY post_id
            )
            SELECT
                p.post_id,
                substr(p.created_time, 1, 10) as post_date,
                SUBSTR(p.message, 1, 80) as message_preview,
                pc.format_type,
                pc.issue_topic,
                pp.engagement_rate,
                pp.share_rate,
                pp.comment_rate,
                pp.click_through_rate,
                pp.virality_score,
                pp.discussion_depth,
                pp.performance_tier,
                pp.percentile_rank,
                ms.post_impressions_unique as reach,
                ms.likes_count,
                ms.comments_count,
                ms.shares_count,
                ms.post_clicks,
                (ms.likes_count + ms.comments_count + ms.shares_count) as total_engagement,
                p.permalink_url
            FROM posts p
            LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
            LEFT JOIN posts_performance pp ON p.post_id = pp.post_id
            LEFT JOIN max_snapshots ms ON p.post_id = ms.post_id
            ORDER BY pp.engagement_rate DESC
            LIMIT ?
        """, (limit,))

        rows_data = cursor.fetchall()

        headers = [
            '貼文 ID', '發布日期', '內容預覽', '行動', '議題',
            '互動率 (%)', '分享率 (%)', '留言率 (%)', '點擊率 (%)',
            '病毒性分數', '討論深度',
            '表現等級', '百分位數',
            '觸及', '讚數', '留言數', '分享數', '點擊數', '總互動數',
            '連結'
        ]
        rows = [headers]

        for row in rows_data:
            rows.append([
                row[0][-15:],  # post_id 後 15 碼
                row[1],  # post_date
                row[2] or '',  # message_preview
                translate_format_type(row[3]),  # format_type
                translate_issue_topic(row[4]),  # issue_topic
                round(row[5], 2) if row[5] is not None else '',  # engagement_rate
                round(row[6], 2) if row[6] is not None else '',  # share_rate
                round(row[7], 2) if row[7] is not None else '',  # comment_rate
                round(row[8], 2) if row[8] is not None else '',  # click_through_rate
                round(row[9], 2) if row[9] is not None else '',  # virality_score
                round(row[10], 2) if row[10] is not None else '',  # discussion_depth
                translate_performance_tier(row[11]),  # performance_tier
                round(row[12], 1) if row[12] is not None else '',  # percentile_rank
                row[13] or 0,  # reach
                row[14] or 0,  # likes
                row[15] or 0,  # comments
                row[16] or 0,  # shares
                row[17] or 0,  # clicks
                row[18] or 0,  # total_engagement
                row[19] or ''  # permalink
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化標題 - 深藍色
        worksheet.format('A1:T1', {
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.7},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        # 條件格式化 - 互動率 (F欄)
        # 綠色: > 3%, 黃色: 1-3%, 紅色: < 1%
        # 註：Google Sheets API 的條件格式較複雜，這裡只做基本格式化

        print(f"  ✓ 已導出深度指標分析（{len(rows_data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出深度指標分析失敗: {e}")
        return False


def export_ad_recommendations(client, conn, limit=50):
    """導出投廣推薦清單（含歷史最佳組合建議）"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('ad_recommendations')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='ad_recommendations', rows=300, cols=15)

        worksheet.clear()

        # 更新投廣潛力分數
        ad_predictor.update_all_ad_potentials(conn)

        # === Section 1: 歷史最佳組合建議（供未發布內容參考） ===
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(pc.issue_topic, '未分類') as issue_topic,
                COALESCE(pc.format_type, '未分類') as format_type,
                pc.time_slot,
                CASE pc.day_of_week
                    WHEN 0 THEN '週一' WHEN 1 THEN '週二' WHEN 2 THEN '週三'
                    WHEN 3 THEN '週四' WHEN 4 THEN '週五' WHEN 5 THEN '週六' WHEN 6 THEN '週日'
                END as day_name,
                COUNT(*) as post_count,
                ROUND(AVG(pp.engagement_rate), 2) as avg_er,
                SUM(CASE WHEN pp.performance_tier IN ('viral', 'high') THEN 1 ELSE 0 END) as high_performers
            FROM posts_classification pc
            JOIN posts_performance pp ON pc.post_id = pp.post_id
            GROUP BY pc.issue_topic, pc.format_type, pc.time_slot, pc.day_of_week
            HAVING post_count >= 3
            ORDER BY avg_er DESC
            LIMIT 15
        """)
        best_combos = cursor.fetchall()

        rows = [
            ['📊 歷史最佳組合（供新內容投廣參考）', '', '', '', '', '', ''],
            ['議題', '行動', '時段', '星期', '樣本數', '平均互動率 (%)', '高表現數'],
        ]

        for combo in best_combos:
            rows.append([
                translate_issue_topic(combo[0]),
                translate_format_type(combo[1]),
                translate_time_slot(combo[2]),
                combo[3] or '未分類',
                combo[4],
                combo[5],
                combo[6]
            ])

        rows.append(['', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])

        # === Section 2: 已發布貼文推薦 ===
        rows.append(['📌 已發布貼文投廣推薦', '', '', '', '', '', '', '', '', '', '', '', ''])
        headers = [
            '貼文 ID', '發布時間', '投廣建議', '潛力分數', '表現等級',
            '行動', '議題', '互動率分數', '分享率分數', '留言率分數',
            '議題因子', '時段因子', '貼文連結'
        ]
        rows.append(headers)

        # 取得推薦貼文
        recommended = ad_predictor.get_recommended_posts(conn, limit=limit, min_score=40)

        for item in recommended:
            breakdown = item.get('breakdown', {})
            rows.append([
                item['post_id'][-15:],
                convert_to_gmt8(item.get('created_time', ''))[:10],
                item['ad_recommendation'],
                item['ad_potential_score'],
                translate_performance_tier(item['performance_tier']),
                translate_format_type(item['format_type']),
                translate_issue_topic(item['issue_topic']),
                round(breakdown.get('engagement_rate_score', 0), 1),
                round(breakdown.get('share_rate_score', 0), 1),
                round(breakdown.get('comment_rate_score', 0), 1),
                breakdown.get('topic_factor', 1),
                breakdown.get('time_factor', 1),
                item.get('permalink_url', '')
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化歷史建議標題
        worksheet.format('A1:G1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.4},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
        })
        worksheet.format('A2:G2', {
            "backgroundColor": {"red": 0.3, "green": 0.5, "blue": 0.4},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        # 格式化已發布推薦標題
        detail_header_row = len(best_combos) + 5
        worksheet.format(f'A{detail_header_row}:M{detail_header_row}', {
            "backgroundColor": {"red": 0.8, "green": 0.4, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
        })
        worksheet.format(f'A{detail_header_row + 1}:M{detail_header_row + 1}', {
            "backgroundColor": {"red": 0.7, "green": 0.4, "blue": 0.3},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出投廣推薦清單（歷史組合: {len(best_combos)}, 貼文: {len(recommended)}）")
        return True

    except Exception as e:
        print(f"  ✗ 導出投廣推薦清單失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_trending_posts(client, conn, hours=96):
    """導出近期熱門貼文（正在起飛的貼文）"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('trending_posts')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='trending_posts', rows=100, cols=12)

        worksheet.clear()

        # 取得熱門貼文
        trending = analytics_trends.get_trending_posts(conn, hours=hours)

        headers = [
            '貼文 ID', '內容預覽', '發布時間', '已發布小時數',
            '當前互動數', '觸及', '每小時互動', '互動率 (%)'
        ]
        rows = [headers]

        for item in trending:
            rows.append([
                item['post_id'][-15:],
                (item['message_preview'] or '')[:50],
                item['created_time'][:16] if item['created_time'] else '',
                item['hours_since_post'],
                item['current_engagement'],
                item['reach'] or 0,
                item['engagement_per_hour'],
                item['engagement_rate']
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化
        worksheet.format('A1:H1', {
            "backgroundColor": {"red": 0.3, "green": 0.7, "blue": 0.3},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出近期熱門貼文（{len(trending)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出近期熱門貼文失敗: {e}")
        return False


def export_organic_vs_paid(client, conn):
    """導出自然 vs 付費貼文成效比較"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('organic_vs_paid')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='organic_vs_paid', rows=200, cols=20)

        worksheet.clear()

        cursor = conn.cursor()
        
        # 取得最新的 post_insights_snapshots（避免重複）
        cursor.execute("""
            WITH latest_snapshots AS (
                SELECT post_id, MAX(fetch_date) as latest_date
                FROM post_insights_snapshots
                GROUP BY post_id
            ),
            promoted_posts AS (
                SELECT DISTINCT post_id FROM ads WHERE post_id IS NOT NULL
            )
            SELECT 
                p.post_id,
                SUBSTR(p.message, 1, 60) as message_preview,
                DATE(p.created_time) as post_date,
                CASE WHEN pp.post_id IS NOT NULL THEN '有廣告' ELSE '自然觸及' END as ad_status,
                COALESCE(pc.format_type, '未分類') as format_type,
                COALESCE(pc.issue_topic, '未分類') as issue_topic,
                perf.engagement_rate,
                perf.share_rate,
                perf.comment_rate,
                perf.click_through_rate,
                perf.performance_tier,
                i.post_impressions_unique as reach,
                i.likes_count + i.comments_count + i.shares_count as total_engagement,
                i.likes_count,
                i.comments_count,
                i.shares_count,
                i.post_clicks,
                p.permalink_url
            FROM posts p
            JOIN latest_snapshots ls ON p.post_id = ls.post_id
            JOIN post_insights_snapshots i ON p.post_id = i.post_id AND i.fetch_date = ls.latest_date
            LEFT JOIN promoted_posts pp ON p.post_id = pp.post_id
            LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
            LEFT JOIN posts_performance perf ON p.post_id = perf.post_id
            ORDER BY i.post_impressions_unique DESC
            LIMIT 600
        """)
        rows_data = cursor.fetchall()

        # 計算摘要統計
        cursor.execute("""
            WITH latest_snapshots AS (
                SELECT post_id, MAX(fetch_date) as latest_date
                FROM post_insights_snapshots
                GROUP BY post_id
            ),
            promoted_posts AS (
                SELECT DISTINCT post_id FROM ads WHERE post_id IS NOT NULL
            )
            SELECT 
                CASE WHEN pp.post_id IS NOT NULL THEN 'paid' ELSE 'organic' END as ad_status,
                COUNT(*) as post_count,
                ROUND(AVG(perf.engagement_rate), 2) as avg_er,
                ROUND(AVG(perf.share_rate), 2) as avg_sr,
                ROUND(AVG(perf.comment_rate), 2) as avg_cr,
                ROUND(AVG(perf.click_through_rate), 2) as avg_ctr,
                SUM(i.post_impressions_unique) as total_reach,
                SUM(i.likes_count + i.comments_count + i.shares_count) as total_engagement
            FROM posts p
            JOIN latest_snapshots ls ON p.post_id = ls.post_id
            JOIN post_insights_snapshots i ON p.post_id = i.post_id AND i.fetch_date = ls.latest_date
            LEFT JOIN promoted_posts pp ON p.post_id = pp.post_id
            LEFT JOIN posts_performance perf ON p.post_id = perf.post_id
            GROUP BY ad_status
        """)
        summary_data = cursor.fetchall()

        # 準備摘要區塊
        rows = [
            ['自然 vs 付費貼文成效比較', '', '', '', '', '', '', ''],
            ['（表現等級依互動率百分位計算：前5%=熱門, 前25%=優質, 中間50%=一般, 後25%=待改進）', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['類型', '貼文數', '平均互動率 (%)', '平均分享率 (%)', '平均留言率 (%)', '平均點擊率 (%)', '總觸及', '總互動數'],
        ]
        
        for row in summary_data:
            status = '有廣告' if row[0] == 'paid' else '自然觸及'
            rows.append([
                status, row[1], row[2] or 0, row[3] or 0, row[4] or 0, row[5] or 0, row[6] or 0, row[7] or 0
            ])
        
        rows.append(['', '', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', '', ''])
        
        # 詳細數據標題
        detail_headers = [
            '貼文 ID', '內容預覽', '發布日期', '廣告狀態', '行動', '議題',
            '互動率 (%)', '分享率 (%)', '留言率 (%)', '點擊率 (%)',
            '表現等級', '觸及', '總互動', '讚數', '留言數', '分享數', '點擊數', '連結'
        ]
        rows.append(detail_headers)

        for row in rows_data:
            rows.append([
                row[0][-15:],
                row[1] or '',
                row[2] or '',
                row[3],
                translate_format_type(row[4]),
                translate_issue_topic(row[5]),
                round(row[6], 2) if row[6] else 0,
                round(row[7], 2) if row[7] else 0,
                round(row[8], 2) if row[8] else 0,
                round(row[9], 2) if row[9] else 0,
                translate_performance_tier(row[10]),
                row[11] or 0,
                row[12] or 0,
                row[13] or 0,
                row[14] or 0,
                row[15] or 0,
                row[16] or 0,
                row[17] or ''
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化摘要標題
        worksheet.format('A1:H1', {
            "backgroundColor": {"red": 0.6, "green": 0.2, "blue": 0.6},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 14}
        })
        worksheet.format('A2:H2', {
            "textFormat": {"italic": True, "foregroundColor": {"red": 0.4, "green": 0.4, "blue": 0.4}, "fontSize": 10}
        })
        worksheet.format('A4:H4', {
            "backgroundColor": {"red": 0.4, "green": 0.2, "blue": 0.5},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出自然 vs 付費比較（{len(rows_data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出自然 vs 付費比較失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_ad_campaigns(client, conn):
    """導出廣告活動清單"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('ad_campaigns')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='ad_campaigns', rows=100, cols=12)

        worksheet.clear()

        cursor = conn.cursor()
        
        # 檢查 ad_campaigns 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_campaigns'")
        if not cursor.fetchone():
            print("  ⊘ 廣告活動表尚未建立")
            return True  # 非致命錯誤

        cursor.execute("""
            SELECT 
                ac.campaign_id,
                ac.name,
                ac.objective,
                ac.status,
                COALESCE(ac.daily_budget, 0) as daily_budget,
                COALESCE(ac.lifetime_budget, 0) as lifetime_budget,
                DATE(ac.created_time) as created_date,
                COUNT(DISTINCT a.ad_id) as ad_count,
                COALESCE(SUM(ai.spend), 0) as total_spend,
                COALESCE(SUM(ai.impressions), 0) as total_impressions,
                COALESCE(SUM(ai.clicks), 0) as total_clicks,
                CASE WHEN SUM(ai.clicks) > 0 
                     THEN ROUND(SUM(ai.spend) / SUM(ai.clicks), 2) 
                     ELSE 0 END as avg_cpc
            FROM ad_campaigns ac
            LEFT JOIN ads a ON ac.campaign_id = a.campaign_id
            LEFT JOIN ad_insights ai ON a.ad_id = ai.ad_id
            GROUP BY ac.campaign_id
            ORDER BY total_spend DESC
        """)
        rows_data = cursor.fetchall()

        headers = [
            '活動 ID', '活動名稱', '目標', '狀態', '每日預算 (NT$)', '總預算 (NT$)',
            '建立日期', '廣告數', '總花費 (NT$)', '總曝光', '總點擊', '平均 CPC (NT$)'
        ]
        rows = [headers]

        # 目標翻譯
        objective_chinese = {
            'OUTCOME_AWARENESS': '品牌知名度',
            'OUTCOME_ENGAGEMENT': '互動推廣',
            'OUTCOME_TRAFFIC': '流量導引',
            'OUTCOME_LEADS': '名單收集',
            'OUTCOME_SALES': '銷售轉換',
            'LINK_CLICKS': '連結點擊',
            'POST_ENGAGEMENT': '貼文互動',
            'PAGE_LIKES': '粉專按讚',
            'VIDEO_VIEWS': '影片觀看',
        }
        
        status_chinese = {
            'ACTIVE': '進行中',
            'PAUSED': '暫停',
            'DELETED': '已刪除',
            'ARCHIVED': '已封存',
        }

        for row in rows_data:
            rows.append([
                row[0][-15:] if row[0] else '',
                row[1] or '',
                objective_chinese.get(row[2], row[2] or ''),
                status_chinese.get(row[3], row[3] or ''),
                round(row[4], 0) if row[4] else 0,
                round(row[5], 0) if row[5] else 0,
                row[6] or '',
                row[7] or 0,
                round(row[8], 0) if row[8] else 0,
                row[9] or 0,
                row[10] or 0,
                row[11] or 0
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:L1', {
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.7},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出廣告活動清單（{len(rows_data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出廣告活動清單失敗: {e}")
        return False


def export_ad_roi_analysis(client, conn):
    """導出廣告 ROI 分析（逐筆廣告）"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('ad_roi_analysis')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='ad_roi_analysis', rows=500, cols=18)

        worksheet.clear()

        cursor = conn.cursor()
        
        # 檢查必要表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ads'")
        if not cursor.fetchone():
            print("  ⊘ 廣告表尚未建立")
            return True

        # 逐筆廣告 ROI 分析
        cursor.execute("""
            SELECT 
                a.ad_id,
                a.name as ad_name,
                ac.name as campaign_name,
                a.post_id,
                SUBSTR(p.message, 1, 50) as post_preview,
                COALESCE(pc.format_type, '未分類') as format_type,
                COALESCE(pc.issue_topic, '未分類') as issue_topic,
                a.status,
                COALESCE(ai.impressions, 0) as impressions,
                COALESCE(ai.reach, 0) as reach,
                COALESCE(ai.clicks, 0) as clicks,
                COALESCE(ai.spend, 0) as spend,
                COALESCE(ai.cpm, 0) as cpm,
                COALESCE(ai.cpc, 0) as cpc,
                COALESCE(ai.ctr, 0) as ctr,
                ai.date_start,
                ai.date_stop
            FROM ads a
            LEFT JOIN ad_campaigns ac ON a.campaign_id = ac.campaign_id
            LEFT JOIN posts p ON a.post_id = p.post_id
            LEFT JOIN posts_classification pc ON a.post_id = pc.post_id
            LEFT JOIN (
                SELECT ad_id,
                       SUM(impressions) as impressions,
                       SUM(reach) as reach,
                       SUM(clicks) as clicks,
                       SUM(spend) as spend,
                       CASE WHEN SUM(impressions) > 0
                            THEN ROUND((SUM(spend) / SUM(impressions)) * 1000, 2)
                            ELSE 0 END as cpm,
                       CASE WHEN SUM(clicks) > 0
                            THEN ROUND(SUM(spend) / SUM(clicks), 2)
                            ELSE 0 END as cpc,
                       CASE WHEN SUM(impressions) > 0
                            THEN ROUND((SUM(clicks) / CAST(SUM(impressions) AS FLOAT)) * 100, 2)
                            ELSE 0 END as ctr,
                       MIN(date_start) as date_start,
                       MAX(date_stop) as date_stop
                FROM ad_insights
                GROUP BY ad_id
            ) ai ON a.ad_id = ai.ad_id
            ORDER BY ai.spend DESC NULLS LAST, a.ad_id
        """)
        rows_data = cursor.fetchall()

        headers = [
            '廣告 ID', '廣告名稱', '活動名稱', '貼文 ID', '貼文預覽',
            '行動', '議題', '狀態',
            '曝光', '觸及', '點擊', '花費 (NT$)',
            'CPM', 'CPC', 'CTR (%)',
            '開始日期', '結束日期'
        ]
        rows = [headers]

        status_chinese = {
            'ACTIVE': '進行中',
            'PAUSED': '暫停',
            'DELETED': '已刪除',
            'ARCHIVED': '已封存',
        }

        for row in rows_data:
            rows.append([
                row[0][-15:] if row[0] else '',
                row[1] or '',
                row[2] or '',
                row[3][-15:] if row[3] else '',
                row[4] or '',
                translate_format_type(row[5]),
                translate_issue_topic(row[6]),
                status_chinese.get(row[7], row[7] or ''),
                row[8] or 0,
                row[9] or 0,
                row[10] or 0,
                round(row[11], 0) if row[11] else 0,
                round(row[12], 2) if row[12] else 0,
                round(row[13], 2) if row[13] else 0,
                round(row[14], 2) if row[14] else 0,
                row[15] or '',
                row[16] or ''
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:Q1', {
            "backgroundColor": {"red": 0.7, "green": 0.3, "blue": 0.3},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        # 統計有無 insights 資料
        with_insights = sum(1 for r in rows_data if r[8] and r[8] > 0)
        print(f"  ✓ 已導出廣告 ROI 分析（{len(rows_data)} 筆，{with_insights} 筆有 insights）")
        return True

    except Exception as e:
        print(f"  ✗ 導出廣告 ROI 分析失敗: {e}")
        return False


def export_ad_recommendations_data(client, conn):
    """導出投廣推薦清單 (Flat Sheet for Looker Studio)"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('ad_recommendations_data')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='ad_recommendations_data', rows=200, cols=12)

        worksheet.clear()

        # 取得推薦貼文 (使用 ad_predictor)
        # Limit 設大一點以獲取更多資料供 Looker Studio 篩選
        recommended = ad_predictor.get_recommended_posts(conn, limit=200, min_score=40)
        
        # 標題 (Row 1)
        headers = [
            '貼文 ID', '內容預覽', '發布日期', '潛力分數', '建議', 
            '互動率 (%)', '分享率 (%)', '留言率 (%)', '點擊率 (%)',
            '議題因子', '時段因子', 
            '議題', '行動', '表現等級', '推薦原因', '連結'
        ]
        
        rows = [headers]
        
        # 資料內容
        for item in recommended:
            breakdown = item.get('breakdown', {})
            reason = []
            if breakdown.get('engagement_rate_score', 0) > 30: reason.append('高互動')
            if breakdown.get('share_rate_score', 0) > 25: reason.append('高分享')
            if breakdown.get('topic_factor', 1) > 1.1: reason.append('熱門議題')
            if breakdown.get('time_factor', 1) > 1.1: reason.append('熱門時段')
            
            rows.append([
                item['post_id'][-15:],
                item.get('message', '')[:50].replace('\n', ' ') if item.get('message') else '',
                convert_to_gmt8(item.get('created_time', ''))[:10],
                item['ad_potential_score'],
                item['ad_recommendation'],
                round(breakdown.get('engagement_rate_score', 0), 2), # 這裡原本是分數，改為實際 ER 會更好，但先維持一致
                round(breakdown.get('share_rate_score', 0), 2),
                round(breakdown.get('comment_rate_score', 0), 2),
                0, # CTR 目前在 predictor 中可能沒有直接傳遞，暫置 0
                breakdown.get('topic_factor', 1),
                breakdown.get('time_factor', 1),
                translate_issue_topic(item.get('issue_topic')),
                translate_format_type(item.get('format_type')),
                translate_performance_tier(item.get('performance_tier')),
                ','.join(reason),
                item.get('permalink_url', '')
            ])
            
        update_with_timestamp(worksheet, 'A1', rows)
        
        print(f"  ✓ 已導出投廣推薦清單資料版 (Looker Ready, {len(rows)-1} 筆)")
        return True

    except Exception as e:
        print(f"  ✗ 導出投廣推薦清單資料版失敗: {e}")
        return False


def export_organic_vs_paid_data(client, conn):
    """導出自然 vs 付費比較資料版 (Flat Sheet for Looker Studio)"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('organic_vs_paid_data')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='organic_vs_paid_data', rows=500, cols=18)

        worksheet.clear()

        cursor = conn.cursor()
        
        # 取得詳細資料 (重複利用既有 SQL 邏輯，修正 latest_insights 為子查詢)
        cursor.execute("""
            SELECT 
                p.post_id,
                SUBSTR(p.message, 1, 50) as post_preview,
                DATE(p.created_time) as created_date,
                CASE WHEN a.post_id IS NOT NULL THEN 'paid' ELSE 'organic' END as ad_status,
                COALESCE(pc.format_type, '未分類') as format_type,
                COALESCE(pc.issue_topic, '未分類') as issue_topic,
                perf.engagement_rate,
                perf.share_rate,
                perf.comment_rate,
                perf.click_through_rate,
                perf.performance_tier,
                i.reach,
                i.total_interactions,
                i.reactions,
                i.comments,
                i.shares,
                i.post_clicks,
                p.permalink_url
            FROM posts p
            LEFT JOIN (SELECT DISTINCT post_id FROM ads) a ON p.post_id = a.post_id
            LEFT JOIN (
                SELECT 
                    post_id,
                    MAX(post_impressions_unique) as reach,
                    MAX(post_clicks) as post_clicks,
                    MAX(post_reactions_like_total + post_reactions_love_total + post_reactions_wow_total + post_reactions_haha_total + post_reactions_sorry_total + post_reactions_anger_total) as reactions,
                    MAX(comments_count) as comments,
                    MAX(shares_count) as shares,
                    (MAX(post_reactions_like_total + post_reactions_love_total + post_reactions_wow_total + post_reactions_haha_total + post_reactions_sorry_total + post_reactions_anger_total) + MAX(comments_count) + MAX(shares_count)) as total_interactions
                FROM post_insights_snapshots
                GROUP BY post_id
            ) i ON p.post_id = i.post_id
            LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
            LEFT JOIN posts_performance perf ON p.post_id = perf.post_id
            ORDER BY created_date DESC
        """)
        rows_data = cursor.fetchall()
        
        # 標題 (Row 1)
        headers = [
            '貼文 ID', '內容預覽', '發布日期', '廣告狀態', '行動', '議題',
            '互動率 (%)', '分享率 (%)', '留言率 (%)', '點擊率 (%)',
            '表現等級', '觸及', '總互動', '讚數', '留言數', '分享數', '點擊數', '連結'
        ]
        
        rows = [headers]
        
        # 資料內容
        for row in rows_data:
            rows.append([
                row[0][-15:],
                row[1] or '',
                row[2] or '',
                row[3],
                translate_format_type(row[4]),
                translate_issue_topic(row[5]),
                round(row[6], 2) if row[6] else 0,
                round(row[7], 2) if row[7] else 0,
                round(row[8], 2) if row[8] else 0,
                round(row[9], 2) if row[9] else 0,
                row[10] or 'low',
                row[11] or 0,
                row[12] or 0,
                row[13] or 0,
                row[14] or 0,
                row[15] or 0,
                row[16] or 0,
                row[17] or ''
            ])
            
        update_with_timestamp(worksheet, 'A1', rows)
        
        print(f"  ✓ 已導出自然 vs 付費比較資料版 (Looker Ready, {len(rows)-1} 筆)")
        return True

    except Exception as e:
        print(f"  ✗ 導出自然 vs 付費比較資料版失敗: {e}")
        return False
    """導出資料字典與說明 - 重新設計版"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        # 完全刪除並重建工作表以清除所有格式
        try:
            old_worksheet = spreadsheet.worksheet('documentation')
            spreadsheet.del_worksheet(old_worksheet)
        except gspread.exceptions.WorksheetNotFound:
            pass
        
        # 建立全新的工作表
        worksheet = spreadsheet.add_worksheet(title='documentation', rows=150, cols=5)

        # 定義文件內容
        docs = []
        
        # ===== 第一區塊：標題 =====
        docs.append(['📊 Facebook 社群數據分析 - 資料字典', '', '', '', ''])
        docs.append([f'最後更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}', '', '', '', ''])
        docs.append(['', '', '', '', ''])
        
        # ===== 第二區塊：報表總覽 =====
        docs.append(['📁 報表總覽', '', '', '', ''])
        docs.append(['報表名稱', '用途說明', '資料範圍', '更新方式', '建議用法'])
        docs.append(['raw_posts', '貼文原始資料', '所有貼文', '每日覆蓋', '查詢特定貼文詳情'])
        docs.append(['raw_post_insights', '貼文洞察數據', '發布 30 天內', '每日累加', '追蹤貼文成長趨勢'])
        docs.append(['page_daily_metrics', '頁面每日指標', '近 7 天', '每日累加', '監控整體粉專健康'])
        docs.append(['top_posts', '表現最佳貼文', '近 1 年 / 前 100 名', '每日覆蓋', '找出成功案例'])
        docs.append(['weekly_trends', '週度趨勢', '近 2 年 (104 週)', '每日覆蓋', '觀察長期變化'])
        docs.append(['best_posting_times', '最佳發文時間', '依時段/議題/行動分組', '每日覆蓋', '規劃發文排程'])
        docs.append(['format_type_performance', '行動表現分析', '依貼文行動分類', '每日覆蓋', '評估不同行動效果'])
        docs.append(['issue_topic_performance', '議題表現分析', '依政策議題分類', '每日覆蓋', '評估不同議題熱度'])
        docs.append(['format_issue_cross', '行動×議題交叉', '≥2 篇貼文的組合', '每日覆蓋', '找出最佳內容組合'])
        docs.append(['hourly_performance', '每小時表現', '全部時段', '每日覆蓋', '精準排程決策'])
        docs.append(['deep_dive_metrics', '深度指標分析', '前 200 篇', '每日覆蓋', '完整 KPI 分析'])
        docs.append(['quadrant_analysis', '象限分析', '全部貼文', '每日覆蓋', 'Looker Studio 視覺化'])
        docs.append(['trending_posts', '近期熱門貼文', '48 小時內發布', '每日覆蓋', '識別正在起飛的內容'])
        docs.append(['ad_recommendations', '投廣推薦清單', '潛力分數 ≥ 40', '每日覆蓋', '選擇投廣素材'])
        docs.append(['organic_vs_paid', '自然 vs 付費', '全部貼文', '每日覆蓋', '評估付費效益'])
        docs.append(['ad_campaigns', '廣告活動清單', '全部 campaigns', '每日覆蓋', '廣告績效總覽'])
        docs.append(['ad_roi_analysis', '廣告 ROI 分析', '全部廣告', '每日覆蓋', '廣告細項分析'])
        docs.append(['yearly_posting_analysis', '年度發文分析', '按月份分組', '每日覆蓋', '季節性規劃'])
        docs.append(['pipeline_logs', '執行紀錄', '近 50 次', '每次執行後', '監控系統狀態'])
        docs.append(['', '', '', '', ''])
        
        # ===== 第三區塊：核心指標說明 =====
        docs.append(['📈 核心指標說明', '', '', '', ''])
        docs.append(['指標名稱', '計算公式', '意義', '參考標準', '來源依據'])
        docs.append(['互動率 (ER)', '(讚+留言+分享) ÷ 觸及 × 100', '內容引起互動的能力', '> 3% 為佳', 'Hootsuite 2024: FB 平均 0.5-1%, NGO 約 2-4%'])
        docs.append(['分享率 (SR)', '分享 ÷ 觸及 × 100', '內容傳播潛力', '> 0.5% 為佳', '分享是最高價值互動'])
        docs.append(['留言率 (CR)', '留言 ÷ 觸及 × 100', '引發討論的能力', '> 0.3% 為佳', 'Sprout Social: 通常為按讚的 10%'])
        docs.append(['點擊率 (CTR)', '點擊 ÷ 觸及 × 100', '吸引點擊的能力', '> 2% 為佳', 'WordStream 2024: FB 中位數 1.6%, NGO 約 2.1%'])
        docs.append(['病毒性 (VS)', '分享 ÷ 反應', '分享意願強度', '> 0.5 為佳', '每 2 次反應有 1 次分享'])
        docs.append(['討論深度 (DD)', '留言 ÷ 按讚', '討論 vs 快速反應', '> 0.1 為佳', '1:10 比例表示引發思考'])
        docs.append(['', '', '', '', ''])
        
        # ===== 第四區塊：表現等級 =====
        docs.append(['🏆 表現等級說明', '', '', '', ''])
        docs.append(['等級名稱', '中文', '條件', '佔比', '說明'])
        docs.append(['viral', '熱門', '互動率 ≥ P95 (前 5%)', '~5%', '爆款貼文，可作為成功案例'])
        docs.append(['high', '優質', '互動率 ≥ P75 (前 25%)', '~20%', '表現良好，適合投廣'])
        docs.append(['average', '一般', '互動率 ≥ P25 (中間)', '~50%', '正常表現'])
        docs.append(['low', '待改進', '互動率 < P25 (後 25%)', '~25%', '需檢視原因'])
        docs.append(['', '', '', '', ''])
        
        # ===== 第五區塊：yearly_posting_analysis 欄位說明 =====
        docs.append(['📊 yearly_posting_analysis 欄位說明', '', '', '', ''])
        docs.append(['欄位名稱', '說明', '', '', ''])
        docs.append(['月份', '發文月份 (1-12月)', '', '', ''])
        docs.append(['時段', '發文時段 (早晨/中午/下午/晚間/深夜)', '', '', ''])
        docs.append(['議題', '貼文議題分類', '', '', ''])
        docs.append(['行動', '貼文行動分類 (活動/聲明/報告等)', '', '', ''])
        docs.append(['貼文數', '該組合的貼文總數', '', '', ''])
        docs.append(['平均互動率', '該組合貼文的平均互動率', '', '', ''])
        docs.append(['平均點擊率', '該組合貼文的平均點擊率', '', '', ''])
        docs.append(['平均分享率', '該組合貼文的平均分享率', '', '', ''])
        docs.append(['高表現數', '該組合中「熱門 viral」或「優質 high」等級的貼文數量', '', '', ''])
        docs.append(['總點擊數', '該組合所有貼文的點擊總和', '', '', ''])
        docs.append(['總分享數', '該組合所有貼文的分享總和', '', '', ''])
        docs.append(['', '', '', '', ''])
        
        # ===== 第六區塊：象限分析 =====
        docs.append(['🎯 象限分析說明', '', '', '', ''])
        docs.append(['象限名稱', '觸及', '互動率', '特徵', '建議行動'])
        docs.append(['王牌貼文', '高 (≥中位數)', '高 (≥中位數)', '擴散力+吸引力俱佳', '最佳投廣素材'])
        docs.append(['潛力珍寶', '低 (<中位數)', '高 (≥中位數)', '內容優質但觸及不足', '投廣推廣，提升曝光'])
        docs.append(['廣傳陷阱', '高 (≥中位數)', '低 (<中位數)', '觸及大但沒人互動', '檢視內容，改善吸引力'])
        docs.append(['常態內容', '低 (<中位數)', '低 (<中位數)', '一般表現', '參考用，分析改善空間'])
        docs.append(['', '', '', '', ''])
        
        # ===== 第七區塊：行動分類 =====
        docs.append(['🏷️ 行動分類 (Format Type)', '', '', '', ''])
        docs.append(['代碼', '中文名稱', '判斷關鍵字', '', ''])
        docs.append(['event', '定期活動', '影展、講座、論壇、工作坊、分享會、座談、活動報名', '', ''])
        docs.append(['press', '記者會', '記者會、媒體、採訪、新聞稿', '', ''])
        docs.append(['statement', '聲明稿', '聲明、發言、立場、呼籲、強調', '', ''])
        docs.append(['opinion', '新聞觀點', '觀點、評論、分析、看法、時事', '', ''])
        docs.append(['op_ed', '投書', '投書、專欄、刊登、媒體投書', '', ''])
        docs.append(['report', '報告發布', '報告、發布、研究、調查、數據', '', ''])
        docs.append(['booth', '擺攤資訊', '擺攤、市集、現場、來找我們', '', ''])
        docs.append(['edu', '科普/Podcast', '懶人包、Podcast、科普、Q&A、知識、解說', '', ''])
        docs.append(['action', '行動號召', '連署、捐款、志工、行動、參與、支持我們', '', ''])
        docs.append(['', '', '', '', ''])
        
        # ===== 第八區塊：議題分類 =====
        docs.append(['🏷️ 議題分類 (Issue Topic)', '', '', '', ''])
        docs.append(['代碼', '中文名稱', '判斷關鍵字', '', ''])
        docs.append(['nuclear', '核能發電', '核電、核能、核四、核廢、核安、輻射', '', ''])
        docs.append(['climate', '氣候問題', '氣候、暖化、碳排、COP、極端天氣', '', ''])
        docs.append(['net_zero', '淨零政策', '淨零、碳中和、2050、減碳', '', ''])
        docs.append(['industry', '產業分析', '產業、企業、ESG、永續、供應鏈', '', ''])
        docs.append(['renewable', '能源發展', '光電、風電、再生能源、綠電、太陽能', '', ''])
        docs.append(['other', '其他議題', '勞動、環評、空污、水資源、生態', '', ''])
        docs.append(['', '', '', '', ''])
        
        # ===== 第九區塊：投廣推薦 =====
        docs.append(['💰 投廣推薦評分說明', '', '', '', ''])
        docs.append(['分數項目', '權重', '說明', '', ''])
        docs.append(['互動率分數', '30%', '互動率正規化後 × 100', '', ''])
        docs.append(['分享率分數', '25%', '分享率正規化後 × 100 (病毒潛力)', '', ''])
        docs.append(['留言率分數', '15%', '留言率正規化後 × 100 (討論深度)', '', ''])
        docs.append(['議題因子', '15%', '該議題歷史 ER ÷ 整體 ER (>1 = 熱門議題)', '', ''])
        docs.append(['時段因子', '15%', '該時段歷史 ER ÷ 整體 ER (>1 = 熱門時段)', '', ''])
        docs.append(['', '', '', '', ''])
        docs.append(['投廣建議', '條件', '', '', ''])
        docs.append(['Yes (推薦)', '潛力分數 ≥ 70', '', '', ''])
        docs.append(['Maybe (考慮)', '潛力分數 50-69', '', '', ''])
        docs.append(['No (不建議)', '潛力分數 < 50', '', '', ''])
        docs.append(['', '', '', '', ''])
        
        # ===== 第十區塊：注意事項 =====
        docs.append(['⚠️ 注意事項', '', '', '', ''])
        docs.append(['1. Facebook API 對超過 90 天的 Insights 數據有存取限制', '', '', '', ''])
        docs.append(['2. 所有時間已轉換為 GMT+8 台灣時區', '', '', '', ''])
        docs.append(['3. raw_post_insights 僅追蹤發布後 30 天內的貼文 (每日快照)', '', '', '', ''])
        docs.append(['4. 廣告數據中「無數據」的廣告表示從未投遞過 (草稿或未啟用)', '', '', '', ''])
        docs.append(['5. 歷史廣告數據最多可回溯 37 個月', '', '', '', ''])
        
        # 寫入資料
        update_with_timestamp(worksheet, 'A1', docs)
        
        # ===== 格式化 - 使用 batch_format 一次套用 =====
        # Level 1: 主標題 (深藍底白字 14pt)
        # Level 2: 區塊標題 (淺藍底深藍字 11pt 粗體) - 共 9 個
        # Level 3: 欄位標題列 (淺灰底 10pt 粗體) - 共 9 個
        
        formats = []
        
        # Level 1: 主標題
        formats.append({
            'range': 'A1:E1',
            'format': {
                "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.65},
                "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            }
        })
        
        # 更新時間
        formats.append({
            'range': 'A2:E2',
            'format': {
                "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.5, "green": 0.5, "blue": 0.5}}
            }
        })
        
        # Level 2: 區塊標題 (emoji 開頭的行)
        section_rows = [4, 26, 35, 42, 56, 63, 75, 84, 97]
        for row in section_rows:
            formats.append({
                'range': f'A{row}:E{row}',
                'format': {
                    "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 1.0},
                    "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.1, "green": 0.25, "blue": 0.5}}
                }
            })
        
        # Level 3: 欄位標題列 (緊接在區塊標題後面)
        header_rows = [5, 27, 36, 43, 57, 64, 76, 85, 92]
        for row in header_rows:
            formats.append({
                'range': f'A{row}:E{row}',
                'format': {
                    "backgroundColor": {"red": 0.94, "green": 0.94, "blue": 0.94},
                    "textFormat": {"bold": True, "fontSize": 10}
                }
            })
        
        # 一次性套用所有格式
        worksheet.batch_format(formats)

        print(f"  ✓ 已導出資料字典與說明")
        return True

    except Exception as e:
        print(f"  ✗ 導出說明文件失敗: {e}")
        return False

def export_yearly_posting_analysis(client, conn):
    """導出年度最佳發文時間分析（按月份分組，含議題/行動篩選器）"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('yearly_posting_analysis')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='yearly_posting_analysis', rows=500, cols=12)

        worksheet.clear()

        cursor = conn.cursor()
        
        # 按月份 + 時段 + 議題 + 行動分組的最佳發文時間
        # 使用 MAX 取各指標最大值，避免不完整 snapshot 導致數據為 0
        cursor.execute("""
            SELECT 
                strftime('%m', substr(p.created_time, 1, 10)) as month,
                pc.time_slot,
                COALESCE(pc.issue_topic, '未分類') as issue_topic,
                COALESCE(pc.format_type, '未分類') as format_type,
                COUNT(*) as post_count,
                ROUND(AVG(pp.engagement_rate), 4) as avg_er,
                ROUND(AVG(pp.click_through_rate), 4) as avg_ctr,
                ROUND(AVG(pp.share_rate), 4) as avg_sr,
                SUM(CASE WHEN pp.performance_tier IN ('viral', 'high') THEN 1 ELSE 0 END) as high_performer_count,
                COALESCE(SUM(bs.max_clicks), 0) as sum_max_clicks,
                COALESCE(SUM(bs.max_shares), 0) as sum_max_shares
            FROM posts p
            JOIN posts_classification pc ON p.post_id = pc.post_id
            JOIN posts_performance pp ON p.post_id = pp.post_id
            LEFT JOIN (
                SELECT post_id, 
                       MAX(post_clicks) as max_clicks,
                       MAX(shares_count) as max_shares
                FROM post_insights_snapshots
                GROUP BY post_id
            ) bs ON p.post_id = bs.post_id
            GROUP BY month, pc.time_slot, pc.issue_topic, pc.format_type
            ORDER BY month, avg_er DESC
        """)
        rows_data = cursor.fetchall()

        # 月份對照
        month_names = {
            '01': '1月', '02': '2月', '03': '3月', '04': '4月',
            '05': '5月', '06': '6月', '07': '7月', '08': '8月',
            '09': '9月', '10': '10月', '11': '11月', '12': '12月'
        }
        
        time_slot_map = {
            'morning': '早晨 (6-12)',
            'noon': '中午 (12-15)',
            'afternoon': '下午 (15-18)',
            'evening': '晚間 (18-23)',
            'night': '深夜 (23-6)',
            None: '未分類'
        }

        headers = ['月份', '時段', '議題', '行動', '貼文數',
                   '平均互動率 (%)', '平均點擊率 (%)', '平均分享率 (%)', '高表現數',
                   '累積最高點擊數', '累積最高分享數']
        rows = [headers]

        for row in rows_data:
            rows.append([
                month_names.get(row[0], row[0]),
                time_slot_map.get(row[1], row[1] or '未分類'),
                translate_issue_topic(row[2]),
                translate_format_type(row[3]),
                row[4],
                round(row[5], 2) if row[5] else 0,
                round(row[6], 2) if row[6] else 0,
                round(row[7], 2) if row[7] else 0,
                row[8] or 0,
                row[9] or 0,
                row[10] or 0
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化標題
        worksheet.format('A1:K1', {
            "backgroundColor": {"red": 0.3, "green": 0.5, "blue": 0.7},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出年度發文時間分析（{len(rows_data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出年度發文時間分析失敗: {e}")
        return False


def export_pipeline_logs(client, conn):
    """導出 Pipeline 執行紀錄"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('pipeline_logs')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='pipeline_logs', rows=100, cols=10)

        worksheet.clear()

        cursor = conn.cursor()
        
        # 檢查 pipeline_runs 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_runs'")
        if not cursor.fetchone():
            # 建立表格
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
            conn.commit()
            
            # 首次執行時僅顯示標題
            headers = ['執行 ID', '日期', '時間', '狀態', '收集貼文數', 
                       '分析貼文數', '匯出報表數', '錯誤訊息', '執行秒數']
            worksheet.update([headers], 'A1')
            print("  ⊘ Pipeline 紀錄表已建立（尚無紀錄）")
            return True

        cursor.execute("""
            SELECT id, run_date, run_time, status, 
                   posts_collected, posts_analyzed, sheets_exported,
                   error_message, duration_seconds
            FROM pipeline_runs
            ORDER BY run_date DESC, run_time DESC
            LIMIT 50
        """)
        rows_data = cursor.fetchall()

        headers = ['執行 ID', '日期', '時間', '狀態', '收集貼文數', 
                   '分析貼文數', '匯出報表數', '錯誤訊息', '執行秒數']
        rows = [headers]

        for row in rows_data:
            rows.append(list(row))

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化標題
        worksheet.format('A1:I1', {
            "backgroundColor": {"red": 0.5, "green": 0.5, "blue": 0.5},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

        print(f"  ✓ 已導出 Pipeline 執行紀錄（{len(rows_data)} 筆）")
        return True

    except Exception as e:
        print(f"  ✗ 導出 Pipeline 執行紀錄失敗: {e}")
        return False



def export_tab_documentation(client):
    """
    導出工作表說明文件
    解釋每個 tab 的作用與使用方式
    """
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        try:
            worksheet = spreadsheet.worksheet('📖 Tab Documentation')
        except:
            worksheet = spreadsheet.add_worksheet(title='📖 Tab Documentation', rows=100, cols=5)
        
        # Clear existing content
        worksheet.clear()
        
        # Documentation data
        docs = [
            ['Tab Name', 'Category', 'Purpose', 'Update Frequency', 'Key Columns'],
            
            # Raw Data
            ['raw_posts', 'Raw Data', '貼文基本資訊（ID、內容、發佈時間、連結等）', 'Daily', 'post_id, message, created_time, permalink_url'],
            ['raw_post_insights', 'Raw Data', '貼文洞察數據快照（按抓取日期儲存）', 'Daily', 'post_id, fetch_date, likes/comments/shares, impressions'],
            ['raw_page_daily', 'Raw Data', '粉絲專頁每日指標（粉絲數、觸及、互動）', 'Daily', 'date, fan_count, page_impressions_unique, post_count'],
            
            # Analytics - Best Times
            ['best_posting_times_general', 'Analytics', '最佳發文時間分析（整體）', 'Daily', 'time_slot, avg_engagement_rate, post_count'],
            ['best_posting_times_by_topic', 'Analytics', '最佳發文時間分析（依議題分類）', 'Daily', 'issue_topic, time_slot, avg_engagement_rate'],
            ['best_posting_times_by_action', 'Analytics', '最佳發文時間分析（依行動類型）', 'Daily', 'format_type, time_slot, avg_engagement_rate'],
            
            # Analytics - Performance
            ['format_type_performance', 'Analytics', '貼文形式表現分析（行動類型：活動/連署/懶人包等）', 'Daily', 'format_type, post_count, avg_engagement_rate'],
            ['issue_topic_performance', 'Analytics', '議題表現分析（氣候/能源/教育等主題）', 'Daily', 'issue_topic, post_count, avg_engagement_rate'],
            ['format_issue_cross', 'Analytics', '行動×議題交叉分析（哪種形式配哪種議題最有效）', 'Daily', 'format_type, issue_topic, post_count, avg_er'],
            
            # Analytics - Posts
            ['top_posts', 'Analytics', 'Top 貼文排行（依互動率排序）', 'Daily', 'post_id, engagement_rate, reach, performance_tier'],
            ['quadrant_analysis', 'Analytics', '象限分析：王牌/珍寶/常態/陷阱四類貼文', 'Daily', 'post_id, quadrant, engagement_rate, share_rate'],
            ['deep_dive_metrics', 'Analytics', '深度指標分析（discussion_depth, virality_score等）', 'Daily', 'post_id, virality_score, discussion_depth'],
            
            # Analytics - Trends
            ['weekly_trends', 'Analytics', '週度趨勢（觀察長期表現變化）', 'Daily', 'week_start, post_count, avg_engagement_rate'],
            ['hourly_performance', 'Analytics', '每小時表現統計（0-23點）', 'Daily', 'hour, avg_engagement_rate, post_count'],
            
            # Ad Analytics
            ['ad_recommendations', 'Ad Analytics', '投廣推薦清單（哪些貼文適合投廣）', 'Daily', 'post_id, ad_potential_score, organic_er, predicted_paid_er'],
            ['trending_posts', 'Ad Analytics', '近期熱門貼文（96小時內高互動）', 'Daily', 'post_id, engagement_rate, created_time'],
            ['organic_vs_paid', 'Ad Analytics', '自然 vs 付費比較', 'Daily', 'post_id, organic_reach, paid_reach, organic_er, paid_er'],
            ['ad_campaigns', 'Ad Analytics', '廣告活動清單', 'Daily', 'campaign_id, campaign_name, status, objective'],
            ['ad_roi_analysis', 'Ad Analytics', '廣告 ROI 分析（成本效益）', 'Daily', 'ad_id, spend, impressions, clicks, cpc, ctr'],
            
            # Data Versions (Looker Studio Ready)
            ['ad_recommendations_data', 'Data Export', 'Looker Studio 用：投廣推薦資料版', 'Daily', '...'],
            ['organic_vs_paid_data', 'Data Export', 'Looker Studio 用：自然付費比較資料版', 'Daily', '...'],
            
            # Reports
            ['yearly_posting_analysis', 'Reports', '年度發文時間分析（歷年發文模式）', 'Daily', 'year, month, hour, post_count'],
            ['pipeline_logs', 'Reports', 'Pipeline 執行紀錄（系統運行日誌）', 'Daily', 'run_date, status, posts_collected, duration'],
            
            ['', '', '', '', ''],
            ['使用說明', '', '', '', ''],
            ['1. 每個 tab 右側最後一欄會顯示「data_updated_at」時間戳記', '', '', '', ''],
            ['2. 資料每日自動更新（透過 Cloud Run + Cloud Scheduler）', '', '', '', ''],
            ['3. Raw data tabs 保留完整歷史記錄，analytics tabs 基於最新快照計算', '', '', '', ''],
            ['4. 若某個 tab 資料為空，代表沒有符合條件的資料（例如近期無投廣）', '', '', '', ''],
            ['', '', '', '', ''],
            ['資料來源', '', '', '', ''],
            ['• Facebook Graph API v23.0', '', '', '', ''],
            ['• 貼文資料：2024-01-01 至今', '', '', '', ''],
            ['• Insights 資料：過去 90 天（Facebook API 限制）', '', '', '', ''],
        ]
        
        # Write to sheet
        update_with_timestamp(worksheet, 'A1', docs)
        
        # Format header row
        worksheet.format('A1:E1', {
            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        
        # Auto-resize columns
        worksheet.columns_auto_resize(0, 4)
        
        print(f"  ✓ 已導出 Tab Documentation ({len(docs)-1} tabs documented)")
        return True
        
    except Exception as e:
        print(f"  ✗ 導出 Tab Documentation 失敗: {e}")
        return False


# ==================== 整合導出函數 ====================

def export_content_analysis(client, conn):
    """整合導出: 行動表現 + 議題表現 + 交叉分析"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('📊 content_analysis')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='📊 content_analysis', rows=300, cols=15)

        worksheet.clear()
        rows = []

        # === Section 1: 行動類型表現 ===
        rows.append(['📌 行動類型表現分析', '', '', '', '', '', ''])
        rows.append(['行動類型', '貼文數', '平均互動率 (%)', '平均分享率 (%)',
                     '平均留言率 (%)', '熱門數 (前5%)', '優質數 (前25%)'])

        format_data = analytics_reports.get_format_type_performance(conn)
        for item in format_data:
            rows.append([
                translate_format_type(item['format_type']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_share_rate'], 2),
                round(item['avg_comment_rate'], 2),
                item['viral_count'],
                item['high_count']
            ])

        rows.append(['', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])

        # === Section 2: 議題表現 ===
        rows.append(['📌 議題表現分析', '', '', '', '', '', ''])
        rows.append(['議題', '貼文數', '平均互動率 (%)', '平均分享率 (%)',
                     '平均留言率 (%)', '熱門數 (前5%)', '優質數 (前25%)'])

        issue_data = analytics_reports.get_issue_topic_performance(conn)
        for item in issue_data:
            rows.append([
                translate_issue_topic(item['issue_topic']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_share_rate'], 2),
                round(item['avg_comment_rate'], 2),
                item['viral_count'],
                item['high_count']
            ])

        rows.append(['', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])

        # === Section 3: 交叉分析 ===
        rows.append(['📌 行動 × 議題交叉分析', '', '', '', '', ''])
        rows.append(['行動', '議題', '貼文數', '平均互動率 (%)', '平均分享率 (%)', '高表現貼文數'])

        cross_data = analytics_reports.get_format_issue_cross_performance(conn)
        for item in cross_data:
            rows.append([
                translate_format_type(item['format_type']),
                translate_issue_topic(item['issue_topic']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_share_rate'], 2),
                item['high_performer_count']
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        # 格式化各區塊標題
        worksheet.format('A1:G1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
        })

        print(f"  ✓ 已導出內容分析（行動: {len(format_data)}, 議題: {len(issue_data)}, 交叉: {len(cross_data)}）")
        return True

    except Exception as e:
        print(f"  ✗ 導出內容分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_posting_times(client, conn):
    """整合導出: 最佳發文時間 + 每小時表現 + 年度分析"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('⏰ posting_times')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='⏰ posting_times', rows=400, cols=15)

        worksheet.clear()
        rows = []

        time_slot_map = {
            'morning': '早上 (6-12點)',
            'noon': '中午 (12-15點)',
            'afternoon': '下午 (15-18點)',
            'evening': '晚上 (18-23點)',
            'night': '深夜 (23-6點)'
        }

        # === Section 1: 整體最佳發文時間 ===
        rows.append(['📊 整體最佳發文時間', '', '', '', ''])
        rows.append(['時段', '星期', '貼文數', '平均互動率 (%)', '平均點擊率 (%)'])

        data_general = analytics_reports.get_best_posting_times(conn, limit=20)
        for item in data_general:
            rows.append([
                time_slot_map.get(item['time_slot'], item['time_slot']),
                get_day_name_chinese(item['day_of_week']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        rows.append(['', '', '', '', ''])
        rows.append(['', '', '', '', ''])

        # === Section 2: 按議題分組 ===
        rows.append(['📌 按議題分組', '', '', '', '', ''])
        rows.append(['議題', '時段', '星期', '貼文數', '平均互動率 (%)', '平均點擊率 (%)'])

        data_topic = analytics_reports.get_best_posting_times_by_topic(conn, limit=50)
        for item in data_topic:
            rows.append([
                translate_issue_topic(item['issue_topic']),
                time_slot_map.get(item['time_slot'], item['time_slot']),
                get_day_name_chinese(item['day_of_week']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        rows.append(['', '', '', '', '', ''])
        rows.append(['', '', '', '', '', ''])

        # === Section 3: 按行動分組 ===
        rows.append(['🎯 按行動分組', '', '', '', '', ''])
        rows.append(['行動', '時段', '星期', '貼文數', '平均互動率 (%)', '平均點擊率 (%)'])

        data_format = analytics_reports.get_best_posting_times_by_format(conn, limit=50)
        for item in data_format:
            rows.append([
                translate_format_type(item['format_type']),
                time_slot_map.get(item['time_slot'], item['time_slot']),
                get_day_name_chinese(item['day_of_week']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        rows.append(['', '', '', '', '', ''])
        rows.append(['', '', '', '', '', ''])

        # === Section 4: 每小時表現 ===
        rows.append(['🕐 每小時表現統計', '', '', ''])
        rows.append(['時間', '貼文數', '平均互動率 (%)', '平均點擊率 (%)'])

        hourly_data = analytics_reports.get_hourly_performance(conn)
        for item in hourly_data:
            rows.append([
                hour_to_12h_format(item['hour_of_day']),
                item['post_count'],
                round(item['avg_er'], 2),
                round(item['avg_ctr'], 2)
            ])

        rows.append(['', '', '', ''])
        rows.append(['', '', '', ''])

        # === Section 5: 年度發文分析 ===
        rows.append(['📅 年度發文時間分析', '', '', '', '', '', '', '', '', ''])
        rows.append(['年份', '月份', '貼文數', '00-06時', '06-09時', '09-12時', '12-15時', '15-18時', '18-21時', '21-24時'])

        cursor = conn.cursor()
        cursor.execute("""
            WITH hourly_posts AS (
                SELECT
                    strftime('%Y', created_time) as year,
                    strftime('%m', created_time) as month,
                    CAST(strftime('%H', created_time) AS INTEGER) as hour,
                    post_id
                FROM posts
            )
            SELECT
                year, month,
                COUNT(*) as total_posts,
                SUM(CASE WHEN hour BETWEEN 0 AND 5 THEN 1 ELSE 0 END) as h_00_06,
                SUM(CASE WHEN hour BETWEEN 6 AND 8 THEN 1 ELSE 0 END) as h_06_09,
                SUM(CASE WHEN hour BETWEEN 9 AND 11 THEN 1 ELSE 0 END) as h_09_12,
                SUM(CASE WHEN hour BETWEEN 12 AND 14 THEN 1 ELSE 0 END) as h_12_15,
                SUM(CASE WHEN hour BETWEEN 15 AND 17 THEN 1 ELSE 0 END) as h_15_18,
                SUM(CASE WHEN hour BETWEEN 18 AND 20 THEN 1 ELSE 0 END) as h_18_21,
                SUM(CASE WHEN hour BETWEEN 21 AND 23 THEN 1 ELSE 0 END) as h_21_24
            FROM hourly_posts
            GROUP BY year, month
            ORDER BY year DESC, month DESC
        """)
        yearly_data = cursor.fetchall()

        for row in yearly_data:
            rows.append([
                row[0], row[1], row[2],
                row[3] or 0, row[4] or 0, row[5] or 0, row[6] or 0,
                row[7] or 0, row[8] or 0, row[9] or 0
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:E1', {
            "backgroundColor": {"red": 0.9, "green": 0.5, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
        })

        print(f"  ✓ 已導出發文時間分析（整體: {len(data_general)}, 議題: {len(data_topic)}, 行動: {len(data_format)}, 每小時: {len(hourly_data)}, 年度: {len(yearly_data)}）")
        return True

    except Exception as e:
        print(f"  ✗ 導出發文時間分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_posts_performance(client, conn):
    """整合導出: Top 貼文 + 象限分析 + 深度指標 + 週趨勢"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('📈 posts_performance')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='📈 posts_performance', rows=500, cols=20)

        worksheet.clear()
        rows = []

        # === Section 1: Top 貼文 ===
        rows.append(['🏆 Top 100 貼文排行', '', '', '', '', '', '', '', '', '', '', ''])
        rows.append(['貼文 ID', '內容預覽', '發布日期', '行動', '議題', '時段',
                     '互動率 (%)', '表現等級', '百分位數', '觸及', '總互動數', '連結'])

        top_data = analytics_reports.get_top_posts(conn, days=365, limit=100)
        for item in top_data:
            rows.append([
                item['post_id'][-15:],
                (item['message_preview'] or '')[:50],
                convert_to_gmt8(item['created_time'])[:10],
                translate_format_type(item['topic_primary']),
                translate_issue_topic(item.get('issue_topic')),
                translate_time_slot(item['time_slot']),
                round(item['engagement_rate'], 2),
                translate_performance_tier(item['performance_tier']),
                round(item['percentile_rank'], 1),
                item['reach'],
                item['total_engagement'],
                item.get('permalink_url', '')
            ])

        rows.append(['', '', '', '', '', '', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', '', '', '', '', '', ''])

        # === Section 2: 象限分析 ===
        rows.append(['📊 象限分析 (Viral/High/Average/Low)', '', '', '', '', '', '', '', '', '', ''])
        rows.append(['貼文 ID', '發布日期', '觸及人數', '互動率 (%)',
                     '中位數觸及', '中位數互動率 (%)', '象限', '議題', '行動', '內容預覽', '連結'])

        quadrant_data = analytics_reports.get_quadrant_analysis(conn)
        for item in quadrant_data:
            rows.append([
                item['post_id'][-18:],
                convert_to_gmt8(item['created_time'])[:10],
                item['reach'],
                round(item['engagement_rate'] * 100, 2),
                item['median_reach'],
                round(item['median_er'] * 100, 2),
                item['quadrant'],
                translate_issue_topic(item['topic_tag']),
                translate_format_type(item['format_type']),
                (item['content_short'] or '')[:40],
                item['permalink_url'] or ''
            ])

        rows.append(['', '', '', '', '', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', '', '', '', '', ''])

        # === Section 3: 週趨勢 ===
        rows.append(['📈 週度趨勢 (近兩年)', '', '', '', ''])
        rows.append(['週次 (日期範圍)', '貼文數', '平均互動率 (%)', '總觸及', '總互動數'])

        weekly_data = analytics_reports.get_weekly_trends(conn, weeks=104)
        for item in weekly_data:
            week_range = f"{item.get('week_start', '')} ~ {item.get('week_end', '')}"
            rows.append([
                week_range,
                item['post_count'],
                round(item['avg_er'], 2),
                item['total_reach'],
                item['total_engagement']
            ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:L1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
        })

        print(f"  ✓ 已導出貼文表現分析（Top: {len(top_data)}, 象限: {len(quadrant_data)}, 週趨勢: {len(weekly_data)}）")
        return True

    except Exception as e:
        print(f"  ✗ 導出貼文表現分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_ad_analytics(client, conn):
    """整合導出: 投廣建議 + 熱門貼文 + 自然vs付費 + 廣告活動 + ROI"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('💰 ad_analytics')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='💰 ad_analytics', rows=800, cols=20)

        worksheet.clear()
        rows = []

        # === Section 1: 近期熱門貼文 ===
        rows.append(['🔥 近期熱門貼文 (72小時內)', '', '', '', '', '', '', ''])
        rows.append(['貼文 ID', '內容預覽', '發布時間', '已發布小時數',
                     '當前互動數', '觸及', '每小時互動', '互動率 (%)'])

        trending = analytics_trends.get_trending_posts(conn, hours=72)
        for item in trending:
            rows.append([
                item['post_id'][-15:],
                (item['message_preview'] or '')[:50],
                item['created_time'][:16] if item['created_time'] else '',
                item['hours_since_post'],
                item['current_engagement'],
                item['reach'] or 0,
                item['engagement_per_hour'],
                item['engagement_rate']
            ])

        rows.append(['', '', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', '', ''])

        # === Section 2: 投廣推薦 ===
        ad_predictor.update_all_ad_potentials(conn)

        # 歷史最佳組合
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(pc.issue_topic, '未分類') as issue_topic,
                COALESCE(pc.format_type, '未分類') as format_type,
                pc.time_slot,
                CASE pc.day_of_week
                    WHEN 0 THEN '週一' WHEN 1 THEN '週二' WHEN 2 THEN '週三'
                    WHEN 3 THEN '週四' WHEN 4 THEN '週五' WHEN 5 THEN '週六' WHEN 6 THEN '週日'
                END as day_name,
                COUNT(*) as post_count,
                ROUND(AVG(pp.engagement_rate), 2) as avg_er,
                SUM(CASE WHEN pp.performance_tier IN ('viral', 'high') THEN 1 ELSE 0 END) as high_performers
            FROM posts_classification pc
            JOIN posts_performance pp ON pc.post_id = pp.post_id
            GROUP BY pc.issue_topic, pc.format_type, pc.time_slot, pc.day_of_week
            HAVING post_count >= 3
            ORDER BY avg_er DESC
            LIMIT 15
        """)
        best_combos = cursor.fetchall()

        rows.append(['📊 歷史最佳組合（供新內容投廣參考）', '', '', '', '', '', ''])
        rows.append(['議題', '行動', '時段', '星期', '樣本數', '平均互動率 (%)', '高表現數'])

        for combo in best_combos:
            rows.append([
                translate_issue_topic(combo[0]),
                translate_format_type(combo[1]),
                translate_time_slot(combo[2]),
                combo[3] or '未分類',
                combo[4],
                combo[5],
                combo[6]
            ])

        rows.append(['', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])

        # 已發布貼文推薦
        rows.append(['📌 已發布貼文投廣推薦', '', '', '', '', '', '', '', '', '', '', '', ''])
        rows.append([
            '貼文 ID', '發布時間', '投廣建議', '潛力分數', '表現等級',
            '行動', '議題', '互動率分數', '分享率分數', '留言率分數',
            '議題因子', '時段因子', '貼文連結'
        ])

        recommended = ad_predictor.get_recommended_posts(conn, limit=50, min_score=40)
        for item in recommended:
            breakdown = item.get('breakdown', {})
            rows.append([
                item['post_id'][-15:],
                convert_to_gmt8(item.get('created_time', ''))[:10],
                item['ad_recommendation'],
                item['ad_potential_score'],
                translate_performance_tier(item['performance_tier']),
                translate_format_type(item['format_type']),
                translate_issue_topic(item['issue_topic']),
                round(breakdown.get('engagement_rate_score', 0), 1),
                round(breakdown.get('share_rate_score', 0), 1),
                round(breakdown.get('comment_rate_score', 0), 1),
                breakdown.get('topic_factor', 1),
                breakdown.get('time_factor', 1),
                item.get('permalink_url', '')
            ])

        rows.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

        # === Section 3: 自然 vs 付費 ===
        rows.append(['⚖️ 自然 vs 付費貼文成效比較', '', '', '', '', '', '', ''])

        cursor.execute("""
            WITH latest_snapshots AS (
                SELECT post_id, MAX(fetch_date) as latest_date
                FROM post_insights_snapshots
                GROUP BY post_id
            ),
            promoted_posts AS (
                SELECT DISTINCT post_id FROM ads WHERE post_id IS NOT NULL
            )
            SELECT
                CASE WHEN pp.post_id IS NOT NULL THEN 'paid' ELSE 'organic' END as ad_status,
                COUNT(*) as post_count,
                ROUND(AVG(perf.engagement_rate), 2) as avg_er,
                ROUND(AVG(perf.share_rate), 2) as avg_sr,
                ROUND(AVG(perf.comment_rate), 2) as avg_cr,
                ROUND(AVG(perf.click_through_rate), 2) as avg_ctr,
                SUM(i.post_impressions_unique) as total_reach,
                SUM(i.likes_count + i.comments_count + i.shares_count) as total_engagement
            FROM posts p
            JOIN latest_snapshots ls ON p.post_id = ls.post_id
            JOIN post_insights_snapshots i ON p.post_id = i.post_id AND i.fetch_date = ls.latest_date
            LEFT JOIN promoted_posts pp ON p.post_id = pp.post_id
            LEFT JOIN posts_performance perf ON p.post_id = perf.post_id
            GROUP BY ad_status
        """)
        summary_data = cursor.fetchall()

        rows.append(['類型', '貼文數', '平均互動率 (%)', '平均分享率 (%)', '平均留言率 (%)', '平均點擊率 (%)', '總觸及', '總互動數'])
        for row in summary_data:
            status = '有廣告' if row[0] == 'paid' else '自然觸及'
            rows.append([
                status, row[1], row[2] or 0, row[3] or 0, row[4] or 0, row[5] or 0, row[6] or 0, row[7] or 0
            ])

        rows.append(['', '', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', '', ''])

        # === Section 4: 廣告活動清單 ===
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_campaigns'")
        if cursor.fetchone():
            rows.append(['📋 廣告活動清單', '', '', '', '', '', '', '', '', '', '', ''])
            rows.append([
                '活動 ID', '活動名稱', '目標', '狀態', '每日預算 (NT$)', '總預算 (NT$)',
                '建立日期', '廣告數', '總花費 (NT$)', '總曝光', '總點擊', '平均 CPC (NT$)'
            ])

            objective_chinese = {
                'OUTCOME_AWARENESS': '品牌知名度',
                'OUTCOME_ENGAGEMENT': '互動推廣',
                'OUTCOME_TRAFFIC': '流量導引',
                'OUTCOME_LEADS': '名單收集',
                'OUTCOME_SALES': '銷售轉換',
                'LINK_CLICKS': '連結點擊',
                'POST_ENGAGEMENT': '貼文互動',
                'PAGE_LIKES': '粉專按讚',
            }

            cursor.execute("""
                SELECT
                    ac.campaign_id,
                    ac.name,
                    ac.objective,
                    ac.status,
                    COALESCE(ac.daily_budget, 0) as daily_budget,
                    COALESCE(ac.lifetime_budget, 0) as lifetime_budget,
                    DATE(ac.created_time) as created_date,
                    COUNT(DISTINCT a.ad_id) as ad_count,
                    COALESCE(SUM(ai.spend), 0) as total_spend,
                    COALESCE(SUM(ai.impressions), 0) as total_impressions,
                    COALESCE(SUM(ai.clicks), 0) as total_clicks,
                    CASE WHEN SUM(ai.clicks) > 0
                         THEN ROUND(SUM(ai.spend) / SUM(ai.clicks), 2)
                         ELSE 0 END as avg_cpc
                FROM ad_campaigns ac
                LEFT JOIN ads a ON ac.campaign_id = a.campaign_id
                LEFT JOIN ad_insights ai ON a.ad_id = ai.ad_id
                GROUP BY ac.campaign_id
                ORDER BY total_spend DESC
            """)
            campaigns = cursor.fetchall()

            for row in campaigns:
                rows.append([
                    row[0][-15:] if row[0] else '',
                    row[1] or '',
                    objective_chinese.get(row[2], row[2] or ''),
                    row[3] or '',
                    row[4], row[5],
                    row[6] or '',
                    row[7], row[8], row[9], row[10], row[11]
                ])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:H1', {
            "backgroundColor": {"red": 0.8, "green": 0.4, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
        })

        print(f"  ✓ 已導出投廣分析（熱門: {len(trending)}, 推薦: {len(recommended)}, 組合: {len(best_combos)}）")
        return True

    except Exception as e:
        print(f"  ✗ 導出投廣分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_system_info(client, conn):
    """整合導出: Pipeline 紀錄 + Tab 說明"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        try:
            worksheet = spreadsheet.worksheet('⚙️ system_info')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='⚙️ system_info', rows=150, cols=10)

        worksheet.clear()
        rows = []

        # === Section 1: Tab 說明 ===
        rows.append(['📖 分頁說明', '', '', '', ''])
        rows.append(['分頁名稱', '類別', '說明', '更新頻率', '主要欄位'])

        docs = [
            ['📦 raw_posts', '原始資料', '貼文基本資訊（ID、內容、發佈時間、連結等）', '每日', 'post_id, message, created_time'],
            ['📦 raw_post_insights', '原始資料', '貼文洞察數據（每貼文最新快照）', '每日', 'post_id, likes, comments, shares, reach'],
            ['📦 page_daily_metrics', '原始資料', '粉絲專頁每日指標（粉絲數、觸及、互動）', '每日', 'date, fan_count, page_impressions_unique'],
            ['📦 raw_ads', '原始資料', '廣告原始資料（廣告 + 成效數據合併）', '每日', 'ad_id, impressions, reach, spend, cpc'],
            ['📊 content_analysis', '內容分析', '行動類型表現 + 議題表現 + 交叉分析', '每日', 'format_type, issue_topic, avg_er'],
            ['⏰ posting_times', '時間分析', '最佳發文時間 + 每小時表現 + 年度分析', '每日', 'time_slot, hour, avg_engagement_rate'],
            ['📈 posts_performance', '貼文表現', 'Top 貼文 + 象限分析 + 週趨勢', '每日', 'post_id, engagement_rate, performance_tier'],
            ['💰 ad_analytics', '投廣分析', '熱門貼文 + 投廣建議 + 自然vs付費 + 廣告活動', '每日', 'ad_potential_score, ad_recommendation'],
            ['⚙️ system_info', '系統資訊', '分頁說明 + Pipeline 執行紀錄', '每日', 'run_date, status, duration'],
        ]

        for doc in docs:
            rows.append(doc)

        rows.append(['', '', '', '', ''])
        rows.append(['', '', '', '', ''])

        # === Section 2: 行動類型分類標準 ===
        rows.append(['🎯 行動類型 (Format Type) 分類標準', '', '', ''])
        rows.append(['代碼', '中文名稱', '說明', '匹配關鍵字（完整清單）'])

        format_types = [
            ['event', '定期活動', '影展、演講、座談會等定期舉辦的活動', '影展, 講座, 論壇, 工作坊, 分享會, 座談, 活動報名, 歡迎參加'],
            ['press', '記者會', '召開記者會發布訊息', '記者會, 媒體, 採訪, 新聞稿'],
            ['statement', '聲明稿', '公開發言或正式聲明', '聲明, 發言, 立場, 呼籲, 強調, 我們認為'],
            ['opinion', '新聞觀點', '針對時事新聞的評論觀點', '觀點, 評論, 分析, 看法, 時事'],
            ['op_ed', '投書', '綠盟投書至媒體的文章', '投書, 專欄, 刊登, 媒體投書'],
            ['report', '報告發布', '研究報告或調查報告發布', '報告, 發布, 研究, 調查, 數據, 出爐'],
            ['booth', '擺攤資訊', '擺攤活動或市集資訊', '擺攤, 市集, 現場, 來找我們'],
            ['edu', '科普/Podcast', '科普文章或 Podcast 節目', '懶人包, Podcast, 科普, Q&A, 知識, 解說, 你知道嗎, 一次看懂'],
            ['action', '行動號召', '連署、行動呼籲等', '連署, 捐款, 志工, 行動, 參與, 支持我們, 一起'],
            ['(空白)', '其他行動', '無法歸類的其他內容', '（無關鍵字匹配時預設）'],
        ]
        for ft in format_types:
            rows.append(ft)

        rows.append(['', '', '', ''])
        rows.append(['', '', '', ''])

        # === Section 3: 議題分類標準 ===
        rows.append(['📌 議題類型 (Issue Topic) 分類標準', '', '', ''])
        rows.append(['代碼', '中文名稱', '說明', '匹配關鍵字（完整清單）'])

        issue_topics = [
            ['nuclear', '核能發電', '核電廠、核廢料、核能政策相關', '核電, 核能, 核四, 核廢, 核安, 輻射'],
            ['climate', '氣候問題', '氣候變遷、極端氣候相關', '氣候, 暖化, 碳排, COP, 極端天氣, 氣候變遷'],
            ['net_zero', '淨零政策', '2050淨零、減碳政策相關', '淨零, 碳中和, 2050, 淨零轉型, 減碳'],
            ['industry', '產業分析', '產業碳排、企業責任相關', '產業, 企業, ESG, 永續, 供應鏈, 碳盤查'],
            ['renewable', '能源發展', '再生能源、能源轉型相關', '光電, 風電, 再生能源, 綠電, 太陽能, 離岸風電, 屋頂, 公民電廠'],
            ['other', '其他議題', '其他環境或公民議題', '勞動, 環評, 空污, 水資源, 生態'],
        ]
        for it in issue_topics:
            rows.append(it)

        rows.append(['', '', '', ''])
        rows.append(['', '', '', ''])

        # === Section 4: 使用說明 ===
        rows.append(['📋 使用說明', '', '', '', ''])
        rows.append(['1. 每個分頁右側最後一欄顯示「data_updated_at」更新時間', '', '', '', ''])
        rows.append(['2. 資料每日自動更新（透過 Cloud Run + Cloud Scheduler）', '', '', '', ''])
        rows.append(['3. 原始資料分頁保留完整歷史記錄，分析分頁基於最新快照計算', '', '', '', ''])
        rows.append(['4. 若某個分頁資料為空，代表沒有符合條件的資料', '', '', '', ''])

        rows.append(['', '', '', '', ''])
        rows.append(['', '', '', '', ''])

        # === Section 5: Pipeline 執行紀錄 ===
        rows.append(['🔧 Pipeline 執行紀錄', '', '', '', '', '', '', '', ''])

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_runs'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT id, run_date, run_time, status,
                       posts_collected, posts_analyzed, sheets_exported,
                       error_message, duration_seconds
                FROM pipeline_runs
                ORDER BY run_date DESC, run_time DESC
                LIMIT 30
            """)
            logs = cursor.fetchall()

            rows.append(['執行 ID', '日期', '時間', '狀態', '收集貼文數',
                         '分析貼文數', '匯出報表數', '錯誤訊息', '執行秒數'])
            for log in logs:
                rows.append(list(log))
        else:
            rows.append(['尚無執行紀錄', '', '', '', '', '', '', '', ''])

        rows.append(['', '', '', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', '', '', ''])

        # === Section 6: 資料來源 ===
        rows.append(['📡 資料來源', '', '', '', ''])
        rows.append(['• Facebook Graph API v23.0', '', '', '', ''])
        rows.append(['• 貼文資料：2024-01-01 至今', '', '', '', ''])
        rows.append(['• Insights 資料：過去 90 天（Facebook API 限制）', '', '', '', ''])

        update_with_timestamp(worksheet, 'A1', rows)

        worksheet.format('A1:E1', {
            "backgroundColor": {"red": 0.5, "green": 0.5, "blue": 0.5},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
        })

        print(f"  ✓ 已導出系統資訊")
        return True

    except Exception as e:
        print(f"  ✗ 導出系統資訊失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_old_tabs(client):
    """刪除舊的不需要的分頁，只保留 9 個新分頁"""
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)

        # 要保留的分頁名稱
        keep_tabs = {
            'raw_posts',
            'raw_post_insights',
            'page_daily_metrics',
            'raw_ads',
            '📊 content_analysis',
            '⏰ posting_times',
            '📈 posts_performance',
            '💰 ad_analytics',
            '⚙️ system_info',
        }

        # 取得所有現有分頁
        all_worksheets = spreadsheet.worksheets()

        deleted_count = 0
        for ws in all_worksheets:
            if ws.title not in keep_tabs:
                try:
                    spreadsheet.del_worksheet(ws)
                    print(f"  🗑️ 已刪除: {ws.title}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ⚠️ 無法刪除 {ws.title}: {e}")

        if deleted_count > 0:
            print(f"  ✓ 已清理 {deleted_count} 個舊分頁")
        else:
            print("  ✓ 無需清理舊分頁")

        return True

    except Exception as e:
        print(f"  ✗ 清理舊分頁失敗: {e}")
        return False


def main():
    """主程式 - 導出所有分析報表（整合版：9 個分頁）"""
    print("\n" + "="*60)
    print("Facebook 分析報表導出至 Google Sheets")
    print("="*60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 設定 Google Sheets 客戶端
    client = setup_google_sheets_client()
    if not client:
        print("\n✗ 無法設定 Google Sheets 客戶端")
        return False

    # 清理舊分頁
    print("🧹 清理舊分頁:")
    cleanup_old_tabs(client)

    # 連接資料庫
    conn = analytics_reports.get_connection()

    print("\n開始導出分析報表...\n")

    # 導出各項報表（整合版：9 個分頁）
    success_count = 0
    total_count = 8  # raw_posts 已合併到 raw_post_insights

    # 📦 原始資料 (3 個分頁: raw_post_insights, page_daily_metrics, raw_ads)
    print("📦 原始資料導出:")
    if export_raw_post_insights(client, conn):  # 包含貼文基本資訊 + 分類 + 互動數據
        success_count += 1
    if export_page_daily_metrics(client, conn):
        success_count += 1
    if export_raw_ads(client, conn):           # 廣告原始資料
        success_count += 1

    # 📊 整合分析報表 (4 個分頁)
    print("\n📊 整合分析報表導出:")
    if export_content_analysis(client, conn):  # 行動+議題+交叉
        success_count += 1
    if export_posting_times(client, conn):     # 時間分析
        success_count += 1
    if export_posts_performance(client, conn): # 貼文表現
        success_count += 1
    if export_ad_analytics(client, conn):      # 投廣分析
        success_count += 1

    # ⚙️ 系統資訊 (1 個分頁)
    print("\n⚙️ 系統資訊導出:")
    if export_system_info(client, conn):       # 說明+紀錄
        success_count += 1

    conn.close()

    print(f"\n{'='*60}")
    print(f"導出完成: {success_count}/{total_count} 項報表成功")
    print(f"試算表: {SPREADSHEET_NAME}")
    print(f"{'='*60}\n")

    return success_count == total_count


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
