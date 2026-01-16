#!/usr/bin/env python3
"""
GCAA 社群分析 - 資料同步腳本
從 Google Sheets 讀取 raw_posts + raw_post_insights，生成 JSON 檔案供前端使用
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 設定
SPREADSHEET_ID = '1HJXQrlB0eYJsHmioLMNfCKV_OXHqqgwtwRtO9s5qbB0'
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), '..', 'esg-reports-collection-9661012923ed.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data')

# Sheets 設定
SHEETS = {
    'raw_insights': 'raw_post_insights',
    'content_analysis': '📊 content_analysis',
    'posts_performance': '📈 posts_performance',
    'ad_analytics': '💰 ad_analytics'
}

def get_sheets_service():
    """建立 Google Sheets API 連線"""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return build('sheets', 'v4', credentials=credentials)

def fetch_sheet_data(service, sheet_name):
    """從 Google Sheets 讀取資料 (使用 header 模式)"""
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name
    ).execute()

    values = result.get('values', [])
    if len(values) < 2:
        return []

    headers = values[0]
    data = []
    for row in values[1:]:
        obj = {}
        for i, header in enumerate(headers):
            obj[header] = row[i] if i < len(row) else ''
        data.append(obj)

    return data


def fetch_sheet_raw(service, sheet_name):
    """從 Google Sheets 讀取原始資料 (不使用 header 模式)"""
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name
    ).execute()

    values = result.get('values', [])
    return values  # Return raw 2D array

def parse_datetime(date_str):
    """解析日期時間字串"""
    if not date_str:
        return None
    try:
        # 嘗試多種格式
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None

def parse_int(value):
    """安全解析整數"""
    if not value:
        return 0
    try:
        # 移除逗號 (例如 "52,143" -> 52143)
        return int(str(value).replace(',', '').replace(' ', ''))
    except (ValueError, TypeError):
        return 0

def parse_float(value):
    """安全解析浮點數"""
    if not value:
        return 0.0
    try:
        return float(str(value).replace(',', '').replace(' ', ''))
    except (ValueError, TypeError):
        return 0.0

def process_insights_data(raw_insights):
    """處理 raw_post_insights 資料（已整合所有貼文資訊）"""
    posts = []
    for row in raw_insights:
        post_id = row.get('Post ID', '')
        if not post_id:
            continue

        # 基本資訊 (現在都在 raw_post_insights 中)
        published_at = parse_datetime(row.get('發布時間 (GMT+8)', ''))
        content = row.get('內容預覽', '') or ''

        # 互動指標
        likes = parse_int(row.get('總讚數', 0))
        comments = parse_int(row.get('留言數', 0))
        shares = parse_int(row.get('分享數', 0))
        clicks = parse_int(row.get('點擊數', 0))
        reach = parse_int(row.get('觸及人數', 0))
        video_views = parse_int(row.get('影片觀看', 0))

        # 表情反應
        reactions = {
            'like': parse_int(row.get('👍反應', 0)),
            'love': parse_int(row.get('❤️反應', 0)),
            'wow': parse_int(row.get('😮反應', 0)),
            'haha': parse_int(row.get('😆反應', 0)),
            'sad': parse_int(row.get('😢反應', 0)),
            'angry': parse_int(row.get('😠反應', 0))
        }

        # 計算衍生指標
        total_engagement = likes + comments + shares
        engagement_rate = (total_engagement / reach * 100) if reach > 0 else 0
        share_rate = (shares / reach * 100) if reach > 0 else 0

        # 廣告資訊
        is_promoted = row.get('有投廣', '否') == '是'
        ad_status = row.get('廣告狀態', '')
        ad_spend = parse_float(row.get('廣告花費', 0))

        posts.append({
            'id': post_id,
            'publishedAt': published_at.isoformat() if published_at else None,
            'content': content,
            'contentPreview': content[:80] + '...' if len(content) > 80 else content,
            'actionType': row.get('行動類型', '') or '其他',
            'topic': row.get('議題類型', '') or '其他',
            'permalink': row.get('貼文連結', ''),
            'isPromoted': is_promoted,
            'adStatus': ad_status,
            'adSpend': ad_spend,
            'metrics': {
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'clicks': clicks,
                'reach': reach,
                'videoViews': video_views,
                'reactions': reactions
            },
            'computed': {
                'engagementRate': round(engagement_rate, 2),
                'totalEngagement': total_engagement,
                'shareRate': round(share_rate, 2)
            }
        })

    # 按發布時間排序 (新到舊)
    posts.sort(key=lambda x: x['publishedAt'] or '', reverse=True)

    return posts

def generate_daily_data(posts):
    """生成每日聚合資料"""
    daily_map = defaultdict(lambda: {
        'postCount': 0,
        'totalReach': 0,
        'totalEngagement': 0,
        'totalShares': 0,
        'totalClicks': 0,
        'engagementRates': []
    })

    for post in posts:
        if not post['publishedAt']:
            continue

        date = post['publishedAt'][:10]  # YYYY-MM-DD
        daily = daily_map[date]

        daily['postCount'] += 1
        daily['totalReach'] += post['metrics']['reach']
        daily['totalEngagement'] += post['computed']['totalEngagement']
        daily['totalShares'] += post['metrics']['shares']
        daily['totalClicks'] += post['metrics']['clicks']
        if post['computed']['engagementRate'] > 0:
            daily['engagementRates'].append(post['computed']['engagementRate'])

    daily_data = []
    for date, data in sorted(daily_map.items(), reverse=True):
        avg_er = sum(data['engagementRates']) / len(data['engagementRates']) if data['engagementRates'] else 0
        daily_data.append({
            'date': date,
            'postCount': data['postCount'],
            'totalReach': data['totalReach'],
            'totalEngagement': data['totalEngagement'],
            'avgEngagementRate': round(avg_er, 2),
            'totalShares': data['totalShares'],
            'totalClicks': data['totalClicks']
        })

    return daily_data

def generate_stats(posts):
    """生成統計摘要"""
    # 按行動類型分組
    by_action = defaultdict(lambda: {'count': 0, 'totalER': 0, 'totalReach': 0})
    for post in posts:
        action = post['actionType']
        by_action[action]['count'] += 1
        by_action[action]['totalER'] += post['computed']['engagementRate']
        by_action[action]['totalReach'] += post['metrics']['reach']

    action_stats = []
    for name, data in sorted(by_action.items(), key=lambda x: -x[1]['count']):
        action_stats.append({
            'name': name,
            'count': data['count'],
            'avgER': round(data['totalER'] / data['count'], 2) if data['count'] > 0 else 0,
            'avgReach': round(data['totalReach'] / data['count']) if data['count'] > 0 else 0
        })

    # 按議題分組
    by_topic = defaultdict(lambda: {'count': 0, 'totalER': 0, 'totalReach': 0})
    for post in posts:
        topic = post['topic']
        by_topic[topic]['count'] += 1
        by_topic[topic]['totalER'] += post['computed']['engagementRate']
        by_topic[topic]['totalReach'] += post['metrics']['reach']

    topic_stats = []
    for name, data in sorted(by_topic.items(), key=lambda x: -x[1]['count']):
        topic_stats.append({
            'name': name,
            'count': data['count'],
            'avgER': round(data['totalER'] / data['count'], 2) if data['count'] > 0 else 0,
            'avgReach': round(data['totalReach'] / data['count']) if data['count'] > 0 else 0
        })

    # 按小時分組
    by_hour = defaultdict(lambda: {'count': 0, 'totalER': 0})
    for post in posts:
        if not post['publishedAt']:
            continue
        try:
            hour = int(post['publishedAt'][11:13])
            by_hour[hour]['count'] += 1
            by_hour[hour]['totalER'] += post['computed']['engagementRate']
        except (ValueError, IndexError):
            continue

    hour_stats = []
    for hour in range(24):
        data = by_hour[hour]
        hour_stats.append({
            'hour': hour,
            'label': f'{hour:02d}:00',
            'count': data['count'],
            'avgER': round(data['totalER'] / data['count'], 2) if data['count'] > 0 else 0
        })

    # 按星期分組
    weekday_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
    by_weekday = defaultdict(lambda: {'count': 0, 'totalER': 0})
    for post in posts:
        if not post['publishedAt']:
            continue
        try:
            dt = datetime.fromisoformat(post['publishedAt'])
            weekday = dt.weekday()
            by_weekday[weekday]['count'] += 1
            by_weekday[weekday]['totalER'] += post['computed']['engagementRate']
        except (ValueError, TypeError):
            continue

    weekday_stats = []
    for i in range(7):
        data = by_weekday[i]
        weekday_stats.append({
            'weekday': i,
            'name': weekday_names[i],
            'count': data['count'],
            'avgER': round(data['totalER'] / data['count'], 2) if data['count'] > 0 else 0
        })

    # 時段熱力圖 (星期 x 小時)
    heatmap = []
    by_weekday_hour = defaultdict(lambda: {'count': 0, 'totalER': 0})
    for post in posts:
        if not post['publishedAt']:
            continue
        try:
            dt = datetime.fromisoformat(post['publishedAt'])
            key = (dt.weekday(), dt.hour)
            by_weekday_hour[key]['count'] += 1
            by_weekday_hour[key]['totalER'] += post['computed']['engagementRate']
        except (ValueError, TypeError):
            continue

    for weekday in range(7):
        for hour in range(24):
            data = by_weekday_hour[(weekday, hour)]
            heatmap.append({
                'weekday': weekday,
                'weekdayName': weekday_names[weekday],
                'hour': hour,
                'count': data['count'],
                'avgER': round(data['totalER'] / data['count'], 2) if data['count'] > 0 else 0
            })

    return {
        'lastUpdated': datetime.now().isoformat(),
        'totalPosts': len(posts),
        'byActionType': action_stats,
        'byTopic': topic_stats,
        'byHour': hour_stats,
        'byDayOfWeek': weekday_stats,
        'heatmap': heatmap
    }


def parse_section_data(rows, section_marker):
    """
    Parse a section from the sheet data.
    Returns data rows starting after the header row.
    """
    data = []
    in_section = False

    for row in rows:
        # Check for section marker
        first_cell = row.get(list(row.keys())[0] if row else '', '') if row else ''

        if section_marker in str(first_cell):
            in_section = True
            continue

        # Skip empty rows or other section markers
        if in_section:
            if not any(row.values()):
                continue
            # Check if this is another section marker (starts with emoji)
            if first_cell and (first_cell.startswith('📌') or first_cell.startswith('📊') or
                              first_cell.startswith('🔥') or first_cell.startswith('⚖️') or
                              first_cell.startswith('🏆') or first_cell.startswith('📈') or
                              first_cell.startswith('💰')):
                break
            data.append(row)

    return data


def process_content_analysis(raw_rows):
    """處理 content_analysis 資料 (raw 2D array)"""
    by_action_type = []
    by_topic = []
    cross_analysis = []

    current_section = None

    for row in raw_rows:
        if not row:
            continue

        first_val = str(row[0]) if row else ''

        # Detect section headers
        if '行動類型表現' in first_val:
            current_section = 'action'
            continue
        elif '議題表現' in first_val:
            current_section = 'topic'
            continue
        elif '交叉分析' in first_val:
            current_section = 'cross'
            continue

        # Skip header rows (they contain column names like '貼文數')
        if '貼文數' in first_val or first_val == '行動類型' or first_val == '議題' or first_val == '行動':
            continue

        # Skip empty rows
        if not first_val or first_val.strip() == '':
            continue

        # Parse data based on section
        if current_section == 'action' and len(row) >= 7:
            by_action_type.append({
                'actionType': str(row[0]),
                'postCount': parse_int(row[1]),
                'avgER': parse_float(row[2]),
                'avgShareRate': parse_float(row[3]),
                'avgCommentRate': parse_float(row[4]),
                'viralCount': parse_int(row[5]),
                'highCount': parse_int(row[6])
            })
        elif current_section == 'topic' and len(row) >= 7:
            by_topic.append({
                'topic': str(row[0]),
                'postCount': parse_int(row[1]),
                'avgER': parse_float(row[2]),
                'avgShareRate': parse_float(row[3]),
                'avgCommentRate': parse_float(row[4]),
                'viralCount': parse_int(row[5]),
                'highCount': parse_int(row[6])
            })
        elif current_section == 'cross' and len(row) >= 6:
            cross_analysis.append({
                'actionType': str(row[0]),
                'topic': str(row[1]),
                'postCount': parse_int(row[2]),
                'avgER': parse_float(row[3]),
                'avgShareRate': parse_float(row[4]),
                'highPerformerCount': parse_int(row[5])
            })

    return {
        'byActionType': by_action_type,
        'byTopic': by_topic,
        'crossAnalysis': cross_analysis
    }


def process_posts_performance(raw_rows):
    """處理 posts_performance 資料 (raw 2D array)"""
    top_posts = []
    quadrant_analysis = []
    weekly_trends = []

    current_section = None

    for row in raw_rows:
        if not row:
            continue

        first_val = str(row[0]) if row else ''

        # Detect section headers
        if 'Top' in first_val or '貼文排行' in first_val:
            current_section = 'top'
            continue
        elif '象限' in first_val:
            current_section = 'quadrant'
            continue
        elif '週度趨勢' in first_val or '週趨勢' in first_val:
            current_section = 'weekly'
            continue

        # Skip header rows
        if '貼文 ID' in first_val or '週次' in first_val:
            continue

        # Skip empty rows
        if not first_val or first_val.strip() == '':
            continue

        # Parse data based on section
        if current_section == 'top' and len(row) >= 12:
            top_posts.append({
                'postId': str(row[0]),
                'contentPreview': str(row[1]) if len(row) > 1 else '',
                'publishedAt': str(row[2]) if len(row) > 2 else '',
                'actionType': str(row[3]) if len(row) > 3 else '',
                'topic': str(row[4]) if len(row) > 4 else '',
                'timeSlot': str(row[5]) if len(row) > 5 else '',
                'engagementRate': parse_float(row[6]) if len(row) > 6 else 0,
                'performanceTier': str(row[7]) if len(row) > 7 else '',
                'percentileRank': parse_float(row[8]) if len(row) > 8 else 0,
                'reach': parse_int(row[9]) if len(row) > 9 else 0,
                'totalEngagement': parse_int(row[10]) if len(row) > 10 else 0,
                'permalink': str(row[11]) if len(row) > 11 else ''
            })
        elif current_section == 'quadrant' and len(row) >= 11:
            quadrant_analysis.append({
                'postId': str(row[0]),
                'publishedAt': str(row[1]) if len(row) > 1 else '',
                'reach': parse_int(row[2]) if len(row) > 2 else 0,
                'engagementRate': parse_float(row[3]) if len(row) > 3 else 0,
                'medianReach': parse_int(row[4]) if len(row) > 4 else 0,
                'medianER': parse_float(row[5]) if len(row) > 5 else 0,
                'quadrant': str(row[6]) if len(row) > 6 else '',
                'topic': str(row[7]) if len(row) > 7 else '',
                'actionType': str(row[8]) if len(row) > 8 else '',
                'contentPreview': str(row[9]) if len(row) > 9 else '',
                'permalink': str(row[10]) if len(row) > 10 else ''
            })
        elif current_section == 'weekly' and len(row) >= 5:
            weekly_trends.append({
                'weekRange': str(row[0]),
                'postCount': parse_int(row[1]) if len(row) > 1 else 0,
                'avgER': parse_float(row[2]) if len(row) > 2 else 0,
                'totalReach': parse_int(row[3]) if len(row) > 3 else 0,
                'totalEngagement': parse_int(row[4]) if len(row) > 4 else 0
            })

    return {
        'topPosts': top_posts[:100],  # Limit to 100
        'quadrantAnalysis': quadrant_analysis,
        'weeklyTrends': weekly_trends
    }


def process_ad_analytics(raw_rows):
    """處理 ad_analytics 資料 (raw 2D array)"""
    trending_posts = []
    best_combos = []
    recommendations = []
    organic_vs_paid = []
    campaigns = []
    roi_by_type = []

    current_section = None

    for row in raw_rows:
        if not row:
            continue

        first_val = str(row[0]) if row else ''

        # Detect section headers
        if '熱門貼文' in first_val or '近期熱門' in first_val:
            current_section = 'trending'
            continue
        elif '最佳組合' in first_val or '歷史最佳' in first_val:
            current_section = 'combos'
            continue
        elif '投廣推薦' in first_val:
            current_section = 'recommendations'
            continue
        elif '自然 vs 付費' in first_val or '自然vs付費' in first_val:
            current_section = 'organic_paid'
            continue
        elif '廣告活動' in first_val:
            current_section = 'campaigns'
            continue
        elif 'ROI' in first_val or '效益' in first_val:
            current_section = 'roi'
            continue

        # Skip header rows
        if '貼文 ID' in first_val or '議題' in first_val or '類型' in first_val:
            continue

        # Skip empty rows
        if not first_val or first_val.strip() == '':
            continue

        # Parse data based on section
        if current_section == 'trending' and len(row) >= 8:
            trending_posts.append({
                'postId': str(row[0]),
                'messagePreview': str(row[1]) if len(row) > 1 else '',
                'createdTime': str(row[2]) if len(row) > 2 else '',
                'hoursSincePost': parse_int(row[3]) if len(row) > 3 else 0,
                'currentEngagement': parse_int(row[4]) if len(row) > 4 else 0,
                'reach': parse_int(row[5]) if len(row) > 5 else 0,
                'engagementPerHour': parse_float(row[6]) if len(row) > 6 else 0,
                'engagementRate': parse_float(row[7]) if len(row) > 7 else 0
            })
        elif current_section == 'combos' and len(row) >= 7:
            best_combos.append({
                'issueTopic': str(row[0]),
                'formatType': str(row[1]) if len(row) > 1 else '',
                'timeSlot': str(row[2]) if len(row) > 2 else '',
                'dayName': str(row[3]) if len(row) > 3 else '',
                'postCount': parse_int(row[4]) if len(row) > 4 else 0,
                'avgER': parse_float(row[5]) if len(row) > 5 else 0,
                'highPerformers': parse_int(row[6]) if len(row) > 6 else 0
            })
        elif current_section == 'recommendations' and len(row) >= 13:
            recommendations.append({
                'postId': str(row[0]),
                'createdTime': str(row[1]) if len(row) > 1 else '',
                'adRecommendation': str(row[2]) if len(row) > 2 else '',
                'adPotentialScore': parse_int(row[3]) if len(row) > 3 else 0,
                'performanceTier': str(row[4]) if len(row) > 4 else '',
                'formatType': str(row[5]) if len(row) > 5 else '',
                'issueTopic': str(row[6]) if len(row) > 6 else '',
                'breakdown': {
                    'engagementRateScore': parse_float(row[7]) if len(row) > 7 else 0,
                    'shareRateScore': parse_float(row[8]) if len(row) > 8 else 0,
                    'commentRateScore': parse_float(row[9]) if len(row) > 9 else 0,
                    'topicFactor': parse_float(row[10]) if len(row) > 10 else 1,
                    'timeFactor': parse_float(row[11]) if len(row) > 11 else 1
                },
                'permalinkUrl': str(row[12]) if len(row) > 12 else ''
            })
        elif current_section == 'organic_paid' and len(row) >= 8:
            organic_vs_paid.append({
                'type': 'paid' if '廣告' in str(row[0]) or 'paid' in str(row[0]).lower() else 'organic',
                'postCount': parse_int(row[1]) if len(row) > 1 else 0,
                'avgER': parse_float(row[2]) if len(row) > 2 else 0,
                'avgShareRate': parse_float(row[3]) if len(row) > 3 else 0,
                'avgCommentRate': parse_float(row[4]) if len(row) > 4 else 0,
                'avgCTR': parse_float(row[5]) if len(row) > 5 else 0,
                'totalReach': parse_int(row[6]) if len(row) > 6 else 0,
                'totalEngagement': parse_int(row[7]) if len(row) > 7 else 0
            })

    return {
        'trendingPosts': trending_posts,
        'bestCombos': best_combos,
        'recommendations': recommendations[:50],  # Limit to 50
        'organicVsPaid': organic_vs_paid,
        'campaigns': campaigns,
        'roiByType': roi_by_type
    }


def main():
    print('GCAA 社群分析 - 資料同步開始')
    print(f'Service Account: {SERVICE_ACCOUNT_FILE}')
    print(f'Spreadsheet ID: {SPREADSHEET_ID}')

    # 確保輸出目錄存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 連接 Google Sheets
    print('\n連接 Google Sheets...')
    service = get_sheets_service()

    # ===== 1. 讀取 raw_post_insights =====
    print('\n讀取 raw_post_insights...')
    raw_insights = fetch_sheet_data(service, SHEETS['raw_insights'])
    print(f'  - {len(raw_insights)} 筆貼文')

    # 處理資料
    print('\n處理資料...')
    posts = process_insights_data(raw_insights)
    print(f'  - 處理後: {len(posts)} 筆貼文')

    # 生成聚合資料
    daily = generate_daily_data(posts)
    print(f'  - 每日資料: {len(daily)} 天')

    stats = generate_stats(posts)
    print(f'  - 行動類型: {len(stats["byActionType"])} 種')
    print(f'  - 議題: {len(stats["byTopic"])} 種')

    # ===== 2. 讀取 content_analysis =====
    print('\n讀取 content_analysis...')
    try:
        raw_content = fetch_sheet_raw(service, SHEETS['content_analysis'])
        print(f'  - 原始資料: {len(raw_content)} 列')
        content_analysis = process_content_analysis(raw_content)
        print(f'  - 行動類型: {len(content_analysis["byActionType"])} 種')
        print(f'  - 議題: {len(content_analysis["byTopic"])} 種')
        print(f'  - 交叉分析: {len(content_analysis["crossAnalysis"])} 組')
    except Exception as e:
        print(f'  - 讀取失敗: {e}')
        import traceback
        traceback.print_exc()
        content_analysis = {'byActionType': [], 'byTopic': [], 'crossAnalysis': []}

    # ===== 3. 讀取 posts_performance =====
    print('\n讀取 posts_performance...')
    try:
        raw_performance = fetch_sheet_raw(service, SHEETS['posts_performance'])
        print(f'  - 原始資料: {len(raw_performance)} 列')
        posts_performance = process_posts_performance(raw_performance)
        print(f'  - Top 貼文: {len(posts_performance["topPosts"])} 筆')
        print(f'  - 象限分析: {len(posts_performance["quadrantAnalysis"])} 筆')
        print(f'  - 週趨勢: {len(posts_performance["weeklyTrends"])} 週')
    except Exception as e:
        print(f'  - 讀取失敗: {e}')
        import traceback
        traceback.print_exc()
        posts_performance = {'topPosts': [], 'quadrantAnalysis': [], 'weeklyTrends': []}

    # ===== 4. 讀取 ad_analytics =====
    print('\n讀取 ad_analytics...')
    try:
        raw_ads = fetch_sheet_raw(service, SHEETS['ad_analytics'])
        print(f'  - 原始資料: {len(raw_ads)} 列')
        ad_analytics = process_ad_analytics(raw_ads)
        print(f'  - 熱門貼文: {len(ad_analytics["trendingPosts"])} 筆')
        print(f'  - 最佳組合: {len(ad_analytics["bestCombos"])} 組')
        print(f'  - 投廣推薦: {len(ad_analytics["recommendations"])} 筆')
        print(f'  - 自然vs付費: {len(ad_analytics["organicVsPaid"])} 組')
    except Exception as e:
        print(f'  - 讀取失敗: {e}')
        import traceback
        traceback.print_exc()
        ad_analytics = {
            'trendingPosts': [], 'bestCombos': [], 'recommendations': [],
            'organicVsPaid': [], 'campaigns': [], 'roiByType': []
        }

    # ===== 寫入 JSON 檔案 =====
    print('\n寫入 JSON 檔案...')

    # 1. posts.json
    posts_file = os.path.join(OUTPUT_DIR, 'posts.json')
    with open(posts_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f'  - {posts_file}')

    # 2. daily.json
    daily_file = os.path.join(OUTPUT_DIR, 'daily.json')
    with open(daily_file, 'w', encoding='utf-8') as f:
        json.dump(daily, f, ensure_ascii=False, indent=2)
    print(f'  - {daily_file}')

    # 3. stats.json
    stats_file = os.path.join(OUTPUT_DIR, 'stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f'  - {stats_file}')

    # 4. content-analysis.json (NEW)
    content_file = os.path.join(OUTPUT_DIR, 'content-analysis.json')
    with open(content_file, 'w', encoding='utf-8') as f:
        json.dump(content_analysis, f, ensure_ascii=False, indent=2)
    print(f'  - {content_file}')

    # 5. posts-performance.json (NEW)
    performance_file = os.path.join(OUTPUT_DIR, 'posts-performance.json')
    with open(performance_file, 'w', encoding='utf-8') as f:
        json.dump(posts_performance, f, ensure_ascii=False, indent=2)
    print(f'  - {performance_file}')

    # 6. ad-analytics.json (NEW)
    ads_file = os.path.join(OUTPUT_DIR, 'ad-analytics.json')
    with open(ads_file, 'w', encoding='utf-8') as f:
        json.dump(ad_analytics, f, ensure_ascii=False, indent=2)
    print(f'  - {ads_file}')

    print('\n同步完成!')
    print(f'資料更新時間: {stats["lastUpdated"]}')

if __name__ == '__main__':
    main()
