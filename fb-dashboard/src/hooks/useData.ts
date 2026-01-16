/**
 * GCAA Dashboard - Data Hooks
 *
 * Real-time Firestore sync with static JSON fallback.
 */

import { useState, useEffect, useMemo } from 'react';
import {
  collection,
  query,
  orderBy,
  limit,
  onSnapshot,
  doc,
  Unsubscribe,
} from 'firebase/firestore';
import { db } from '../config/firebase';
import type {
  Post,
  DailyMetric,
  Stats,
  FilterState,
  UseDataReturn,
} from '@/types';
import { DATA_PATHS } from '@/utils/constants';

/**
 * useData Hook - Real-time Firestore sync
 *
 * Fetches analytics data from Firestore with real-time updates.
 * Falls back to static JSON if Firestore is not configured.
 */
export function useData(): UseDataReturn {
  const [posts, setPosts] = useState<Post[]>([]);
  const [daily, setDaily] = useState<DailyMetric[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if Firebase is properly configured
    const isFirebaseConfigured =
      db && db.app.options.apiKey && db.app.options.apiKey !== 'YOUR_API_KEY';

    if (!isFirebaseConfigured) {
      console.log('Firebase not configured, using static JSON data');
      fetchStaticData();
      return;
    }

    console.log('Using Firestore for real-time data sync');

    const unsubscribers: Unsubscribe[] = [];

    try {
      setLoading(true);

      // 1. Listen to posts collection
      const postsQuery = query(
        collection(db, 'posts'),
        orderBy('publishedAt', 'desc'),
        limit(500)
      );

      const unsubscribePosts = onSnapshot(
        postsQuery,
        (snapshot) => {
          const postsData: Post[] = snapshot.docs.map((docSnap) => {
            const data = docSnap.data();
            return {
              id: docSnap.id,
              publishedAt: data.publishedAt || null,
              content: data.content || '',
              contentPreview: data.contentPreview || '',
              hashtags: data.hashtags || [],
              actionType: data.classification?.actionType || '',
              topic: data.classification?.topic || '',
              mediaType: data.classification?.mediaType || 'text',
              permalink: data.permalink || '',
              metrics: {
                likes: data.metrics?.likes || 0,
                comments: data.metrics?.comments || 0,
                shares: data.metrics?.shares || 0,
                clicks: data.metrics?.clicks || 0,
                reach: data.metrics?.reach || 0,
                videoViews: data.metrics?.videoViews || 0,
                reactions: data.metrics?.reactions || {},
              },
              computed: {
                engagementRate: data.computed?.engagementRate || 0,
                totalEngagement: data.computed?.totalEngagement || 0,
                shareRate: data.computed?.shareRate || 0,
                performanceTier: data.computed?.performanceTier || 'average',
                percentileRank: data.computed?.percentileRank || 0,
              },
            };
          });
          setPosts(postsData);
          console.log(`✓ Real-time update: ${postsData.length} posts`);
        },
        (err) => {
          console.error('Error listening to posts:', err);
          setError(`Posts sync error: ${err.message}`);
        }
      );

      unsubscribers.push(unsubscribePosts);

      // 2. Listen to daily metrics collection
      const dailyQuery = query(
        collection(db, 'dailyMetrics'),
        orderBy('date', 'desc'),
        limit(90)
      );

      const unsubscribeDaily = onSnapshot(
        dailyQuery,
        (snapshot) => {
          const dailyData: DailyMetric[] = snapshot.docs.map(
            (docSnap) => docSnap.data() as DailyMetric
          );
          setDaily(dailyData);
          console.log(`✓ Real-time update: ${dailyData.length} daily metrics`);
        },
        (err) => {
          console.error('Error listening to daily metrics:', err);
        }
      );

      unsubscribers.push(unsubscribeDaily);

      // 3. Listen to aggregates and build stats object
      const statsObj: Stats = {
        lastUpdated: new Date().toISOString(),
        totalPosts: posts.length,
        byActionType: [],
        byTopic: [],
        byHour: [],
        byDayOfWeek: [],
        heatmap: [],
      };

      // Listen to action types
      const unsubscribeActionTypes = onSnapshot(
        collection(db, 'aggregates/byActionType/data'),
        (snapshot) => {
          statsObj.byActionType = snapshot.docs.map((docSnap) => {
            const data = docSnap.data();
            return {
              // Fallback to document ID if name is missing
              name: data.name || data.actionType || docSnap.id,
              count: data.count || 0,
              // Handle different field naming conventions
              avgER: data.avgER ?? data.avgEngagementRate ?? data.avg_er ?? 0,
              avgReach: data.avgReach ?? data.avg_reach ?? 0,
            };
          });
          setStats({ ...statsObj });
        }
      );

      unsubscribers.push(unsubscribeActionTypes);

      // Listen to topics
      const unsubscribeTopics = onSnapshot(
        collection(db, 'aggregates/byTopic/data'),
        (snapshot) => {
          statsObj.byTopic = snapshot.docs.map((docSnap) => {
            const data = docSnap.data();
            return {
              // Fallback to document ID if name is missing
              name: data.name || data.topic || docSnap.id,
              count: data.count || 0,
              // Handle different field naming conventions
              avgER: data.avgER ?? data.avgEngagementRate ?? data.avg_er ?? 0,
              avgReach: data.avgReach ?? data.avg_reach ?? 0,
            };
          });
          setStats({ ...statsObj });
        }
      );

      unsubscribers.push(unsubscribeTopics);

      // Listen to hourly performance
      const unsubscribeHourly = onSnapshot(
        collection(db, 'aggregates/hourlyPerformance/data'),
        (snapshot) => {
          statsObj.byHour = snapshot.docs.map((docSnap) => {
            const data = docSnap.data();
            return {
              hour: data.hour,
              label: data.label,
              count: data.count,
              avgER: data.avgER,
            };
          });
          setStats({ ...statsObj });
        }
      );

      unsubscribers.push(unsubscribeHourly);

      // Listen to heatmap
      const unsubscribeHeatmap = onSnapshot(
        collection(db, 'aggregates/heatmap/data'),
        (snapshot) => {
          statsObj.heatmap = snapshot.docs.map((docSnap) => {
            const data = docSnap.data();
            return {
              weekday: data.weekday,
              weekdayName: data.weekdayName,
              hour: data.hour,
              count: data.count,
              avgER: data.avgER,
            };
          });
          setStats({ ...statsObj });
        }
      );

      unsubscribers.push(unsubscribeHeatmap);

      // Listen to last sync metadata
      const unsubscribeMetadata = onSnapshot(
        doc(db, 'metadata', 'lastSync'),
        (docSnap) => {
          if (docSnap.exists()) {
            const data = docSnap.data();
            statsObj.lastUpdated =
              data.timestamp?.toDate?.()?.toISOString() ||
              new Date().toISOString();
            statsObj.totalPosts = data.postsCount || posts.length;
            setStats({ ...statsObj });
          }
        }
      );

      unsubscribers.push(unsubscribeMetadata);

      setLoading(false);
    } catch (err) {
      console.error('Firestore initialization error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      fetchStaticData();
    }

    // Cleanup function
    return () => {
      console.log('Cleaning up Firestore listeners');
      unsubscribers.forEach((unsub) => unsub());
    };
  }, []);

  // Fallback to static JSON
  async function fetchStaticData(): Promise<void> {
    try {
      setLoading(true);

      const base = import.meta.env.BASE_URL || '/';
      const [postsRes, dailyRes, statsRes] = await Promise.all([
        fetch(`${base}${DATA_PATHS.posts.slice(1)}`),
        fetch(`${base}${DATA_PATHS.daily.slice(1)}`),
        fetch(`${base}${DATA_PATHS.stats.slice(1)}`),
      ]);

      if (!postsRes.ok || !dailyRes.ok || !statsRes.ok) {
        throw new Error('Failed to fetch static data');
      }

      const [postsData, dailyData, statsData] = await Promise.all([
        postsRes.json() as Promise<Post[]>,
        dailyRes.json() as Promise<DailyMetric[]>,
        statsRes.json() as Promise<Stats>,
      ]);

      setPosts(postsData);
      setDaily(dailyData);
      setStats(statsData);
      setError(null);
      console.log('✓ Loaded static JSON data (fallback mode)');
    } catch (err) {
      console.error('Error fetching static data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  return { posts, daily, stats, loading, error };
}

/**
 * useFilteredData Hook
 *
 * Filters and sorts posts based on provided filter criteria.
 */
export function useFilteredData(
  posts: Post[],
  filters: Partial<FilterState>
): Post[] {
  return useMemo(() => {
    if (!posts.length) {
      return [];
    }

    let result = [...posts];

    // Date range filter
    if (filters.dateRange) {
      const { start, end } = filters.dateRange;
      if (start) {
        result = result.filter((p) => p.publishedAt && p.publishedAt >= start);
      }
      if (end) {
        result = result.filter((p) => p.publishedAt && p.publishedAt <= end);
      }
    }

    // Time range filter (weeks) - skip if 'custom' or 'all'
    if (
      filters.timeRange &&
      filters.timeRange !== 'all' &&
      filters.timeRange !== 'custom'
    ) {
      const weeks = parseInt(filters.timeRange);
      if (!isNaN(weeks)) {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - weeks * 7);
        const cutoffStr = cutoffDate.toISOString();
        result = result.filter((p) => p.publishedAt && p.publishedAt >= cutoffStr);
      }
    }

    // Action type filter
    if (filters.actionType && filters.actionType !== 'all') {
      result = result.filter((p) => p.actionType === filters.actionType);
    }

    // Topic filter
    if (filters.topic && filters.topic !== 'all') {
      result = result.filter((p) => p.topic === filters.topic);
    }

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (p) =>
          p.content.toLowerCase().includes(searchLower) ||
          (p.hashtags?.some((h) => h.toLowerCase().includes(searchLower)) ?? false)
      );
    }

    // Hour filter (from heatmap click)
    if (filters.hour !== undefined && filters.hour !== null) {
      result = result.filter((p) => {
        if (!p.publishedAt) return false;
        const postDate = new Date(p.publishedAt);
        return postDate.getHours() === filters.hour;
      });
    }

    // Weekday filter (from heatmap click)
    // Note: JavaScript getDay() returns 0=Sunday, but heatmap uses 0=Monday
    if (filters.weekday !== undefined && filters.weekday !== null) {
      result = result.filter((p) => {
        if (!p.publishedAt) return false;
        const postDate = new Date(p.publishedAt);
        // Convert JS day (0=Sun) to heatmap day (0=Mon)
        const jsDay = postDate.getDay();
        const heatmapDay = jsDay === 0 ? 6 : jsDay - 1;
        return heatmapDay === filters.weekday;
      });
    }

    // Sorting
    if (filters.sortBy) {
      result.sort((a, b) => {
        let valA: string | number;
        let valB: string | number;

        switch (filters.sortBy) {
          case 'date':
            valA = a.publishedAt || '';
            valB = b.publishedAt || '';
            break;
          case 'engagement':
            valA = a.computed.engagementRate;
            valB = b.computed.engagementRate;
            break;
          case 'reach':
            valA = a.metrics.reach;
            valB = b.metrics.reach;
            break;
          case 'shares':
            valA = a.metrics.shares;
            valB = b.metrics.shares;
            break;
          default:
            return 0;
        }
        return filters.sortOrder === 'asc'
          ? valA > valB
            ? 1
            : -1
          : valA < valB
            ? 1
            : -1;
      });
    }

    return result;
  }, [posts, filters]);
}
