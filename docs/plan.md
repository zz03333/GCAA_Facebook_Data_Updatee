# **Facebook Insights 自動化數據抓取工具開發計畫**

## **1\. 專案目標**

本專案旨在開發一個自動化工具，定期從 Facebook Graph API 獲取指定粉絲專頁的洞察報告（Insights）數據，並將其彙整至指定的 Google Sheets 工作表中。此工具將取代手動複製貼上數據的繁瑣流程，提升公民團體在社群媒體數據分析上的效率與準確性，讓我們能更專注於數據解讀與策略擬定。

## **2\. 環境設定與前置作業**

為了讓團隊成員都能順利執行與協作，我們將採用以雲端為基礎的開發環境。

### **2.1. 開發環境：Google Colab**

* **說明**：Google Colab 是一個免費的雲端 Jupyter Notebook 環境，內建了多數常用的 Python 數據科學函式庫，無需在本機端安裝與設定，只要有瀏覽器即可使用。  
* **優點**：  
  * **無需設定**：省去繁瑣的本機 Python 環境設定。  
  * **方便協作**：團隊成員可以輕易地共享、檢視與編輯同一個 Notebook 檔案。  
  * **整合 Google 服務**：能順暢地與 Google Sheets、Google Drive 等服務串接。  
* **執行方式**：將我們提供的 `.ipynb` 檔案上傳至 Google Colab 即可開始執行。

### **2.2. 相依套件 (Python Libraries)**

專案將使用以下 Python 函式庫，這些在 Google Colab 中多數已預先安裝，若有缺少，可在 Notebook 中透過 `!pip install` 指令安裝。

* `requests`: 用於發送 HTTP 請求至 Facebook Graph API。  
* `pandas`: 用於數據處理與整理，將 API 回傳的 JSON 資料轉換為結構化的 DataFrame。  
* `gspread`: 用於與 Google Sheets API 互動，將處理好的數據寫入指定的試算表。  
* `google-auth`: 用於 Google 服務的身份驗證。

### **2.3. 憑證與授權 (Credentials & Authorization)**

在執行程式前，需要完成以下授權設定：

* **Facebook Graph API Access Token**:  
  * **用途**：作為呼叫 Facebook API 的身份驗證金鑰。  
  * **需求**：需要一個**長期有效 (Long-lived)** 的 Access Token，以避免頻繁重新授權。  
  * **權限 (Permissions)**：此 Token 必須包含 `read_insights` 與 `pages_read_engagement` 權限。  
  * **提供資訊**：你已經提供了所需的 App ID、Page ID 與 Long-lived access token。  
* **Google Cloud Platform (GCP) Service Account**:  
  * **用途**：讓我們的 Python 程式能以服務帳號的身份，自動化地存取 Google Sheets，而不需要每次都手動登入 Google 帳號。  
  * **設定步驟**：  
    1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。  
    2. 建立一個新的專案（或使用現有專案）。  
    3. 在「IAM 與管理員」\>「服務帳戶」中，建立一個新的服務帳戶。  
    4. 為此服務帳戶產生一個 JSON 格式的金鑰，並將其下載保存（例如命名為 `credentials.json`）。**此金鑰非常重要，請妥善保管，切勿公開**。  
    5. 啟用專案的 **Google Drive API** 與 **Google Sheets API**。  
    6. 將服務帳戶的電子郵件地址（格式如 `your-service-account@your-project.iam.gserviceaccount.com`），加入目標 Google Sheets 的共享清單中，並給予「編輯者」權限。

## **3\. 開發流程設計**

程式的執行流程將分為以下幾個主要步驟：

1. **載入設定與憑證**：  
   * 讀取 Facebook API 的相關設定（Page ID, Access Token）。  
   * 使用 `credentials.json` 金鑰檔案，進行 Google 服務的身份驗證。  
2. **定義欲抓取的數據指標 (Metrics)**：  
   * 在程式碼中明確定義一個列表，包含所有我們希望從 Facebook Insights API 獲取的指標名稱（例如：`page_impressions`, `page_engaged_users` 等）。  
   * 這個列表將方便我們未來彈性增減所需指標。  
3. **呼叫 Facebook Graph API**：  
   * 建構 API 請求的 URL，指定 Page ID、欲抓取的 `metrics` 以及時間範圍 (`since`, `until`)。  
   * 使用 `requests` 函式庫發送 GET 請求。  
   * 處理 API 回應，檢查是否有錯誤發生。  
4. **解析與整理數據**：  
   * API 回傳的資料為 JSON 格式，其中每個指標的數據結構可能不盡相同。  
   * 我們需要編寫一個解析函式，將巢狀的 JSON 資料攤平，轉換為一個乾淨、二維的表格格式。  
   * 使用 `pandas` 將整理好的資料轉換為 DataFrame，方便後續操作。DataFrame 的欄位應包含：`end_time`（數據日期）、`metric_name`（指標名稱）、`value`（指標數值）。  
5. **寫入 Google Sheets**：  
   * 使用 `gspread` 函式庫，開啟指定的 Google Sheets 檔案（`Faceboook Insights Metrics_Data Warehouse`）與工作表（`raw_data`）。  
   * 將 `pandas` DataFrame 中的數據，附加（append）到 `raw_data` 工作表的末端。  
   * **注意**：為避免重複寫入，我們可以在寫入前先檢查工作表中是否已存在相同日期與指標的數據。但初期版本可先以附加方式實現。

## **4\. 功能需求與特定規範**

### **4.1. 重要更新：已棄用指標 (CRITICAL)**

**⚠️ 根據最新 Facebook API 文件（2025年11月1日生效）：**

以下指標已被棄用，API 將回傳無效指標錯誤：
- `page_impressions*` (所有 page_impressions 相關指標)
- `page_engaged_users`
- `page_impressions_frequency_distribution`
- `post_impressions*` (所有 post_impressions 相關指標)

### **4.2. 目前可用的 Page Insights 指標**

⚠️ **重要更新 (2025年8月27日)**：經最新測試驗證，以下指標仍可使用但將於 2025年11月1日棄用，應視為短期過渡方案：

**即將棄用但目前仍可用的指標**：
- `page_impressions_unique` - 頁面觸及人數
- `page_impressions_paid` - 付費的頁面曝光次數
- 所有 `page_impressions` 相關指標
- 所有 `post_impressions` 相關指標  
- 所有 `page_fans` 相關指標

**確認可用的穩定指標 (未列於棄用清單)**：

**貼文互動指標**：
- `post_reactions_like_total` - 貼文的「讚」總數
- `post_reactions_love_total` - 貼文的「大心」總數  
- `post_reactions_wow_total` - 貼文的「哇」總數

**影片廣告時段指標**：
- `page_daily_video_ad_break_ad_impressions_by_crosspost_status` - 每日頁面影片廣告時段的曝光次數 (依交叉發布狀態區分)
- `post_video_ad_break_ad_impressions` - 貼文影片廣告時段的曝光次數

**已確認棄用的指標 (自 2024年3月14日起)**：
- `page_consumptions` - 頁面消費次數
- `page_content_activity` - 頁面內容活動
- `page_content_activity_unique` - 唯一頁面內容活動
- `page_engaged_users` - 頁面互動用戶
- `page_fans_gender_age` - 粉絲性別年齡分布
- 所有 `page_views_*` 相關指標
- `post_activity` - 貼文活動
- `post_activity_unique` - 唯一貼文活動

**可用於 breakdowns 參數的維度欄位**：
- `age` - 年齡區間
- `gender` - 性別
- `country` - 國家
- `region` - 地區  
- `device_platform` - 裝置平台
- `publisher_platform` - 發布平台
- `platform_position` - 平台版位
- `impression_device` - 曝光裝置

### **4.3. 核心功能**

* **從 Facebook API 獲取數據**：使用指定的 Page ID 與 Access Token，向 Graph API 的 `/{page-id}/insights` 端點發送請求，並獲取可用指標數據。  
* **數據時間範圍**：程式應能設定欲抓取數據的起始與結束日期。初期可設定為抓取「昨天」的數據。  
* **數據指標彈性**：將目前可用的指標列表設計為可配置的變數，方便未來調整。  
* **數據寫入 Google Sheets**：將抓取並整理後的數據，正確寫入指定的 Google Sheets 工作表中。

### **4.4. 數據格式規範**

寫入 `raw_data` 工作表的數據，應至少包含以下欄位：

| 欄位名稱 (Header) | 說明 | 範例 |
| ----- | ----- | ----- |
| `fetch_date` | 執行程式抓取數據的日期 | `2023-10-27` |
| `data_date` | 該筆數據所代表的日期 | `2023-10-26` |
| `metric` | 指標的名稱 | `page_impressions_unique` |
| `period` | 指標的計算週期 (day, week, days\_28) | `day` |
| `value` | 指標的數值 | `15023` |

### **4.5. 錯誤處理**

* **API 請求失敗**：若呼叫 Facebook API 失敗（例如：網路問題、Token 失效），程式應能捕捉錯誤並印出有意義的錯誤訊息。  
* **Google Sheets 寫入失敗**：若寫入 Google Sheets 失敗（例如：權限不足、找不到工作表），程式也應提示錯誤。

## **5. 更新後的實作策略 - 改為貼文層級數據**

### **5.1. 重要變更：從頁面層級改為貼文層級數據**

根據最新需求，本工具將調整為抓取**貼文層級 (Post-level)** 的數據，而非頁面層級 (Page-level) 的洞察報告。這將更符合 Facebook Insights 匯出報表的格式，包含每則貼文的詳細資訊與互動數據。

### **5.2. 貼文層級數據結構**

每則貼文將包含以下資訊：

**基本資訊欄位**：
- `post_id` - 貼文編號
- `page_id` - 粉絲專頁編號
- `page_name` - 粉絲專頁名稱
- `message` - 貼文文字內容
- `created_time` - 發佈時間
- `permalink_url` - 永久連結
- `type` - 貼文類型 (相片/影片/連結/狀態)

**互動指標欄位** (透過 `/{post-id}/insights` API)：
- `post_impressions` - 觸及相關指標
- `post_engaged_users` - 互動用戶數
- `post_reactions_*` - 各種心情反應數 (讚、愛心、哇等)
- `post_clicks` - 點擊次數
- `post_video_views` - 影片觀看次數 (如為影片貼文)

### **5.3. API 端點使用**

1. **取得貼文列表**：`GET /{page-id}/posts` 或 `/{page-id}/published_posts`
   - 參數：`fields=id,message,created_time,permalink_url,type,shares`
   - 取得指定時間範圍內的所有貼文

2. **取得貼文洞察數據**：`GET /{post-id}/insights`
   - 參數：`metric=post_reactions_like_total,post_reactions_love_total,...`
   - 針對每則貼文取得詳細的互動指標

3. **貼文基本統計**：直接從貼文物件取得
   - `likes.summary(true)` - 讚數
   - `comments.summary(true)` - 留言數
   - `shares` - 分享數

### **5.4. 實作優先順序 (已更新)**

1. **基礎架構**：建立 API 連接和 Google Sheets 整合 ✅ 已完成
2. **取得貼文列表**：實作從頁面取得所有貼文的功能 ✅ 已完成
3. **取得貼文詳細資訊**：針對每則貼文取得完整欄位資料 ✅ 已完成
4. **取得貼文洞察數據**：呼叫 insights API 取得互動指標 ✅ 已完成
5. **數據整合與寫入**：將所有數據整合為單一表格，寫入 Google Sheets ✅ 已完成

**✅ 實作完成日期：2025-09-30**

### **5.5. 數據格式更新**

寫入 Google Sheets 的數據格式將調整為**每列代表一則貼文**，包含所有相關欄位：

| 欄位名稱 | 說明 | 範例 |
|---------|------|------|
| `post_id` | 貼文編號 | `123456789_987654321` |
| `page_id` | 粉絲專頁編號 | `123456789` |
| `page_name` | 粉絲專頁名稱 | `綠色公民行動聯盟` |
| `message` | 貼文內容 | `氣候臨界影展 觀影指南懶人包...` |
| `created_time` | 發佈時間 | `2025-04-21T14:54:00+0000` |
| `permalink_url` | 永久連結 | `https://www.facebook.com/...` |
| `type` | 貼文類型 | `photo` |
| `likes_count` | 讚數 | `282` |
| `comments_count` | 留言數 | `9` |
| `shares_count` | 分享數 | `35` |
| `post_impressions` | 觸及人數 | `14247` |
| `post_engaged_users` | 互動用戶數 | `326` |
| ... | 其他互動指標 | ... |

### **5.6. Google Cloud 憑證設定**

- 服務帳戶 JSON 檔案位置：`/content/drive/MyDrive/Colab Notebooks/gemini-api-reports-3a9837dee55c.json`
- 此路徑已針對 Google Colab 環境設定

---

## **6. 實作完成摘要**

### **6.1. 已實現功能**

**核心功能**：
- ✅ Facebook API 連接測試
- ✅ 貼文列表獲取（支援日期範圍篩選和分頁）
- ✅ 貼文詳細資訊獲取（ID、內容、時間、類型、連結）
- ✅ 基本互動統計（讚數、留言數、分享數）
- ✅ 貼文 Insights 指標獲取（觸及、點擊、反應等 17 項指標）
- ✅ 數據處理與結構化
- ✅ Google Sheets 自動寫入

**輔助功能**：
- ✅ 批次處理多個時間段
- ✅ 週/月範圍自動生成
- ✅ 錯誤處理與重試機制
- ✅ API 速率限制控制
- ✅ 詳細的執行日誌
- ✅ 系統診斷工具

### **6.2. 技術架構**

**API 端點使用**：
1. `GET /{page-id}` - 驗證頁面存取權限
2. `GET /{page-id}/posts` - 獲取貼文列表（支援 pagination）
3. `GET /{post-id}/insights` - 獲取貼文 insights 數據

**數據流程**：
```
Facebook API → 貼文列表 → 逐則獲取 Insights → 數據整合 → DataFrame → Google Sheets
```

**貼文數據欄位**：
- 基本欄位：fetch_date, post_id, page_id, page_name, message, created_time, permalink_url, type
- 互動欄位：likes_count, comments_count, shares_count
- Insights 欄位：post_impressions, post_engaged_users, post_reactions_*, post_video_* 等

### **6.3. 使用方式**

**基本執行**（收集最近 7 天）：
```python
success = main_posts_collection()
```

**指定日期範圍**：
```python
success = main_posts_collection(
    since_date='2025-08-01',
    until_date='2025-08-31',
    include_insights=True
)
```

**批次執行**：
```python
weekly_ranges = generate_weekly_ranges(4)
batch_posts_collection(weekly_ranges)
```

### **6.4. 注意事項**

1. **Access Token 管理**：
   - ✅ 已升級為 **Page Access Token**（2025-09-30）
   - 有效期約 60 天，需定期更新
   - 具備 `pages_read_engagement` 權限，可完整存取貼文數據

2. **API 速率限制**：
   - 每則貼文的 insights 請求之間延遲 0.2 秒
   - 批次執行時，每個時間段之間延遲 5 秒
   - 可根據實際狀況調整

3. **指標可用性** (已更新 - 2025-09-30)：
   - **已測試可用的指標 (14 項)**：
     - `post_clicks` - 貼文點擊次數
     - `post_impressions`, `post_impressions_unique`, `post_impressions_organic`, `post_impressions_paid` - 觸及相關
     - `post_reactions_like_total`, `post_reactions_love_total`, `post_reactions_wow_total`, `post_reactions_haha_total`, `post_reactions_sorry_total`, `post_reactions_anger_total` - 反應數
     - `post_video_views`, `post_video_views_organic`, `post_video_views_paid` - 影片相關
   - **已移除的無效指標 (3 項)**：
     - `post_engaged_users` (API 不支援)
     - `post_clicks_unique` (API 不支援)
     - `post_video_view_time` (無數據返回)

4. **數據品質**：
   - 某些貼文（如分享貼文）可能無法獲取 insights
   - Insights 數據可能有 24-48 小時的延遲
   - 建議避免抓取「今天」的數據

5. **API 棄用欄位問題** (已解決 - 2025-09-30)：
   - ✅ 移除了 `type` 欄位（在 v3.3+ 已棄用，會觸發錯誤）
   - ✅ 移除了 `likes.summary(true)` 和 `comments.summary(true)` 的內嵌語法
   - ✅ 改用獨立 API 請求獲取 reactions、comments 和 shares 數據
   - ✅ 將 `likes_count` 改為 `reactions_count`（更符合 Facebook 新 API）

### **6.5. 後續優化建議**

- [ ] 實作增量更新機制（避免重複抓取已有的貼文）
- [ ] 加入 Page Access Token 自動獲取流程
- [ ] 實作更精細的錯誤分類與處理
- [ ] 加入數據視覺化面板
- [ ] 建立自動化排程執行機制（如 Cloud Scheduler）

---

## **7. 頁面層級 Insights 收集器實作**

### **7.1. 實作完成日期**

**✅ 實作完成日期：2025-10-02**

### **7.2. 實現功能**

**核心功能**：
- ✅ Facebook API 連接測試（包含粉絲數、追蹤者數）
- ✅ 頁面層級每日 Insights 獲取（支援日期範圍篩選）
- ✅ 終身指標獲取（粉絲數、追蹤者數）
- ✅ 數據處理與結構化（以日期為主鍵）
- ✅ Google Sheets 自動寫入（含去重機制）
- ✅ 自動建立新工作表（若不存在）

**技術架構**：
1. `GET /{page-id}` - 驗證頁面存取權限與獲取終身指標
2. `GET /{page-id}/insights` - 獲取每日頁面 Insights 數據

**數據流程**：
```
Facebook API → 終身指標 + 每日 Insights → 數據整合 → DataFrame → Google Sheets (raw_page_data)
```

### **7.3. 頁面數據欄位**

**基本欄位**：
- `fetch_date` - 數據抓取日期
- `data_date` - 數據所屬日期
- `page_id` - 粉絲專頁 ID

**每日指標**（period=day）：
- `page_impressions_unique` - 頁面觸及人數
- `page_post_engagements` - 貼文互動數
- `page_video_views` - 影片觀看次數
- `page_actions_post_reactions_total` - 貼文心情總數

**終身指標**：
- `fan_count` - 粉絲總數
- `followers_count` - 追蹤者總數

### **7.4. 使用方式**

**基本執行**（收集最近 90 天）：
```python
success = main_page_collection()
```

**指定日期範圍**：
```python
success = main_page_collection(
    since_date='2025-09-01',
    until_date='2025-09-30'
)
```

### **7.5. 注意事項**

1. **指標可用性**：
   - 許多 `page_*` 指標已被 Facebook API 棄用
   - 當前實作使用的 4 個每日指標為測試後確認可用的指標
   - 如指標無效，API 會返回錯誤，需參考 '合併文章總集.md' 更新指標列表

2. **數據結構差異**：
   - 頁面層級數據：每列代表**一天**的數據
   - 貼文層級數據：每列代表**一則貼文**的數據
   - 兩者儲存在不同工作表（raw_page_data vs raw_data）

3. **去重機制**：
   - 使用 `page_id + data_date` 作為唯一鍵
   - 自動跳過已存在的日期數據

4. **檔案位置**：
   - 檔案名稱：`page_insights_collector.ipynb`
   - 上傳至 Google Colab 執行
   - 工作表名稱：`raw_page_data`

### **7.6. 與貼文層級收集器的關係**

**互補性**：
- `facebook_insights_collector.ipynb` - 收集**貼文層級**數據（每則貼文的詳細表現）
- `page_insights_collector.ipynb` - 收集**頁面層級**數據（整體頁面的每日表現）

**共同特點**：
- 使用相同的 Facebook API 設定與憑證
- 使用相同的 Google Sheets 試算表（不同工作表）
- 採用相同的程式架構與錯誤處理模式

---

## **8. Dashboard 視覺化介面實作**

### **8.1. 實作完成日期**

**✅ 初版完成日期：2026-01-16**

### **8.2. 技術架構**

**前端技術**：
- React 18 + TypeScript
- Vite 7 建置工具
- Recharts 圖表庫
- Tailwind CSS v4 樣式框架

**資料流程**：
```
Cloud Run (08:00) → Meta API → Google Sheets
GitHub Actions (08:30) → Sheets 同步 → 靜態 JSON → 部署 GitHub Pages
```

**部署平台**：
- GitHub Pages: https://zz03333.github.io/gcaa-fb-dashboard/
- Firebase Hosting: https://esg-reports-collection.web.app/

### **8.3. 已實現功能**

**Dashboard 總覽**：
- ✅ KPI 卡片（貼文數、互動率、觸及、分享）- 支援多選最多 2 項
- ✅ 趨勢分析圖表 - 7 天對比功能，顯示實際日期與星期
- ✅ 行動類型表現圖 - 下拉選單切換指標
- ✅ 議題表現圖 - 下拉選單切換指標
- ✅ 發文時段熱力圖 - 可隱藏低數據時段、點擊篩選貼文

**貼文瀏覽**：
- ✅ 貼文列表篩選（時間、行動類型、議題）
- ✅ 搜尋功能
- ✅ 排序功能（日期、互動率、觸及、分享）
- ✅ 貼文時間戳記顯示小時分鐘

**分析頁面**：
- ✅ 散點圖分析（觸及 vs 互動率）

**廣告分析**：
- ✅ 廣告成效追蹤

**內容分析**：
- ✅ 內容類型分析

### **8.4. 自動化部署**

**GitHub Actions 工作流程**：

1. **觸發條件**：
   - 每日 08:30 (UTC 00:30) 排程執行
   - Cloud Run pipeline 完成後觸發 (`repository_dispatch`)
   - 手動觸發 (`workflow_dispatch`)
   - 推送到 main 分支

2. **部署流程**：
   - 同步資料：從 Google Sheets 下載最新資料到 `public/data/*.json`
   - 建置：`npm run build`
   - 部署：GitHub Pages

### **8.5. 已修復問題**

- ✅ 黑屏問題 - 刪除重複的 `useData.js` 檔案（與 `.ts` 衝突）
- ✅ Firebase 初始化錯誤處理
- ✅ 改用靜態 JSON 作為主要資料來源（更穩定）
- ✅ Bundle 大小優化（從 666KB 減少到 520KB）

### **8.6. 待完成功能**

- [ ] 趨勢圖範圍選取（brush）功能
- [ ] Tooltip 點擊篩選該日貼文
- [ ] 貼文數量顯示說明文件

