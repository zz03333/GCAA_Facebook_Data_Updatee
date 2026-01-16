import sqlite3
import os

DB_PATH = 'engagement_data.db'

def create_connection():
    """Create a database connection to the SQLite database specified by DB_PATH."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_tables(conn):
    """Create tables in the database."""
    try:
        cursor = conn.cursor()

        # 1. pages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                page_id TEXT PRIMARY KEY,
                page_name TEXT,
                last_scraped_at DATETIME
            );
        """)

        # 2. page_daily_metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS page_daily_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id TEXT NOT NULL,
                date DATE NOT NULL,
                fan_count INTEGER,
                followers_count INTEGER,
                page_impressions_unique INTEGER,
                page_post_engagements INTEGER,
                page_video_views INTEGER,
                reactions_like INTEGER,
                reactions_love INTEGER,
                reactions_wow INTEGER,
                reactions_haha INTEGER,
                reactions_sorry INTEGER,
                reactions_anger INTEGER,
                reactions_total INTEGER,
                FOREIGN KEY (page_id) REFERENCES pages (page_id),
                UNIQUE(page_id, date)
            );
        """)

        # 3. posts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                page_id TEXT NOT NULL,
                created_time DATETIME,
                message TEXT,
                type TEXT,
                permalink_url TEXT,
                FOREIGN KEY (page_id) REFERENCES pages (page_id)
            );
        """)

        # 4. post_insights_snapshots
        # 更新日期: 2025-12-12 - 移除已棄用的 impressions 相關欄位
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_insights_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT NOT NULL,
                fetch_date DATE NOT NULL,
                likes_count INTEGER,
                comments_count INTEGER,
                shares_count INTEGER,
                post_clicks INTEGER,
                post_impressions_unique INTEGER,
                -- 已移除: post_impressions, post_impressions_organic, post_impressions_paid (已棄用)
                post_video_views INTEGER,
                post_video_views_organic INTEGER,
                post_video_views_paid INTEGER,
                post_reactions_like_total INTEGER,
                post_reactions_love_total INTEGER,
                post_reactions_wow_total INTEGER,
                post_reactions_haha_total INTEGER,
                post_reactions_sorry_total INTEGER,
                post_reactions_anger_total INTEGER,
                FOREIGN KEY (post_id) REFERENCES posts (post_id),
                UNIQUE(post_id, fetch_date)
            );
        """)

        # 5. posts_classification - 內容分類表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts_classification (
                post_id TEXT PRIMARY KEY,
                media_type TEXT,
                has_link BOOLEAN DEFAULT 0,
                has_hashtag BOOLEAN DEFAULT 0,
                hashtag_count INTEGER DEFAULT 0,
                message_length INTEGER DEFAULT 0,
                message_length_tier TEXT,
                word_count INTEGER DEFAULT 0,
                topic_primary TEXT,
                topic_secondary TEXT,
                format_type TEXT,
                issue_topic TEXT,
                campaign_id TEXT,
                sentiment_score FLOAT,
                has_cta BOOLEAN DEFAULT 0,
                cta_type TEXT,
                is_sponsored BOOLEAN DEFAULT 0,
                is_reshare BOOLEAN DEFAULT 0,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                week_of_year INTEGER,
                month INTEGER,
                is_weekend BOOLEAN DEFAULT 0,
                time_slot TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (post_id)
            );
        """)

        # 6. posts_performance - 貼文表現快照表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT NOT NULL,
                snapshot_date DATE NOT NULL,
                engagement_rate FLOAT,
                click_through_rate FLOAT,
                share_rate FLOAT,
                comment_rate FLOAT,
                vs_page_avg_7d FLOAT,
                vs_page_avg_30d FLOAT,
                performance_tier TEXT,
                percentile_rank FLOAT,
                organic_ratio FLOAT,
                reach_efficiency FLOAT,
                virality_score FLOAT,
                discussion_depth FLOAT,
                UNIQUE(post_id, snapshot_date),
                FOREIGN KEY (post_id) REFERENCES posts (post_id)
            );
        """)

        # 7. analytics_summary - 聚合統計表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_date DATE NOT NULL,
                granularity TEXT NOT NULL,
                time_period TEXT,
                topic TEXT,
                media_type TEXT,
                time_slot TEXT,
                day_of_week TEXT,
                post_count INTEGER DEFAULT 0,
                total_impressions INTEGER DEFAULT 0,
                total_reach INTEGER DEFAULT 0,
                total_reactions INTEGER DEFAULT 0,
                total_comments INTEGER DEFAULT 0,
                total_shares INTEGER DEFAULT 0,
                total_clicks INTEGER DEFAULT 0,
                total_video_views INTEGER DEFAULT 0,
                avg_engagement_rate FLOAT,
                avg_ctr FLOAT,
                avg_reach_per_post FLOAT,
                vs_prev_period_pct FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 8. benchmarks - 成效基準表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benchmark_type TEXT NOT NULL,
                benchmark_key TEXT NOT NULL,
                period TEXT NOT NULL,
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

        # Create indexes for analytics tables
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_classification_topic ON posts_classification(topic_primary);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_classification_media ON posts_classification(media_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_classification_time_slot ON posts_classification(time_slot);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_tier ON posts_performance(performance_tier);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_date ON posts_performance(snapshot_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_granularity ON analytics_summary(granularity, summary_date);")

        conn.commit()
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

def main():
    if os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} already exists. Updating schema if needed...")
    
    conn = create_connection()
    if conn:
        create_tables(conn)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
