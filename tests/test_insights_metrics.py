#!/usr/bin/env python3
"""
Test which post-level insights metrics are available
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

# All post-level metrics from the ipynb file
POST_INSIGHTS_METRICS = [
    'post_engaged_users',
    'post_clicks',
    'post_clicks_unique',
    'post_impressions',
    'post_impressions_unique',
    'post_impressions_organic',
    'post_impressions_paid',
    'post_reactions_like_total',
    'post_reactions_love_total',
    'post_reactions_wow_total',
    'post_reactions_haha_total',
    'post_reactions_sorry_total',
    'post_reactions_anger_total',
    'post_video_views',
    'post_video_views_organic',
    'post_video_views_paid',
    'post_video_view_time',
]

def get_recent_post():
    """Get a recent post to test insights"""
    url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{FACEBOOK_CONFIG['page_id']}/posts"
    params = {
        'access_token': FACEBOOK_CONFIG['access_token'],
        'fields': 'id,message,created_time,type',
        'limit': 1
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        posts = data.get('data', [])
        if posts:
            return posts[0]
    return None

def test_insights_metric(post_id, metric):
    """Test a single insights metric"""
    url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{post_id}/insights"
    params = {
        'access_token': FACEBOOK_CONFIG['access_token'],
        'metric': metric
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200:
            insights_data = data.get('data', [])
            if insights_data:
                metric_info = insights_data[0]
                values = metric_info.get('values', [])
                if values:
                    value = values[0].get('value', 0)
                    return True, value, None
                else:
                    return False, None, "No values returned"
            else:
                return False, None, "No data in response"
        else:
            error_msg = data.get('error', {}).get('message', 'Unknown error')
            return False, None, error_msg
    except Exception as e:
        return False, None, str(e)

def test_batch_insights(post_id, metrics):
    """Test metrics in batch (faster)"""
    url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{post_id}/insights"
    params = {
        'access_token': FACEBOOK_CONFIG['access_token'],
        'metric': ','.join(metrics)
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200:
            insights_data = data.get('data', [])
            results = {}
            for metric_info in insights_data:
                metric_name = metric_info.get('name')
                values = metric_info.get('values', [])
                if values:
                    value = values[0].get('value', 0)
                    results[metric_name] = value
            return True, results, None
        else:
            error_msg = data.get('error', {}).get('message', 'Unknown error')
            return False, None, error_msg
    except Exception as e:
        return False, None, str(e)

def main():
    print("="*60)
    print("Facebook Post Insights Metrics Testing")
    print("="*60)

    # Get a recent post
    print("\nFetching a recent post to test...")
    post = get_recent_post()

    if not post:
        print("✗ Could not fetch a recent post")
        return

    post_id = post['id']
    print(f"✓ Found post: {post_id}")
    print(f"  Type: {post.get('type')}")
    print(f"  Created: {post.get('created_time')}")
    print(f"  Message: {post.get('message', 'N/A')[:100]}...")

    # Test batch request first (faster)
    print(f"\n{'='*60}")
    print("Testing all metrics in batch...")
    print(f"{'='*60}")

    success, results, error = test_batch_insights(post_id, POST_INSIGHTS_METRICS)

    if success:
        print(f"✓ Batch request successful! Found {len(results)} metrics with data:")
        print()

        working_metrics = []
        for metric, value in results.items():
            print(f"  ✓ {metric}: {value}")
            working_metrics.append(metric)

        # Find which metrics are missing
        missing_metrics = [m for m in POST_INSIGHTS_METRICS if m not in results]
        if missing_metrics:
            print(f"\n⚠️  Metrics not returned (may not be available for this post):")
            for metric in missing_metrics:
                print(f"  - {metric}")

        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"Working metrics: {len(working_metrics)}/{len(POST_INSIGHTS_METRICS)}")
        print(f"\nWorking metrics list:")
        print(json.dumps(working_metrics, indent=2))

    else:
        print(f"✗ Batch request failed: {error}")
        print(f"\nTrying individual metric tests...")

        working_metrics = []
        failed_metrics = []

        for i, metric in enumerate(POST_INSIGHTS_METRICS, 1):
            print(f"\n[{i}/{len(POST_INSIGHTS_METRICS)}] Testing: {metric}")
            success, value, error_msg = test_insights_metric(post_id, metric)

            if success:
                print(f"  ✓ Success: {value}")
                working_metrics.append(metric)
            else:
                print(f"  ✗ Failed: {error_msg}")
                failed_metrics.append((metric, error_msg))

        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"Working: {len(working_metrics)}/{len(POST_INSIGHTS_METRICS)}")
        print(f"Failed: {len(failed_metrics)}/{len(POST_INSIGHTS_METRICS)}")

        if working_metrics:
            print(f"\n✓ Working metrics:")
            for metric in working_metrics:
                print(f"  - {metric}")

        if failed_metrics:
            print(f"\n✗ Failed metrics:")
            for metric, error in failed_metrics:
                print(f"  - {metric}: {error}")

    # Test with different post types if available
    print(f"\n{'='*60}")
    print("Testing different post types...")
    print(f"{'='*60}")

    # Get posts of different types
    url = f"https://graph.facebook.com/{FACEBOOK_CONFIG['api_version']}/{FACEBOOK_CONFIG['page_id']}/posts"
    params = {
        'access_token': FACEBOOK_CONFIG['access_token'],
        'fields': 'id,type,created_time',
        'limit': 20
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        posts = response.json().get('data', [])

        # Group by type
        posts_by_type = {}
        for p in posts:
            ptype = p.get('type', 'unknown')
            if ptype not in posts_by_type:
                posts_by_type[ptype] = p

        print(f"Found {len(posts_by_type)} different post types: {list(posts_by_type.keys())}")

        for ptype, sample_post in posts_by_type.items():
            print(f"\n--- Testing {ptype} post: {sample_post['id']} ---")
            success, results, error = test_batch_insights(sample_post['id'], POST_INSIGHTS_METRICS)
            if success:
                print(f"  Available metrics for {ptype}: {len(results)}")
                print(f"  Metrics: {', '.join(results.keys())}")
            else:
                print(f"  Error: {error}")

if __name__ == '__main__':
    main()