# collector_page.py
import requests
import time
from datetime import datetime, timedelta
from utils import config
from utils import db_utils

def fetch_page_info(access_token, page_id, api_version):
    url = f"https://graph.facebook.com/{api_version}/{page_id}"
    params = {
        'access_token': access_token,
        'fields': 'id,name,fan_count,followers_count'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching page info: {response.text}")
        return None

def fetch_daily_insights(access_token, page_id, api_version, since, until, metrics):
    url = f"https://graph.facebook.com/{api_version}/{page_id}/insights"
    
    # metrics is a list of strings
    metric_param = ','.join(metrics)
    
    params = {
        'access_token': access_token,
        'metric': metric_param,
        'period': 'day',
        'since': since,
        'until': until
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching insights: {response.text}")
        return None

def process_and_save_page_data(days_back=7):
    conn = db_utils.get_db_connection()
    if not conn:
        return

    # 1. Fetch Page Info (Lifetime)
    page_info = fetch_page_info(
        config.FACEBOOK_CONFIG['access_token'],
        config.FACEBOOK_CONFIG['page_id'],
        config.FACEBOOK_CONFIG['api_version']
    )
    
    if page_info:
        print(f"Page: {page_info.get('name')} (ID: {page_info.get('id')})")
        db_utils.upsert_page_info(conn, page_info['id'], page_info['name'])
        
        # Prepare lifetime metrics to be added to daily rows
        lifetime_data = {
            'fan_count': page_info.get('fan_count'),
            'followers_count': page_info.get('followers_count')
        }
    else:
        print("Failed to fetch page info. Aborting.")
        conn.close()
        return

    # 2. Fetch Daily Insights
    since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    until_date = datetime.now().strftime('%Y-%m-%d') # Facebook 'until' is exclusive for timestamps, but for date strings it usually works as end date. Using timestamps is safer.
    
    # Convert to timestamps for API safety
    since_ts = int(datetime.strptime(since_date, '%Y-%m-%d').timestamp())
    until_ts = int(datetime.strptime(until_date, '%Y-%m-%d').timestamp())

    print(f"Fetching insights from {since_date} to {until_date}...")
    
    insights_response = fetch_daily_insights(
        config.FACEBOOK_CONFIG['access_token'],
        config.FACEBOOK_CONFIG['page_id'],
        config.FACEBOOK_CONFIG['api_version'],
        since_ts,
        until_ts,
        config.PAGE_METRICS
    )

    if insights_response and 'data' in insights_response:
        # Transform data: Date -> Metric -> Value
        daily_records = {} # {'2023-10-27': {'metric1': val, ...}}
        
        for item in insights_response['data']:
            metric_name = item['name']
            for value_entry in item['values']:
                # value_entry['end_time'] is like '2023-10-28T07:00:00+0000'
                # The data represents the day BEFORE the end_time usually.
                # However, typically we just take the date part of end_time - 1 day or as is depending on timezone. 
                # Facebook Insights 'end_time' usually means the data extraction time for the previous period.
                # E.g. Period=day, end_time=2023-10-28 means data for 2023-10-27.
                
                end_time_str = value_entry['end_time']
                end_time_dt = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S%z")
                data_date = (end_time_dt - timedelta(days=1)).strftime('%Y-%m-%d')
                
                if data_date not in daily_records:
                    daily_records[data_date] = {}
                
                # Handle complex metrics like page_actions_post_reactions_total
                val = value_entry['value']
                
                if metric_name == 'page_actions_post_reactions_total' and isinstance(val, dict):
                    daily_records[data_date]['reactions_like'] = val.get('like', 0)
                    daily_records[data_date]['reactions_love'] = val.get('love', 0)
                    daily_records[data_date]['reactions_wow'] = val.get('wow', 0)
                    daily_records[data_date]['reactions_haha'] = val.get('haha', 0)
                    daily_records[data_date]['reactions_sorry'] = val.get('sorry', 0)
                    daily_records[data_date]['reactions_anger'] = val.get('anger', 0)
                    daily_records[data_date]['reactions_total'] = sum(val.values())
                else:
                    daily_records[data_date][metric_name] = val

        # Save to DB
        for date_str, metrics in daily_records.items():
            # Merge lifetime data
            full_record = {**metrics, **lifetime_data}
            success = db_utils.upsert_page_daily_metrics(conn, page_info['id'], date_str, full_record)
            if success:
                print(f"Saved data for {date_str}")
            else:
                print(f"Failed to save data for {date_str}")

    else:
        print("No insights data returned.")

    conn.close()

if __name__ == '__main__':
    process_and_save_page_data(days_back=5)
