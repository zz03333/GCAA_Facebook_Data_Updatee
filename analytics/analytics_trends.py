"""
Facebook 社群數據分析框架 - 趨勢分析模組
追蹤貼文互動數據隨時間變化
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.config import DB_PATH


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== 貼文生命週期分析 ====================

def get_post_lifecycle_curve(conn, post_id: str) -> List[Dict]:
    """
    取得單一貼文的互動曲線
    
    返回每個抓取日期的互動數據，可繪製成長曲線
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            i.fetch_date,
            i.likes_count,
            i.comments_count,
            i.shares_count,
            (i.likes_count + i.comments_count + i.shares_count) as total_engagement,
            i.post_impressions_unique as reach,
            i.post_clicks
        FROM post_insights_snapshots i
        WHERE i.post_id = ?
        ORDER BY i.fetch_date ASC
    """, (post_id,))
    
    return [dict(row) for row in cursor.fetchall()]


def get_posts_growth_rate(conn, days: int = 7) -> List[Dict]:
    """
    計算近 N 天內貼文的互動成長率
    
    比較同一貼文最新與最舊快照的差異
    """
    cursor = conn.cursor()
    cursor.execute("""
        WITH post_snapshots AS (
            SELECT 
                post_id,
                fetch_date,
                likes_count + comments_count + shares_count as total_engagement,
                ROW_NUMBER() OVER (PARTITION BY post_id ORDER BY fetch_date ASC) as rn_first,
                ROW_NUMBER() OVER (PARTITION BY post_id ORDER BY fetch_date DESC) as rn_last
            FROM post_insights_snapshots
            WHERE fetch_date >= date('now', ? || ' days')
        ),
        first_snapshot AS (
            SELECT post_id, total_engagement as first_engagement, fetch_date as first_date
            FROM post_snapshots WHERE rn_first = 1
        ),
        last_snapshot AS (
            SELECT post_id, total_engagement as last_engagement, fetch_date as last_date
            FROM post_snapshots WHERE rn_last = 1
        )
        SELECT 
            f.post_id,
            p.message,
            f.first_date,
            l.last_date,
            f.first_engagement,
            l.last_engagement,
            (l.last_engagement - f.first_engagement) as engagement_growth,
            CASE 
                WHEN f.first_engagement > 0 
                THEN ROUND((l.last_engagement - f.first_engagement) * 100.0 / f.first_engagement, 2)
                ELSE 0 
            END as growth_rate_pct
        FROM first_snapshot f
        JOIN last_snapshot l ON f.post_id = l.post_id
        JOIN posts p ON f.post_id = p.post_id
        WHERE f.first_date != l.last_date
        ORDER BY growth_rate_pct DESC
        LIMIT 50
    """, (f'-{days}',))
    
    return [dict(row) for row in cursor.fetchall()]


def get_trending_posts(conn, hours: int = 96) -> List[Dict]:
    """
    取得近 N 小時內互動成長最快的貼文

    用於識別「正在起飛」的貼文（投廣候選）
    """
    cursor = conn.cursor()
    # 計算每小時平均成長
    # 注意: created_time 格式為 ISO 8601 (2026-01-14T09:06:06+0000)
    # 需要轉換為 SQLite 可解析的格式
    cursor.execute("""
        WITH recent_posts AS (
            SELECT
                p.post_id,
                SUBSTR(p.message, 1, 100) as message_preview,
                p.created_time,
                JULIANDAY('now') - JULIANDAY(
                    REPLACE(REPLACE(p.created_time, 'T', ' '), '+0000', '')
                ) as days_since_post
            FROM posts p
            WHERE REPLACE(REPLACE(p.created_time, 'T', ' '), '+0000', '') >= datetime('now', ? || ' hours')
        ),
        engagement_data AS (
            SELECT 
                i.post_id,
                MAX(i.likes_count + i.comments_count + i.shares_count) as current_engagement,
                MAX(i.post_impressions_unique) as reach
            FROM post_insights_snapshots i
            GROUP BY i.post_id
        )
        SELECT 
            rp.post_id,
            rp.message_preview,
            rp.created_time,
            ROUND(rp.days_since_post * 24, 1) as hours_since_post,
            ed.current_engagement,
            ed.reach,
            CASE 
                WHEN rp.days_since_post > 0 
                THEN ROUND(ed.current_engagement / (rp.days_since_post * 24), 2)
                ELSE ed.current_engagement
            END as engagement_per_hour,
            CASE 
                WHEN ed.reach > 0 
                THEN ROUND(ed.current_engagement * 100.0 / ed.reach, 2)
                ELSE 0
            END as engagement_rate
        FROM recent_posts rp
        JOIN engagement_data ed ON rp.post_id = ed.post_id
        ORDER BY engagement_per_hour DESC
        LIMIT 30
    """, (f'-{hours}',))
    
    return [dict(row) for row in cursor.fetchall()]


def calculate_engagement_velocity(conn, post_id: str) -> Dict:
    """
    計算單一貼文的互動速度
    
    返回每日/每小時的平均互動增量
    """
    snapshots = get_post_lifecycle_curve(conn, post_id)
    
    if len(snapshots) < 2:
        return {
            'post_id': post_id,
            'snapshots_count': len(snapshots),
            'daily_velocity': 0,
            'hourly_velocity': 0
        }
    
    first = snapshots[0]
    last = snapshots[-1]
    
    # 計算天數差
    first_date = datetime.strptime(first['fetch_date'], '%Y-%m-%d')
    last_date = datetime.strptime(last['fetch_date'], '%Y-%m-%d')
    days_diff = (last_date - first_date).days
    
    if days_diff == 0:
        days_diff = 1
    
    engagement_diff = last['total_engagement'] - first['total_engagement']
    
    return {
        'post_id': post_id,
        'snapshots_count': len(snapshots),
        'first_date': first['fetch_date'],
        'last_date': last['fetch_date'],
        'days_tracked': days_diff,
        'engagement_growth': engagement_diff,
        'daily_velocity': round(engagement_diff / days_diff, 2),
        'hourly_velocity': round(engagement_diff / (days_diff * 24), 2)
    }


# ==================== 時間序列分析 ====================

def get_daily_engagement_summary(conn, days: int = 30) -> List[Dict]:
    """
    取得每日互動總量摘要
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            DATE(p.created_time) as post_date,
            COUNT(DISTINCT p.post_id) as posts_count,
            SUM(i.likes_count + i.comments_count + i.shares_count) as total_engagement,
            SUM(i.post_impressions_unique) as total_reach,
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate
        FROM posts p
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        LEFT JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE p.created_time >= date('now', ? || ' days')
        GROUP BY post_date
        ORDER BY post_date DESC
    """, (f'-{days}',))
    
    return [dict(row) for row in cursor.fetchall()]


def get_post_age_performance(conn) -> List[Dict]:
    """
    分析貼文年齡與互動表現的關係
    
    了解貼文在發布後多久達到互動高峰
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            CASE 
                WHEN JULIANDAY(i.fetch_date) - JULIANDAY(DATE(p.created_time)) <= 1 THEN '0-1天'
                WHEN JULIANDAY(i.fetch_date) - JULIANDAY(DATE(p.created_time)) <= 3 THEN '1-3天'
                WHEN JULIANDAY(i.fetch_date) - JULIANDAY(DATE(p.created_time)) <= 7 THEN '3-7天'
                WHEN JULIANDAY(i.fetch_date) - JULIANDAY(DATE(p.created_time)) <= 14 THEN '7-14天'
                ELSE '14天以上'
            END as age_bucket,
            COUNT(*) as snapshot_count,
            ROUND(AVG(i.likes_count + i.comments_count + i.shares_count), 0) as avg_engagement,
            ROUND(AVG(i.post_impressions_unique), 0) as avg_reach
        FROM posts p
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        GROUP BY age_bucket
        ORDER BY 
            CASE age_bucket
                WHEN '0-1天' THEN 1
                WHEN '1-3天' THEN 2
                WHEN '3-7天' THEN 3
                WHEN '7-14天' THEN 4
                ELSE 5
            END
    """)
    
    return [dict(row) for row in cursor.fetchall()]


# ==================== 主程式 ====================

def main():
    """示範趨勢分析"""
    conn = get_connection()
    
    try:
        print("=== 近 7 天互動成長率 ===")
        growth = get_posts_growth_rate(conn, days=7)
        for item in growth[:5]:
            print(f"  {item['post_id'][-15:]}: +{item['growth_rate_pct']}% ({item['engagement_growth']} 互動)")
        
        print("\n=== 近 48 小時熱門貼文 ===")
        trending = get_trending_posts(conn, hours=48)
        for item in trending[:5]:
            print(f"  {item['message_preview'][:30]}...")
            print(f"    互動/小時: {item['engagement_per_hour']}, ER: {item['engagement_rate']}%")
        
        print("\n=== 貼文年齡表現 ===")
        age_perf = get_post_age_performance(conn)
        for item in age_perf:
            print(f"  {item['age_bucket']}: 平均 {item['avg_engagement']} 互動, {item['avg_reach']} 觸及")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
