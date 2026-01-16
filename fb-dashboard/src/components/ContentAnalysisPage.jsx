/**
 * Content Analysis Page - Displays action type and topic performance
 */

import { useState, useEffect } from 'react';
import styles from './ContentAnalysisPage.module.css';

export default function ContentAnalysisPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('actionType');

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const base = import.meta.env.BASE_URL || '/';
        const response = await fetch(`${base}data/content-analysis.json`);
        if (!response.ok) throw new Error('Failed to fetch content analysis');
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error('Error fetching content analysis:', err);
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
          <p>載入內容分析資料中...</p>
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
        <h2 className={styles.title}>內容表現分析</h2>
        <p className={styles.subtitle}>分析不同類型貼文的表現，找出最佳內容策略</p>
      </div>

      {/* Tab Navigation */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'actionType' ? styles.active : ''}`}
          onClick={() => setActiveTab('actionType')}
        >
          行動類型
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'topic' ? styles.active : ''}`}
          onClick={() => setActiveTab('topic')}
        >
          議題分析
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'cross' ? styles.active : ''}`}
          onClick={() => setActiveTab('cross')}
        >
          交叉分析
        </button>
      </div>

      {/* Action Type Tab */}
      {activeTab === 'actionType' && data?.byActionType && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>行動類型表現</h3>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>行動類型</th>
                  <th>貼文數</th>
                  <th>平均互動率</th>
                  <th>平均分享率</th>
                  <th>平均留言率</th>
                  <th>熱門貼文</th>
                  <th>優質貼文</th>
                </tr>
              </thead>
              <tbody>
                {data.byActionType.map((row, i) => (
                  <tr key={i}>
                    <td className={styles.actionType}>{row.actionType}</td>
                    <td>{formatNumber(row.postCount)}</td>
                    <td className={styles.highlight}>{formatPercent(row.avgER)}</td>
                    <td>{formatPercent(row.avgShareRate)}</td>
                    <td>{formatPercent(row.avgCommentRate)}</td>
                    <td className={styles.viral}>{row.viralCount}</td>
                    <td className={styles.high}>{row.highCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Topic Tab */}
      {activeTab === 'topic' && data?.byTopic && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>議題表現</h3>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>議題</th>
                  <th>貼文數</th>
                  <th>平均互動率</th>
                  <th>平均分享率</th>
                  <th>平均留言率</th>
                  <th>熱門貼文</th>
                  <th>優質貼文</th>
                </tr>
              </thead>
              <tbody>
                {data.byTopic.map((row, i) => (
                  <tr key={i}>
                    <td className={styles.topic}>{row.topic}</td>
                    <td>{formatNumber(row.postCount)}</td>
                    <td className={styles.highlight}>{formatPercent(row.avgER)}</td>
                    <td>{formatPercent(row.avgShareRate)}</td>
                    <td>{formatPercent(row.avgCommentRate)}</td>
                    <td className={styles.viral}>{row.viralCount}</td>
                    <td className={styles.high}>{row.highCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Cross Analysis Tab */}
      {activeTab === 'cross' && data?.crossAnalysis && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>交叉分析（行動類型 × 議題）</h3>
          <p className={styles.sectionDescription}>
            分析不同行動類型搭配不同議題的表現
          </p>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>行動類型</th>
                  <th>議題</th>
                  <th>貼文數</th>
                  <th>平均互動率</th>
                  <th>平均分享率</th>
                  <th>優質貼文</th>
                </tr>
              </thead>
              <tbody>
                {data.crossAnalysis
                  .filter(row => row.postCount > 0)
                  .sort((a, b) => b.avgER - a.avgER)
                  .slice(0, 30)
                  .map((row, i) => (
                    <tr key={i} className={row.avgER > 5 ? styles.highPerformer : ''}>
                      <td className={styles.actionType}>{row.actionType}</td>
                      <td className={styles.topic}>{row.topic}</td>
                      <td>{formatNumber(row.postCount)}</td>
                      <td className={styles.highlight}>{formatPercent(row.avgER)}</td>
                      <td>{formatPercent(row.avgShareRate)}</td>
                      <td className={styles.high}>{row.highPerformerCount}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
