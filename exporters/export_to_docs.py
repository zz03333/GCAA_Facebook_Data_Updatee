"""
Facebook 社群數據分析 - Google Docs 說明文件導出工具
將資料字典與說明文件導出到獨立的 Google Docs
"""

import os
import json
import base64
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Google Docs 設定
DOCS_TITLE = 'Facebook 社群數據分析 - 資料字典'


def setup_google_docs_client():
    """設定 Google Docs 客戶端"""
    try:
        credentials_json = os.environ.get('GCP_SA_CREDENTIALS')
        credentials_base64 = os.environ.get('GCP_SA_CREDENTIALS_BASE64')

        if credentials_base64:
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
        elif not credentials_json:
            print("⚠️  找不到 Google 憑證環境變數")
            print("   請設定 GCP_SA_CREDENTIALS 或 GCP_SA_CREDENTIALS_BASE64")
            return None, None

        credentials_dict = json.loads(credentials_json)

        scope = [
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive'
        ]

        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=scope)

        docs_service = build('docs', 'v1', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        
        print("✓ Google Docs 客戶端設定成功")
        return docs_service, drive_service

    except Exception as e:
        print(f"✗ Google Docs 客戶端設定失敗: {e}")
        return None, None


def find_or_create_document(docs_service, drive_service, title):
    """尋找現有文件或建立新文件"""
    try:
        # 搜尋現有文件
        results = drive_service.files().list(
            q=f"name='{title}' and mimeType='application/vnd.google-apps.document' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            doc_id = files[0]['id']
            print(f"✓ 找到現有文件: {title}")
            return doc_id
        
        # 建立新文件
        document = docs_service.documents().create(body={'title': title}).execute()
        doc_id = document.get('documentId')
        print(f"✓ 已建立新文件: {title}")
        return doc_id
        
    except Exception as e:
        print(f"✗ 尋找/建立文件失敗: {e}")
        return None


def clear_document(docs_service, doc_id):
    """清空文件內容"""
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])
        
        if len(content) > 1:
            end_index = content[-1].get('endIndex', 1) - 1
            if end_index > 1:
                requests = [{
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': end_index
                        }
                    }
                }]
                docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        return True
    except Exception as e:
        print(f"  清空文件時發生錯誤（可忽略）: {e}")
        return True


def build_documentation_content():
    """建立說明文件內容"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = f"""Facebook 社群數據分析 - 資料字典

更新時間: {now}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 工作表說明

Google Sheets 名稱: Faceboook Insights Metrics_Data Warehouse

工作表結構:

1. raw_posts
   說明: 貼文原始資料（ID、內容、發布時間等）
   更新頻率: 每日
   資料來源: Facebook Graph API

2. raw_post_insights
   說明: 貼文洞察數據（觸及、互動、影片觀看等）
   更新頻率: 每日
   資料來源: Facebook Insights API

3. page_daily_metrics
   說明: 頁面每日指標（粉絲數、整體觸及等）
   更新頻率: 每日
   資料來源: Facebook Insights API

4. best_posting_times
   說明: 最佳發文時間分析
   更新頻率: 每日
   資料來源: 分析計算

5. topic_performance
   說明: 主題表現分析
   更新頻率: 每日
   資料來源: 分析計算

6. top_posts
   說明: 表現最佳貼文排名
   更新頻率: 每日
   資料來源: 分析計算

7. weekly_trends
   說明: 週度趨勢
   更新頻率: 每週
   資料來源: 分析計算

8. hourly_performance
   說明: 每小時表現分析
   更新頻率: 每日
   資料來源: 分析計算

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 指標說明

Post Level 貼文層級指標:

• post_impressions_unique
  說明: 觸及人數（不重複用戶）
  單位: 人

• post_clicks
  說明: 貼文點擊數
  單位: 次

• likes_count
  說明: 按讚數（含所有心情）
  單位: 次

• comments_count
  說明: 留言數
  單位: 則

• shares_count
  說明: 分享數
  單位: 次

• engagement_rate
  說明: 互動率 = (讚+留言+分享) / 觸及人數 × 100
  單位: %

• post_video_views
  說明: 影片觀看次數（3秒以上）
  單位: 次

• post_video_views_organic
  說明: 自然觸及影片觀看
  單位: 次

• post_video_views_paid
  說明: 付費觸及影片觀看
  單位: 次

心情 Reactions 指標:
• post_reactions_like_total - 讚
• post_reactions_love_total - 愛心
• post_reactions_wow_total - 哇
• post_reactions_haha_total - 哈哈
• post_reactions_sorry_total - 嗚嗚
• post_reactions_anger_total - 怒

Page Level 頁面層級指標:

• fan_count
  說明: 粉絲專頁粉絲數
  單位: 人

• page_impressions_unique
  說明: 頁面每日觸及人數
  單位: 人

• page_post_engagements
  說明: 頁面每日互動數
  單位: 次

• page_video_views
  說明: 頁面每日影片觀看數
  單位: 次

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 注意事項

1. Facebook API 對超過 90 天的 Insights 數據有存取限制
2. 部分指標已被 Facebook 棄用（如 post_impressions, post_impressions_organic）
3. 資料收集時間為 UTC 時區

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

技術資訊:
- 資料來源: Facebook Graph API v23.0
- 儲存格式: SQLite + Google Sheets
- 自動化: Cloud Run + Cloud Scheduler
"""
    return content


def export_to_google_docs():
    """主程式 - 導出說明文件到 Google Docs"""
    print("\n" + "="*60)
    print("Facebook 資料字典導出至 Google Docs")
    print("="*60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 設定客戶端
    docs_service, drive_service = setup_google_docs_client()
    if not docs_service or not drive_service:
        print("\n✗ 無法設定 Google Docs 客戶端")
        return False, None

    # 尋找或建立文件
    doc_id = find_or_create_document(docs_service, drive_service, DOCS_TITLE)
    if not doc_id:
        return False, None

    # 清空現有內容
    clear_document(docs_service, doc_id)

    # 建立內容
    content = build_documentation_content()
    
    # 寫入內容
    try:
        requests = [{
            'insertText': {
                'location': {'index': 1},
                'text': content
            }
        }]
        
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        
        print(f"\n{'='*60}")
        print(f"✓ 說明文件導出成功！")
        print(f"文件名稱: {DOCS_TITLE}")
        print(f"文件連結: {doc_url}")
        print(f"{'='*60}\n")
        
        return True, doc_url
        
    except Exception as e:
        print(f"✗ 寫入文件失敗: {e}")
        return False, None


def main():
    """主程式入口"""
    success, url = export_to_google_docs()
    return success


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
