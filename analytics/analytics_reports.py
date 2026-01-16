"""
Facebook 社群數據分析框架 - 報表查詢工具
提供常用分析查詢與報表產出
"""

import sqlite3
from datetime import datetime
from typing import Dict, List
from utils.config import DB_PATH


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== 發文時間分析 ====================

def get_best_posting_times(conn, limit: int = 10) -> List[Dict]:
    """
    找出最佳發文時間組合
    """
    cursor = conn.cursor()
    cursor.execute(""" 
        SELECT 
            pc.time_slot,
            CASE pc.day_of_week
                WHEN 0 THEN 'Mon'
                WHEN 1 THEN 'Tue'
                WHEN 2 THEN 'Wed'
                WHEN 3 THEN 'Thu'
                WHEN 4 THEN 'Fri'
                WHEN 5 THEN 'Sat'
                WHEN 6 THEN 'Sun'
            END as day_of_week,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            ROUND(AVG(pp.click_through_rate), 4) as avg_ctr
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        GROUP BY pc.time_slot, pc.day_of_week
        HAVING post_count >= 3
        ORDER BY avg_er DESC
        LIMIT ?
    """, (limit,))
    
    return [dict(row) for row in cursor.fetchall()]


def get_hourly_performance(conn) -> List[Dict]:
    """
    取得每小時的平均表現
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            pc.hour_of_day,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            ROUND(AVG(pp.click_through_rate), 4) as avg_ctr
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        GROUP BY pc.hour_of_day
        ORDER BY pc.hour_of_day
    """)
    
    return [dict(row) for row in cursor.fetchall()]


def get_best_posting_times_by_topic(conn, limit: int = 30) -> List[Dict]:
    """
    找出各議題的最佳發文時間組合
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(pc.issue_topic, 'unclassified') as issue_topic,
            pc.time_slot,
            CASE pc.day_of_week
                WHEN 0 THEN 'Mon'
                WHEN 1 THEN 'Tue'
                WHEN 2 THEN 'Wed'
                WHEN 3 THEN 'Thu'
                WHEN 4 THEN 'Fri'
                WHEN 5 THEN 'Sat'
                WHEN 6 THEN 'Sun'
            END as day_of_week,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            ROUND(AVG(pp.click_through_rate), 4) as avg_ctr
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        GROUP BY issue_topic, pc.time_slot, pc.day_of_week
        ORDER BY issue_topic, avg_er DESC
    """)
    
    return [dict(row) for row in cursor.fetchall()]


def get_best_posting_times_by_format(conn, limit: int = 30) -> List[Dict]:
    """
    找出各行動類型的最佳發文時間組合
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(pc.format_type, pc.topic_primary, 'unclassified') as format_type,
            pc.time_slot,
            CASE pc.day_of_week
                WHEN 0 THEN 'Mon'
                WHEN 1 THEN 'Tue'
                WHEN 2 THEN 'Wed'
                WHEN 3 THEN 'Thu'
                WHEN 4 THEN 'Fri'
                WHEN 5 THEN 'Sat'
                WHEN 6 THEN 'Sun'
            END as day_of_week,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            ROUND(AVG(pp.click_through_rate), 4) as avg_ctr
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        GROUP BY format_type, pc.time_slot, pc.day_of_week
        ORDER BY format_type, avg_er DESC
    """)
    
    return [dict(row) for row in cursor.fetchall()]


def get_quadrant_analysis(conn) -> List[Dict]:
    """
    取得象限分析資料（用於 Looker Studio 視覺化）
    X軸：觸及人數 (reach)
    Y軸：互動率 (engagement_rate)
    基準線：中位數
    """
    cursor = conn.cursor()
    
    # 先計算中位數
    cursor.execute("""
        WITH latest_snapshots AS (
            SELECT post_id, post_impressions_unique
            FROM post_insights_snapshots
            WHERE (post_id, fetch_date) IN (
                SELECT post_id, MAX(fetch_date) 
                FROM post_insights_snapshots 
                GROUP BY post_id
            )
        ),
        stats AS (
            SELECT 
                ls.post_impressions_unique as reach,
                pp.engagement_rate
            FROM posts_performance pp
            JOIN latest_snapshots ls ON pp.post_id = ls.post_id
            WHERE ls.post_impressions_unique > 0
        )
        SELECT 
            (SELECT reach FROM stats ORDER BY reach LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM stats)) as median_reach,
            (SELECT engagement_rate FROM stats ORDER BY engagement_rate LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM stats)) as median_er
    """)
    medians = cursor.fetchone()
    median_reach = medians['median_reach'] or 1000
    median_er = medians['median_er'] or 0.03
    
    # 取得所有貼文資料 (使用最新 snapshot)
    cursor.execute("""
        WITH latest_insights AS (
            SELECT post_id, post_impressions_unique
            FROM post_insights_snapshots
            WHERE (post_id, fetch_date) IN (
                SELECT post_id, MAX(fetch_date)
                FROM post_insights_snapshots
                GROUP BY post_id
            )
        ),
        latest_performance AS (
            SELECT post_id, engagement_rate
            FROM posts_performance
            WHERE (post_id, snapshot_date) IN (
                SELECT post_id, MAX(snapshot_date)
                FROM posts_performance
                GROUP BY post_id
            )
        )
        SELECT
            p.post_id,
            p.created_time,
            p.permalink_url,
            SUBSTR(p.message, 1, 50) as content_short,
            li.post_impressions_unique as reach,
            lp.engagement_rate,
            COALESCE(pc.issue_topic, 'unclassified') as topic_tag,
            COALESCE(pc.format_type, pc.topic_primary, 'unclassified') as format_type
        FROM posts p
        JOIN latest_performance lp ON p.post_id = lp.post_id
        JOIN posts_classification pc ON p.post_id = pc.post_id
        JOIN latest_insights li ON p.post_id = li.post_id
        WHERE li.post_impressions_unique > 0
        ORDER BY p.created_time DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        d = dict(row)
        d['median_reach'] = median_reach
        d['median_er'] = median_er
        
        # 計算象限
        is_high_reach = d['reach'] >= median_reach
        is_high_er = d['engagement_rate'] >= median_er
        
        if is_high_reach and is_high_er:
            d['quadrant'] = '王牌貼文'
        elif not is_high_reach and is_high_er:
            d['quadrant'] = '潛力珍寶'
        elif is_high_reach and not is_high_er:
            d['quadrant'] = '廣傳陷阱'
        else:
            d['quadrant'] = '常態內容'
        
        results.append(d)
    
    return results


# ==================== 主題分析 (雙維度) ====================

# 定義顯示名稱對照
FORMAT_TYPE_NAMES = {
    'event': '定期活動（影展、演講）',
    'press': '記者會',
    'statement': '公開發言/聲明稿',
    'opinion': '新聞觀點',
    'op_ed': '綠盟投書',
    'report': '報告發布',
    'booth': '擺攤資訊',
    'edu': '科普文章/Podcast',
    'action': '其他行動號召',
}

ISSUE_TOPIC_NAMES = {
    'nuclear': '核能發電',
    'climate': '氣候問題',
    'net_zero': '淨零政策',
    'industry': '產業分析',
    'renewable': '能源發展',
    'other': '其他議題',
}


def get_format_type_performance(conn) -> List[Dict]:
    """
    取得各貼文形式 (Format Type) 的表現比較
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(pc.format_type, pc.topic_primary, 'unclassified') as format_type,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            ROUND(AVG(pp.share_rate), 4) as avg_share_rate,
            ROUND(AVG(pp.comment_rate), 4) as avg_comment_rate,
            SUM(CASE WHEN pp.performance_tier = 'viral' THEN 1 ELSE 0 END) as viral_count,
            SUM(CASE WHEN pp.performance_tier = 'high' THEN 1 ELSE 0 END) as high_count
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        GROUP BY format_type
        ORDER BY avg_er DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        d = dict(row)
        d['format_type_name'] = FORMAT_TYPE_NAMES.get(d['format_type'], d['format_type'])
        results.append(d)
    return results


def get_issue_topic_performance(conn) -> List[Dict]:
    """
    取得各議題 (Issue Topic) 的表現比較
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(pc.issue_topic, pc.topic_secondary, 'unclassified') as issue_topic,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            ROUND(AVG(pp.share_rate), 4) as avg_share_rate,
            ROUND(AVG(pp.comment_rate), 4) as avg_comment_rate,
            SUM(CASE WHEN pp.performance_tier = 'viral' THEN 1 ELSE 0 END) as viral_count,
            SUM(CASE WHEN pp.performance_tier = 'high' THEN 1 ELSE 0 END) as high_count
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        GROUP BY issue_topic
        ORDER BY avg_er DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        d = dict(row)
        d['issue_topic_name'] = ISSUE_TOPIC_NAMES.get(d['issue_topic'], d['issue_topic'])
        results.append(d)
    return results


def get_format_issue_cross_performance(conn) -> List[Dict]:
    """
    取得貼文形式 × 議題的交叉表現分析
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(pc.format_type, pc.topic_primary, 'unclassified') as format_type,
            COALESCE(pc.issue_topic, pc.topic_secondary, 'unclassified') as issue_topic,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            ROUND(AVG(pp.share_rate), 4) as avg_share_rate,
            SUM(CASE WHEN pp.performance_tier IN ('viral', 'high') THEN 1 ELSE 0 END) as high_performer_count
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        GROUP BY format_type, issue_topic
        HAVING post_count >= 2
        ORDER BY avg_er DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        d = dict(row)
        d['format_type_name'] = FORMAT_TYPE_NAMES.get(d['format_type'], d['format_type'])
        d['issue_topic_name'] = ISSUE_TOPIC_NAMES.get(d['issue_topic'], d['issue_topic'])
        results.append(d)
    return results


# 保留舊函數名稱以相容現有程式碼
def get_topic_performance(conn) -> List[Dict]:
    """
    取得各主題的表現比較 (向後相容)
    """
    return get_format_type_performance(conn)


# ==================== 高表現貼文分析 ====================

def get_top_posts(conn, days: int = 30, limit: int = 10) -> List[Dict]:
    """
    取得近期表現最佳的貼文 (使用最新 snapshot)
    """
    cursor = conn.cursor()
    cursor.execute("""
        WITH latest_insights AS (
            SELECT post_id,
                   post_impressions_unique,
                   likes_count,
                   comments_count,
                   shares_count
            FROM post_insights_snapshots
            WHERE (post_id, fetch_date) IN (
                SELECT post_id, MAX(fetch_date)
                FROM post_insights_snapshots
                GROUP BY post_id
            )
        ),
        latest_performance AS (
            SELECT post_id, engagement_rate, performance_tier, percentile_rank
            FROM posts_performance
            WHERE (post_id, snapshot_date) IN (
                SELECT post_id, MAX(snapshot_date)
                FROM posts_performance
                GROUP BY post_id
            )
        )
        SELECT
            p.post_id,
            SUBSTR(p.message, 1, 100) as message_preview,
            p.created_time,
            p.permalink_url,
            pc.topic_primary,
            pc.issue_topic,
            pc.time_slot,
            lp.engagement_rate,
            lp.performance_tier,
            lp.percentile_rank,
            li.post_impressions_unique as reach,
            li.likes_count + li.comments_count + li.shares_count as total_engagement
        FROM posts p
        JOIN posts_classification pc ON p.post_id = pc.post_id
        JOIN latest_performance lp ON p.post_id = lp.post_id
        JOIN latest_insights li ON p.post_id = li.post_id
        WHERE p.created_time >= date('now', ? || ' days')
        ORDER BY lp.engagement_rate DESC
        LIMIT ?
    """, (f'-{days}', limit))

    return [dict(row) for row in cursor.fetchall()]


def get_viral_post_patterns(conn) -> List[Dict]:
    """
    分析病毒貼文的共同特徵
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            pc.media_type,
            pc.message_length_tier,
            pc.has_cta,
            pc.time_slot,
            COUNT(*) as viral_count,
            ROUND(AVG(pc.message_length), 0) as avg_length,
            ROUND(AVG(pc.hashtag_count), 1) as avg_hashtags
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        WHERE pp.performance_tier = 'viral'
        GROUP BY pc.media_type, pc.message_length_tier, pc.has_cta, pc.time_slot
        ORDER BY viral_count DESC
        LIMIT 15
    """)
    
    return [dict(row) for row in cursor.fetchall()]


# ==================== 趨勢分析 ====================

def get_weekly_trends(conn, weeks: int = 52) -> List[Dict]:
    """
    取得週度趨勢 - 週次以週一～週日為準
    """
    cursor = conn.cursor()
    # 使用正確的週一計算：
    # strftime('%w') 返回 0=週日, 1=週一, ..., 6=週六
    # 週一 = 日期 - ((weekday + 6) % 7) 天
    # 
    # 使用 MAX 取得各指標最大值，避免不完整 snapshot 導致互動數為 0
    cursor.execute("""
        WITH best_snapshots AS (
            SELECT post_id, 
                   MAX(post_impressions_unique) as post_impressions_unique, 
                   MAX(likes_count) as likes_count, 
                   MAX(comments_count) as comments_count, 
                   MAX(shares_count) as shares_count
            FROM post_insights_snapshots
            GROUP BY post_id
        ),
        post_weeks AS (
            SELECT 
                p.post_id,
                date(substr(p.created_time, 1, 10), 
                     '-' || ((strftime('%w', substr(p.created_time, 1, 10)) + 6) % 7) || ' days'
                ) as week_monday
            FROM posts p
        )
        SELECT
            pw.week_monday as week_start,
            date(pw.week_monday, '+6 days') as week_end,
            COUNT(DISTINCT p.post_id) as post_count,
            ROUND(AVG(pp.engagement_rate), 4) as avg_er,
            SUM(bs.post_impressions_unique) as total_reach,
            SUM(bs.likes_count + bs.comments_count + bs.shares_count) as total_engagement
        FROM posts p
        JOIN post_weeks pw ON p.post_id = pw.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN best_snapshots bs ON p.post_id = bs.post_id
        GROUP BY pw.week_monday
        ORDER BY pw.week_monday DESC
        LIMIT ?
    """, (weeks,))

    return [dict(row) for row in cursor.fetchall()]



def get_performance_distribution(conn) -> Dict:
    """
    取得表現等級分布
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            performance_tier,
            COUNT(*) as count
        FROM posts_performance
        GROUP BY performance_tier
    """)
    
    distribution = {}
    for row in cursor.fetchall():
        distribution[row['performance_tier']] = row['count']
    
    return distribution


# ==================== 基準對照 ====================

def get_benchmarks_summary(conn) -> List[Dict]:
    """
    取得所有基準值摘要
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            benchmark_type,
            benchmark_key,
            period,
            ROUND(avg_engagement_rate, 4) as avg_er,
            sample_size,
            updated_at
        FROM benchmarks
        ORDER BY benchmark_type, benchmark_key, period
    """)
    
    return [dict(row) for row in cursor.fetchall()]


# ==================== 報表產出 ====================

def generate_weekly_report(conn) -> str:
    """
    產出週報文字摘要
    """
    report = []
    report.append("=" * 50)
    report.append(f"Facebook 社群週報 - {datetime.now().strftime('%Y-%m-%d')}")
    report.append("=" * 50)
    
    # 本週表現
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 2) as avg_er,
            SUM(pi.post_impressions_unique) as total_reach
        FROM posts p
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN post_insights_snapshots pi ON p.post_id = pi.post_id
        WHERE p.created_time >= date('now', '-7 days')
    """)
    week_stats = cursor.fetchone()
    
    report.append("\n📊 本週摘要")
    report.append(f"  發文數: {week_stats['post_count'] or 0}")
    report.append(f"  平均互動率: {week_stats['avg_er'] or 0:.2f}%")
    report.append(f"  總觸及人數: {week_stats['total_reach'] or 0:,}")
    
    # Top 3 貼文
    top_posts = get_top_posts(conn, days=7, limit=3)
    report.append("\n🏆 本週 Top 3 貼文")
    for i, post in enumerate(top_posts, 1):
        msg = post['message_preview'][:50] + '...' if post['message_preview'] else '(無文字)'
        report.append(f"  {i}. ER={post['engagement_rate']:.2f}% | {msg}")
    
    # 表現分布
    dist = get_performance_distribution(conn)
    report.append("\n📈 表現分布")
    for tier in ['viral', 'high', 'average', 'low']:
        count = dist.get(tier, 0)
        report.append(f"  {tier}: {count}")
    
    # 最佳時間
    best_times = get_best_posting_times(conn, limit=3)
    report.append("\n⏰ 最佳發文時間")
    for t in best_times:
        report.append(f"  {t['day_of_week']} {t['time_slot']}: ER={t['avg_er']:.2f}%")
    
    report.append("\n" + "=" * 50)
    
    return "\n".join(report)


# ==================== 主程式 ====================

def main():
    """示範報表查詢"""
    conn = get_connection()
    
    try:
        print(generate_weekly_report(conn))
        
        print("\n\n=== 主題表現比較 ===")
        topics = get_topic_performance(conn)
        for t in topics:
            print(f"  {t['topic']}: ER={t['avg_er']:.2f}%, Posts={t['post_count']}")
        
        print("\n=== 病毒貼文特徵 ===")
        patterns = get_viral_post_patterns(conn)
        for p in patterns[:5]:
            print(f"  {p['media_type']} / {p['message_length_tier']} / CTA={p['has_cta']}: {p['viral_count']} posts")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
