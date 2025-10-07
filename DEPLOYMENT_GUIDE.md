# Facebook Insights Collector - Cloud Run 部署指南

此指南將協助你將 Facebook Insights 自動化工具部署到 Google Cloud Run，並設定每日自動執行。

## 📋 前置準備

### 1. 必要工具

- **Google Cloud SDK (gcloud CLI)**
  - 安裝: https://cloud.google.com/sdk/docs/install
  - 驗證安裝: `gcloud --version`

- **Docker**
  - 安裝: https://docs.docker.com/get-docker/
  - 驗證安裝: `docker --version`

### 2. GCP 專案設定

你已經有 GCP 專案 ID: `401828143560`

### 3. 服務帳戶金鑰

確保你已經完成以下步驟：

#### a. 建立服務帳戶（如果尚未建立）

1. 前往 [Google Cloud Console](https://console.cloud.google.com)
2. 選擇專案 `401828143560`
3. 前往「IAM 與管理員」>「服務帳戶」
4. 點擊「建立服務帳戶」
   - 名稱: `facebook-insights-bot`
   - 角色: 無需額外角色（權限由 Google Sheets 共享控制）
5. 點擊「完成」

#### b. 產生 JSON 金鑰

1. 在服務帳戶列表中，找到剛建立的帳戶
2. 點擊「操作」(三個點) >「管理金鑰」
3. 點擊「新增金鑰」>「建立新的金鑰」
4. 選擇 **JSON** 格式
5. 下載並妥善保管 JSON 檔案（例如命名為 `service-account-key.json`）

#### c. 分享 Google Sheet 給服務帳戶

1. 打開下載的 JSON 檔案
2. 複製 `client_email` 欄位的值（類似 `facebook-insights-bot@PROJECT_ID.iam.gserviceaccount.com`）
3. 前往你的 Google Sheet: **Faceboook Insights Metrics_Data Warehouse**
4. 點擊右上角「共用」
5. 貼上服務帳戶的 email
6. 設定權限為「編輯者」
7. 點擊「傳送」

#### d. 啟用必要的 API

執行以下命令啟用 API：

```bash
gcloud config set project 401828143560

gcloud services enable \
    drive.googleapis.com \
    sheets.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com
```

## 🚀 部署步驟

### 步驟 1: 設定環境變數

在終端機中設定必要的環境變數：

```bash
# 設定服務帳戶憑證（將 JSON 檔案內容轉為環境變數）
export GCP_SA_CREDENTIALS=$(cat /path/to/service-account-key.json)

# 設定 Facebook Access Token（選擇性，也可以在部署後從 Cloud Console 設定）
export FACEBOOK_ACCESS_TOKEN="你的_Facebook_Access_Token"
```

**重要提醒**：
- 將 `/path/to/service-account-key.json` 替換為你實際的檔案路徑
- Facebook Access Token 可以從你的 Facebook App 取得

### 步驟 2: 執行部署腳本

```bash
# 切換到專案目錄
cd /Users/jinsoon/Documents/GCAA/社群宣傳/API_Parser

# 執行部署腳本
./deploy.sh
```

部署腳本會自動完成以下工作：
1. ✅ 檢查必要工具
2. ✅ 設定 GCP 專案
3. ✅ 啟用必要的 API
4. ✅ 建立 Docker 映像
5. ✅ 推送映像到 Google Container Registry
6. ✅ 部署到 Cloud Run
7. ✅ 設定 Cloud Scheduler（每天早上 8:00 GMT+8）

### 步驟 3: 驗證部署

部署完成後，你會看到服務 URL，例如：
```
https://facebook-insights-collector-xxxx-de.a.run.app
```

測試服務是否正常運作：

```bash
# 健康檢查
curl https://YOUR_SERVICE_URL/health

# 手動觸發數據收集
curl -X POST https://YOUR_SERVICE_URL/
```

## ⏰ Cloud Scheduler 設定

### 自動排程資訊

- **執行時間**: 每天早上 8:00
- **時區**: Asia/Taipei (GMT+8)
- **Cron 表達式**: `0 8 * * *`

### 手動測試排程

```bash
gcloud scheduler jobs run facebook-insights-daily-collection \
    --location=asia-east1 \
    --project=401828143560
```

### 查看排程狀態

```bash
gcloud scheduler jobs describe facebook-insights-daily-collection \
    --location=asia-east1 \
    --project=401828143560
```

### 查看執行歷史

前往 [Cloud Scheduler Console](https://console.cloud.google.com/cloudscheduler)，選擇你的專案，即可查看執行歷史和日誌。

## 🔧 進階設定

### 更新環境變數（無需重新部署）

如果你需要更新 Facebook Access Token：

```bash
gcloud run services update facebook-insights-collector \
    --region=asia-east1 \
    --update-env-vars="FACEBOOK_ACCESS_TOKEN=新的_Token" \
    --project=401828143560
```

### 查看服務日誌

```bash
# 查看最近的日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=facebook-insights-collector" \
    --limit=50 \
    --format=json \
    --project=401828143560
```

或前往 [Cloud Logging Console](https://console.cloud.google.com/logs)

### 修改排程時間

如果需要更改執行時間：

```bash
gcloud scheduler jobs update http facebook-insights-daily-collection \
    --location=asia-east1 \
    --schedule="0 9 * * *" \
    --time-zone="Asia/Taipei" \
    --project=401828143560
```

## 📊 監控與維護

### 查看 Cloud Run 服務狀態

前往 [Cloud Run Console](https://console.cloud.google.com/run)

你可以看到：
- 請求數量
- 錯誤率
- 延遲時間
- 記憶體使用量

### 設定警報（選擇性）

你可以在 Cloud Console 設定警報，當服務出現錯誤時收到通知：

1. 前往「監控」>「警報」
2. 建立新的警報政策
3. 選擇指標：Cloud Run > 請求計數 > 錯誤率
4. 設定通知管道（Email、SMS 等）

## 💰 成本估算

Cloud Run 採用按需付費：

- **免費額度**（每月）:
  - 200 萬次請求
  - 360,000 GB-秒的記憶體
  - 180,000 vCPU-秒的 CPU 時間

- **你的用量估算**:
  - 每天執行 1 次
  - 每月約 30 次請求
  - 預計在免費額度內

Cloud Scheduler:
- 每月前 3 個作業免費
- 你只有 1 個作業，完全免費

**總結**: 基本上不會產生費用 💚

## 🔒 安全性建議

1. **不要將服務帳戶 JSON 金鑰上傳到 GitHub**
   - 已在 `.gitignore` 中排除
   - 使用環境變數傳遞

2. **定期更新 Access Token**
   - Facebook Access Token 有效期限
   - 建議設定為長期 Token

3. **限制服務帳戶權限**
   - 只共享必要的 Google Sheets
   - 不要授予專案層級的權限

## ❓ 疑難排解

### 問題 1: 部署時 Docker 推送失敗

**解決方法**:
```bash
gcloud auth configure-docker
docker push gcr.io/401828143560/facebook-insights-collector
```

### 問題 2: Cloud Run 服務返回 500 錯誤

**檢查事項**:
1. 確認環境變數 `GCP_SA_CREDENTIALS` 設定正確
2. 確認 Facebook Access Token 有效
3. 查看日誌: `gcloud logging read ...`

### 問題 3: 無法寫入 Google Sheets

**檢查事項**:
1. 服務帳戶 email 是否已加入 Google Sheet 的編輯者
2. Google Sheets API 是否已啟用
3. 試算表名稱是否正確：`Faceboook Insights Metrics_Data Warehouse`

### 問題 4: Cloud Scheduler 未執行

**檢查事項**:
1. Cloud Scheduler API 是否已啟用
2. 時區設定是否正確
3. 查看排程日誌

## 📞 取得協助

- [Cloud Run 文件](https://cloud.google.com/run/docs)
- [Cloud Scheduler 文件](https://cloud.google.com/scheduler/docs)
- [Facebook Graph API 文件](https://developers.facebook.com/docs/graph-api)

---

## 快速命令參考

```bash
# 部署服務
./deploy.sh

# 查看服務狀態
gcloud run services describe facebook-insights-collector --region=asia-east1 --project=401828143560

# 手動執行排程
gcloud scheduler jobs run facebook-insights-daily-collection --location=asia-east1 --project=401828143560

# 查看日誌
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --project=401828143560

# 更新環境變數
gcloud run services update facebook-insights-collector \
    --region=asia-east1 \
    --update-env-vars="KEY=VALUE" \
    --project=401828143560
```

祝部署順利！🎉
