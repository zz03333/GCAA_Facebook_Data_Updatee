/**
 * GCAA Dashboard - Content Analysis Hook
 *
 * Fetches content analysis data from static JSON.
 */

import { useState, useEffect, useMemo } from 'react';
import type { ContentAnalysisData, UseContentAnalysisReturn } from '@/types';
import { DATA_PATHS } from '@/utils/constants';

/**
 * useContentAnalysis Hook
 *
 * Fetches content analysis data including action type performance,
 * topic performance, and cross-analysis matrix.
 */
export function useContentAnalysis(): UseContentAnalysisReturn {
  const [data, setData] = useState<ContentAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData(): Promise<void> {
      try {
        setLoading(true);
        setError(null);

        const base = import.meta.env.BASE_URL || '/';
        const response = await fetch(
          `${base}${DATA_PATHS.contentAnalysis.slice(1)}`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch content analysis: ${response.status}`);
        }

        const jsonData = (await response.json()) as ContentAnalysisData;
        setData(jsonData);
        console.log('✓ Loaded content analysis data');
      } catch (err) {
        console.error('Error fetching content analysis:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Get sorted action types by a specific metric
 */
export function useSortedActionTypes(
  data: ContentAnalysisData | null,
  sortBy: 'postCount' | 'avgER' | 'avgShareRate' = 'postCount'
) {
  return useMemo(() => {
    if (!data?.byActionType) return [];

    return [...data.byActionType].sort((a, b) => {
      switch (sortBy) {
        case 'postCount':
          return b.postCount - a.postCount;
        case 'avgER':
          return b.avgER - a.avgER;
        case 'avgShareRate':
          return b.avgShareRate - a.avgShareRate;
        default:
          return 0;
      }
    });
  }, [data, sortBy]);
}

/**
 * Get sorted topics by a specific metric
 */
export function useSortedTopics(
  data: ContentAnalysisData | null,
  sortBy: 'postCount' | 'avgER' | 'avgShareRate' = 'postCount'
) {
  return useMemo(() => {
    if (!data?.byTopic) return [];

    return [...data.byTopic].sort((a, b) => {
      switch (sortBy) {
        case 'postCount':
          return b.postCount - a.postCount;
        case 'avgER':
          return b.avgER - a.avgER;
        case 'avgShareRate':
          return b.avgShareRate - a.avgShareRate;
        default:
          return 0;
      }
    });
  }, [data, sortBy]);
}

/**
 * Transform cross-analysis data into heatmap format
 */
export function useCrossAnalysisHeatmap(data: ContentAnalysisData | null) {
  return useMemo(() => {
    if (!data?.crossAnalysis) return { cells: [], actionTypes: [], topics: [] };

    // Get unique action types and topics
    const actionTypes = [...new Set(data.crossAnalysis.map((c) => c.actionType))];
    const topics = [...new Set(data.crossAnalysis.map((c) => c.topic))];

    // Find max values for normalization
    const maxCount = Math.max(...data.crossAnalysis.map((c) => c.postCount));
    const maxER = Math.max(...data.crossAnalysis.map((c) => c.avgER));

    // Create cell data with normalized intensity
    const cells = data.crossAnalysis.map((cell) => ({
      ...cell,
      countIntensity: maxCount > 0 ? cell.postCount / maxCount : 0,
      erIntensity: maxER > 0 ? cell.avgER / maxER : 0,
    }));

    return { cells, actionTypes, topics };
  }, [data]);
}

/**
 * Calculate aggregate metrics from content analysis data
 */
export function useContentAnalyticsMetrics(data: ContentAnalysisData | null) {
  return useMemo(() => {
    if (!data) {
      return {
        totalActionTypes: 0,
        totalTopics: 0,
        topActionType: null,
        topTopic: null,
        avgEngagementRate: 0,
      };
    }

    const totalActionTypes = data.byActionType?.length || 0;
    const totalTopics = data.byTopic?.length || 0;

    // Find top performing action type by engagement rate
    const topActionType = data.byActionType?.reduce(
      (best, current) => (current.avgER > (best?.avgER || 0) ? current : best),
      data.byActionType[0]
    );

    // Find top performing topic by engagement rate
    const topTopic = data.byTopic?.reduce(
      (best, current) => (current.avgER > (best?.avgER || 0) ? current : best),
      data.byTopic[0]
    );

    // Calculate overall average engagement rate
    const totalPosts = data.byActionType?.reduce((sum, a) => sum + a.postCount, 0) || 0;
    const weightedER =
      data.byActionType?.reduce((sum, a) => sum + a.avgER * a.postCount, 0) || 0;
    const avgEngagementRate = totalPosts > 0 ? weightedER / totalPosts : 0;

    return {
      totalActionTypes,
      totalTopics,
      topActionType,
      topTopic,
      avgEngagementRate,
    };
  }, [data]);
}
