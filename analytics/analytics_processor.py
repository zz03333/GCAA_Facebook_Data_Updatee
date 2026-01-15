"""
Facebook 社群數據分析框架 - 數據處理與 KPI 計算
負責內容分類、KPI 計算、聚合統計
"""

import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from utils.config import DB_PATH


# ==================== 常數定義 ====================

# 時段分類
TIME_SLOTS = {
    'morning': (6, 11),      # 06:00-11:59
    'noon': (12, 14),        # 12:00-14:59
    'afternoon': (15, 17),   # 15:00-17:59
    'evening': (18, 22),     # 18:00-22:59
    'night': (23, 5),        # 23:00-05:59
}

# 文字長度分級
LENGTH_TIERS = {
    'short': (0, 100),       # 0-100 字
    'medium': (101, 300),    # 101-300 字
    'long': (301, float('inf')),  # 300+ 字
}

# 主題關鍵字對照 - 貼文形式/活動類型 (Format Type)
FORMAT_TYPE_KEYWORDS = {
    'event': ['影展', '講座', '論壇', '工作坊', '分享會', '座談', '活動報名', '歡迎參加'],
    'press': ['記者會', '媒體', '採訪', '新聞稿'],
    'statement': ['聲明', '發言', '立場', '呼籲', '強調', '我們認為'],
    'opinion': ['觀點', '評論', '分析', '看法', '時事'],
    'op_ed': ['投書', '專欄', '刊登', '媒體投書'],
    'report': ['報告', '發布', '研究', '調查', '數據', '出爐'],
    'booth': ['擺攤', '市集', '現場', '來找我們'],
    'edu': ['懶人包', 'Podcast', '科普', 'Q&A', '知識', '解說', '你知道嗎', '一次看懂'],
    'action': ['連署', '捐款', '志工', '行動', '參與', '支持我們', '一起'],
}

# 議題關鍵字對照 - 政策議題 (Issue Topic)
ISSUE_TOPIC_KEYWORDS = {
    'nuclear': ['核電', '核能', '核四', '核廢', '核安', '輻射'],
    'climate': ['氣候', '暖化', '碳排', 'COP', '極端天氣', '氣候變遷'],
    'net_zero': ['淨零', '碳中和', '2050', '淨零轉型', '減碳'],
    'industry': ['產業', '企業', 'ESG', '永續', '供應鏈', '碳盤查'],
    'renewable': ['光電', '風電', '再生能源', '綠電', '太陽能', '離岸風電', '屋頂', '公民電廠'],
    'other': ['勞動', '環評', '空污', '水資源', '生態'],
}

# CTA 關鍵字
CTA_KEYWORDS = {
    'learn_more': ['了解更多', '看更多', '詳情'],
    'sign_up': ['報名', '參加', '加入'],
    'donate': ['捐款', '支持', '贊助'],
    'share': ['分享', '轉發', '擴散'],
}


# ==================== 工具函式 ====================

def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_time_slot(hour: int) -> str:
    """根據小時判斷時段"""
    if 6 <= hour <= 11:
        return 'morning'
    elif 12 <= hour <= 14:
        return 'noon'
    elif 15 <= hour <= 17:
        return 'afternoon'
    elif 18 <= hour <= 22:
        return 'evening'
    else:
        return 'night'


def get_length_tier(length: int) -> str:
    """根據文字長度判斷分級"""
    if length <= 100:
        return 'short'
    elif length <= 300:
        return 'medium'
    else:
        return 'long'


def detect_format_type(text: str) -> Optional[str]:
    """
    偵測貼文形式/活動類型
    回傳最符合的 format_type
    """
    if not text:
        return None
    
    type_scores = {}
    
    for format_type, keywords in FORMAT_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            type_scores[format_type] = score
    
    if not type_scores:
        return None
    
    # 回傳分數最高的類型
    return max(type_scores.items(), key=lambda x: x[1])[0]


def detect_issue_topic(text: str) -> Optional[str]:
    """
    偵測政策議題
    回傳最符合的 issue_topic
    """
    if not text:
        return None
    
    topic_scores = {}
    
    for topic, keywords in ISSUE_TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            topic_scores[topic] = score
    
    if not topic_scores:
        return None
    
    # 回傳分數最高的議題
    return max(topic_scores.items(), key=lambda x: x[1])[0]


def detect_cta(text: str) -> Tuple[bool, Optional[str]]:
    """
    偵測是否含有 CTA 以及 CTA 類型
    """
    if not text:
        return False, None
    
    text_lower = text.lower()
    
    for cta_type, keywords in CTA_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return True, cta_type
    
    return False, None


def detect_media_type(message: str, permalink: str) -> str:
    """
    根據內容判斷媒體類型
    注意：這是簡化版，實際應從 API 取得
    """
    if not message:
        return 'link'
    
    # 簡易判斷 (實際應從貼文 attachments 取得)
    if 'video' in permalink.lower():
        return 'video'
    elif 'photo' in permalink.lower():
        return 'image'
    else:
        return 'text'


# ==================== 分類處理 ====================

def classify_post(post_id: str, message: str, created_time: str, permalink: str) -> Dict:
    """
    對單一貼文進行分類
    使用雙維度分類：format_type（貼文形式）和 issue_topic（議題）
    """
    # 解析時間 (UTC)
    try:
        dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        dt = datetime.now()
    
    # 轉換為 GMT+8 台灣時區
    from datetime import timedelta
    dt_gmt8 = dt + timedelta(hours=8)
    
    # 文字特徵
    message_length = len(message) if message else 0
    word_count = len(message.split()) if message else 0
    
    # Hashtag 檢測
    hashtags = re.findall(r'#\\w+', message) if message else []
    has_hashtag = len(hashtags) > 0
    hashtag_count = len(hashtags)
    
    # 連結檢測
    has_link = bool(re.search(r'https?://', message)) if message else False
    
    # 新雙維度分類
    format_type = detect_format_type(message)
    issue_topic = detect_issue_topic(message)
    
    # CTA 偵測
    has_cta, cta_type = detect_cta(message)
    
    # 媒體類型
    media_type = detect_media_type(message, permalink)
    
    # 使用 GMT+8 時間計算時間相關欄位
    return {
        'post_id': post_id,
        'media_type': media_type,
        'has_link': has_link,
        'has_hashtag': has_hashtag,
        'hashtag_count': hashtag_count,
        'message_length': message_length,
        'message_length_tier': get_length_tier(message_length),
        'word_count': word_count,
        'format_type': format_type,      # 新：貼文形式
        'issue_topic': issue_topic,       # 新：政策議題
        'topic_primary': format_type,     # 保留舊欄位相容性
        'topic_secondary': issue_topic,   # 保留舊欄位相容性
        'has_cta': has_cta,
        'cta_type': cta_type,
        'hour_of_day': dt_gmt8.hour,      # 使用 GMT+8 小時
        'day_of_week': dt_gmt8.weekday(), # 使用 GMT+8 星期
        'week_of_year': dt_gmt8.isocalendar()[1],
        'month': dt_gmt8.month,
        'is_weekend': dt_gmt8.weekday() >= 5,  # 使用 GMT+8
        'time_slot': get_time_slot(dt_gmt8.hour),  # 使用 GMT+8 小時
    }


def process_all_posts_classification(conn):
    """
    處理所有未分類的貼文
    """
    cursor = conn.cursor()
    
    # 找出未分類的貼文
    cursor.execute("""
        SELECT p.post_id, p.message, p.created_time, p.permalink_url
        FROM posts p
        LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
        WHERE pc.post_id IS NULL
    """)
    
    unclassified = cursor.fetchall()
    print(f"找到 {len(unclassified)} 則未分類貼文")
    
    if not unclassified:
        return 0
    
    # 批次分類
    classified_count = 0
    for row in unclassified:
        classification = classify_post(
            row['post_id'],
            row['message'],
            row['created_time'],
            row['permalink_url']
        )
        
        # 插入分類資料
        cursor.execute("""
            INSERT OR REPLACE INTO posts_classification (
                post_id, media_type, has_link, has_hashtag, hashtag_count,
                message_length, message_length_tier, word_count,
                format_type, issue_topic, topic_primary, topic_secondary,
                has_cta, cta_type,
                hour_of_day, day_of_week, week_of_year, month, is_weekend, time_slot,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            classification['post_id'],
            classification['media_type'],
            classification['has_link'],
            classification['has_hashtag'],
            classification['hashtag_count'],
            classification['message_length'],
            classification['message_length_tier'],
            classification['word_count'],
            classification['format_type'],
            classification['issue_topic'],
            classification['topic_primary'],
            classification['topic_secondary'],
            classification['has_cta'],
            classification['cta_type'],
            classification['hour_of_day'],
            classification['day_of_week'],
            classification['week_of_year'],
            classification['month'],
            classification['is_weekend'],
            classification['time_slot'],
        ))
        classified_count += 1
    
    conn.commit()
    print(f"✓ 已分類 {classified_count} 則貼文")
    return classified_count


# ==================== KPI 計算 ====================

def calculate_post_kpis(conn, snapshot_date: str = None):
    """
    計算所有貼文的 KPI 並儲存
    """
    if snapshot_date is None:
        snapshot_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor = conn.cursor()
    
    # 取得每個貼文的最佳洞察數據（使用各指標的最大值，避免 API 回傳不完整數據）
    # 因為 Facebook API 有時會回傳 0 值，我們取各指標歷史最大值
    cursor.execute("""
        SELECT
            post_id,
            MAX(likes_count) as likes_count,
            MAX(comments_count) as comments_count,
            MAX(shares_count) as shares_count,
            MAX(post_clicks) as post_clicks,
            MAX(post_impressions_unique) as post_impressions_unique,
            MAX(post_reactions_like_total + post_reactions_love_total +
                post_reactions_wow_total + post_reactions_haha_total +
                post_reactions_sorry_total + post_reactions_anger_total) as total_reactions
        FROM post_insights_snapshots
        GROUP BY post_id
    """)
    
    posts_data = cursor.fetchall()
    print(f"計算 {len(posts_data)} 則貼文的 KPI")
    
    # 計算頁面平均值作為基準
    cursor.execute("""
        SELECT 
            AVG(
                CASE WHEN post_impressions_unique > 0 
                THEN (likes_count + comments_count + shares_count) * 100.0 / post_impressions_unique 
                ELSE 0 END
            ) as avg_er_7d
        FROM post_insights_snapshots
        WHERE fetch_date >= date('now', '-7 days')
    """)
    avg_7d = cursor.fetchone()['avg_er_7d'] or 0
    
    cursor.execute("""
        SELECT 
            AVG(
                CASE WHEN post_impressions_unique > 0 
                THEN (likes_count + comments_count + shares_count) * 100.0 / post_impressions_unique 
                ELSE 0 END
            ) as avg_er_30d
        FROM post_insights_snapshots
        WHERE fetch_date >= date('now', '-30 days')
    """)
    avg_30d = cursor.fetchone()['avg_er_30d'] or 0
    
    # 計算各貼文 KPI
    kpi_count = 0
    all_ers = []
    
    for row in posts_data:
        reach = row['post_impressions_unique'] or 0
        reactions = row['total_reactions'] or 0
        comments = row['comments_count'] or 0
        shares = row['shares_count'] or 0
        clicks = row['post_clicks'] or 0
        likes = row['likes_count'] or 0

        # 計算 KPI (移除依賴已棄用欄位的指標)
        engagement_rate = (reactions + comments + shares) / reach * 100 if reach > 0 else 0
        ctr = clicks / reach * 100 if reach > 0 else 0  # 改用 reach 而非 impressions
        share_rate = shares / reach * 100 if reach > 0 else 0
        comment_rate = comments / reach * 100 if reach > 0 else 0
        organic_ratio = 0  # 無法計算 (已無 organic/paid 數據)
        virality_score = shares / reactions if reactions > 0 else 0
        discussion_depth = comments / (likes + 1)
        
        # 相對表現
        vs_7d = engagement_rate / avg_7d if avg_7d > 0 else 0
        vs_30d = engagement_rate / avg_30d if avg_30d > 0 else 0
        
        all_ers.append((row['post_id'], engagement_rate))
        
        # 暫存 (稍後計算 percentile 和 tier)
    
    # 計算 percentile 和 tier
    if all_ers:
        sorted_ers = sorted(all_ers, key=lambda x: x[1])
        n = len(sorted_ers)
        
        # 計算 percentile thresholds
        p25 = sorted_ers[int(n * 0.25)][1] if n > 0 else 0
        p75 = sorted_ers[int(n * 0.75)][1] if n > 0 else 0
        p95 = sorted_ers[int(n * 0.95)][1] if n > 0 else 0
        
        for row in posts_data:
            reach = row['post_impressions_unique'] or 0
            reactions = row['total_reactions'] or 0
            comments = row['comments_count'] or 0
            shares = row['shares_count'] or 0
            clicks = row['post_clicks'] or 0
            likes = row['likes_count'] or 0

            # 計算 KPI
            er = (reactions + comments + shares) / reach * 100 if reach > 0 else 0
            ctr = clicks / reach * 100 if reach > 0 else 0
            share_rate = shares / reach * 100 if reach > 0 else 0
            comment_rate = comments / reach * 100 if reach > 0 else 0
            organic_ratio = 0  # 無法計算 (已無 organic/paid 數據)
            virality_score = shares / reactions if reactions > 0 else 0
            discussion_depth = comments / (likes + 1)
            
            vs_7d = er / avg_7d if avg_7d > 0 else 0
            vs_30d = er / avg_30d if avg_30d > 0 else 0
            
            # 計算 percentile rank
            rank = sum(1 for _, e in sorted_ers if e <= er) / n * 100 if n > 0 else 0
            
            # 判斷 tier
            if er >= p95:
                tier = 'viral'
            elif er >= p75:
                tier = 'high'
            elif er >= p25:
                tier = 'average'
            else:
                tier = 'low'
            
            # 儲存 KPI
            cursor.execute("""
                INSERT OR REPLACE INTO posts_performance (
                    post_id, snapshot_date,
                    engagement_rate, click_through_rate, share_rate, comment_rate,
                    vs_page_avg_7d, vs_page_avg_30d, performance_tier, percentile_rank,
                    organic_ratio, virality_score, discussion_depth
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['post_id'], snapshot_date,
                round(er, 4), round(ctr, 4), round(share_rate, 4), round(comment_rate, 4),
                round(vs_7d, 4), round(vs_30d, 4), tier, round(rank, 2),
                round(organic_ratio, 4), round(virality_score, 4), round(discussion_depth, 4)
            ))
            kpi_count += 1
    
    conn.commit()
    print(f"✓ 已計算 {kpi_count} 則貼文的 KPI")
    return kpi_count


# ==================== 基準計算 ====================

def update_benchmarks(conn):
    """
    更新各維度的基準值
    """
    cursor = conn.cursor()
    
    # 頁面整體基準
    for period, days in [('rolling_7d', 7), ('rolling_30d', 30), ('all_time', 9999)]:
        cursor.execute(f"""
            SELECT 
                AVG(engagement_rate) as avg_er,
                AVG(click_through_rate) as avg_ctr,
                COUNT(*) as sample_size
            FROM posts_performance
            WHERE snapshot_date >= date('now', '-{days} days')
        """)
        row = cursor.fetchone()
        
        if row and row['sample_size'] > 0:
            cursor.execute("""
                INSERT OR REPLACE INTO benchmarks (
                    benchmark_type, benchmark_key, period,
                    avg_engagement_rate, sample_size, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, ('page', 'overall', period, row['avg_er'], row['sample_size']))
    
    # 依主題基準
    cursor.execute("""
        SELECT DISTINCT topic_primary FROM posts_classification WHERE topic_primary IS NOT NULL
    """)
    topics = [r['topic_primary'] for r in cursor.fetchall()]
    
    for topic in topics:
        for period, days in [('rolling_30d', 30)]:
            cursor.execute(f"""
                SELECT 
                    AVG(pp.engagement_rate) as avg_er,
                    COUNT(*) as sample_size
                FROM posts_performance pp
                JOIN posts_classification pc ON pp.post_id = pc.post_id
                WHERE pc.topic_primary = ?
                AND pp.snapshot_date >= date('now', '-{days} days')
            """, (topic,))
            row = cursor.fetchone()
            
            if row and row['sample_size'] > 0:
                cursor.execute("""
                    INSERT OR REPLACE INTO benchmarks (
                        benchmark_type, benchmark_key, period,
                        avg_engagement_rate, sample_size, updated_at
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, ('topic', topic, period, row['avg_er'], row['sample_size']))
    
    # 依時段基準
    for time_slot in ['morning', 'noon', 'afternoon', 'evening', 'night']:
        cursor.execute(f"""
            SELECT 
                AVG(pp.engagement_rate) as avg_er,
                COUNT(*) as sample_size
            FROM posts_performance pp
            JOIN posts_classification pc ON pp.post_id = pc.post_id
            WHERE pc.time_slot = ?
            AND pp.snapshot_date >= date('now', '-30 days')
        """, (time_slot,))
        row = cursor.fetchone()
        
        if row and row['sample_size'] > 0:
            cursor.execute("""
                INSERT OR REPLACE INTO benchmarks (
                    benchmark_type, benchmark_key, period,
                    avg_engagement_rate, sample_size, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, ('time_slot', time_slot, 'rolling_30d', row['avg_er'], row['sample_size']))
    
    conn.commit()
    print("✓ 已更新基準值")


# ==================== 主程式 ====================

def run_analytics_pipeline():
    """
    執行完整分析流程
    """
    print("=== 開始數據分析處理 ===\n")
    
    conn = get_connection()
    
    try:
        # Step 1: 分類貼文
        print("Step 1: 內容分類")
        process_all_posts_classification(conn)
        
        # Step 2: 計算 KPI
        print("\nStep 2: KPI 計算")
        calculate_post_kpis(conn)
        
        # Step 3: 更新基準
        print("\nStep 3: 基準更新")
        update_benchmarks(conn)
        
        print("\n✓ 分析處理完成")
        
    except Exception as e:
        print(f"✗ 處理失敗: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    run_analytics_pipeline()
