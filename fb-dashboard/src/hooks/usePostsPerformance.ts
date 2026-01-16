/**
 * GCAA Dashboard - Posts Performance Hook
 *
 * Fetches posts performance data from static JSON.
 */

import { useState, useEffect, useMemo } from 'react';
import type { PostsPerformanceData, UsePostsPerformanceReturn, QuadrantPost } from '@/types';
import { DATA_PATHS } from '@/utils/constants';

/**
 * usePostsPerformance Hook
 *
 * Fetches posts performance data including top posts,
 * quadrant analysis, and weekly trends.
 */
export function usePostsPerformance(): UsePostsPerformanceReturn {
  const [data, setData] = useState<PostsPerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData(): Promise<void> {
      try {
        setLoading(true);
        setError(null);

        const base = import.meta.env.BASE_URL || '/';
        const response = await fetch(
          `${base}${DATA_PATHS.postsPerformance.slice(1)}`
        );

        if (!response.ok) {
          throw new Error(
            `Failed to fetch posts performance: ${response.status}`
          );
        }

        const jsonData = (await response.json()) as PostsPerformanceData;
        setData(jsonData);
        console.log('✓ Loaded posts performance data');
      } catch (err) {
        console.error('Error fetching posts performance:', err);
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
 * Get top posts sorted by a specific metric
 */
export function useSortedTopPosts(
  data: PostsPerformanceData | null,
  sortBy: 'reach' | 'engagementRate' | 'shares' | 'clicks' = 'reach',
  limit = 10
) {
  return useMemo(() => {
    if (!data?.topPosts) return [];

    const sorted = [...data.topPosts].sort((a, b) => {
      switch (sortBy) {
        case 'reach':
          return b.reach - a.reach;
        case 'engagementRate':
          return b.engagementRate - a.engagementRate;
        case 'shares':
          return (b.shares || 0) - (a.shares || 0);
        case 'clicks':
          return (b.clicks || 0) - (a.clicks || 0);
        default:
          return 0;
      }
    });

    return sorted.slice(0, limit);
  }, [data, sortBy, limit]);
}

/**
 * Get posts grouped by quadrant
 */
export function useQuadrantData(data: PostsPerformanceData | null) {
  return useMemo(() => {
    if (!data?.quadrantAnalysis) {
      return {
        highReachHighER: [],
        highReachLowER: [],
        lowReachHighER: [],
        lowReachLowER: [],
        medians: { reach: 0, er: 0 },
      };
    }

    const quadrants: Record<string, QuadrantPost[]> = {
      highReachHighER: [],
      highReachLowER: [],
      lowReachHighER: [],
      lowReachLowER: [],
    };

    // Calculate medians for quadrant boundaries
    const reachValues = data.quadrantAnalysis.map((p) => p.reach).sort((a, b) => a - b);
    const erValues = data.quadrantAnalysis.map((p) => p.engagementRate).sort((a, b) => a - b);

    const medianReach = reachValues[Math.floor(reachValues.length / 2)] || 0;
    const medianER = erValues[Math.floor(erValues.length / 2)] || 0;

    // Group posts by quadrant
    const highReachHighER: QuadrantPost[] = [];
    const highReachLowER: QuadrantPost[] = [];
    const lowReachHighER: QuadrantPost[] = [];
    const lowReachLowER: QuadrantPost[] = [];

    data.quadrantAnalysis.forEach((post) => {
      const isHighReach = post.reach >= medianReach;
      const isHighER = post.engagementRate >= medianER;

      if (isHighReach && isHighER) {
        highReachHighER.push(post);
      } else if (isHighReach && !isHighER) {
        highReachLowER.push(post);
      } else if (!isHighReach && isHighER) {
        lowReachHighER.push(post);
      } else {
        lowReachLowER.push(post);
      }
    });

    Object.assign(quadrants, { highReachHighER, highReachLowER, lowReachHighER, lowReachLowER });

    return {
      ...quadrants,
      medians: { reach: medianReach, er: medianER },
    };
  }, [data]);
}

/**
 * Get weekly trend data for charting
 */
export function useWeeklyTrends(data: PostsPerformanceData | null) {
  return useMemo(() => {
    if (!data?.weeklyTrends) return [];

    // Sort by week ascending
    return [...data.weeklyTrends].sort((a, b) => a.weekStart.localeCompare(b.weekStart));
  }, [data]);
}

/**
 * Calculate aggregate metrics from posts performance data
 */
export function usePerformanceMetrics(data: PostsPerformanceData | null) {
  return useMemo(() => {
    if (!data) {
      return {
        totalTopPosts: 0,
        totalQuadrantPosts: 0,
        avgReach: 0,
        avgER: 0,
        viralCount: 0,
        highPerformingCount: 0,
      };
    }

    const topPosts = data.topPosts || [];
    const quadrantPosts = data.quadrantAnalysis || [];

    // Calculate averages from top posts
    const avgReach =
      topPosts.length > 0
        ? topPosts.reduce((sum, p) => sum + p.reach, 0) / topPosts.length
        : 0;

    const avgER =
      topPosts.length > 0
        ? topPosts.reduce((sum, p) => sum + p.engagementRate, 0) / topPosts.length
        : 0;

    // Count viral and high-performing posts (top 10% and top 25%)
    const sortedByReach = [...topPosts].sort((a, b) => b.reach - a.reach);
    const viralThreshold = sortedByReach[Math.floor(topPosts.length * 0.1)]?.reach || 0;
    const highThreshold = sortedByReach[Math.floor(topPosts.length * 0.25)]?.reach || 0;

    const viralCount = topPosts.filter((p) => p.reach >= viralThreshold).length;
    const highPerformingCount = topPosts.filter(
      (p) => p.reach >= highThreshold
    ).length;

    return {
      totalTopPosts: topPosts.length,
      totalQuadrantPosts: quadrantPosts.length,
      avgReach,
      avgER,
      viralCount,
      highPerformingCount,
    };
  }, [data]);
}
