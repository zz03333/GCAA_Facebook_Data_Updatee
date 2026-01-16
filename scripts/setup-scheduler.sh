#!/bin/bash

# 設定 Cloud Scheduler 的腳本
# 在 Cloud Run 服務部署完成後執行此腳本

set -e

PROJECT_ID="gemini-api-reports"
SERVICE_NAME="facebook-insights-collector"
REGION="asia-east1"
SCHEDULER_NAME="facebook-insights-daily-collection"

echo "正在取得 Cloud Run 服務 URL..."

# 取得 Cloud Run 服務 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)' \
  --project ${PROJECT_ID})

if [ -z "$SERVICE_URL" ]; then
    echo "✗ 無法取得服務 URL，請確認 Cloud Run 服務已部署"
    exit 1
fi

echo "✓ 服務 URL: ${SERVICE_URL}"

# 檢查是否已存在排程
if gcloud scheduler jobs describe ${SCHEDULER_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} &> /dev/null; then

    echo "排程已存在，正在更新..."
    gcloud scheduler jobs update http ${SCHEDULER_NAME} \
        --location=${REGION} \
        --schedule="0 8 * * *" \
        --uri="${SERVICE_URL}/" \
        --http-method=POST \
        --time-zone="Asia/Taipei" \
        --attempt-deadline=900s \
        --project=${PROJECT_ID}
else
    echo "建立新的排程..."
    gcloud scheduler jobs create http ${SCHEDULER_NAME} \
        --location=${REGION} \
        --schedule="0 8 * * *" \
        --uri="${SERVICE_URL}/" \
        --http-method=POST \
        --time-zone="Asia/Taipei" \
        --attempt-deadline=900s \
        --project=${PROJECT_ID}
fi

echo ""
echo "✓ Cloud Scheduler 設定完成！"
echo ""
echo "排程資訊："
echo "  名稱: ${SCHEDULER_NAME}"
echo "  時區: Asia/Taipei (GMT+8)"
echo "  執行時間: 每天早上 8:00"
echo ""
echo "手動測試排程："
echo "  gcloud scheduler jobs run ${SCHEDULER_NAME} --location=${REGION} --project=${PROJECT_ID}"
