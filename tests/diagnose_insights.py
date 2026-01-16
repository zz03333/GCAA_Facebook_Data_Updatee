"""
診斷工具：檢查 Facebook Insights API 實際返回的數據
"""

import requests
import json
from datetime import datetime
import config

def test_single_post_insights(post_id):
    """測試單一貼文的 insights API 返回內容"""

    print(f"\n{'='*60}")
    print(f"測試貼文: {post_id}")
    print(f"{'='*60}\n")

    # 1. 獲取貼文基本資訊
    print("[1] 貼文基本資訊")
    url = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{post_id}"
    params = {
        'access_token': config.FACEBOOK_CONFIG['access_token'],
        'fields': 'id,message,created_time,permalink_url'
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"  Created: {data.get('created_time')}")
        print(f"  Message: {data.get('message', '')[:80]}...")
        print(f"  ✓ 基本資訊獲取成功")
    else:
        print(f"  ✗ 錯誤: {response.text}")
        return

    # 2. 獲取互動數
    print("\n[2] 互動數據")

    # Reactions
    url_reactions = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{post_id}/reactions"
    params_reactions = {
        'access_token': config.FACEBOOK_CONFIG['access_token'],
        'summary': 'total_count',
        'limit': 0
    }
    resp = requests.get(url_reactions, params=params_reactions)
    if resp.status_code == 200:
        reactions = resp.json().get('summary', {}).get('total_count', 0)
        print(f"  Reactions: {reactions}")

    # Comments
    url_comments = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{post_id}/comments"
    params_comments = {
        'access_token': config.FACEBOOK_CONFIG['access_token'],
        'summary': 'total_count',
        'limit': 0
    }
    resp = requests.get(url_comments, params=params_comments)
    if resp.status_code == 200:
        comments = resp.json().get('summary', {}).get('total_count', 0)
        print(f"  Comments: {comments}")

    # Shares
    url_shares = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{post_id}"
    params_shares = {
        'access_token': config.FACEBOOK_CONFIG['access_token'],
        'fields': 'shares'
    }
    resp = requests.get(url_shares, params=params_shares)
    if resp.status_code == 200:
        shares = resp.json().get('shares', {}).get('count', 0)
        print(f"  Shares: {shares}")

    # 3. 測試 Insights API
    print("\n[3] Insights 數據")

    metrics_to_test = config.POST_METRICS

    url_insights = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{post_id}/insights"
    params_insights = {
        'access_token': config.FACEBOOK_CONFIG['access_token'],
        'metric': ','.join(metrics_to_test)
    }

    response = requests.get(url_insights, params=params_insights)

    if response.status_code == 200:
        insights_data = response.json()

        print(f"  API 回應狀態: ✓ 成功")
        print(f"  返回的指標數量: {len(insights_data.get('data', []))}")

        if insights_data.get('data'):
            print("\n  詳細數據:")
            for metric in insights_data['data']:
                metric_name = metric.get('name')
                values = metric.get('values', [])
                if values:
                    value = values[0].get('value', 'N/A')
                    print(f"    {metric_name:35s}: {value}")
                else:
                    print(f"    {metric_name:35s}: (無數據)")
        else:
            print("  ⚠ 警告: API 返回成功但無數據")

        # 顯示完整 JSON（用於調試）
        print("\n  [完整 JSON 回應]")
        print(json.dumps(insights_data, indent=2, ensure_ascii=False)[:500] + "...")

    else:
        print(f"  ✗ API 錯誤: {response.status_code}")
        print(f"  錯誤訊息: {response.text}")


def main():
    """主程式"""
    print("\n" + "="*60)
    print("Facebook Insights API 診斷工具")
    print("="*60)

    # 從資料庫獲取最近的貼文來測試
    import sqlite3
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT post_id, created_time
        FROM posts
        ORDER BY created_time DESC
        LIMIT 3
    """)

    posts = cursor.fetchall()
    conn.close()

    if not posts:
        print("\n⚠ 資料庫中無貼文數據")
        return

    print(f"\n將測試 {len(posts)} 則貼文的 Insights API")

    for post_id, created_time in posts:
        test_single_post_insights(post_id)

    print("\n" + "="*60)
    print("診斷完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
