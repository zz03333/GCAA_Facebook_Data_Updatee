"""
Facebook 社群數據分析框架 - 投廣預測模型
識別高潛力貼文並建議投放廣告
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


# ==================== 評分權重 ====================

SCORING_WEIGHTS = {
    'early_engagement_rate': 0.30,    # 24h 內互動率
    'share_rate': 0.25,               # 分享率（病毒潛力）
    'comment_rate': 0.15,             # 留言率（討論深度）
    'topic_performance': 0.15,        # 議題歷史表現
    'time_slot_factor': 0.15          # 發文時段效果
}


# ==================== 評分函數 ====================

def get_percentile_benchmarks(conn) -> Dict:
    """
    取得各指標的百分位基準值
    用於將原始數值轉換為 0-100 分數
    """
    cursor = conn.cursor()
    
    # 取得互動率的百分位
    cursor.execute("""
        SELECT 
            AVG(engagement_rate) as avg_er,
            MAX(engagement_rate) as max_er,
            MIN(engagement_rate) as min_er
        FROM posts_performance
        WHERE engagement_rate IS NOT NULL AND engagement_rate < 100
    """)
    er_stats = dict(cursor.fetchone())
    
    # 取得分享率的百分位
    cursor.execute("""
        SELECT 
            AVG(share_rate) as avg_sr,
            MAX(share_rate) as max_sr
        FROM posts_performance
        WHERE share_rate IS NOT NULL
    """)
    sr_stats = dict(cursor.fetchone())
    
    # 取得留言率的百分位
    cursor.execute("""
        SELECT 
            AVG(comment_rate) as avg_cr,
            MAX(comment_rate) as max_cr
        FROM posts_performance
        WHERE comment_rate IS NOT NULL
    """)
    cr_stats = dict(cursor.fetchone())
    
    return {
        'engagement_rate': er_stats,
        'share_rate': sr_stats,
        'comment_rate': cr_stats
    }


def get_topic_historical_performance(conn, topic: str) -> float:
    """
    取得特定議題的歷史平均互動率
    返回相對於整體平均的倍數
    """
    cursor = conn.cursor()
    
    # 該議題平均
    cursor.execute("""
        SELECT AVG(pp.engagement_rate) as topic_avg
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        WHERE pc.issue_topic = ?
    """, (topic,))
    topic_result = cursor.fetchone()
    topic_avg = topic_result['topic_avg'] if topic_result['topic_avg'] else 0
    
    # 整體平均
    cursor.execute("""
        SELECT AVG(engagement_rate) as overall_avg
        FROM posts_performance
    """)
    overall_result = cursor.fetchone()
    overall_avg = overall_result['overall_avg'] if overall_result['overall_avg'] else 1
    
    return topic_avg / overall_avg if overall_avg > 0 else 1


def get_time_slot_factor(conn, time_slot: str, day_of_week: int) -> float:
    """
    取得特定時段的歷史表現因子
    返回相對於整體平均的倍數
    """
    cursor = conn.cursor()
    
    # 該時段平均
    cursor.execute("""
        SELECT AVG(pp.engagement_rate) as slot_avg
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        WHERE pc.time_slot = ? AND pc.day_of_week = ?
    """, (time_slot, day_of_week))
    slot_result = cursor.fetchone()
    slot_avg = slot_result['slot_avg'] if slot_result['slot_avg'] else 0
    
    # 整體平均
    cursor.execute("""
        SELECT AVG(engagement_rate) as overall_avg
        FROM posts_performance
    """)
    overall_result = cursor.fetchone()
    overall_avg = overall_result['overall_avg'] if overall_result['overall_avg'] else 1
    
    return slot_avg / overall_avg if overall_avg > 0 else 1


def normalize_score(value: float, max_value: float, min_value: float = 0) -> float:
    """
    將數值正規化到 0-100 範圍
    """
    if max_value <= min_value:
        return 50
    
    score = (value - min_value) / (max_value - min_value) * 100
    return max(0, min(100, score))


def calculate_ad_potential(conn, post_id: str) -> Dict:
    """
    計算單一貼文的投廣潛力分數
    
    返回:
    - ad_potential_score: 0-100 分數
    - ad_recommendation: Yes/No/Maybe
    - breakdown: 各項指標明細
    """
    cursor = conn.cursor()
    
    # 取得貼文基本數據
    cursor.execute("""
        SELECT 
            pp.engagement_rate,
            pp.share_rate,
            pp.comment_rate,
            pp.performance_tier,
            pc.issue_topic,
            pc.format_type,
            pc.time_slot,
            pc.day_of_week,
            p.created_time
        FROM posts p
        JOIN posts_performance pp ON p.post_id = pp.post_id
        LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
        WHERE p.post_id = ?
    """, (post_id,))
    
    result = cursor.fetchone()
    if not result:
        return None
    
    data = dict(result)
    
    # 取得基準值
    benchmarks = get_percentile_benchmarks(conn)
    
    # 計算各項分數
    breakdown = {}
    
    # 1. 互動率分數 (30%)
    er = data['engagement_rate'] or 0
    er_max = benchmarks['engagement_rate']['max_er'] or 10
    breakdown['engagement_rate_score'] = normalize_score(er, er_max)
    
    # 2. 分享率分數 (25%)
    sr = data['share_rate'] or 0
    sr_max = benchmarks['share_rate']['max_sr'] or 5
    breakdown['share_rate_score'] = normalize_score(sr, sr_max)
    
    # 3. 留言率分數 (15%)
    cr = data['comment_rate'] or 0
    cr_max = benchmarks['comment_rate']['max_cr'] or 3
    breakdown['comment_rate_score'] = normalize_score(cr, cr_max)
    
    # 4. 議題表現因子 (15%)
    topic = data['issue_topic'] or 'unclassified'
    topic_factor = get_topic_historical_performance(conn, topic)
    breakdown['topic_factor'] = round(topic_factor, 2)
    breakdown['topic_score'] = min(100, topic_factor * 50)  # 因子 2x = 100分
    
    # 5. 時段因子 (15%)
    time_slot = data['time_slot'] or 'unclassified'
    day_of_week = data['day_of_week'] or 0
    time_factor = get_time_slot_factor(conn, time_slot, day_of_week)
    breakdown['time_factor'] = round(time_factor, 2)
    breakdown['time_score'] = min(100, time_factor * 50)
    
    # 計算加權總分
    total_score = (
        breakdown['engagement_rate_score'] * SCORING_WEIGHTS['early_engagement_rate'] +
        breakdown['share_rate_score'] * SCORING_WEIGHTS['share_rate'] +
        breakdown['comment_rate_score'] * SCORING_WEIGHTS['comment_rate'] +
        breakdown['topic_score'] * SCORING_WEIGHTS['topic_performance'] +
        breakdown['time_score'] * SCORING_WEIGHTS['time_slot_factor']
    )
    
    # 決定建議
    if total_score >= 70:
        recommendation = 'Yes'
    elif total_score >= 50:
        recommendation = 'Maybe'
    else:
        recommendation = 'No'
    
    # 取得貼文連結和發布時間
    cursor.execute("""
        SELECT permalink_url, created_time FROM posts WHERE post_id = ?
    """, (post_id,))
    post_info = cursor.fetchone()
    
    return {
        'post_id': post_id,
        'ad_potential_score': round(total_score, 1),
        'ad_recommendation': recommendation,
        'performance_tier': data['performance_tier'],
        'issue_topic': data['issue_topic'],
        'format_type': data['format_type'],
        'permalink_url': post_info['permalink_url'] if post_info else '',
        'created_time': post_info['created_time'] if post_info else '',
        'breakdown': breakdown
    }


def get_recommended_posts(conn, limit: int = 20, min_score: float = 50) -> List[Dict]:
    """
    取得建議投廣的貼文清單
    
    返回分數最高的前 N 則貼文
    """
    cursor = conn.cursor()
    
    # 取得近期貼文（30天內）
    cursor.execute("""
        SELECT p.post_id
        FROM posts p
        JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE p.created_time >= datetime('now', '-30 days')
        ORDER BY pp.engagement_rate DESC
        LIMIT 100
    """)
    
    candidates = [row['post_id'] for row in cursor.fetchall()]
    
    # 計算每則貼文的投廣潛力
    results = []
    for post_id in candidates:
        score_data = calculate_ad_potential(conn, post_id)
        if score_data and score_data['ad_potential_score'] >= min_score:
            results.append(score_data)
    
    # 排序並取前 N 則
    results.sort(key=lambda x: x['ad_potential_score'], reverse=True)
    return results[:limit]


def get_recent_high_performers(conn, hours: int = 48) -> List[Dict]:
    """
    取得近 N 小時內表現突出的貼文
    
    這些是「正在起飛」的貼文，適合立即投廣
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.post_id,
            SUBSTR(p.message, 1, 80) as message_preview,
            p.created_time,
            pp.engagement_rate,
            pp.share_rate,
            pp.performance_tier,
            pc.issue_topic,
            pc.format_type
        FROM posts p
        JOIN posts_performance pp ON p.post_id = pp.post_id
        LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
        WHERE p.created_time >= datetime('now', ? || ' hours')
        AND pp.engagement_rate >= (
            SELECT AVG(engagement_rate) * 1.5 FROM posts_performance
        )
        ORDER BY pp.engagement_rate DESC
        LIMIT 20
    """, (f'-{hours}',))
    
    results = []
    for row in cursor.fetchall():
        data = dict(row)
        score_data = calculate_ad_potential(conn, data['post_id'])
        if score_data:
            data['ad_potential_score'] = score_data['ad_potential_score']
            data['ad_recommendation'] = score_data['ad_recommendation']
        results.append(data)
    
    return results


def update_all_ad_potentials(conn):
    """
    更新所有貼文的投廣潛力分數
    儲存到 posts_classification 表
    """
    cursor = conn.cursor()
    
    # 確保欄位存在
    try:
        cursor.execute("ALTER TABLE posts_classification ADD COLUMN ad_potential_score REAL")
        cursor.execute("ALTER TABLE posts_classification ADD COLUMN ad_recommendation TEXT")
        conn.commit()
    except:
        pass  # 欄位已存在
    
    # 取得所有貼文
    cursor.execute("SELECT post_id FROM posts_classification")
    post_ids = [row['post_id'] for row in cursor.fetchall()]
    
    print(f"更新 {len(post_ids)} 則貼文的投廣潛力分數...")
    
    updated = 0
    for post_id in post_ids:
        score_data = calculate_ad_potential(conn, post_id)
        if score_data:
            cursor.execute("""
                UPDATE posts_classification
                SET ad_potential_score = ?, ad_recommendation = ?
                WHERE post_id = ?
            """, (
                score_data['ad_potential_score'],
                score_data['ad_recommendation'],
                post_id
            ))
            updated += 1
    
    conn.commit()
    print(f"✓ 已更新 {updated} 則貼文")
    return updated


# ==================== 主程式 ====================

def main():
    """示範投廣預測"""
    conn = get_connection()
    
    try:
        print("=== 更新投廣潛力分數 ===")
        update_all_ad_potentials(conn)
        
        print("\n=== 建議投廣貼文 (Top 10) ===")
        recommended = get_recommended_posts(conn, limit=10)
        for i, item in enumerate(recommended, 1):
            print(f"\n{i}. [{item['ad_recommendation']}] 分數: {item['ad_potential_score']}")
            print(f"   議題: {item['issue_topic']} | 類型: {item['format_type']}")
            print(f"   表現等級: {item['performance_tier']}")
        
        print("\n=== 近 48 小時高表現貼文 ===")
        recent = get_recent_high_performers(conn, hours=48)
        for item in recent[:5]:
            print(f"\n  {item['message_preview']}...")
            print(f"    ER: {item['engagement_rate']}% | 建議: {item.get('ad_recommendation', 'N/A')}")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
