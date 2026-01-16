"""
測試每個 Insights 指標的有效性
"""

import requests
import config
import sqlite3

def test_metric(post_id, metric_name):
    """測試單一指標是否有效"""
    url = f"https://graph.facebook.com/{config.FACEBOOK_CONFIG['api_version']}/{post_id}/insights"
    params = {
        'access_token': config.FACEBOOK_CONFIG['access_token'],
        'metric': metric_name
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            value = data['data'][0].get('values', [{}])[0].get('value', 'N/A')
            return True, value
        return True, 'no_data'
    else:
        error_msg = response.json().get('error', {}).get('message', 'Unknown error')
        return False, error_msg


def main():
    """測試所有配置的指標"""
    print("\n" + "="*70)
    print("測試 Facebook Insights 指標有效性")
    print("="*70)

    # 獲取一則測試貼文
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT post_id FROM posts LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("\n✗ 資料庫中無貼文")
        return

    post_id = result[0]
    print(f"\n測試貼文: {post_id}")
    print(f"\n{'指標名稱':40s} {'狀態':8s} {'數值/錯誤訊息':30s}")
    print("-" * 70)

    valid_metrics = []
    invalid_metrics = []

    for metric in config.POST_METRICS:
        is_valid, result = test_metric(post_id, metric)

        if is_valid:
            status = "✓ 有效"
            valid_metrics.append(metric)
            value_str = str(result)[:30]
        else:
            status = "✗ 無效"
            invalid_metrics.append(metric)
            value_str = result[:30]

        print(f"{metric:40s} {status:8s} {value_str}")

    print("\n" + "="*70)
    print(f"有效指標: {len(valid_metrics)} / {len(config.POST_METRICS)}")
    print(f"無效指標: {len(invalid_metrics)} / {len(config.POST_METRICS)}")

    if valid_metrics:
        print("\n✓ 有效的指標清單:")
        for m in valid_metrics:
            print(f"    '{m}',")

    if invalid_metrics:
        print("\n✗ 無效的指標清單:")
        for m in invalid_metrics:
            print(f"    # '{m}',  # 已棄用或無效")

    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
