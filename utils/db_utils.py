# db_utils.py
import sqlite3
from utils.config import DB_PATH

def get_db_connection():
    try:
        # Ensure data directory exists
        import os
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Initialize database schema if needed
        from utils.setup_database import create_tables
        create_tables(conn)

        return conn
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

def upsert_page_info(conn, page_id, page_name):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pages (page_id, page_name, last_scraped_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(page_id) DO UPDATE SET
            page_name = excluded.page_name,
            last_scraped_at = excluded.last_scraped_at;
        """, (page_id, page_name))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error upserting page info: {e}")

def upsert_page_daily_metrics(conn, page_id, date, metrics_data):
    try:
        cursor = conn.cursor()
        
        # Prepare columns and values dynamically based on Schema
        # We need to extract specific keys from metrics_data
        
        columns = [
            'page_id', 'date', 'fan_count', 'followers_count',
            'page_impressions_unique', 'page_post_engagements', 'page_video_views',
            'reactions_like', 'reactions_love', 'reactions_wow',
            'reactions_haha', 'reactions_sorry', 'reactions_anger', 'reactions_total'
        ]
        
        values = [
            page_id,
            date,
            metrics_data.get('fan_count'),
            metrics_data.get('followers_count'),
            metrics_data.get('page_impressions_unique'),
            metrics_data.get('page_post_engagements'),
            metrics_data.get('page_video_views'),
            metrics_data.get('reactions_like'),
            metrics_data.get('reactions_love'),
            metrics_data.get('reactions_wow'),
            metrics_data.get('reactions_haha'),
            metrics_data.get('reactions_sorry'),
            metrics_data.get('reactions_anger'),
            metrics_data.get('reactions_total')
        ]
        
        placeholders = ', '.join(['?'] * len(columns))
        columns_str = ', '.join(columns)
        
        update_clause = ', '.join([f"{col}=excluded.{col}" for col in columns if col not in ('page_id', 'date')])
        
        sql = f"""
            INSERT INTO page_daily_metrics ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT(page_id, date) DO UPDATE SET
            {update_clause};
        """
        
        cursor.execute(sql, values)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error upserting page metrics: {e}")
        return False

def upsert_post(conn, post_data):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO posts (
                post_id, page_id, created_time, message, type, permalink_url
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_id) DO UPDATE SET
            message = excluded.message,
            type = excluded.type,
            permalink_url = excluded.permalink_url;
        """, (
            post_data['id'],
            post_data['page_id'],
            post_data['created_time'],
            post_data.get('message'),
            post_data.get('type'), # Might be None if not available or deprecated logic isn't used
            post_data.get('permalink_url')
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error upserting post: {e}")
        return False

def upsert_post_insights(conn, post_id, fetch_date, insights_data, basic_stats=None):
    try:
        cursor = conn.cursor()
        
        # Merge basic stats (reactions, comments, shares from post object) with insights
        if basic_stats:
            insights_data.update(basic_stats)
            
        columns = [
            'post_id', 'fetch_date',
            'likes_count', 'comments_count', 'shares_count',
            'post_clicks', 'post_impressions_unique',
            # 移除已棄用的欄位: post_impressions, post_impressions_organic, post_impressions_paid
            'post_video_views', 'post_video_views_organic', 'post_video_views_paid',
            'post_reactions_like_total', 'post_reactions_love_total',
            'post_reactions_wow_total', 'post_reactions_haha_total',
            'post_reactions_sorry_total', 'post_reactions_anger_total'
        ]
        
        # Prepare values dict with defaults
        vals = {col: insights_data.get(col, 0) for col in columns if col not in ('post_id', 'fetch_date')}
        vals['post_id'] = post_id
        vals['fetch_date'] = fetch_date
        
        # Construct SQL
        placeholders = ', '.join(['?'] * len(columns))
        columns_str = ', '.join(columns)
        
        update_clause = ', '.join([f"{col}=excluded.{col}" for col in columns if col not in ('post_id', 'fetch_date')])
        
        sql = f"""
            INSERT INTO post_insights_snapshots ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT(post_id, fetch_date) DO UPDATE SET
            {update_clause};
        """
        
        # Create tuple in correct order
        values_tuple = tuple(vals[col] for col in columns)
        
        cursor.execute(sql, values_tuple)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error upserting post insights: {e}")
        return False
