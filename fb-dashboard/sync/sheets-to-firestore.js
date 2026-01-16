/**
 * Google Sheets to Firestore Sync Script
 *
 * This script reads data from Google Sheets and syncs it to Firestore
 * for real-time dashboard updates.
 *
 * Usage:
 *   npm run sync          - Run once
 *   npm run sync:watch    - Run continuously (every 5 minutes)
 *
 * Prerequisites:
 *   1. Create a service account in Firebase Console for 'facebook-reports-e388f'
 *   2. Download the JSON key and save as 'serviceAccountKey.json' in this directory
 *   3. Grant the service account access to Firestore (Cloud Datastore User role)
 *   4. Run: npm install
 */

const admin = require('firebase-admin');
const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

// Configuration
const CONFIG = {
    // Google Sheets settings (same as frontend config.js)
    sheets: {
        spreadsheetId: '1HJXQrlB0eYJsHmioLMNfCKV_OXHqqgwtwRtO9s5qbB0',
        apiKey: '***REMOVED***', // For fallback
        sheetNames: {
            weeklyTrends: 'weekly_trends',
            formatType: 'format_type_performance',
            issueTopic: 'issue_topic_performance',
            hourlyPerformance: 'hourly_performance',
            bestTimes: 'best_posting_times',
            topPosts: 'top_posts',
            rawPosts: 'raw_posts'
        }
    },
    // Firebase project ID (same as service account)
    firebaseProjectId: 'esg-reports-collection',
    // Sync interval in milliseconds (5 minutes)
    syncInterval: 5 * 60 * 1000
};

// Service account key path options
const SERVICE_ACCOUNT_PATHS = [
    path.join(__dirname, 'serviceAccountKey.json'),
    path.join(__dirname, '..', 'esg-reports-collection-9661012923ed.json'),
];

// Find service account key
function findServiceAccountKey() {
    for (const keyPath of SERVICE_ACCOUNT_PATHS) {
        if (fs.existsSync(keyPath)) {
            console.log(`Using service account key: ${keyPath}`);
            return require(keyPath);
        }
    }
    throw new Error(
        'Service account key not found. Please create one:\n' +
        '1. Go to Firebase Console > Project Settings > Service Accounts\n' +
        '2. Click "Generate New Private Key"\n' +
        '3. Save as "sync/serviceAccountKey.json"'
    );
}

// Initialize Firebase Admin
function initFirebase() {
    const serviceAccount = findServiceAccountKey();

    admin.initializeApp({
        credential: admin.credential.cert(serviceAccount),
        projectId: CONFIG.firebaseProjectId
    });

    return admin.firestore();
}

// Initialize Google Sheets API
async function initSheetsAPI() {
    const serviceAccount = findServiceAccountKey();

    const auth = new google.auth.GoogleAuth({
        credentials: serviceAccount,
        scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly']
    });

    const sheets = google.sheets({ version: 'v4', auth });
    return sheets;
}

// Fetch data from a sheet
async function fetchSheetData(sheets, sheetName) {
    try {
        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: CONFIG.sheets.spreadsheetId,
            range: sheetName
        });

        const values = response.data.values;
        if (!values || values.length < 2) {
            console.log(`No data in sheet: ${sheetName}`);
            return [];
        }

        // Convert to objects using first row as headers
        const headers = values[0];
        return values.slice(1).map(row => {
            const obj = {};
            headers.forEach((header, i) => {
                obj[header] = row[i] || '';
            });
            return obj;
        });
    } catch (error) {
        console.error(`Error fetching ${sheetName}:`, error.message);
        return [];
    }
}

// Sync weekly trends to Firestore
async function syncWeeklyTrends(db, data) {
    if (!data || data.length === 0) return 0;

    const batch = db.batch();
    const collection = db.collection('weeklyTrends');

    data.forEach(row => {
        const dateRange = row['週次 (日期範圍)'] || '';
        const docId = dateRange.replace(/[\/\s~]/g, '_') || `week_${Date.now()}`;

        const docRef = collection.doc(docId);
        batch.set(docRef, {
            dateRange: dateRange,
            postCount: parseInt(row['貼文數'] || 0),
            totalReach: parseInt(row['總觸及'] || 0),
            totalEngagement: parseInt(row['總互動數'] || 0),
            avgEngagementRate: parseFloat(row['平均互動率 (%)'] || 0),
            updatedAt: admin.firestore.FieldValue.serverTimestamp()
        }, { merge: true });
    });

    await batch.commit();
    return data.length;
}

// Sync raw posts to Firestore
async function syncPosts(db, data) {
    if (!data || data.length === 0) return 0;

    const collection = db.collection('posts');
    let count = 0;

    // Process in batches of 500 (Firestore limit)
    const batchSize = 500;
    for (let i = 0; i < data.length; i += batchSize) {
        const batch = db.batch();
        const chunk = data.slice(i, i + batchSize);

        chunk.forEach(row => {
            const postId = row['Post ID'] || row['貼文 ID'] || `post_${Date.now()}_${Math.random()}`;
            const docRef = collection.doc(postId.replace(/[\/]/g, '_'));

            batch.set(docRef, {
                postId: postId,
                content: row['內容'] || row['Content'] || '',
                reach: parseInt(row['觸及'] || row['Reach'] || 0),
                engagementRate: parseFloat(row['互動率 (%)'] || row['ER (%)'] || 0),
                totalInteractions: parseInt(row['互動數'] || row['Interactions'] || 0),
                likes: parseInt(row['讚'] || row['Likes'] || 0),
                comments: parseInt(row['留言'] || row['Comments'] || 0),
                shares: parseInt(row['分享'] || row['Shares'] || 0),
                formatType: row['行動'] || row['Format'] || '',
                issueTopic: row['議題'] || row['Issue'] || '',
                performanceTier: row['表現等級'] || '',
                permalink: row['連結'] || row['Permalink'] || '',
                postedAt: row['發布時間']
                    ? admin.firestore.Timestamp.fromDate(new Date(row['發布時間']))
                    : admin.firestore.FieldValue.serverTimestamp(),
                updatedAt: admin.firestore.FieldValue.serverTimestamp()
            }, { merge: true });
        });

        await batch.commit();
        count += chunk.length;
    }

    return count;
}

// Sync aggregates to Firestore
async function syncAggregates(db, format, issue, hourly, bestTimes, topPosts) {
    const collection = db.collection('aggregates');
    const batch = db.batch();

    // Format performance
    batch.set(collection.doc('formatPerformance'), {
        data: format.map(row => ({
            '行動': row['行動'] || '',
            '貼文數': parseInt(row['貼文數'] || 0),
            '平均互動率 (%)': parseFloat(row['平均互動率 (%)'] || 0),
            '爆款數 (前5%)': parseInt(row['爆款數 (前5%)'] || 0)
        })),
        updatedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // Issue performance
    batch.set(collection.doc('issuePerformance'), {
        data: issue.map(row => ({
            '議題': row['議題'] || '',
            '貼文數': parseInt(row['貼文數'] || 0),
            '平均互動率 (%)': parseFloat(row['平均互動率 (%)'] || 0)
        })),
        updatedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // Hourly performance
    batch.set(collection.doc('hourlyPerformance'), {
        data: hourly.map(row => ({
            '時間': row['時間'] || '',
            '貼文數': parseInt(row['貼文數'] || 0),
            '平均互動率 (%)': parseFloat(row['平均互動率 (%)'] || 0)
        })),
        updatedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // Best times
    batch.set(collection.doc('bestTimes'), {
        data: bestTimes.slice(0, 5).map(row => ({
            '星期': row['星期'] || '',
            '時段': row['時段'] || '',
            '平均互動率 (%)': row['平均互動率 (%)'] || '',
            '貼文數': row['貼文數'] || ''
        })),
        updatedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // Top posts
    batch.set(collection.doc('topPosts'), {
        data: topPosts.slice(0, 10).map(row => ({
            '貼文 ID': row['貼文 ID'] || '',
            '內容預覽': row['內容預覽'] || '',
            '行動': row['行動'] || '',
            '議題': row['議題'] || '',
            '表現等級': row['表現等級'] || '',
            '互動率 (%)': row['互動率 (%)'] || '',
            '連結': row['連結'] || ''
        })),
        updatedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    await batch.commit();
    return 5; // Number of aggregate docs
}

// Update sync metadata
async function updateSyncMetadata(db, status, details = {}) {
    await db.collection('metadata').doc('lastSync').set({
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        status: status,
        ...details
    });
}

// Main sync function
async function syncAll() {
    console.log('\n========================================');
    console.log('Starting sync:', new Date().toLocaleString('zh-TW'));
    console.log('========================================\n');

    try {
        const db = admin.apps.length ? admin.firestore() : initFirebase();
        const sheets = await initSheetsAPI();

        // Fetch all data from Google Sheets
        console.log('Fetching data from Google Sheets...');
        const [weeklyTrends, formatType, issueTopic, hourly, bestTimes, topPosts, rawPosts] = await Promise.all([
            fetchSheetData(sheets, CONFIG.sheets.sheetNames.weeklyTrends),
            fetchSheetData(sheets, CONFIG.sheets.sheetNames.formatType),
            fetchSheetData(sheets, CONFIG.sheets.sheetNames.issueTopic),
            fetchSheetData(sheets, CONFIG.sheets.sheetNames.hourlyPerformance),
            fetchSheetData(sheets, CONFIG.sheets.sheetNames.bestTimes),
            fetchSheetData(sheets, CONFIG.sheets.sheetNames.topPosts),
            fetchSheetData(sheets, CONFIG.sheets.sheetNames.rawPosts)
        ]);

        console.log(`Fetched: weekly=${weeklyTrends.length}, format=${formatType.length}, issue=${issueTopic.length}, hourly=${hourly.length}, bestTimes=${bestTimes.length}, topPosts=${topPosts.length}, rawPosts=${rawPosts.length}`);

        // Sync to Firestore
        console.log('\nSyncing to Firestore...');

        const weeklyCount = await syncWeeklyTrends(db, weeklyTrends);
        console.log(`  Weekly trends: ${weeklyCount} documents`);

        const postsCount = await syncPosts(db, rawPosts);
        console.log(`  Posts: ${postsCount} documents`);

        const aggCount = await syncAggregates(db, formatType, issueTopic, hourly, bestTimes, topPosts);
        console.log(`  Aggregates: ${aggCount} documents`);

        // Update metadata
        await updateSyncMetadata(db, 'success', {
            weeklyCount,
            postsCount,
            aggregatesCount: aggCount
        });

        console.log('\nSync completed successfully!');
        return true;

    } catch (error) {
        console.error('\nSync failed:', error);

        try {
            const db = admin.apps.length ? admin.firestore() : null;
            if (db) {
                await updateSyncMetadata(db, 'failed', { error: error.message });
            }
        } catch (e) {
            // Ignore metadata update errors
        }

        return false;
    }
}

// Watch mode - continuous sync
async function watchMode() {
    console.log('Starting watch mode...');
    console.log(`Sync interval: ${CONFIG.syncInterval / 1000} seconds`);

    // Initial sync
    await syncAll();

    // Schedule periodic syncs
    setInterval(async () => {
        await syncAll();
    }, CONFIG.syncInterval);
}

// Main entry point
async function main() {
    const args = process.argv.slice(2);

    if (args.includes('--watch') || args.includes('-w')) {
        await watchMode();
    } else {
        await syncAll();
        process.exit(0);
    }
}

main().catch(console.error);
