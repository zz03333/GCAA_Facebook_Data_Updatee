"""
Facebook Analytics Export - Rebuilt Version
Exports comprehensive analytics to Google Sheets with clear, actionable insights.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import gspread
from google.oauth2 import service_account
import json
import os
import base64
import sqlite3
from datetime import datetime, timedelta

# Configuration
SPREADSHEET_NAME = 'Facebook Insights Metrics_Data Warehouse'
DB_PATH = 'data/engagement_data.db'


def get_connection():
    """Get SQLite database connection"""
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data' / 'engagement_data.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def setup_google_sheets_client():
    """Set up Google Sheets client"""
    try:
        credentials_json = os.environ.get('GCP_SA_CREDENTIALS')
        credentials_base64 = os.environ.get('GCP_SA_CREDENTIALS_BASE64')

        if credentials_base64:
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
        elif not credentials_json:
            print("⚠️  找不到 Google Sheets 憑證環境變數")
            return None

        credentials_dict = json.loads(credentials_json)
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=scope)
        client = gspread.authorize(credentials)
        print("✓ Google Sheets 客戶端設定成功")
        return client

    except Exception as e:
        print(f"✗ Google Sheets 客戶端設定失敗: {e}")
        return None


def delete_all_worksheets(client, keep_sheets=None):
    """Delete all worksheets except specified ones"""
    keep_sheets = keep_sheets or []
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheets = spreadsheet.worksheets()
        
        for ws in worksheets:
            if ws.title not in keep_sheets:
                try:
                    spreadsheet.del_worksheet(ws)
                    print(f"  🗑️ 刪除: {ws.title}")
                except Exception as e:
                    print(f"  ⚠️ 無法刪除 {ws.title}: {e}")
        
        return True
    except Exception as e:
        print(f"✗ 刪除工作表失敗: {e}")
        return False


def create_worksheet(client, name, rows=1000, cols=20):
    """Create or get worksheet"""
    spreadsheet = client.open(SPREADSHEET_NAME)
    try:
        ws = spreadsheet.worksheet(name)
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)
    return ws


def format_header(ws, col_range):
    """Format header row with styling"""
    ws.format(col_range, {
        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.7},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER"
    })


def export_raw_posts(client, conn):
    """Export raw posts data"""
    ws = create_worksheet(client, '📋 Raw Posts')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.post_id,
            datetime(substr(p.created_time, 1, 19)) as published_at,
            substr(p.message, 1, 200) as content_preview,
            p.permalink_url,
            pc.format_type,
            pc.issue_topic,
            pc.media_type,
            i.post_impressions_unique as reach,
            i.likes_count,
            i.comments_count,
            i.shares_count,
            i.post_clicks,
            pp.engagement_rate,
            pp.performance_tier
        FROM posts p
        LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
        LEFT JOIN post_insights_snapshots i ON p.post_id = i.post_id
        LEFT JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = p.post_id)
        ORDER BY p.created_time DESC
    """)
    
    rows = cursor.fetchall()
    
    headers = ['Post ID', '發布時間', '內容預覽', '連結', '行動類型', '議題', '媒體類型',
               '觸及', '讚數', '留言', '分享', '點擊', '互動率%', '表現等級']
    data = [headers]
    
    for row in rows:
        data.append(list(row))
    
    ws.update('A1', data)
    format_header(ws, 'A1:N1')
    
    print(f"  ✓ Raw Posts: {len(rows)} 筆")
    return len(rows)


def export_raw_insights(client, conn):
    """Export raw insights snapshots"""
    ws = create_worksheet(client, '📊 Raw Insights')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.post_id,
            datetime(substr(p.created_time, 1, 19)) as published_at,
            i.fetch_date,
            i.post_impressions_unique as reach,
            i.likes_count,
            i.comments_count,
            i.shares_count,
            i.post_clicks,
            i.post_video_views,
            i.post_reactions_like_total as like_reactions,
            i.post_reactions_love_total as love,
            i.post_reactions_wow_total as wow,
            i.post_reactions_haha_total as haha,
            i.post_reactions_sorry_total as sad,
            i.post_reactions_anger_total as angry,
            p.permalink_url
        FROM post_insights_snapshots i
        JOIN posts p ON i.post_id = p.post_id
        WHERE i.fetch_date >= '2025-12-01'
        ORDER BY p.created_time DESC, i.fetch_date DESC
    """)
    
    rows = cursor.fetchall()
    
    headers = ['Post ID', '發布時間', '抓取日期', '觸及', '讚', '留言', '分享', '點擊',
               '影片觀看', '👍', '❤️', '😮', '😂', '😢', '😡', '連結']
    data = [headers]
    
    for row in rows:
        data.append(list(row))
    
    ws.update('A1', data)
    format_header(ws, 'A1:P1')
    
    print(f"  ✓ Raw Insights: {len(rows)} 筆")
    return len(rows)


def export_performance_summary(client, conn):
    """Export overall performance summary"""
    ws = create_worksheet(client, '🎯 Performance Summary')
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_posts,
            SUM(i.post_impressions_unique) as total_reach,
            SUM(i.likes_count + i.comments_count + i.shares_count) as total_engagement,
            AVG(pp.engagement_rate) as avg_er,
            SUM(i.post_clicks) as total_clicks,
            SUM(i.shares_count) as total_shares
        FROM posts p
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = p.post_id)
    """)
    overall = cursor.fetchone()
    
    # Performance tier breakdown
    cursor.execute("""
        SELECT 
            pp.performance_tier,
            COUNT(*) as count,
            AVG(pp.engagement_rate) as avg_er,
            AVG(i.post_impressions_unique) as avg_reach
        FROM posts_performance pp
        JOIN post_insights_snapshots i ON pp.post_id = i.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = pp.post_id)
        GROUP BY pp.performance_tier
        ORDER BY avg_er DESC
    """)
    tiers = cursor.fetchall()
    
    data = [
        ['📊 整體表現摘要', '', '', ''],
        ['', '', '', ''],
        ['指標', '數值', '', ''],
        ['總貼文數', overall['total_posts'], '', ''],
        ['總觸及人數', f"{overall['total_reach']:,}", '', ''],
        ['總互動數', f"{overall['total_engagement']:,}", '', ''],
        ['平均互動率', f"{overall['avg_er']:.2f}%", '', ''],
        ['總點擊數', f"{overall['total_clicks']:,}", '', ''],
        ['總分享數', f"{overall['total_shares']:,}", '', ''],
        ['', '', '', ''],
        ['📈 表現等級分布', '', '', ''],
        ['等級', '貼文數', '平均互動率%', '平均觸及'],
    ]
    
    tier_names = {'viral': '🔥 熱門', 'high': '⭐ 優質', 'average': '📌 一般', 'low': '📉 待改進'}
    for t in tiers:
        data.append([
            tier_names.get(t['performance_tier'], t['performance_tier']),
            t['count'],
            f"{t['avg_er']:.2f}",
            int(t['avg_reach'])
        ])
    
    ws.update('A1', data)
    ws.format('A1:D1', {
        "backgroundColor": {"red": 0.9, "green": 0.5, "blue": 0.2},
        "textFormat": {"bold": True, "fontSize": 14}
    })
    
    print("  ✓ Performance Summary")
    return 1


def export_best_times(client, conn):
    """Export best posting times analysis"""
    ws = create_worksheet(client, '⏰ Best Times')
    cursor = conn.cursor()
    
    # By hour
    cursor.execute("""
        SELECT 
            pc.hour_of_day as hour,
            COUNT(*) as posts,
            AVG(pp.engagement_rate) as avg_er,
            AVG(i.post_impressions_unique) as avg_reach
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        JOIN post_insights_snapshots i ON pc.post_id = i.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = pc.post_id)
        GROUP BY pc.hour_of_day
        ORDER BY avg_er DESC
    """)
    hourly = cursor.fetchall()
    
    # By day of week
    cursor.execute("""
        SELECT 
            pc.day_of_week,
            COUNT(*) as posts,
            AVG(pp.engagement_rate) as avg_er
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        WHERE pc.day_of_week IS NOT NULL
        GROUP BY pc.day_of_week
        ORDER BY avg_er DESC
    """)
    daily = cursor.fetchall()
    
    day_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
    
    data = [
        ['⏰ 最佳發文時間分析', '', '', '', ''],
        ['', '', '', '', ''],
        ['🕐 依小時 (互動率排序)', '', '', '', ''],
        ['時間', '貼文數', '平均互動率%', '平均觸及', '建議'],
    ]
    
    for i, h in enumerate(hourly):
        hour = h['hour']
        time_str = f"{hour:02d}:00"
        suggestion = '⭐ 推薦' if i < 3 else ''
        data.append([time_str, h['posts'], f"{h['avg_er']:.2f}", int(h['avg_reach']), suggestion])
    
    data.extend([
        ['', '', '', '', ''],
        ['📅 依星期 (互動率排序)', '', '', '', ''],
        ['星期', '貼文數', '平均互動率%', '', ''],
    ])
    
    for d in daily:
        day_idx = d['day_of_week']
        day_name = day_names[day_idx] if 0 <= day_idx < 7 else str(day_idx)
        data.append([day_name, d['posts'], f"{d['avg_er']:.2f}", '', ''])
    
    ws.update('A1', data)
    format_header(ws, 'A1:E1')
    
    print("  ✓ Best Times")
    return 1


def export_content_analysis(client, conn):
    """Export content type analysis"""
    ws = create_worksheet(client, '📝 Content Analysis')
    cursor = conn.cursor()
    
    # By action type
    cursor.execute("""
        SELECT 
            COALESCE(pc.format_type, 'unclassified') as action_type,
            COUNT(*) as posts,
            AVG(pp.engagement_rate) as avg_er,
            SUM(i.shares_count) as total_shares,
            AVG(i.post_impressions_unique) as avg_reach
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        JOIN post_insights_snapshots i ON pc.post_id = i.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = pc.post_id)
        GROUP BY pc.format_type
        ORDER BY avg_er DESC
    """)
    actions = cursor.fetchall()
    
    # By topic
    cursor.execute("""
        SELECT 
            COALESCE(pc.issue_topic, 'other') as topic,
            COUNT(*) as posts,
            AVG(pp.engagement_rate) as avg_er,
            SUM(i.shares_count) as total_shares
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        JOIN post_insights_snapshots i ON pc.post_id = i.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = pc.post_id)
        GROUP BY pc.issue_topic
        ORDER BY avg_er DESC
    """)
    topics = cursor.fetchall()
    
    action_names = {
        'event': '📅 活動', 'press': '📰 記者會', 'statement': '📜 聲明稿',
        'opinion': '💭 觀點', 'op_ed': '✍️ 投書', 'report': '📊 報告',
        'booth': '🏪 擺攤', 'edu': '📚 科普', 'action': '📢 行動號召',
        'unclassified': '❓ 未分類'
    }
    
    topic_names = {
        'nuclear': '☢️ 核能', 'climate': '🌍 氣候', 'net_zero': '🎯 淨零',
        'industry': '🏭 產業', 'renewable': '🌱 再生能源', 'other': '📌 其他'
    }
    
    data = [
        ['📝 內容類型分析', '', '', '', ''],
        ['', '', '', '', ''],
        ['🎬 依行動類型', '', '', '', ''],
        ['類型', '貼文數', '平均互動率%', '總分享', '平均觸及'],
    ]
    
    for a in actions:
        name = action_names.get(a['action_type'], a['action_type'])
        data.append([name, a['posts'], f"{a['avg_er']:.2f}", a['total_shares'], int(a['avg_reach'])])
    
    data.extend([
        ['', '', '', '', ''],
        ['🏷️ 依議題', '', '', '', ''],
        ['議題', '貼文數', '平均互動率%', '總分享', ''],
    ])
    
    for t in topics:
        name = topic_names.get(t['topic'], t['topic'])
        data.append([name, t['posts'], f"{t['avg_er']:.2f}", t['total_shares'], ''])
    
    ws.update('A1', data)
    format_header(ws, 'A1:E1')
    
    print("  ✓ Content Analysis")
    return 1


def export_top_posts(client, conn):
    """Export top performing posts"""
    ws = create_worksheet(client, '🏆 Top Posts')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            substr(p.message, 1, 100) as preview,
            datetime(substr(p.created_time, 1, 19)) as published,
            pc.format_type,
            pc.issue_topic,
            i.post_impressions_unique as reach,
            pp.engagement_rate,
            i.likes_count + i.comments_count + i.shares_count as total_engagement,
            i.shares_count,
            p.permalink_url
        FROM posts p
        JOIN posts_classification pc ON p.post_id = pc.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = p.post_id)
        ORDER BY pp.engagement_rate DESC
        LIMIT 50
    """)
    
    rows = cursor.fetchall()
    
    headers = ['內容預覽', '發布時間', '行動', '議題', '觸及', '互動率%', '總互動', '分享', '連結']
    data = [headers]
    
    for row in rows:
        data.append(list(row))
    
    ws.update('A1', data)
    format_header(ws, 'A1:I1')
    
    print(f"  ✓ Top Posts: {len(rows)} 筆")
    return len(rows)


def export_monthly_trends(client, conn):
    """Export monthly trends"""
    ws = create_worksheet(client, '📈 Monthly Trends')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', p.created_time) as month,
            COUNT(*) as posts,
            SUM(i.post_impressions_unique) as total_reach,
            AVG(pp.engagement_rate) as avg_er,
            SUM(i.shares_count) as total_shares
        FROM posts p
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE i.fetch_date = (SELECT MAX(fetch_date) FROM post_insights_snapshots WHERE post_id = p.post_id)
        GROUP BY strftime('%Y-%m', p.created_time)
        ORDER BY month DESC
    """)
    
    rows = cursor.fetchall()
    
    headers = ['月份', '貼文數', '總觸及', '平均互動率%', '總分享']
    data = [headers]
    
    for row in rows:
        data.append([row['month'], row['posts'], row['total_reach'], f"{row['avg_er']:.2f}", row['total_shares']])
    
    ws.update('A1', data)
    format_header(ws, 'A1:E1')
    
    print(f"  ✓ Monthly Trends: {len(rows)} 個月")
    return len(rows)


def main():
    """Main export function"""
    print("\n" + "="*60)
    print("🔄 Facebook Analytics Export - Rebuilt Version")
    print("="*60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Setup
    client = setup_google_sheets_client()
    if not client:
        return False
    
    conn = get_connection()
    
    # Delete old worksheets
    print("\n🗑️ 刪除舊工作表...")
    delete_all_worksheets(client, keep_sheets=[])
    
    # Create a blank sheet first (spreadsheet needs at least one)
    spreadsheet = client.open(SPREADSHEET_NAME)
    try:
        spreadsheet.add_worksheet(title='_temp', rows=1, cols=1)
    except:
        pass
    
    # Export new analytics
    print("\n📊 匯出新分析報表...")
    
    try:
        export_performance_summary(client, conn)
        export_best_times(client, conn)
        export_content_analysis(client, conn)
        export_top_posts(client, conn)
        export_monthly_trends(client, conn)
        export_raw_posts(client, conn)
        export_raw_insights(client, conn)
        
        # Delete temp sheet
        try:
            temp = spreadsheet.worksheet('_temp')
            spreadsheet.del_worksheet(temp)
        except:
            pass
        
        print("\n" + "="*60)
        print("✅ 匯出完成!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 匯出失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
