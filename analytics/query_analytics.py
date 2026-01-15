"""
Facebook 社群數據分析框架 - 彈性查詢工具
支援自訂時間範圍與粒度的數據查詢
"""

import argparse
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
from utils.config import DB_PATH


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== 時間範圍查詢 ====================

def query_by_date_range(conn, start_date: str, end_date: str, granularity: str = 'daily') -> List[Dict]:
    """
    依日期範圍查詢數據

    Args:
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        granularity: 粒度 (daily/weekly/monthly)

    Returns:
        查詢結果列表
    """
    cursor = conn.cursor()

    # 根據粒度選擇不同的時間分組
    # 注意: created_time 格式為 '2025-12-11T01:30:00+0000'，需先移除時區
    if granularity == 'daily':
        time_format = "%Y-%m-%d"
        group_by = "SUBSTR(p.created_time, 1, 10)"
    elif granularity == 'weekly':
        time_format = "%Y-W%W"
        group_by = "strftime('%Y-W%W', SUBSTR(p.created_time, 1, 19))"
    elif granularity == 'monthly':
        time_format = "%Y-%m"
        group_by = "SUBSTR(p.created_time, 1, 7)"
    else:
        raise ValueError(f"不支援的粒度: {granularity}")

    query = f"""
        SELECT
            {"strftime('" + time_format + "', SUBSTR(p.created_time, 1, 19))" if granularity in ['weekly'] else group_by} as time_period,
            COUNT(DISTINCT p.post_id) as post_count,

            -- 互動指標
            SUM(pi.likes_count) as total_likes,
            SUM(pi.comments_count) as total_comments,
            SUM(pi.shares_count) as total_shares,
            SUM(pi.likes_count + pi.comments_count + pi.shares_count) as total_engagement,

            -- 觸及指標
            SUM(pi.post_impressions_unique) as total_reach,
            SUM(pi.post_clicks) as total_clicks,

            -- 平均 KPI
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate,
            ROUND(AVG(pp.click_through_rate), 2) as avg_click_rate,
            ROUND(AVG(pp.share_rate), 2) as avg_share_rate,
            ROUND(AVG(pp.comment_rate), 2) as avg_comment_rate,

            -- 表現分級統計
            SUM(CASE WHEN pp.performance_tier = 'viral' THEN 1 ELSE 0 END) as viral_count,
            SUM(CASE WHEN pp.performance_tier = 'high' THEN 1 ELSE 0 END) as high_count,
            SUM(CASE WHEN pp.performance_tier = 'average' THEN 1 ELSE 0 END) as average_count,
            SUM(CASE WHEN pp.performance_tier = 'low' THEN 1 ELSE 0 END) as low_count

        FROM posts p
        JOIN post_insights_snapshots pi ON p.post_id = pi.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE SUBSTR(p.created_time, 1, 10) BETWEEN ? AND ?
        GROUP BY {group_by}
        ORDER BY time_period DESC
    """

    cursor.execute(query, (start_date, end_date))
    return [dict(row) for row in cursor.fetchall()]


def query_topic_performance(conn, start_date: str, end_date: str, topic: Optional[str] = None) -> List[Dict]:
    """
    查詢主題表現（可指定時間範圍）

    Args:
        start_date: 起始日期
        end_date: 結束日期
        topic: 特定主題 (可選)
    """
    cursor = conn.cursor()

    where_clause = "WHERE SUBSTR(p.created_time, 1, 10) BETWEEN ? AND ?"
    params = [start_date, end_date]

    if topic:
        where_clause += " AND pc.topic_primary = ?"
        params.append(topic)

    query = f"""
        SELECT
            COALESCE(pc.topic_primary, 'unclassified') as topic,
            COUNT(*) as post_count,
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate,
            ROUND(AVG(pp.share_rate), 2) as avg_share_rate,
            ROUND(AVG(pp.comment_rate), 2) as avg_comment_rate,
            SUM(CASE WHEN pp.performance_tier = 'viral' THEN 1 ELSE 0 END) as viral_count,
            SUM(CASE WHEN pp.performance_tier = 'high' THEN 1 ELSE 0 END) as high_count,
            SUM(pi.post_impressions_unique) as total_reach,
            SUM(pi.likes_count + pi.comments_count + pi.shares_count) as total_engagement
        FROM posts p
        JOIN posts_classification pc ON p.post_id = pc.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN post_insights_snapshots pi ON p.post_id = pi.post_id
        {where_clause}
        GROUP BY pc.topic_primary
        ORDER BY avg_engagement_rate DESC
    """

    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def query_time_slot_performance(conn, start_date: str, end_date: str) -> List[Dict]:
    """
    查詢時段表現（可指定時間範圍）
    """
    cursor = conn.cursor()

    query = """
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
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate,
            ROUND(AVG(pp.click_through_rate), 2) as avg_click_rate,
            SUM(pi.post_impressions_unique) as total_reach
        FROM posts p
        JOIN posts_classification pc ON p.post_id = pc.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN post_insights_snapshots pi ON p.post_id = pi.post_id
        WHERE SUBSTR(p.created_time, 1, 10) BETWEEN ? AND ?
        GROUP BY pc.time_slot, pc.day_of_week
        HAVING post_count >= 2
        ORDER BY avg_engagement_rate DESC
    """

    cursor.execute(query, (start_date, end_date))
    return [dict(row) for row in cursor.fetchall()]


def query_top_posts(conn, start_date: str, end_date: str, limit: int = 10,
                    topic: Optional[str] = None, time_slot: Optional[str] = None) -> List[Dict]:
    """
    查詢 Top 貼文（支援篩選條件）

    Args:
        start_date: 起始日期
        end_date: 結束日期
        limit: 回傳數量
        topic: 篩選主題 (可選)
        time_slot: 篩選時段 (可選)
    """
    cursor = conn.cursor()

    where_clauses = ["SUBSTR(p.created_time, 1, 10) BETWEEN ? AND ?"]
    params = [start_date, end_date]

    if topic:
        where_clauses.append("pc.topic_primary = ?")
        params.append(topic)

    if time_slot:
        where_clauses.append("pc.time_slot = ?")
        params.append(time_slot)

    where_clause = " AND ".join(where_clauses)
    params.append(limit)

    query = f"""
        SELECT
            p.post_id,
            SUBSTR(p.message, 1, 100) as message_preview,
            p.created_time,
            pc.topic_primary,
            pc.time_slot,
            pp.engagement_rate,
            pp.performance_tier,
            pp.percentile_rank,
            pi.post_impressions_unique as reach,
            (pi.likes_count + pi.comments_count + pi.shares_count) as total_engagement,
            pi.likes_count,
            pi.comments_count,
            pi.shares_count
        FROM posts p
        JOIN posts_classification pc ON p.post_id = pc.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN post_insights_snapshots pi ON p.post_id = pi.post_id
        WHERE {where_clause}
        ORDER BY pp.engagement_rate DESC
        LIMIT ?
    """

    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def query_comparison(conn, period1_start: str, period1_end: str,
                     period2_start: str, period2_end: str) -> Dict:
    """
    比較兩個時間段的表現

    Args:
        period1_start: 期間1起始
        period1_end: 期間1結束
        period2_start: 期間2起始
        period2_end: 期間2結束

    Returns:
        包含兩期比較的字典
    """
    cursor = conn.cursor()

    query = """
        SELECT
            COUNT(*) as post_count,
            SUM(pi.post_impressions_unique) as total_reach,
            SUM(pi.likes_count + pi.comments_count + pi.shares_count) as total_engagement,
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate,
            SUM(CASE WHEN pp.performance_tier = 'viral' THEN 1 ELSE 0 END) as viral_count,
            SUM(CASE WHEN pp.performance_tier = 'high' THEN 1 ELSE 0 END) as high_count
        FROM posts p
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN post_insights_snapshots pi ON p.post_id = pi.post_id
        WHERE SUBSTR(p.created_time, 1, 10) BETWEEN ? AND ?
    """

    # 查詢期間1
    cursor.execute(query, (period1_start, period1_end))
    period1 = dict(cursor.fetchone())

    # 查詢期間2
    cursor.execute(query, (period2_start, period2_end))
    period2 = dict(cursor.fetchone())

    # 計算變化
    result = {
        'period1': {
            'start': period1_start,
            'end': period1_end,
            **period1
        },
        'period2': {
            'start': period2_start,
            'end': period2_end,
            **period2
        },
        'changes': {}
    }

    # 計算各項變化百分比
    for key in ['post_count', 'total_reach', 'total_engagement', 'avg_engagement_rate']:
        val1 = period1[key] or 0
        val2 = period2[key] or 0

        if val2 > 0:
            change_pct = ((val1 - val2) / val2) * 100
            result['changes'][key] = round(change_pct, 1)
        else:
            result['changes'][key] = None

    return result


# ==================== 報表產出 ====================

def generate_custom_report(conn, start_date: str, end_date: str, granularity: str = 'weekly') -> str:
    """
    產出自訂時間範圍的報表
    """
    report = []
    report.append("=" * 70)
    report.append(f"Facebook 社群分析報表")
    report.append(f"時間範圍: {start_date} ~ {end_date}")
    report.append(f"粒度: {granularity}")
    report.append(f"產出時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)

    # 整體摘要
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as post_count,
            SUM(pi.post_impressions_unique) as total_reach,
            SUM(pi.likes_count + pi.comments_count + pi.shares_count) as total_engagement,
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate
        FROM posts p
        JOIN posts_performance pp ON p.post_id = pp.post_id
        JOIN post_insights_snapshots pi ON p.post_id = pi.post_id
        WHERE SUBSTR(p.created_time, 1, 10) BETWEEN ? AND ?
    """, (start_date, end_date))

    summary = cursor.fetchone()

    report.append("\n📊 整體摘要")
    report.append(f"  發文總數: {summary['post_count'] or 0}")
    report.append(f"  總觸及人數: {summary['total_reach'] or 0:,}")
    report.append(f"  總互動數: {summary['total_engagement'] or 0:,}")
    report.append(f"  平均互動率: {summary['avg_engagement_rate'] or 0:.2f}%")

    # 時間趨勢
    trends = query_by_date_range(conn, start_date, end_date, granularity)

    report.append(f"\n📈 {granularity.capitalize()} 趨勢")
    report.append(f"{'時期':15s} {'貼文數':>8s} {'觸及':>10s} {'互動率':>10s} {'Viral':>6s}")
    report.append("-" * 70)

    for row in trends[:10]:  # 只顯示最近10期
        report.append(
            f"{row['time_period']:15s} "
            f"{row['post_count']:8d} "
            f"{row['total_reach']:10,d} "
            f"{row['avg_engagement_rate']:9.2f}% "
            f"{row['viral_count']:6d}"
        )

    # 主題表現
    topics = query_topic_performance(conn, start_date, end_date)

    report.append("\n🎯 主題表現")
    for topic in topics[:5]:
        report.append(
            f"  {topic['topic']:15s}: "
            f"ER={topic['avg_engagement_rate']:5.2f}%, "
            f"Posts={topic['post_count']}, "
            f"Viral={topic['viral_count']}"
        )

    # 最佳發文時間
    time_slots = query_time_slot_performance(conn, start_date, end_date)

    report.append("\n⏰ 最佳發文時間 (Top 5)")
    for slot in time_slots[:5]:
        report.append(
            f"  {slot['day_of_week']:3s} {slot['time_slot']:10s}: "
            f"ER={slot['avg_engagement_rate']:5.2f}%, "
            f"Posts={slot['post_count']}"
        )

    # Top 貼文
    top_posts = query_top_posts(conn, start_date, end_date, limit=3)

    report.append("\n🏆 Top 3 貼文")
    for i, post in enumerate(top_posts, 1):
        msg = (post['message_preview'] or '')[:50]
        report.append(f"  {i}. ER={post['engagement_rate']:.2f}% | {msg}...")

    report.append("\n" + "=" * 70)

    return "\n".join(report)


# ==================== 命令列介面 ====================

def main():
    """命令列執行入口"""
    parser = argparse.ArgumentParser(
        description='Facebook 社群數據分析 - 彈性查詢工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:

  # 查詢最近 7 天的每日數據
  python3 query_analytics.py --days 7 --granularity daily

  # 查詢特定時間範圍的週度數據
  python3 query_analytics.py --start 2025-11-01 --end 2025-11-30 --granularity weekly

  # 查詢特定主題的表現
  python3 query_analytics.py --days 30 --topic energy

  # 比較兩個時間段
  python3 query_analytics.py --compare --period1 2025-10-01,2025-10-31 --period2 2025-11-01,2025-11-30

  # 查詢特定時段的 Top 貼文
  python3 query_analytics.py --days 30 --top 10 --time-slot evening

        """
    )

    # 時間範圍選項
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument('--days', type=int, help='查詢最近 N 天')
    time_group.add_argument('--weeks', type=int, help='查詢最近 N 週')
    time_group.add_argument('--months', type=int, help='查詢最近 N 個月')

    parser.add_argument('--start', help='起始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', help='結束日期 (YYYY-MM-DD)')

    # 粒度選項
    parser.add_argument('--granularity', choices=['daily', 'weekly', 'monthly'],
                        default='weekly', help='數據粒度 (預設: weekly)')

    # 篩選選項
    parser.add_argument('--topic', help='篩選特定主題')
    parser.add_argument('--time-slot',
                        choices=['morning', 'noon', 'afternoon', 'evening', 'night'],
                        help='篩選特定時段')

    # 查詢類型
    parser.add_argument('--top', type=int, metavar='N', help='顯示 Top N 貼文')
    parser.add_argument('--compare', action='store_true', help='比較兩個時間段')
    parser.add_argument('--period1', help='比較期間1 (start,end)')
    parser.add_argument('--period2', help='比較期間2 (start,end)')

    # 輸出選項
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                        help='輸出格式 (預設: text)')

    args = parser.parse_args()

    # 計算時間範圍
    if args.start and args.end:
        start_date = args.start
        end_date = args.end
    elif args.days:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    elif args.weeks:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(weeks=args.weeks)).strftime('%Y-%m-%d')
    elif args.months:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.months*30)).strftime('%Y-%m-%d')
    else:
        # 預設最近 7 天
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    # 執行查詢
    conn = get_connection()

    try:
        if args.compare:
            # 比較模式
            if not (args.period1 and args.period2):
                print("錯誤: 比較模式需要 --period1 和 --period2 參數")
                print("範例: --period1 2025-10-01,2025-10-31 --period2 2025-11-01,2025-11-30")
                return

            p1_start, p1_end = args.period1.split(',')
            p2_start, p2_end = args.period2.split(',')

            result = query_comparison(conn, p1_start, p1_end, p2_start, p2_end)

            if args.format == 'json':
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print("\n" + "="*60)
                print("時間段比較分析")
                print("="*60)
                print(f"\n期間1: {p1_start} ~ {p1_end}")
                print(f"  發文數: {result['period1']['post_count']}")
                print(f"  總觸及: {result['period1']['total_reach']:,}")
                print(f"  平均ER: {result['period1']['avg_engagement_rate']}%")

                print(f"\n期間2: {p2_start} ~ {p2_end}")
                print(f"  發文數: {result['period2']['post_count']}")
                print(f"  總觸及: {result['period2']['total_reach']:,}")
                print(f"  平均ER: {result['period2']['avg_engagement_rate']}%")

                print("\n📊 變化")
                for key, value in result['changes'].items():
                    if value is not None:
                        symbol = "📈" if value > 0 else "📉" if value < 0 else "→"
                        print(f"  {symbol} {key}: {value:+.1f}%")
                print()

        elif args.top:
            # Top 貼文查詢
            posts = query_top_posts(conn, start_date, end_date, args.top, args.topic, args.time_slot)

            if args.format == 'json':
                import json
                print(json.dumps(posts, indent=2, ensure_ascii=False))
            else:
                print(f"\n{'='*70}")
                print(f"Top {args.top} 貼文 ({start_date} ~ {end_date})")
                if args.topic:
                    print(f"主題篩選: {args.topic}")
                if args.time_slot:
                    print(f"時段篩選: {args.time_slot}")
                print("="*70)

                for i, post in enumerate(posts, 1):
                    print(f"\n{i}. ER: {post['engagement_rate']:.2f}% | Tier: {post['performance_tier']}")
                    print(f"   發布: {post['created_time'][:10]} | 主題: {post['topic_primary'] or 'N/A'} | 時段: {post['time_slot']}")
                    print(f"   觸及: {post['reach']:,} | 互動: {post['total_engagement']} (👍{post['likes_count']} 💬{post['comments_count']} 🔗{post['shares_count']})")
                    print(f"   內容: {post['message_preview']}...")
                print()

        else:
            # 一般報表
            report = generate_custom_report(conn, start_date, end_date, args.granularity)

            if args.format == 'json':
                # JSON 格式輸出
                data = {
                    'trends': query_by_date_range(conn, start_date, end_date, args.granularity),
                    'topics': query_topic_performance(conn, start_date, end_date, args.topic),
                    'time_slots': query_time_slot_performance(conn, start_date, end_date)
                }
                import json
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(report)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
