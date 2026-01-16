/**
 * GCAA Dashboard - Hooks Index
 */

// Main data hook
export { useData, useFilteredData } from './useData';

// New data hooks
export {
  useAdAnalytics,
  useAdAnalyticsMetrics,
} from './useAdAnalytics';

export {
  useContentAnalysis,
  useSortedActionTypes,
  useSortedTopics,
  useCrossAnalysisHeatmap,
  useContentAnalyticsMetrics,
} from './useContentAnalysis';

export {
  usePostsPerformance,
  useSortedTopPosts,
  useQuadrantData,
  useWeeklyTrends,
  usePerformanceMetrics,
} from './usePostsPerformance';
