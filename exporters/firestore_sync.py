"""
Firestore Sync Module
Syncs analytics data from SQLite to Firestore for real-time dashboard updates.
"""

import os
import json
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase Admin SDK not installed. Run: pip install firebase-admin")


def get_connection():
    """Get SQLite database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'engagement_data.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_firestore() -> Optional[Any]:
    """
    Initialize Firestore using service account from environment variable

    Returns:
        Firestore client or None if initialization fails
    """
    if not FIREBASE_AVAILABLE:
        print("✗ Firebase Admin SDK not available")
        return None

    try:
        # Check if already initialized
        try:
            app = firebase_admin.get_app()
            print("✓ Firebase already initialized")
            return firestore.client()
        except ValueError:
            pass

        # Get credentials from environment variable
        credentials_json = os.environ.get('GCP_SA_CREDENTIALS')
        credentials_base64 = os.environ.get('GCP_SA_CREDENTIALS_BASE64')

        if credentials_base64:
            # Decode base64 if provided
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
        elif not credentials_json:
            print("✗ No GCP_SA_CREDENTIALS or GCP_SA_CREDENTIALS_BASE64 found in environment")

            # Try loading from fb-dashboard service account file as fallback
            fallback_path = os.path.join(
                os.path.dirname(__file__),
                'fb-dashboard',
                'esg-reports-collection-9661012923ed.json'
            )
            if os.path.exists(fallback_path):
                print(f"  Using fallback credentials: {fallback_path}")
                cred = credentials.Certificate(fallback_path)
                firebase_admin.initialize_app(cred)
                return firestore.client()
            else:
                print("  Fallback credentials not found")
                return None

        # Parse JSON credentials
        credentials_dict = json.loads(credentials_json)
        cred = credentials.Certificate(credentials_dict)

        # Initialize Firebase Admin
        firebase_admin.initialize_app(cred)

        print("✓ Firestore initialized successfully")
        return firestore.client()

    except Exception as e:
        print(f"✗ Firestore initialization failed: {e}")
        return None


def sync_posts_to_firestore(db_conn: sqlite3.Connection, firestore_db: Any) -> int:
    """
    Sync posts from SQLite to Firestore

    Uses batch writes (max 500 documents per batch) for efficiency.

    Args:
        db_conn: SQLite connection
        firestore_db: Firestore client

    Returns:
        Number of posts synced
    """
    cursor = db_conn.cursor()

    # Get all posts with latest insights snapshot and analytics
    cursor.execute("""
        SELECT
            p.post_id,
            p.message,
            p.created_time,
            p.permalink_url,
            p.type as post_type,
            i.likes_count,
            i.comments_count,
            i.shares_count,
            i.post_impressions_unique as reach,
            i.post_clicks,
            i.post_video_views,
            i.post_reactions_like_total,
            i.post_reactions_love_total,
            i.post_reactions_wow_total,
            i.post_reactions_haha_total,
            i.post_reactions_sorry_total,
            i.post_reactions_anger_total,
            pp.engagement_rate,
            pp.performance_tier,
            pp.percentile_rank,
            pp.share_rate,
            pp.click_through_rate,
            pc.format_type,
            pc.issue_topic,
            pc.media_type,
            pc.time_slot,
            pc.hour_of_day,
            pc.day_of_week,
            pc.is_weekend
        FROM posts p
        LEFT JOIN post_insights_snapshots i ON p.post_id = i.post_id
        LEFT JOIN posts_performance pp ON p.post_id = pp.post_id
        LEFT JOIN posts_classification pc ON p.post_id = pc.post_id
        WHERE i.fetch_date = (
            SELECT MAX(fetch_date)
            FROM post_insights_snapshots
            WHERE post_id = p.post_id
        )
        OR i.post_id IS NULL
        ORDER BY p.created_time DESC
    """)

    posts = cursor.fetchall()

    if not posts:
        print("⚠️  No posts found in database")
        return 0

    print(f"\nSyncing {len(posts)} posts to Firestore...")

    # Batch write (max 500 per batch)
    batch = firestore_db.batch()
    count = 0
    batch_count = 0

    for post in posts:
        post_id = post['post_id']
        doc_ref = firestore_db.collection('posts').document(post_id)

        # Convert Row to dict with safe defaults
        post_data = {
            'postId': post_id,
            'content': post['message'] or '',
            'contentPreview': (post['message'] or '')[:80] + '...' if post['message'] and len(post['message']) > 80 else (post['message'] or ''),
            'publishedAt': post['created_time'] or '',
            'permalink': post['permalink_url'] or '',
            'postType': post['post_type'] or 'status',

            'metrics': {
                'reach': int(post['reach'] or 0),
                'likes': int(post['likes_count'] or 0),
                'comments': int(post['comments_count'] or 0),
                'shares': int(post['shares_count'] or 0),
                'clicks': int(post['post_clicks'] or 0),
                'videoViews': int(post['post_video_views'] or 0),
                'reactions': {
                    'like': int(post['post_reactions_like_total'] or 0),
                    'love': int(post['post_reactions_love_total'] or 0),
                    'wow': int(post['post_reactions_wow_total'] or 0),
                    'haha': int(post['post_reactions_haha_total'] or 0),
                    'sad': int(post['post_reactions_sorry_total'] or 0),
                    'angry': int(post['post_reactions_anger_total'] or 0),
                }
            },

            'computed': {
                'engagementRate': round(float(post['engagement_rate'] or 0), 2),
                'shareRate': round(float(post['share_rate'] or 0), 2),
                'clickRate': round(float(post['click_through_rate'] or 0), 2),
                'performanceTier': post['performance_tier'] or 'average',
                'percentileRank': round(float(post['percentile_rank'] or 0), 1),
                'totalEngagement': int((post['likes_count'] or 0) + (post['comments_count'] or 0) + (post['shares_count'] or 0))
            },

            'classification': {
                'actionType': post['format_type'] or '',
                'topic': post['issue_topic'] or '',
                'mediaType': post['media_type'] or 'text',
                'timeSlot': post['time_slot'] or '',
                'hourOfDay': int(post['hour_of_day'] or 0),
                'dayOfWeek': int(post['day_of_week'] or 0),
                'isWeekend': bool(post['is_weekend'])
            },

            'updatedAt': firestore.SERVER_TIMESTAMP
        }

        batch.set(doc_ref, post_data)
        count += 1

        # Commit batch every 500 documents
        if count % 500 == 0:
            batch.commit()
            batch_count += 1
            print(f"  Committed batch {batch_count} ({count} posts)")
            batch = firestore_db.batch()

    # Commit remaining documents
    if count % 500 != 0:
        batch.commit()
        batch_count += 1
        print(f"  Committed final batch {batch_count} ({count} posts)")

    print(f"✓ Successfully synced {count} posts to Firestore")
    return count


def sync_daily_metrics_to_firestore(db_conn: sqlite3.Connection, firestore_db: Any) -> int:
    """
    Sync daily aggregated metrics to Firestore

    Args:
        db_conn: SQLite connection
        firestore_db: Firestore client

    Returns:
        Number of daily records synced
    """
    cursor = db_conn.cursor()

    # Calculate daily metrics from posts
    cursor.execute("""
        SELECT
            DATE(p.created_time) as date,
            COUNT(*) as post_count,
            SUM(i.post_impressions_unique) as total_reach,
            SUM(i.likes_count + i.comments_count + i.shares_count) as total_engagement,
            AVG(pp.engagement_rate) as avg_engagement_rate,
            SUM(i.shares_count) as total_shares,
            SUM(i.post_clicks) as total_clicks
        FROM posts p
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE i.fetch_date = (
            SELECT MAX(fetch_date)
            FROM post_insights_snapshots
            WHERE post_id = p.post_id
        )
        GROUP BY DATE(p.created_time)
        ORDER BY date DESC
        LIMIT 365
    """)

    daily_records = cursor.fetchall()

    if not daily_records:
        print("⚠️  No daily metrics to sync")
        return 0

    print(f"\nSyncing {len(daily_records)} daily metric records...")

    batch = firestore_db.batch()
    count = 0

    for record in daily_records:
        date_str = record['date']
        doc_ref = firestore_db.collection('dailyMetrics').document(date_str)

        daily_data = {
            'date': date_str,
            'postCount': int(record['post_count'] or 0),
            'totalReach': int(record['total_reach'] or 0),
            'totalEngagement': int(record['total_engagement'] or 0),
            'avgEngagementRate': round(float(record['avg_engagement_rate'] or 0), 2),
            'totalShares': int(record['total_shares'] or 0),
            'totalClicks': int(record['total_clicks'] or 0),
            'updatedAt': firestore.SERVER_TIMESTAMP
        }

        batch.set(doc_ref, daily_data)
        count += 1

        if count % 500 == 0:
            batch.commit()
            batch = firestore_db.batch()

    if count % 500 != 0:
        batch.commit()

    print(f"✓ Successfully synced {count} daily metric records")
    return count


def sync_aggregates_to_firestore(db_conn: sqlite3.Connection, firestore_db: Any) -> int:
    """
    Sync pre-computed aggregates (action types, topics, time slots) to Firestore

    Args:
        db_conn: SQLite connection
        firestore_db: Firestore client

    Returns:
        Number of aggregate records synced
    """
    cursor = db_conn.cursor()
    total_count = 0

    # 1. By Action Type
    cursor.execute("""
        SELECT
            pc.format_type as name,
            COUNT(*) as count,
            AVG(pp.engagement_rate) as avg_er,
            AVG(i.post_impressions_unique) as avg_reach
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        JOIN post_insights_snapshots i ON pc.post_id = i.post_id
        WHERE pc.format_type IS NOT NULL AND pc.format_type != ''
        AND i.fetch_date = (
            SELECT MAX(fetch_date)
            FROM post_insights_snapshots
            WHERE post_id = pc.post_id
        )
        GROUP BY pc.format_type
        ORDER BY count DESC
    """)

    action_types = cursor.fetchall()
    print(f"\nSyncing {len(action_types)} action type aggregates...")

    for record in action_types:
        doc_ref = firestore_db.collection('aggregates').document('byActionType').collection('data').document(record['name'])
        doc_ref.set({
            'name': record['name'],
            'count': int(record['count']),
            'avgER': round(float(record['avg_er'] or 0), 2),
            'avgReach': int(record['avg_reach'] or 0),
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        total_count += 1

    # 2. By Topic
    cursor.execute("""
        SELECT
            pc.issue_topic as name,
            COUNT(*) as count,
            AVG(pp.engagement_rate) as avg_er,
            AVG(i.post_impressions_unique) as avg_reach
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        JOIN post_insights_snapshots i ON pc.post_id = i.post_id
        WHERE pc.issue_topic IS NOT NULL AND pc.issue_topic != ''
        AND i.fetch_date = (
            SELECT MAX(fetch_date)
            FROM post_insights_snapshots
            WHERE post_id = pc.post_id
        )
        GROUP BY pc.issue_topic
        ORDER BY count DESC
    """)

    topics = cursor.fetchall()
    print(f"Syncing {len(topics)} topic aggregates...")

    for record in topics:
        doc_ref = firestore_db.collection('aggregates').document('byTopic').collection('data').document(record['name'])
        doc_ref.set({
            'name': record['name'],
            'count': int(record['count']),
            'avgER': round(float(record['avg_er'] or 0), 2),
            'avgReach': int(record['avg_reach'] or 0),
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        total_count += 1

    # 3. By Hour
    cursor.execute("""
        SELECT
            pc.hour_of_day as hour,
            COUNT(*) as count,
            AVG(pp.engagement_rate) as avg_er
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        WHERE pc.hour_of_day IS NOT NULL
        GROUP BY pc.hour_of_day
        ORDER BY hour
    """)

    hours = cursor.fetchall()
    print(f"Syncing {len(hours)} hourly performance aggregates...")

    for record in hours:
        hour = int(record['hour'])
        doc_ref = firestore_db.collection('aggregates').document('hourlyPerformance').collection('data').document(f'{hour:02d}')
        doc_ref.set({
            'hour': hour,
            'label': f'{hour:02d}:00',
            'count': int(record['count']),
            'avgER': round(float(record['avg_er'] or 0), 2),
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        total_count += 1

    # 4. Heatmap (weekday × hour)
    cursor.execute("""
        SELECT
            pc.day_of_week as weekday,
            pc.hour_of_day as hour,
            COUNT(*) as count,
            AVG(pp.engagement_rate) as avg_er
        FROM posts_classification pc
        JOIN posts_performance pp ON pc.post_id = pp.post_id
        WHERE pc.day_of_week IS NOT NULL AND pc.hour_of_day IS NOT NULL
        GROUP BY pc.day_of_week, pc.hour_of_day
    """)

    heatmap_cells = cursor.fetchall()
    print(f"Syncing {len(heatmap_cells)} heatmap cells...")

    weekday_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']

    for record in heatmap_cells:
        weekday = int(record['weekday'])
        hour = int(record['hour'])
        doc_id = f'{weekday}-{hour:02d}'

        doc_ref = firestore_db.collection('aggregates').document('heatmap').collection('data').document(doc_id)
        doc_ref.set({
            'weekday': weekday,
            'weekdayName': weekday_names[weekday] if 0 <= weekday < 7 else '',
            'hour': hour,
            'count': int(record['count']),
            'avgER': round(float(record['avg_er'] or 0), 2),
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        total_count += 1

    print(f"✓ Successfully synced {total_count} aggregate records")
    return total_count


def sync_metadata_to_firestore(firestore_db: Any, posts_count: int) -> None:
    """
    Update metadata collection with sync status and KPIs

    Args:
        firestore_db: Firestore client
        posts_count: Number of posts synced
    """
    # Last sync status
    firestore_db.collection('metadata').document('lastSync').set({
        'timestamp': firestore.SERVER_TIMESTAMP,
        'status': 'success',
        'postsCount': posts_count,
        'message': f'Successfully synced {posts_count} posts'
    })

    print("✓ Updated metadata/lastSync")


def sync_all() -> bool:
    """
    Main sync function - syncs all data from SQLite to Firestore

    Returns:
        True if successful, False otherwise
    """
    print("=" * 60)
    print("Firestore Sync Started")
    print("=" * 60)

    # Initialize Firestore
    firestore_db = init_firestore()
    if not firestore_db:
        print("✗ Cannot proceed without Firestore client")
        return False

    # Get SQLite connection
    db_conn = get_connection()

    try:
        # Sync posts (main data)
        posts_count = sync_posts_to_firestore(db_conn, firestore_db)

        # Sync daily metrics
        daily_count = sync_daily_metrics_to_firestore(db_conn, firestore_db)

        # Sync aggregates
        aggregates_count = sync_aggregates_to_firestore(db_conn, firestore_db)

        # Update metadata
        sync_metadata_to_firestore(firestore_db, posts_count)

        print("\n" + "=" * 60)
        print("Firestore Sync Completed Successfully")
        print("=" * 60)
        print(f"Posts synced: {posts_count}")
        print(f"Daily metrics synced: {daily_count}")
        print(f"Aggregates synced: {aggregates_count}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Sync failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db_conn.close()


if __name__ == '__main__':
    # Run sync when executed directly
    success = sync_all()
    exit(0 if success else 1)
