import { useState, useEffect } from 'react';
import {
  collection,
  query,
  orderBy,
  limit,
  onSnapshot,
  doc
} from 'firebase/firestore';
import { db } from '../config/firebase';

/**
 * useData Hook - Real-time Firestore sync
 *
 * Fetches analytics data from Firestore with real-time updates.
 * Falls back to static JSON if Firestore is not configured.
 *
 * @returns {{posts: Array, daily: Array, stats: Object|null, loading: boolean, error: string|null}}
 */
export function useData() {
  const [posts, setPosts] = useState([]);
  const [daily, setDaily] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [useFirestore, setUseFirestore] = useState(true);

  useEffect(() => {
    // Check if Firebase is properly configured
    // Only fall back to static JSON if Firebase is not configured at all
    const isFirebaseConfigured = db && db.app.options.apiKey && db.app.options.apiKey !== 'YOUR_API_KEY';

    if (!isFirebaseConfigured) {
      console.log('Firebase not configured, using static JSON data');
      setUseFirestore(false);
      fetchStaticData();
      return;
    }

    console.log('Using Firestore for real-time data sync');

    // Real-time listeners for Firestore
    const unsubscribers = [];

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
          const postsData = snapshot.docs.map(doc => {
            const data = doc.data();
            // Transform Firestore schema to match React component expectations
            return {
              id: doc.id,
              publishedAt: data.publishedAt || '',
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
                reactions: data.metrics?.reactions || {}
              },
              computed: {
                engagementRate: data.computed?.engagementRate || 0,
                totalEngagement: data.computed?.totalEngagement || 0,
                shareRate: data.computed?.shareRate || 0,
                performanceTier: data.computed?.performanceTier || 'average',
                percentileRank: data.computed?.percentileRank || 0
              }
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
          const dailyData = snapshot.docs.map(doc => doc.data());
          setDaily(dailyData);
          console.log(`✓ Real-time update: ${dailyData.length} daily metrics`);
        },
        (err) => {
          console.error('Error listening to daily metrics:', err);
        }
      );

      unsubscribers.push(unsubscribeDaily);

      // 3. Listen to aggregates and build stats object
      // This is a composite of multiple subcollections
      const buildStatsFromAggregates = async () => {
        const statsObj = {
          lastUpdated: new Date().toISOString(),
          totalPosts: posts.length,
          byActionType: [],
          byTopic: [],
          byHour: [],
          byDayOfWeek: [],
          heatmap: []
        };

        // Listen to action types
        const unsubscribeActionTypes = onSnapshot(
          collection(db, 'aggregates/byActionType/data'),
          (snapshot) => {
            statsObj.byActionType = snapshot.docs.map(doc => ({
              name: doc.data().name,
              count: doc.data().count,
              avgER: doc.data().avgER,
              avgReach: doc.data().avgReach
            }));
            setStats({ ...statsObj });
          }
        );

        unsubscribers.push(unsubscribeActionTypes);

        // Listen to topics
        const unsubscribeTopics = onSnapshot(
          collection(db, 'aggregates/byTopic/data'),
          (snapshot) => {
            statsObj.byTopic = snapshot.docs.map(doc => ({
              name: doc.data().name,
              count: doc.data().count,
              avgER: doc.data().avgER,
              avgReach: doc.data().avgReach
            }));
            setStats({ ...statsObj });
          }
        );

        unsubscribers.push(unsubscribeTopics);

        // Listen to hourly performance
        const unsubscribeHourly = onSnapshot(
          collection(db, 'aggregates/hourlyPerformance/data'),
          (snapshot) => {
            statsObj.byHour = snapshot.docs.map(doc => ({
              hour: doc.data().hour,
              label: doc.data().label,
              count: doc.data().count,
              avgER: doc.data().avgER
            }));
            setStats({ ...statsObj });
          }
        );

        unsubscribers.push(unsubscribeHourly);

        // Listen to heatmap
        const unsubscribeHeatmap = onSnapshot(
          collection(db, 'aggregates/heatmap/data'),
          (snapshot) => {
            statsObj.heatmap = snapshot.docs.map(doc => ({
              weekday: doc.data().weekday,
              weekdayName: doc.data().weekdayName,
              hour: doc.data().hour,
              count: doc.data().count,
              avgER: doc.data().avgER
            }));
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
              statsObj.lastUpdated = data.timestamp?.toDate?.()?.toISOString() || new Date().toISOString();
              statsObj.totalPosts = data.postsCount || posts.length;
              setStats({ ...statsObj });
            }
          }
        );

        unsubscribers.push(unsubscribeMetadata);
      };

      buildStatsFromAggregates();

      setLoading(false);

    } catch (err) {
      console.error('Firestore initialization error:', err);
      setError(err.message);
      setUseFirestore(false);
      fetchStaticData();
    }

    // Cleanup function
    return () => {
      console.log('Cleaning up Firestore listeners');
      unsubscribers.forEach(unsub => unsub());
    };

  }, []);  // Empty dependency array - only run once on mount

  // Fallback to static JSON (for backward compatibility)
  async function fetchStaticData() {
    try {
      setLoading(true);

      const base = import.meta.env.BASE_URL || '/';
      const [postsRes, dailyRes, statsRes] = await Promise.all([
        fetch(`${base}data/posts.json`),
        fetch(`${base}data/daily.json`),
        fetch(`${base}data/stats.json`)
      ]);

      if (!postsRes.ok || !dailyRes.ok || !statsRes.ok) {
        throw new Error('Failed to fetch static data');
      }

      const [postsData, dailyData, statsData] = await Promise.all([
        postsRes.json(),
        dailyRes.json(),
        statsRes.json()
      ]);

      setPosts(postsData);
      setDaily(dailyData);
      setStats(statsData);
      setError(null);
      console.log('✓ Loaded static JSON data (fallback mode)');
    } catch (err) {
      console.error('Error fetching static data:', err);
      setError(err.message);
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
 * This hook remains unchanged from the original implementation.
 */
export function useFilteredData(posts, filters) {
  const [filtered, setFiltered] = useState([]);

  useEffect(() => {
    if (!posts.length) {
      setFiltered([]);
      return;
    }

    let result = [...posts];

    // Date range filter
    if (filters.dateRange) {
      const { start, end } = filters.dateRange;
      if (start) {
        result = result.filter(p => p.publishedAt >= start);
      }
      if (end) {
        result = result.filter(p => p.publishedAt <= end);
      }
    }

    // Time range filter (weeks) - skip if 'custom' or 'all'
    if (filters.timeRange && filters.timeRange !== 'all' && filters.timeRange !== 'custom') {
      const weeks = parseInt(filters.timeRange);
      if (!isNaN(weeks)) {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - weeks * 7);
        const cutoffStr = cutoffDate.toISOString();
        result = result.filter(p => p.publishedAt >= cutoffStr);
      }
    }

    // Action type filter
    if (filters.actionType && filters.actionType !== 'all') {
      result = result.filter(p => p.actionType === filters.actionType);
    }

    // Topic filter
    if (filters.topic && filters.topic !== 'all') {
      result = result.filter(p => p.topic === filters.topic);
    }

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(p =>
        p.content.toLowerCase().includes(searchLower) ||
        p.hashtags.some(h => h.toLowerCase().includes(searchLower))
      );
    }

    // Sorting
    if (filters.sortBy) {
      result.sort((a, b) => {
        let valA, valB;
        switch (filters.sortBy) {
          case 'date':
            valA = a.publishedAt;
            valB = b.publishedAt;
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
        return filters.sortOrder === 'asc' ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
      });
    }

    setFiltered(result);
  }, [posts, filters]);

  return filtered;
}
