"""
歷史貼文 Insights 補收腳本
嘗試補收所有貼文的 insights（不限 30 天內）
"""

import time
import requests
import sqlite3
from datetime import datetime
from utils.config import DB_PATH, FACEBOOK_CONFIG
from utils import db_utils


def backfill_post_insights(limit=None, skip_existing=True):
    """
    補收歷史貼文的 insights
    
    Args:
        limit: 限制處理數量（None = 全部）
        skip_existing: 是否跳過已有 snapshot 的貼文
    """
    print("=" * 60)
    print("歷史貼文 Insights 補收")
    print("=" * 60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 找出需要補收的貼文
    if skip_existing:
        cursor.execute("""
            SELECT p.post_id, p.created_time,
                   julianday('now') - julianday(date(substr(p.created_time, 1, 10))) as days_ago
            FROM posts p
            WHERE p.post_id NOT IN (SELECT DISTINCT post_id FROM post_insights_snapshots)
            ORDER BY p.created_time DESC
        """)
    else:
        cursor.execute("""
            SELECT p.post_id, p.created_time,
                   julianday('now') - julianday(date(substr(p.created_time, 1, 10))) as days_ago
            FROM posts p
            ORDER BY p.created_time DESC
        """)
    
    posts = cursor.fetchall()
    
    if limit:
        posts = posts[:limit]
    
    print(f"\n找到 {len(posts)} 篇貼文需要補收 insights")
    
    # Insights 指標
    POST_INSIGHTS_METRICS = [
        'post_impressions_unique',
        'post_clicks',
        'post_reactions_like_total',
        'post_reactions_love_total',
        'post_reactions_wow_total',
        'post_reactions_haha_total',
        'post_reactions_sorry_total',
        'post_reactions_anger_total',
    ]
    
    success_count = 0
    failed_count = 0
    fetch_date = datetime.now().strftime('%Y-%m-%d')
    
    for i, post in enumerate(posts, 1):
        post_id = post['post_id']
        days_ago = int(post['days_ago'])
        
        if i % 25 == 0 or i == 1:
            print(f"\n進度: {i}/{len(posts)} ({success_count} 成功, {failed_count} 失敗)")
        
        insights = {}
        basic_stats = {}
        
        try:
            # 取得 insights
            base_url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{post_id}/insights"
            params = {
                'access_token': FACEBOOK_CONFIG['access_token'],
                'metric': ','.join(POST_INSIGHTS_METRICS)
            }
            
            response = requests.get(base_url, params=params, timeout=15)
            
            if response.ok:
                data = response.json().get('data', [])
                for metric in data:
                    name = metric.get('name')
                    values = metric.get('values', [{}])
                    insights[name] = values[0].get('value', 0) if values else 0
            else:
                # API 可能不提供太舊的數據
                error = response.json().get('error', {})
                if 'Unsupported get request' in str(error) or response.status_code == 400:
                    # 這是正常的限制，跳過
                    pass
                else:
                    print(f"  ⚠ {post_id[-15:]} ({days_ago}天前): {error.get('message', 'Unknown error')[:50]}")
            
            # 取得基本統計
            base_url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{post_id}"
            
            # Reactions
            resp = requests.get(f"{base_url}/reactions", params={
                'access_token': FACEBOOK_CONFIG['access_token'],
                'summary': 'total_count',
                'limit': 0
            }, timeout=10)
            if resp.ok:
                basic_stats['likes_count'] = resp.json().get('summary', {}).get('total_count', 0)
            
            # Comments
            resp = requests.get(f"{base_url}/comments", params={
                'access_token': FACEBOOK_CONFIG['access_token'],
                'summary': 'total_count',
                'limit': 0
            }, timeout=10)
            if resp.ok:
                basic_stats['comments_count'] = resp.json().get('summary', {}).get('total_count', 0)
            
            # Shares
            resp = requests.get(base_url, params={
                'access_token': FACEBOOK_CONFIG['access_token'],
                'fields': 'shares'
            }, timeout=10)
            if resp.ok:
                basic_stats['shares_count'] = resp.json().get('shares', {}).get('count', 0)
            
            # 如果有任何數據，儲存
            if insights or basic_stats:
                if db_utils.upsert_post_insights(conn, post_id, fetch_date, insights, basic_stats):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            failed_count += 1
            if 'timeout' not in str(e).lower():
                print(f"  ✗ {post_id[-15:]}: {str(e)[:50]}")
        
        time.sleep(0.2)  # API 速率限制
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"補收完成:")
    print(f"  成功: {success_count}")
    print(f"  失敗: {failed_count}")
    print("=" * 60)
    
    return success_count, failed_count


if __name__ == '__main__':
    import sys
    
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    
    backfill_post_insights(limit=limit)
