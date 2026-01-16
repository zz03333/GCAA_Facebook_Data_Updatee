/**
 * GCAA Dashboard - Constants
 */

import type { TabConfig, TimeRange } from '@/types';

// Time range options for filter
export const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '1', label: '1 週' },
  { value: '2', label: '2 週' },
  { value: '4', label: '1 月' },
  { value: '12', label: '3 月' },
  { value: '26', label: '6 月' },
  { value: '52', label: '1 年' },
  { value: 'all', label: '全部' },
  { value: 'custom', label: '自訂' },
];

// Navigation tabs configuration
export const TABS: TabConfig[] = [
  { id: 'dashboard', label: '總覽' },
  { id: 'explorer', label: '貼文' },
  { id: 'analytics', label: '分析' },
  { id: 'ads', label: '廣告' },
  { id: 'content', label: '內容' },
];

// Default filter state
export const DEFAULT_FILTER_STATE = {
  timeRange: '4' as TimeRange,
  dateRange: { start: null, end: null },
  actionType: null,
  topic: null,
  search: '',
  sortBy: 'date' as const,
  sortOrder: 'desc' as const,
};

// Chart metric options
export const METRIC_OPTIONS = [
  { value: 'totalReach', label: '觸及人數' },
  { value: 'totalEngagement', label: '總互動數' },
  { value: 'avgEngagementRate', label: '平均互動率' },
  { value: 'totalShares', label: '分享數' },
  { value: 'totalClicks', label: '點擊數' },
  { value: 'postCount', label: '發文數' },
];

// Scatter chart axis options
export const SCATTER_AXIS_OPTIONS = [
  { value: 'reach', label: '觸及人數' },
  { value: 'engagementRate', label: '互動率' },
  { value: 'shares', label: '分享數' },
  { value: 'clicks', label: '點擊數' },
  { value: 'likes', label: '按讚數' },
  { value: 'comments', label: '留言數' },
  { value: 'totalEngagement', label: '總互動數' },
];

// Weekday names in Chinese
export const WEEKDAY_NAMES = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];

// Hour labels for heatmap
export const HOUR_LABELS = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

// Performance tier thresholds (percentile-based)
export const PERFORMANCE_TIERS = {
  viral: { min: 95, label: '熱門', color: '#ef4444' },
  high: { min: 75, label: '優質', color: '#22c55e' },
  average: { min: 25, label: '一般', color: '#f59e0b' },
  low: { min: 0, label: '低表現', color: '#64748b' },
};

// API / Data paths
export const DATA_PATHS = {
  posts: '/data/posts.json',
  daily: '/data/daily.json',
  stats: '/data/stats.json',
  adAnalytics: '/data/ad-analytics.json',
  contentAnalysis: '/data/content-analysis.json',
  postsPerformance: '/data/posts-performance.json',
};

// Firestore collection names
export const FIRESTORE_COLLECTIONS = {
  posts: 'posts',
  dailyMetrics: 'dailyMetrics',
  aggregates: 'aggregates',
  metadata: 'metadata',
  adAnalytics: 'adAnalytics',
  contentAnalysis: 'contentAnalysis',
  postsPerformance: 'postsPerformance',
};

// Animation durations (in ms)
export const ANIMATION = {
  fast: 150,
  base: 250,
  slow: 400,
  chart: 500,
};

// Breakpoints for responsive design
export const BREAKPOINTS = {
  sm: 480,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1440,
};

// Maximum items to display
export const LIMITS = {
  postsPerPage: 50,
  topPosts: 100,
  recentDays: 90,
  heatmapWeeks: 12,
};

// GCAA branding
export const BRANDING = {
  name: 'GCAA 社群分析',
  fullName: '綠色公民行動聯盟 社群分析儀表板',
  facebookUrl: 'https://www.facebook.com/gcaa.org.tw',
  website: 'https://www.gcaa.org.tw',
};
