"""
Facebook Marketing API - 廣告數據收集器
取得廣告活動數據並關聯貼文
"""

import requests
import sqlite3
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.config import DB_PATH


def get_marketing_token():
    """取得 Marketing API Access Token（支援環境變數）"""
    token = os.environ.get('FACEBOOK_MARKETING_TOKEN')
    token_base64 = os.environ.get('FACEBOOK_MARKETING_TOKEN_BASE64')
    
    if token_base64:
        return base64.b64decode(token_base64).decode('utf-8')
    elif token:
        return token
    else:
        # 回退到硬編碼值（僅供本地測試）
        return 'EAAPbnmTSpmoBQEiZAYsZAjc6leDIJperlf74AQAiMgJix2YzhZBKatGCMrUuF7duXFVD7NasOMJZBzxVX9BpCY3mt0YmbB7JZCBRsZBxKDj8hzZByfcJZCuHVULEoAJjuQT3CLL449Ut4ZAjYIG8OgdWE4kZBFDI6C93H9ZB9vyHn1ZAvvv1GFBNNkeVYSMPdaOMiSBL'


# Marketing API 設定
MARKETING_CONFIG = {
    'ad_account_id': 'act_450627926033798',
    'access_token': get_marketing_token(),
    'api_version': 'v23.0'
}


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_ad_tables(conn):
    """建立廣告相關表格"""
    cursor = conn.cursor()
    
    # 廣告活動表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaigns (
            campaign_id TEXT PRIMARY KEY,
            name TEXT,
            objective TEXT,
            status TEXT,
            daily_budget REAL,
            lifetime_budget REAL,
            created_time TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 廣告組表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ad_sets (
            adset_id TEXT PRIMARY KEY,
            campaign_id TEXT,
            name TEXT,
            status TEXT,
            targeting TEXT,
            created_time TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES ad_campaigns(campaign_id)
        )
    """)
    
    # 廣告表 (與貼文關聯)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            ad_id TEXT PRIMARY KEY,
            adset_id TEXT,
            campaign_id TEXT,
            name TEXT,
            status TEXT,
            post_id TEXT,
            creative_id TEXT,
            created_time TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (adset_id) REFERENCES ad_sets(adset_id),
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
    """)
    
    # 廣告洞察表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ad_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id TEXT,
            date_start TEXT,
            date_stop TEXT,
            impressions INTEGER,
            reach INTEGER,
            clicks INTEGER,
            spend REAL,
            cpm REAL,
            cpc REAL,
            ctr REAL,
            actions TEXT,
            fetch_date TEXT DEFAULT CURRENT_DATE,
            FOREIGN KEY (ad_id) REFERENCES ads(ad_id),
            UNIQUE(ad_id, date_start, date_stop)
        )
    """)
    
    # 貼文廣告標記視圖
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS posts_with_ads AS
        SELECT 
            p.*,
            CASE WHEN a.ad_id IS NOT NULL THEN 1 ELSE 0 END as is_promoted,
            a.ad_id,
            ac.name as campaign_name,
            ai.spend as total_spend,
            ai.impressions as paid_impressions,
            ai.clicks as paid_clicks
        FROM posts p
        LEFT JOIN ads a ON p.post_id = a.post_id
        LEFT JOIN ad_campaigns ac ON a.campaign_id = ac.campaign_id
        LEFT JOIN (
            SELECT ad_id, SUM(spend) as spend, SUM(impressions) as impressions, SUM(clicks) as clicks
            FROM ad_insights
            GROUP BY ad_id
        ) ai ON a.ad_id = ai.ad_id
    """)
    
    conn.commit()
    print("✓ 廣告表格建立完成")


def fetch_campaigns(config: Dict = MARKETING_CONFIG) -> List[Dict]:
    """取得廣告活動列表"""
    url = f"https://graph.facebook.com/{config['api_version']}/{config['ad_account_id']}/campaigns"
    params = {
        'access_token': config['access_token'],
        'fields': 'id,name,objective,status,daily_budget,lifetime_budget,created_time',
        'limit': 100
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        campaigns = data.get('data', [])
        print(f"✓ 取得 {len(campaigns)} 個廣告活動")
        return campaigns
    except Exception as e:
        print(f"✗ 取得廣告活動失敗: {e}")
        return []


def fetch_ads_with_posts(config: Dict = MARKETING_CONFIG) -> List[Dict]:
    """取得廣告及其關聯的貼文 ID"""
    url = f"https://graph.facebook.com/{config['api_version']}/{config['ad_account_id']}/ads"
    params = {
        'access_token': config['access_token'],
        'fields': 'id,name,status,campaign_id,adset_id,creative{effective_object_story_id},created_time',
        'limit': 100
    }
    
    all_ads = []
    
    try:
        while url:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            ads = data.get('data', [])
            for ad in ads:
                # 從 creative 中提取關聯的貼文 ID
                creative = ad.get('creative', {})
                story_id = creative.get('effective_object_story_id')
                ad['post_id'] = story_id  # 格式: page_id_post_id
                all_ads.append(ad)
            
            # 分頁
            paging = data.get('paging', {})
            url = paging.get('next')
            params = {}
        
        print(f"✓ 取得 {len(all_ads)} 個廣告")
        return all_ads
        
    except Exception as e:
        print(f"✗ 取得廣告失敗: {e}")
        return []


def fetch_ad_insights(ad_id: str, date_preset: str = 'maximum', config: Dict = MARKETING_CONFIG, debug: bool = False) -> List[Dict]:
    """取得單一廣告的洞察數據
    
    Note: Facebook Marketing API v23.0 不再支援 'lifetime'，
    改用 'maximum' 取得所有可用歷史資料
    """
    url = f"https://graph.facebook.com/{config['api_version']}/{ad_id}/insights"
    params = {
        'access_token': config['access_token'],
        'fields': 'impressions,reach,clicks,spend,cpm,cpc,ctr,actions,date_start,date_stop',
        'date_preset': date_preset,
        'level': 'ad'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        insights = data.get('data', [])
        
        if debug:
            print(f"\n  [DEBUG] Ad {ad_id[-15:]}:")
            print(f"    API Response: {data}")
            if insights:
                for ins in insights:
                    print(f"    Period: {ins.get('date_start')} ~ {ins.get('date_stop')}")
                    print(f"    Impressions: {ins.get('impressions', 0)}, Spend: {ins.get('spend', 0)}")
            else:
                print(f"    → No insights data (ad never spent/delivered)")
        
        return insights
    except Exception as e:
        print(f"  ✗ 取得廣告 {ad_id} 洞察失敗: {e}")
        if debug:
            print(f"    [DEBUG] Error details: {e}")
        return []


def save_campaign(conn, campaign: Dict):
    """儲存廣告活動"""
    cursor = conn.cursor()
    
    # 處理 budget (可能是字串或數字)
    daily_budget = campaign.get('daily_budget')
    lifetime_budget = campaign.get('lifetime_budget')
    
    try:
        daily_budget = float(daily_budget) / 100 if daily_budget else None
    except (TypeError, ValueError):
        daily_budget = None
    
    try:
        lifetime_budget = float(lifetime_budget) / 100 if lifetime_budget else None
    except (TypeError, ValueError):
        lifetime_budget = None
    
    cursor.execute("""
        INSERT OR REPLACE INTO ad_campaigns 
        (campaign_id, name, objective, status, daily_budget, lifetime_budget, created_time, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        campaign.get('id'),
        campaign.get('name'),
        campaign.get('objective'),
        campaign.get('status'),
        daily_budget,
        lifetime_budget,
        campaign.get('created_time')
    ))
    conn.commit()


def save_ad(conn, ad: Dict):
    """儲存廣告"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO ads 
        (ad_id, adset_id, campaign_id, name, status, post_id, creative_id, created_time, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        ad.get('id'),
        ad.get('adset_id'),
        ad.get('campaign_id'),
        ad.get('name'),
        ad.get('status'),
        ad.get('post_id'),
        ad.get('creative', {}).get('id'),
        ad.get('created_time')
    ))
    conn.commit()


def save_ad_insights(conn, ad_id: str, insights: List[Dict]):
    """儲存廣告洞察"""
    cursor = conn.cursor()
    for insight in insights:
        cursor.execute("""
            INSERT OR REPLACE INTO ad_insights 
            (ad_id, date_start, date_stop, impressions, reach, clicks, spend, cpm, cpc, ctr, actions, fetch_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE)
        """, (
            ad_id,
            insight.get('date_start'),
            insight.get('date_stop'),
            insight.get('impressions', 0),
            insight.get('reach', 0),
            insight.get('clicks', 0),
            float(insight.get('spend', 0)),
            float(insight.get('cpm', 0)),
            float(insight.get('cpc', 0)),
            float(insight.get('ctr', 0)),
            str(insight.get('actions', []))
        ))
    conn.commit()


def collect_all_ad_data():
    """收集所有廣告數據"""
    print("\n" + "="*60)
    print("開始收集 Marketing API 廣告數據")
    print("="*60)
    
    conn = get_connection()
    
    try:
        # 建立表格
        setup_ad_tables(conn)
        
        # 取得並儲存廣告活動
        print("\n[1/3] 取得廣告活動...")
        campaigns = fetch_campaigns()
        for campaign in campaigns:
            save_campaign(conn, campaign)
        
        # 取得並儲存廣告
        print("\n[2/3] 取得廣告及貼文關聯...")
        ads = fetch_ads_with_posts()
        for ad in ads:
            save_ad(conn, ad)
        
        # 取得並儲存廣告洞察
        print("\n[3/3] 取得廣告洞察數據...")
        for i, ad in enumerate(ads, 1):
            ad_id = ad.get('id')
            print(f"  處理 {i}/{len(ads)}: {ad_id}", end='')
            insights = fetch_ad_insights(ad_id)
            if insights:
                save_ad_insights(conn, ad_id, insights)
                print(" - ✓")
            else:
                print(" - ⊘")
        
        print("\n✓ 廣告數據收集完成")
        
        # 顯示摘要
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ad_campaigns")
        campaigns_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ads")
        ads_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ads WHERE post_id IS NOT NULL")
        linked_count = cursor.fetchone()[0]
        
        print(f"\n摘要:")
        print(f"  廣告活動: {campaigns_count} 個")
        print(f"  廣告: {ads_count} 個")
        print(f"  關聯貼文: {linked_count} 個")
        
        return True
        
    except Exception as e:
        print(f"✗ 廣告數據收集失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


# ==================== 分析函數 ====================

def get_organic_vs_paid_comparison(conn) -> Dict:
    """
    比較自然觸及與付費觸及的表現差異
    """
    cursor = conn.cursor()
    
    # 有廣告的貼文表現
    cursor.execute("""
        SELECT 
            'paid' as type,
            COUNT(DISTINCT p.post_id) as post_count,
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate,
            ROUND(AVG(pp.share_rate), 2) as avg_share_rate,
            ROUND(AVG(pp.comment_rate), 2) as avg_comment_rate,
            SUM(i.post_impressions_unique) as total_reach,
            SUM(i.likes_count + i.comments_count + i.shares_count) as total_engagement
        FROM posts p
        JOIN ads a ON p.post_id = a.post_id
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        LEFT JOIN posts_performance pp ON p.post_id = pp.post_id
    """)
    paid = dict(cursor.fetchone())
    
    # 無廣告的貼文表現
    cursor.execute("""
        SELECT 
            'organic' as type,
            COUNT(DISTINCT p.post_id) as post_count,
            ROUND(AVG(pp.engagement_rate), 2) as avg_engagement_rate,
            ROUND(AVG(pp.share_rate), 2) as avg_share_rate,
            ROUND(AVG(pp.comment_rate), 2) as avg_comment_rate,
            SUM(i.post_impressions_unique) as total_reach,
            SUM(i.likes_count + i.comments_count + i.shares_count) as total_engagement
        FROM posts p
        LEFT JOIN ads a ON p.post_id = a.post_id
        JOIN post_insights_snapshots i ON p.post_id = i.post_id
        LEFT JOIN posts_performance pp ON p.post_id = pp.post_id
        WHERE a.ad_id IS NULL
    """)
    organic = dict(cursor.fetchone())
    
    return {
        'paid': paid,
        'organic': organic,
        'comparison': {
            'er_diff': round((paid['avg_engagement_rate'] or 0) - (organic['avg_engagement_rate'] or 0), 2),
            'reach_ratio': round((paid['total_reach'] or 1) / (organic['total_reach'] or 1), 2)
        }
    }


def get_ad_roi_by_post_type(conn) -> List[Dict]:
    """
    分析各類貼文的廣告 ROI
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            pc.format_type,
            pc.issue_topic,
            COUNT(DISTINCT a.ad_id) as ad_count,
            SUM(ai.spend) as total_spend,
            SUM(ai.impressions) as total_impressions,
            SUM(ai.clicks) as total_clicks,
            ROUND(AVG(ai.cpm), 2) as avg_cpm,
            ROUND(AVG(ai.cpc), 2) as avg_cpc,
            ROUND(AVG(ai.ctr), 2) as avg_ctr
        FROM ads a
        JOIN posts p ON a.post_id = p.post_id
        JOIN posts_classification pc ON p.post_id = pc.post_id
        JOIN ad_insights ai ON a.ad_id = ai.ad_id
        GROUP BY pc.format_type, pc.issue_topic
        ORDER BY total_spend DESC
    """)
    
    return [dict(row) for row in cursor.fetchall()]


if __name__ == '__main__':
    collect_all_ad_data()
