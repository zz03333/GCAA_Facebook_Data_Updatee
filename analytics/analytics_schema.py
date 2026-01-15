"""
Facebook 社群數據分析框架 - 資料庫 Schema 擴展
新增分類、表現、聚合、基準四張資料表
"""

import sqlite3
from utils.config import DB_PATH


def create_analytics_tables(conn):
    """建立分析用資料表"""
    cursor = conn.cursor()

    # 1. posts_classification - 內容分類表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts_classification (
            post_id TEXT PRIMARY KEY,
            
            -- 媒體形式 (自動判斷)
            media_type TEXT,                    -- text/image/video/link/carousel
            has_link BOOLEAN DEFAULT 0,
            has_hashtag BOOLEAN DEFAULT 0,
            hashtag_count INTEGER DEFAULT 0,
            
            -- 文字特徵
            message_length INTEGER DEFAULT 0,
            message_length_tier TEXT,           -- short/medium/long
            word_count INTEGER DEFAULT 0,
            
            -- 主題分類 (人工/NLP)
            topic_primary TEXT,                 -- 主要主題
            topic_secondary TEXT,               -- 次要主題
            campaign_id TEXT,                   -- 活動代碼 (可選)
            
            -- 內容調性
            sentiment_score FLOAT,              -- -1 到 1
            has_cta BOOLEAN DEFAULT 0,
            cta_type TEXT,                      -- learn_more/sign_up/donate/share
            
            -- 標記
            is_sponsored BOOLEAN DEFAULT 0,
            is_reshare BOOLEAN DEFAULT 0,
            
            -- 時間維度衍生欄位
            hour_of_day INTEGER,                -- 0-23
            day_of_week INTEGER,                -- 0=Mon, 6=Sun
            week_of_year INTEGER,               -- 1-52
            month INTEGER,                      -- 1-12
            is_weekend BOOLEAN DEFAULT 0,
            time_slot TEXT,                     -- morning/noon/afternoon/evening/night
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (post_id) REFERENCES posts (post_id)
        );
    """)

    # 2. posts_performance - 貼文表現快照表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            snapshot_date DATE NOT NULL,
            
            -- 核心 KPI
            engagement_rate FLOAT,              -- (reactions + comments + shares) / reach * 100
            click_through_rate FLOAT,           -- clicks / impressions * 100
            share_rate FLOAT,                   -- shares / reach * 100
            comment_rate FLOAT,                 -- comments / reach * 100
            
            -- 相對表現
            vs_page_avg_7d FLOAT,               -- vs 過去 7 天平均
            vs_page_avg_30d FLOAT,              -- vs 過去 30 天平均
            performance_tier TEXT,              -- viral/high/average/low
            percentile_rank FLOAT,              -- 0-100
            
            -- 觸及分析
            organic_ratio FLOAT,                -- organic / total impressions
            reach_efficiency FLOAT,             -- reach / fan_count (需外部提供)
            
            -- 傳播指標
            virality_score FLOAT,               -- shares / reactions
            discussion_depth FLOAT,             -- comments / (likes + 1)
            
            UNIQUE(post_id, snapshot_date),
            FOREIGN KEY (post_id) REFERENCES posts (post_id)
        );
    """)

    # 3. analytics_summary - 聚合統計表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_date DATE NOT NULL,
            granularity TEXT NOT NULL,           -- daily/weekly/monthly
            
            -- 時間維度
            time_period TEXT,                    -- 2025-W50 / 2025-12 等
            
            -- 聚合維度 (可 NULL)
            topic TEXT,
            media_type TEXT,
            time_slot TEXT,
            day_of_week TEXT,
            
            -- 統計數據
            post_count INTEGER DEFAULT 0,
            total_impressions INTEGER DEFAULT 0,
            total_reach INTEGER DEFAULT 0,
            total_reactions INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            total_shares INTEGER DEFAULT 0,
            total_clicks INTEGER DEFAULT 0,
            total_video_views INTEGER DEFAULT 0,
            
            -- 平均 KPI
            avg_engagement_rate FLOAT,
            avg_ctr FLOAT,
            avg_reach_per_post FLOAT,
            
            -- 基準對照
            vs_prev_period_pct FLOAT,            -- 較上期變化 %
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. benchmarks - 成效基準表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benchmark_type TEXT NOT NULL,        -- page/topic/media_type/time_slot
            benchmark_key TEXT NOT NULL,         -- 具體分類值
            period TEXT NOT NULL,                -- rolling_7d / rolling_30d / all_time
            
            -- 統計指標
            avg_engagement_rate FLOAT,
            median_engagement_rate FLOAT,
            p25_engagement_rate FLOAT,
            p75_engagement_rate FLOAT,
            p95_engagement_rate FLOAT,
            
            avg_reach FLOAT,
            avg_reactions FLOAT,
            avg_comments FLOAT,
            avg_shares FLOAT,
            avg_clicks FLOAT,
            
            sample_size INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(benchmark_type, benchmark_key, period)
        );
    """)

    # 建立索引以加速查詢
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_classification_topic 
        ON posts_classification(topic_primary);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_classification_media 
        ON posts_classification(media_type);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_classification_time_slot 
        ON posts_classification(time_slot);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_performance_tier 
        ON posts_performance(performance_tier);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_performance_date 
        ON posts_performance(snapshot_date);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_summary_granularity 
        ON analytics_summary(granularity, summary_date);
    """)

    conn.commit()
    print("✓ 分析資料表建立完成")


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def main():
    """主程式 - 建立分析資料表"""
    print("=== 建立分析資料表 ===\n")
    
    conn = get_connection()
    if conn:
        create_analytics_tables(conn)
        
        # 驗證表格
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n現有資料表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        print("\n✓ 完成")
    else:
        print("✗ 無法連接資料庫")


if __name__ == '__main__':
    main()
