#!/usr/bin/env python3
"""
Standalone test script for debugging Facebook Posts API
Tests different endpoints and parameters to find why posts aren't being fetched
"""

import requests
from datetime import datetime, timedelta
import json

# Configuration
FACEBOOK_CONFIG = {
    'app_id': '1085898272974442',
    'page_id': '103640919705348',
    'access_token': 'EAAPbnmTSpmoBPmlpUIBh7EOKkZAdLIRnmJst2Y2tGPSHA9Omt2ZAfEULKYEZCNtadAFXPPIKKhHaknTXjQoZBPR8pZA4U6RbH1cribzPRuQ5gZBAp1vVTGQls1xZA81M9cb72krNH6Oe4NuBwyd47Jrk9zLuZBFBcoGjdpBQln9n6LdgNETH2UcTF5Gr3RmeiqkVpimLxe3trNBSsumoppXACFDiZCZAbFkDEHdKyA1rrbmlAZD',
    'api_version': 'v23.0'
}

def test_endpoint(endpoint_name, url, params):
    """Test a specific API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint_name}")
    print(f"URL: {url}")
    print(f"Params: {json.dumps({k: v for k, v in params.items() if k != 'access_token'}, indent=2)}")
    print(f"{'='*60}")

    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")

        data = response.json()

        if response.status_code == 200:
            posts = data.get('data', [])
            print(f"✓ Success! Found {len(posts)} posts")

            if posts:
                print(f"\nFirst post sample:")
                first_post = posts[0]
                print(f"  ID: {first_post.get('id')}")
                print(f"  Created: {first_post.get('created_time', 'N/A')}")
                print(f"  Message: {first_post.get('message', 'N/A')[:100]}")
                print(f"  Available fields: {list(first_post.keys())}")

            # Show pagination info
            if 'paging' in data:
                print(f"\nPagination: {data['paging'].keys()}")

            return True, len(posts)
        else:
            print(f"✗ Error: {data.get('error', {}).get('message', 'Unknown error')}")
            print(f"Full error: {json.dumps(data, indent=2)}")
            return False, 0

    except Exception as e:
        print(f"✗ Exception: {e}")
        return False, 0


def main():
    print("="*60)
    print("Facebook Posts API Debugging Script")
    print("="*60)

    # Test date range
    test_until = datetime.now() - timedelta(days=1)
    test_since = datetime.now() - timedelta(days=30)  # Try 30 days to ensure we catch some posts

    since_str = test_since.strftime('%Y-%m-%d')
    until_str = test_until.strftime('%Y-%m-%d')
    since_ts = int(test_since.timestamp())
    until_ts = int(test_until.timestamp())

    print(f"\nDate Range:")
    print(f"  Since: {since_str} ({since_ts})")
    print(f"  Until: {until_str} ({until_ts})")

    base_url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{FACEBOOK_CONFIG['page_id']}"

    # Test 1: /posts endpoint with timestamps
    test_endpoint(
        "Test 1: /posts with timestamps",
        f"{base_url}/posts",
        {
            'access_token': FACEBOOK_CONFIG['access_token'],
            'fields': 'id,message,created_time',
            'since': since_ts,
            'until': until_ts,
            'limit': 10
        }
    )

    # Test 2: /posts endpoint without date filter
    test_endpoint(
        "Test 2: /posts without date filter",
        f"{base_url}/posts",
        {
            'access_token': FACEBOOK_CONFIG['access_token'],
            'fields': 'id,message,created_time',
            'limit': 10
        }
    )

    # Test 3: /published_posts endpoint
    test_endpoint(
        "Test 3: /published_posts with timestamps",
        f"{base_url}/published_posts",
        {
            'access_token': FACEBOOK_CONFIG['access_token'],
            'fields': 'id,message,created_time',
            'since': since_ts,
            'until': until_ts,
            'limit': 10
        }
    )

    # Test 4: /published_posts without date filter
    test_endpoint(
        "Test 4: /published_posts without date filter",
        f"{base_url}/published_posts",
        {
            'access_token': FACEBOOK_CONFIG['access_token'],
            'fields': 'id,message,created_time',
            'limit': 10
        }
    )

    # Test 5: /feed endpoint
    test_endpoint(
        "Test 5: /feed endpoint",
        f"{base_url}/feed",
        {
            'access_token': FACEBOOK_CONFIG['access_token'],
            'fields': 'id,message,created_time',
            'limit': 10
        }
    )

    # Test 6: Test with full field list to see if that's causing issues
    test_endpoint(
        "Test 6: /posts with full fields (like in ipynb)",
        f"{base_url}/posts",
        {
            'access_token': FACEBOOK_CONFIG['access_token'],
            'fields': 'id,message,created_time,permalink_url,type,shares,likes.summary(true),comments.summary(true)',
            'limit': 10
        }
    )

    # Test 7: Check token permissions
    print(f"\n{'='*60}")
    print("Test 7: Check Access Token Info")
    print(f"{'='*60}")

    token_url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/me"
    token_params = {
        'access_token': FACEBOOK_CONFIG['access_token'],
        'fields': 'id,name'
    }

    try:
        response = requests.get(token_url, params=token_params)
        data = response.json()
        print(f"Token belongs to: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error checking token: {e}")

    # Test 8: Debug token to check permissions
    print(f"\n{'='*60}")
    print("Test 8: Debug Access Token Permissions")
    print(f"{'='*60}")

    debug_url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/debug_token"
    debug_params = {
        'input_token': FACEBOOK_CONFIG['access_token'],
        'access_token': FACEBOOK_CONFIG['access_token']
    }

    try:
        response = requests.get(debug_url, params=debug_params)
        data = response.json()
        if 'data' in data:
            token_data = data['data']
            print(f"App ID: {token_data.get('app_id')}")
            print(f"Type: {token_data.get('type')}")
            print(f"Valid: {token_data.get('is_valid')}")
            print(f"Expires: {token_data.get('expires_at', 'Never')}")
            print(f"Scopes: {token_data.get('scopes', [])}")
            print(f"User ID: {token_data.get('user_id', 'N/A')}")
        else:
            print(f"Error: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error debugging token: {e}")

    print(f"\n{'='*60}")
    print("Testing Complete!")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("1. Review which endpoint returned posts successfully")
    print("2. Check token permissions to ensure you have 'pages_read_engagement'")
    print("3. If using Chrome DevTools MCP, inspect network requests in Graph API Explorer")


if __name__ == '__main__':
    main()