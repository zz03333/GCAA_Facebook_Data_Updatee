/**
 * GCAA Dashboard - Ad Analytics Hook
 *
 * Fetches ad analytics data from static JSON.
 */

import { useState, useEffect } from 'react';
import type { AdAnalyticsData, UseAdAnalyticsReturn } from '@/types';
import { DATA_PATHS } from '@/utils/constants';

/**
 * useAdAnalytics Hook
 *
 * Fetches ad analytics data including trending posts,
 * best combinations, recommendations, and organic vs paid comparison.
 */
export function useAdAnalytics(): UseAdAnalyticsReturn {
  const [data, setData] = useState<AdAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData(): Promise<void> {
      try {
        setLoading(true);
        setError(null);

        const base = import.meta.env.BASE_URL || '/';
        const response = await fetch(`${base}${DATA_PATHS.adAnalytics.slice(1)}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch ad analytics: ${response.status}`);
        }

        const jsonData = (await response.json()) as AdAnalyticsData;
        setData(jsonData);
        console.log('✓ Loaded ad analytics data');
      } catch (err) {
        console.error('Error fetching ad analytics:', err);
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
 * Calculate aggregate metrics from ad analytics data
 */
export function useAdAnalyticsMetrics(data: AdAnalyticsData | null) {
  if (!data) {
    return {
      totalTrending: 0,
      totalCombos: 0,
      avgOrganicER: 0,
      avgPaidER: 0,
      erImprovement: 0,
    };
  }

  const trendingCount = data.trendingPosts?.length || 0;
  const combosCount = data.bestCombos?.length || 0;

  // Calculate average organic vs paid engagement rates
  const organicData = data.organicVsPaid?.find((d) => d.type === 'organic');
  const paidData = data.organicVsPaid?.find((d) => d.type === 'paid');

  const avgOrganicER = organicData?.avgER || 0;
  const avgPaidER = paidData?.avgER || 0;
  const erImprovement =
    avgOrganicER > 0 ? ((avgPaidER - avgOrganicER) / avgOrganicER) * 100 : 0;

  return {
    totalTrending: trendingCount,
    totalCombos: combosCount,
    avgOrganicER,
    avgPaidER,
    erImprovement,
  };
}
