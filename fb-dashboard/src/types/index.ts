/**
 * GCAA Dashboard - TypeScript Type Definitions
 *
 * This file contains all TypeScript interfaces for the dashboard data.
 */

// ============================================================================
// Core Post Types (existing)
// ============================================================================

export interface Reactions {
  like: number;
  love: number;
  wow: number;
  haha: number;
  sad: number;
  angry: number;
}

export interface PostMetrics {
  likes: number;
  comments: number;
  shares: number;
  clicks: number;
  reach: number;
  videoViews: number;
  reactions: Reactions;
}

export interface ComputedMetrics {
  engagementRate: number;
  totalEngagement: number;
  shareRate: number;
  performanceTier?: PerformanceTier;
  percentileRank?: number;
}

export type PerformanceTier = 'viral' | 'high' | 'average' | 'low';

export type ActionType =
  | '行動號召'
  | '定期活動'
  | '記者會'
  | '聲明稿'
  | '新聞觀點'
  | '投書'
  | '報告發布'
  | '擺攤資訊'
  | '科普/Podcast'
  | '其他行動 (無關鍵字匹配)'
  | '其他';

export type Topic =
  | '核能發電'
  | '氣候問題'
  | '淨零政策'
  | '產業分析'
  | '能源發展'
  | '其他議題'
  | '其他議題 (無關鍵字匹配)'
  | '其他';

export type MediaType = 'text' | 'image' | 'video' | 'link';

export interface Post {
  id: string;
  publishedAt: string | null;
  content: string;
  contentPreview: string;
  hashtags?: string[];
  actionType: ActionType | string;
  topic: Topic | string;
  mediaType?: MediaType;
  permalink: string;
  isPromoted?: boolean;
  adStatus?: string;
  adSpend?: number;
  metrics: PostMetrics;
  computed: ComputedMetrics;
}

// ============================================================================
// Daily Metrics (existing)
// ============================================================================

export interface DailyMetric {
  date: string;
  postCount: number;
  totalReach: number;
  totalEngagement: number;
  avgEngagementRate: number;
  totalShares: number;
  totalClicks: number;
}

// ============================================================================
// Stats / Aggregates (existing)
// ============================================================================

export interface ActionTypeStats {
  name: string;
  count: number;
  avgER: number;
  avgReach: number;
}

export interface TopicStats {
  name: string;
  count: number;
  avgER: number;
  avgReach: number;
}

export interface HourStats {
  hour: number;
  label: string;
  count: number;
  avgER: number;
}

export interface WeekdayStats {
  weekday: number;
  name: string;
  count: number;
  avgER: number;
}

export interface HeatmapCell {
  weekday: number;
  weekdayName: string;
  hour: number;
  count: number;
  avgER: number;
}

export interface Stats {
  lastUpdated: string;
  totalPosts: number;
  byActionType: ActionTypeStats[];
  byTopic: TopicStats[];
  byHour: HourStats[];
  byDayOfWeek: WeekdayStats[];
  heatmap: HeatmapCell[];
}

// ============================================================================
// Ad Analytics Types (NEW)
// ============================================================================

export interface TrendingPost {
  postId: string;
  messagePreview: string;
  createdTime: string;
  hoursSincePost: number;
  currentEngagement: number;
  reach: number;
  engagementPerHour: number;
  engagementRate: number;
}

export interface BestCombo {
  issueTopic: string;
  formatType: string;
  timeSlot: string;
  dayName: string;
  postCount: number;
  avgER: number;
  highPerformers: number;
}

export interface AdRecommendation {
  postId: string;
  createdTime: string;
  adRecommendation: string;
  adPotentialScore: number;
  performanceTier: PerformanceTier | string;
  formatType: string;
  issueTopic: string;
  breakdown: {
    engagementRateScore: number;
    shareRateScore: number;
    commentRateScore: number;
    topicFactor: number;
    timeFactor: number;
  };
  permalinkUrl: string;
}

export interface OrganicVsPaid {
  type: 'organic' | 'paid';
  postCount: number;
  avgER: number;
  avgShareRate: number;
  avgCommentRate: number;
  avgCTR: number;
  totalReach: number;
  totalEngagement: number;
}

export interface Campaign {
  campaignId: string;
  name: string;
  objective: string;
  status: string;
  totalSpend: number;
  impressions: number;
  clicks: number;
  cpm: number;
  cpc: number;
  ctr: number;
  startTime?: string;
  endTime?: string;
}

export interface ROIByType {
  actionType: string;
  topic: string;
  adCount: number;
  totalSpend: number;
  impressions: number;
  clicks: number;
  avgCPM: number;
  avgCPC: number;
  avgCTR: number;
}

export interface AdAnalyticsData {
  trendingPosts: TrendingPost[];
  bestCombos: BestCombo[];
  recommendations: AdRecommendation[];
  organicVsPaid: OrganicVsPaid[];
  campaigns: Campaign[];
  roiByType: ROIByType[];
}

// ============================================================================
// Content Analysis Types (NEW)
// ============================================================================

export interface ActionTypePerformance {
  actionType: string;
  postCount: number;
  avgER: number;
  avgShareRate: number;
  avgCommentRate: number;
  viralCount: number;
  highCount: number;
}

export interface TopicPerformance {
  topic: string;
  postCount: number;
  avgER: number;
  avgShareRate: number;
  avgCommentRate: number;
  viralCount: number;
  highCount: number;
}

export interface CrossAnalysisCell {
  actionType: string;
  topic: string;
  postCount: number;
  avgER: number;
  avgShareRate: number;
  highPerformerCount: number;
}

export interface ContentAnalysisData {
  byActionType: ActionTypePerformance[];
  byTopic: TopicPerformance[];
  crossAnalysis: CrossAnalysisCell[];
}

// ============================================================================
// Posts Performance Types (NEW)
// ============================================================================

export interface TopPost {
  postId: string;
  contentPreview: string;
  publishedAt: string;
  actionType: string;
  topic: string;
  timeSlot: string;
  engagementRate: number;
  er?: number; // alias for engagementRate
  performanceTier: PerformanceTier | string;
  percentileRank: number;
  reach: number;
  shares?: number;
  clicks?: number;
  totalEngagement: number;
  permalink: string;
}

// Quadrant values from the data (Chinese labels)
export type Quadrant =
  | '明星內容'      // high-reach-high-er
  | '潛力內容'      // high-reach-low-er
  | '利基內容'      // low-reach-high-er
  | '常態內容';     // low-reach-low-er

export interface QuadrantPost {
  postId: string;
  publishedAt: string;
  reach: number;
  engagementRate: number;
  er?: number; // alias for engagementRate
  medianReach: number;
  medianER: number;
  quadrant: Quadrant | string;
  topic: string;
  actionType: string;
  contentPreview: string;
  permalink: string;
}

export interface WeeklyTrend {
  weekRange: string;
  weekStart: string;
  weekEnd: string;
  postCount: number;
  avgER: number;
  totalReach: number;
  totalEngagement: number;
}

export interface PostsPerformanceData {
  topPosts: TopPost[];
  quadrantAnalysis: QuadrantPost[];
  weeklyTrends: WeeklyTrend[];
}

// ============================================================================
// Filter Types
// ============================================================================

export interface DateRange {
  start: string | null;
  end: string | null;
}

export type TimeRange = '1' | '2' | '4' | '12' | '26' | '52' | 'all' | 'custom';

export interface FilterState {
  timeRange: TimeRange;
  dateRange: DateRange;
  actionType: string | null;
  topic: string | null;
  search: string;
  sortBy: 'date' | 'engagement' | 'reach' | 'shares';
  sortOrder: 'asc' | 'desc';
  // Hour/weekday filter for heatmap click
  hour?: number | null;
  weekday?: number | null;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseDataReturn {
  posts: Post[];
  daily: DailyMetric[];
  stats: Stats | null;
  loading: boolean;
  error: string | null;
}

export interface UseAdAnalyticsReturn {
  data: AdAnalyticsData | null;
  loading: boolean;
  error: string | null;
}

export interface UseContentAnalysisReturn {
  data: ContentAnalysisData | null;
  loading: boolean;
  error: string | null;
}

export interface UsePostsPerformanceReturn {
  data: PostsPerformanceData | null;
  loading: boolean;
  error: string | null;
}

// ============================================================================
// Chart Types
// ============================================================================

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface ScatterDataPoint {
  x: number;
  y: number;
  label?: string;
  category?: string;
  size?: number;
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface KPICardProps {
  title: string;
  value: number;
  format?: 'number' | 'percent' | 'currency';
  color?: 'primary' | 'secondary' | 'tertiary' | 'warning';
  selected?: boolean;
  onClick?: () => void;
}

export interface CardProps {
  title?: string;
  children: React.ReactNode;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
  className?: string;
}

// ============================================================================
// Tab / Navigation Types
// ============================================================================

export type TabId = 'dashboard' | 'explorer' | 'analytics' | 'ads' | 'content';

export interface TabConfig {
  id: TabId;
  label: string;
  icon?: string;
}
