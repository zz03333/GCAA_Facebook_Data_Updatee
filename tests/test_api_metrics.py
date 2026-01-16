"""
測試 Facebook API 指標可用性
"""
import requests

# Page Access Token (從 /me/accounts 取得)
ACCESS_TOKEN = 'EAAPbnmTSpmoBQEIJ3H6KCC1ZA6YFROcXcZAHJAhf2g8eoG4cyParQdkxKXRYyb8ww9vFGIDogWbDqO8kAwY9aVjrV0zfJdqNuDQDLA5JiKas095i3od2NZCHLAgMTo7CFf9kXGza1okttRrAPHZBe70GXUEAlnzh1yZBFIHPmFFkTImusaTBN6F94uIeNsFZBfjD8ms9kZD'
PAGE_ID = '103640919705348'
API_VERSION = 'v23.0'


def test_api_connection():
    """測試 API 連線"""
    print("=== 測試 API 連線 ===")
    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}"
    params = {
        'access_token': ACCESS_TOKEN,
        'fields': 'id,name,fan_count'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API 連線成功")
        print(f"  Page Name: {data.get('name')}")
        print(f"  Fan Count: {data.get('fan_count')}")
        return True
    else:
        print(f"✗ API 連線失敗: {response.status_code}")
        print(f"  錯誤: {response.json()}")
        return False

def test_deprecated_metrics():
    """測試已棄用的指標是否仍可用"""
    print("\n=== 測試已棄用指標 ===")
    
    # 先取得最新一則貼文
    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/posts"
    params = {
        'access_token': ACCESS_TOKEN,
        'fields': 'id',
        'limit': 1
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"✗ 無法取得貼文列表: {response.json()}")
        return
    
    posts = response.json().get('data', [])
    if not posts:
        print("✗ 沒有找到貼文")
        return
    
    post_id = posts[0]['id']
    print(f"測試貼文 ID: {post_id}")
    
    # 測試各個指標
    test_metrics = [
        'post_impressions',
        'post_impressions_organic',
        'post_impressions_paid',
        'post_impressions_unique',
        'post_clicks',
    ]
    
    for metric in test_metrics:
        url = f"https://graph.facebook.com/{API_VERSION}/{post_id}/insights"
        params = {
            'access_token': ACCESS_TOKEN,
            'metric': metric
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown error')
            print(f"  ✗ {metric}: {error_msg[:50]}")
        elif 'data' in data and data['data']:
            value = data['data'][0].get('values', [{}])[0].get('value', 'N/A')
            print(f"  ✓ {metric}: {value}")
        else:
            print(f"  ⊘ {metric}: 無資料返回")

def test_is_published_and_targeting():
    """測試是否有 sponsored/promoted post 標識"""
    print("\n=== 測試 Sponsored Post 識別方式 ===")
    
    # 嘗試取得貼文的 is_published 和 targeting 欄位
    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/posts"
    params = {
        'access_token': ACCESS_TOKEN,
        'fields': 'id,message,created_time,is_published,targeting,promotable_id,is_eligible_for_promotion,is_hidden,is_popular',
        'limit': 3
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        posts = response.json().get('data', [])
        print(f"取得 {len(posts)} 則貼文:")
        for post in posts:
            print(f"\n  Post ID: {post.get('id')}")
            for key, value in post.items():
                if key != 'id':
                    print(f"    {key}: {value}")
    else:
        print(f"✗ 請求失敗: {response.json()}")
    
    # 另一種方式：檢查 post_impressions_paid > 0
    print("\n如果 post_impressions_paid 可用，可透過 paid > 0 識別 sponsored post")

if __name__ == '__main__':
    if test_api_connection():
        test_deprecated_metrics()
        test_is_published_and_targeting()
