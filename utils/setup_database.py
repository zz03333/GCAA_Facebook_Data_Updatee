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
