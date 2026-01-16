# GCAA 社群分析 Dashboard - 設定指南

## 📁 專案位置
```
/Users/jinsoon/Desktop/GCAA/社群宣傳/fb-dashboard/
```

## 🔧 需要手動設定

### 1. Firebase Web App 設定

請到 [Firebase Console](https://console.firebase.google.com/) 完成以下步驟：

1. 開啟專案 `esg-reports-collection`（或建立新專案）
2. 點擊 **專案設定** (齒輪圖示)
3. 往下滾到 **您的應用程式**
4. 點擊 **新增應用程式** → 選擇 **Web** (</> 圖示)
5. 輸入名稱：`GCAA Social Dashboard`
6. 勾選 **同時設定 Firebase Hosting**
7. 點擊 **註冊應用程式**
8. 複製顯示的 `firebaseConfig` 設定

### 2. 更新 config.js

將複製的設定貼到 `public/js/config.js`：

```javascript
const firebaseConfig = {
    apiKey: "你的-api-key",
    authDomain: "你的專案.firebaseapp.com",
    projectId: "你的專案",
    storageBucket: "你的專案.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef123456"
};
```

### 3. 啟用 Google 登入

1. 在 Firebase Console → **Authentication** → **Sign-in method**
2. 點擊 **Google** → 啟用
3. 選擇專案支援電子郵件
4. 儲存

### 4. 設定 Google Sheets API Key

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇你的專案
3. 前往 **APIs & Services** → **Credentials**
4. 點擊 **Create Credentials** → **API Key**
5. 限制金鑰只能存取 Google Sheets API
6. 將 API Key 貼到 `config.js` 的 `SHEETS_CONFIG.apiKey`

### 5. 設定公司 email 網域

在 `config.js` 中更新允許的網域：

```javascript
const ALLOWED_DOMAINS = [
    'gcaa.org.tw',  // 你的公司網域
    // 'gmail.com'  // 測試用，正式上線請移除
];
```

---

## 🚀 本地測試

```bash
cd /Users/jinsoon/Desktop/GCAA/社群宣傳/fb-dashboard

# 安裝 Firebase CLI（如尚未安裝）
npm install -g firebase-tools

# 登入 Firebase
firebase login

# 本地預覽
firebase serve
```

瀏覽器開啟 http://localhost:5000

---

## 📤 部署到 Firebase Hosting

```bash
firebase deploy 
```

部署完成後會得到網址：`https://你的專案.web.app`
