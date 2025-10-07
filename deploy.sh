#!/bin/bash

# Facebook Insights Collector - Cloud Run 部署腳本

set -e  # 發生錯誤時立即停止

# ==================== 設定區 ====================

PROJECT_ID="401828143560"  # 你的 GCP Project ID
SERVICE_NAME="facebook-insights-collector"
REGION="asia-east1"  # 台灣區域
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== 檢查必要工具 ====================

echo -e "${YELLOW}檢查必要工具...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}✗ gcloud CLI 未安裝${NC}"
    echo "請先安裝 Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安裝${NC}"
    echo "請先安裝 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓ 工具檢查完成${NC}"

# ==================== 設定 GCP 專案 ====================

echo -e "\n${YELLOW}設定 GCP 專案...${NC}"
gcloud config set project ${PROJECT_ID}
echo -e "${GREEN}✓ 專案設定為: ${PROJECT_ID}${NC}"

# ==================== 啟用必要的 API ====================

echo -e "\n${YELLOW}啟用必要的 GCP API...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    --project=${PROJECT_ID}

echo -e "${GREEN}✓ API 已啟用${NC}"

# ==================== 建立 Docker 映像 ====================

echo -e "\n${YELLOW}建立 Docker 映像...${NC}"
docker build -t ${IMAGE_NAME} .
echo -e "${GREEN}✓ Docker 映像建立完成${NC}"

# ==================== 推送映像到 Google Container Registry ====================

echo -e "\n${YELLOW}推送映像到 GCR...${NC}"

# 配置 Docker 認證
gcloud auth configure-docker --quiet

# 推送映像
docker push ${IMAGE_NAME}
echo -e "${GREEN}✓ 映像已推送到 GCR${NC}"

# ==================== 部署到 Cloud Run ====================

echo -e "\n${YELLOW}部署到 Cloud Run...${NC}"

# 檢查是否已有服務帳戶憑證設定
if [ -z "${GCP_SA_CREDENTIALS}" ]; then
    echo -e "${RED}✗ 請先設定 GCP_SA_CREDENTIALS 環境變數${NC}"
    echo "範例："
    echo "export GCP_SA_CREDENTIALS=\$(cat /path/to/service-account-key.json)"
    exit 1
fi

# 部署服務
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --memory=512Mi \
    --timeout=540 \
    --set-env-vars="GCP_SA_CREDENTIALS=${GCP_SA_CREDENTIALS}" \
    --set-env-vars="FACEBOOK_ACCESS_TOKEN=${FACEBOOK_ACCESS_TOKEN:-}" \
    --project=${PROJECT_ID}

echo -e "${GREEN}✓ Cloud Run 服務部署完成${NC}"

# 獲取服務 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --format='value(status.url)' \
    --project=${PROJECT_ID})

echo -e "\n${GREEN}=== 部署成功 ===${NC}"
echo -e "服務 URL: ${SERVICE_URL}"
echo -e "\n測試服務："
echo -e "  curl ${SERVICE_URL}/health"
echo -e "\n手動觸發數據收集："
echo -e "  curl -X POST ${SERVICE_URL}/"

# ==================== 設定 Cloud Scheduler ====================

echo -e "\n${YELLOW}是否要設定 Cloud Scheduler 自動排程？ (y/n)${NC}"
read -r SETUP_SCHEDULER

if [ "$SETUP_SCHEDULER" = "y" ]; then
    echo -e "\n${YELLOW}設定 Cloud Scheduler...${NC}"

    SCHEDULER_NAME="facebook-insights-daily-collection"
    SCHEDULER_TIMEZONE="Asia/Taipei"  # GMT+8
    SCHEDULER_SCHEDULE="0 8 * * *"     # 每天早上 8:00

    # 檢查是否已存在排程
    if gcloud scheduler jobs describe ${SCHEDULER_NAME} \
        --location=${REGION} \
        --project=${PROJECT_ID} &> /dev/null; then

        echo -e "${YELLOW}排程已存在，正在更新...${NC}"
        gcloud scheduler jobs update http ${SCHEDULER_NAME} \
            --location=${REGION} \
            --schedule="${SCHEDULER_SCHEDULE}" \
            --uri="${SERVICE_URL}/" \
            --http-method=POST \
            --time-zone="${SCHEDULER_TIMEZONE}" \
            --project=${PROJECT_ID}
    else
        echo -e "${YELLOW}建立新的排程...${NC}"
        gcloud scheduler jobs create http ${SCHEDULER_NAME} \
            --location=${REGION} \
            --schedule="${SCHEDULER_SCHEDULE}" \
            --uri="${SERVICE_URL}/" \
            --http-method=POST \
            --time-zone="${SCHEDULER_TIMEZONE}" \
            --project=${PROJECT_ID}
    fi

    echo -e "${GREEN}✓ Cloud Scheduler 設定完成${NC}"
    echo -e "\n排程資訊："
    echo -e "  名稱: ${SCHEDULER_NAME}"
    echo -e "  時區: ${SCHEDULER_TIMEZONE}"
    echo -e "  執行時間: 每天早上 8:00 (GMT+8)"
    echo -e "\n手動觸發排程測試："
    echo -e "  gcloud scheduler jobs run ${SCHEDULER_NAME} --location=${REGION} --project=${PROJECT_ID}"
fi

echo -e "\n${GREEN}=== 所有設定完成 ===${NC}"
