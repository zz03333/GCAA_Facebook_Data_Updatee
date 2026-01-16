/**
 * Ad Analytics Page - Displays ad recommendations and trending posts
 */

import { useState, useEffect } from 'react';
import styles from './AdAnalyticsPage.module.css';

export default function AdAnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('trending');

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const base = import.meta.env.BASE_URL || '/';
        const response = await fetch(`${base}data/ad-analytics.json`);
        if (!response.ok) throw new Error('Failed to fetch ad analytics');
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Error fetching ad analytics:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>載入廣告分析資料中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.error}>
          <p>載入失敗: {error}</p>
        </div>
      </div>
    );
  }

  const formatPercent = (val) => typeof val === 'number' ? val.toFixed(2) + '%' : '-';
  const formatNumber = (val) => typeof val === 'number' ? val.toLocaleString() : '-';

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2 className={styles.title}>廣告分析</h2>
        <p className={styles.subtitle}>找出最適合投放廣告的貼文與最佳組合</p>
      </div>

      {/* Tab Navigation */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'trending' ? styles.active : ''}`}
          onClick={() => setActiveTab('trending')}
        >
          熱門貼文
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'recommendations' ? styles.active : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          投廣推薦
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'combos' ? styles.active : ''}`}
          onClick={() => setActiveTab('combos')}
        >
          最佳組合
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'comparison' ? styles.active : ''}`}
          onClick={() => setActiveTab('comparison')}
        >
          自然 vs 付費
        </button>
      </div>

      {/* Trending Posts Tab */}
      {activeTab === 'trending' && data?.trendingPosts && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>近期熱門貼文</h3>
          <p className={styles.sectionDescription}>
            目前互動成長最快的貼文，適合考慮投放廣告
          </p>
          <div className={styles.cardGrid}>
            {data.trendingPosts.slice(0, 6).map((post, i) => (
              <div key={i} className={styles.trendingCard}>
                <div className={styles.cardHeader}>
                  <span className={styles.badge}>#{i + 1}</span>
                  <span className={styles.timeAgo}>{post.hoursSincePost}小時前</span>
                </div>
                <p className={styles.cardContent}>{post.messagePreview || '無文字內容'}</p>
                <div className={styles.cardStats}>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>觸及</span>
                    <span className={styles.statValue}>{formatNumber(post.reach)}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>互動</span>
                    <span className={styles.statValue}>{formatNumber(post.currentEngagement)}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>互動率</span>
                    <span className={`${styles.statValue} ${styles.highlight}`}>
                      {formatPercent(post.engagementRate)}
                    </span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>每小時互動</span>
                    <span className={styles.statValue}>{post.engagementPerHour.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations Tab */}
      {activeTab === 'recommendations' && data?.recommendations && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>投廣推薦</h3>
          <p className={styles.sectionDescription}>
            根據互動率、分享率和留言率計算的廣告潛力分數
          </p>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>推薦程度</th>
                  <th>潛力分數</th>
                  <th>表現等級</th>
                  <th>行動類型</th>
                  <th>議題</th>
                  <th>發布時間</th>
                  <th>連結</th>
                </tr>
              </thead>
              <tbody>
                {data.recommendations
                  .sort((a, b) => b.adPotentialScore - a.adPotentialScore)
                  .slice(0, 20)
                  .map((rec, i) => (
                    <tr key={i}>
                      <td>
                        <span className={`${styles.recommendBadge} ${styles[rec.adRecommendation?.replace(/\s/g, '') || 'default']}`}>
                          {rec.adRecommendation || '-'}
                        </span>
                      </td>
                      <td className={styles.score}>{rec.adPotentialScore}</td>
                      <td>
                        <span className={`${styles.tierBadge} ${styles[rec.performanceTier] || ''}`}>
                          {rec.performanceTier}
                        </span>
                      </td>
                      <td>{rec.formatType}</td>
                      <td>{rec.issueTopic}</td>
                      <td>{rec.createdTime?.slice(0, 10) || '-'}</td>
                      <td>
                        {rec.permalinkUrl && (
                          <a href={rec.permalinkUrl} target="_blank" rel="noopener noreferrer" className={styles.link}>
                            查看
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Best Combos Tab */}
      {activeTab === 'combos' && data?.bestCombos && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>歷史最佳組合</h3>
          <p className={styles.sectionDescription}>
            表現最佳的議題、行動類型、時段組合
          </p>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>議題</th>
                  <th>行動類型</th>
                  <th>時段</th>
                  <th>星期</th>
                  <th>貼文數</th>
                  <th>平均互動率</th>
                  <th>優質貼文</th>
                </tr>
              </thead>
              <tbody>
                {data.bestCombos
                  .filter(combo => combo.postCount > 0)
                  .sort((a, b) => b.avgER - a.avgER)
                  .slice(0, 20)
                  .map((combo, i) => (
                    <tr key={i} className={combo.avgER > 5 ? styles.highPerformer : ''}>
                      <td className={styles.topic}>{combo.issueTopic}</td>
                      <td className={styles.actionType}>{combo.formatType}</td>
                      <td>{combo.timeSlot}</td>
                      <td>{combo.dayName}</td>
                      <td>{combo.postCount}</td>
                      <td className={styles.highlight}>{formatPercent(combo.avgER)}</td>
                      <td className={styles.high}>{combo.highPerformers}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Comparison Tab */}
      {activeTab === 'comparison' && data?.organicVsPaid && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>自然 vs 付費比較</h3>
          <p className={styles.sectionDescription}>
            比較自然觸及與付費廣告的表現差異
          </p>
          <div className={styles.comparisonGrid}>
            {data.organicVsPaid.map((item, i) => (
              <div key={i} className={`${styles.comparisonCard} ${item.type === 'paid' ? styles.paid : styles.organic}`}>
                <h4 className={styles.comparisonTitle}>
                  {item.type === 'organic' ? '自然觸及' : '付費廣告'}
                </h4>
                <div className={styles.comparisonStats}>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>貼文數</span>
                    <span className={styles.statValue}>{formatNumber(item.postCount)}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>總觸及</span>
                    <span className={styles.statValue}>{formatNumber(item.totalReach)}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>總互動</span>
                    <span className={styles.statValue}>{formatNumber(item.totalEngagement)}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>平均互動率</span>
                    <span className={`${styles.statValue} ${styles.highlight}`}>
                      {formatPercent(item.avgER)}
                    </span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>平均分享率</span>
                    <span className={styles.statValue}>{formatPercent(item.avgShareRate)}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>平均留言率</span>
                    <span className={styles.statValue}>{formatPercent(item.avgCommentRate)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
