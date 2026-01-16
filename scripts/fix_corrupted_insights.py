"""
修復 2025-12-16 批次抓取的損壞資料
問題：該批次 likes_count/comments_count/shares_count 為 0，
但 post_reactions_like_total 等有正確數值

解決方案：
1. 刪除該日期的 snapshots
2. 重新抓取 reactions/comments/shares
"""

import sqlite3
import requests
import time
from datetime import datetime
from utils.config import DB_PATH, FACEBOOK_CONFIG


def fix_corrupted_insights():
    """修復損壞的 insights 資料"""
    print("=" * 60)
    print("修復損壞的 Post Insights 資料")
    print("=" * 60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 找出有問題的資料（likes_count=0 但有 reactions 數據）
    cursor.execute("""
        SELECT DISTINCT post_id, fetch_date 
        FROM post_insights_snapshots 
        WHERE likes_count = 0 
          AND (post_reactions_like_total > 0 OR post_reactions_love_total > 0 
               OR post_reactions_haha_total > 0 OR post_reactions_anger_total > 0)
        ORDER BY fetch_date DESC
    """)
    corrupted = cursor.fetchall()
    
    print(f"\n找到 {len(corrupted)} 筆損壞資料")
    
    if not corrupted:
        print("沒有需要修復的資料")
        conn.close()
        return
    
    # 統計各日期的問題筆數
    date_counts = {}
    for row in corrupted:
        date = row['fetch_date']
        date_counts[date] = date_counts.get(date, 0) + 1
    
    print("\n各日期問題筆數:")
    for date, count in sorted(date_counts.items()):
        print(f"  {date}: {count} 筆")
    
    success_count = 0
    failed_count = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n開始修復（使用今日日期 {today} 作為新的 fetch_date）...")
    
    for i, row in enumerate(corrupted, 1):
        post_id = row['post_id']
        
        if i % 25 == 0 or i == 1:
            print(f"\n進度: {i}/{len(corrupted)} ({success_count} 成功, {failed_count} 失敗)")
        
        try:
            base_url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{post_id}"
            
            # 取得 Reactions (總讚數)
            resp = requests.get(f"{base_url}/reactions", params={
                'access_token': FACEBOOK_CONFIG['access_token'],
                'summary': 'total_count',
                'limit': 0
            }, timeout=10)
            
            likes_count = 0
            if resp.ok:
                likes_count = resp.json().get('summary', {}).get('total_count', 0)
            
            # 取得 Comments
            resp = requests.get(f"{base_url}/comments", params={
                'access_token': FACEBOOK_CONFIG['access_token'],
                'summary': 'total_count',
                'limit': 0
            }, timeout=10)
            
            comments_count = 0
            if resp.ok:
                comments_count = resp.json().get('summary', {}).get('total_count', 0)
            
            # 取得 Shares
            resp = requests.get(base_url, params={
                'access_token': FACEBOOK_CONFIG['access_token'],
                'fields': 'shares'
            }, timeout=10)
            
            shares_count = 0
            if resp.ok:
                shares_count = resp.json().get('shares', {}).get('count', 0)
            
            # 更新資料庫 - 只更新 likes/comments/shares
            if likes_count > 0 or comments_count > 0 or shares_count > 0:
                cursor.execute("""
                    UPDATE post_insights_snapshots 
                    SET likes_count = ?, comments_count = ?, shares_count = ?
                    WHERE post_id = ? AND fetch_date = ?
                """, (likes_count, comments_count, shares_count, post_id, row['fetch_date']))
                conn.commit()
                success_count += 1
            else:
                # 如果還是抓不到，嘗試用 reactions 的總和作為 fallback
                cursor.execute("""
                    UPDATE post_insights_snapshots 
                    SET likes_count = COALESCE(
                        post_reactions_like_total + post_reactions_love_total + 
                        post_reactions_wow_total + post_reactions_haha_total + 
                        post_reactions_sorry_total + post_reactions_anger_total, 0
                    )
                    WHERE post_id = ? AND fetch_date = ? AND likes_count = 0
                """, (post_id, row['fetch_date']))
                conn.commit()
                success_count += 1
                
        except Exception as e:
            failed_count += 1
            if 'timeout' not in str(e).lower():
                print(f"  ✗ {post_id[-15:]}: {str(e)[:50]}")
        
        time.sleep(0.3)  # API 速率限制
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"修復完成:")
    print(f"  成功: {success_count}")
    print(f"  失敗: {failed_count}")
    print("=" * 60)
    
    return success_count, failed_count


def fallback_fix_from_reactions():
    """備用方案：如果 API 無法取得資料，直接用 reactions 總和填補 likes_count"""
    print("=" * 60)
    print("備用方案：用 reactions 總和填補 likes_count")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 計算 reactions 總和並更新 likes_count
    cursor.execute("""
        UPDATE post_insights_snapshots 
        SET likes_count = (
            COALESCE(post_reactions_like_total, 0) + 
            COALESCE(post_reactions_love_total, 0) + 
            COALESCE(post_reactions_wow_total, 0) + 
            COALESCE(post_reactions_haha_total, 0) + 
            COALESCE(post_reactions_sorry_total, 0) + 
            COALESCE(post_reactions_anger_total, 0)
        )
        WHERE likes_count = 0 
          AND (post_reactions_like_total > 0 OR post_reactions_love_total > 0)
    """)
    
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"已更新 {updated} 筆資料")
    return updated


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--fallback':
        fallback_fix_from_reactions()
    else:
        fix_corrupted_insights()
