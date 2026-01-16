import { useState } from 'react';
import { formatDate, formatNumber, formatPercent, ACTION_COLORS, TOPIC_COLORS } from '../utils/formatters';
import styles from './PostsTable.module.css';

export default function PostsTable({ posts, onSort, sortBy, sortOrder }) {
  const [hoveredCell, setHoveredCell] = useState(null); // { post, column }
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const columns = [
    { key: 'content', label: '內容預覽', sortable: false, width: '35%' },
    { key: 'date', label: '發布時間', sortable: true, width: '12%' },
    { key: 'actionType', label: '行動', sortable: false, width: '12%' },
    { key: 'topic', label: '議題', sortable: false, width: '12%' },
    { key: 'engagement', label: '互動率', sortable: true, width: '10%' },
    { key: 'reach', label: '觸及', sortable: true, width: '10%' },
    { key: 'shares', label: '分享', sortable: true, width: '9%' }
  ];

  const handleSort = (key) => {
    if (!columns.find(c => c.key === key)?.sortable) return;
    if (onSort) onSort(key);
  };

  const handleCellMouseEnter = (post, column, e) => {
    setHoveredCell({ post, column });
    updateTooltipPosition(e);
  };

  const handleMouseMove = (e) => {
    updateTooltipPosition(e);
  };

  const updateTooltipPosition = (e) => {
    const x = Math.min(e.clientX + 16, window.innerWidth - 360);
    const y = Math.min(e.clientY + 16, window.innerHeight - 300);
    setTooltipPos({ x, y });
  };

  const handleMouseLeave = () => {
    setHoveredCell(null);
  };

  const renderTooltipContent = () => {
    if (!hoveredCell) return null;
    const { post, column } = hoveredCell;

    switch (column) {
      case 'content':
        return (
          <>
            <div className={styles.tooltipContent}>
              <p className={styles.tooltipText}>{post.content.slice(0, 300)}{post.content.length > 300 ? '...' : ''}</p>
            </div>
            {post.hashtags && post.hashtags.length > 0 && (
              <div className={styles.tooltipTags}>
                {post.hashtags.slice(0, 5).map((tag, i) => (
                  <span key={i} className={styles.tooltipTag}>{tag}</span>
                ))}
              </div>
            )}
          </>
        );
      case 'engagement':
      case 'reach':
      case 'shares':
        return (
          <div className={styles.tooltipMeta}>
            <div className={styles.tooltipRow}>
              <span>讚</span>
              <span>{formatNumber(post.metrics.likes)}</span>
            </div>
            <div className={styles.tooltipRow}>
              <span>留言</span>
              <span>{formatNumber(post.metrics.comments)}</span>
            </div>
            <div className={styles.tooltipRow}>
              <span>分享</span>
              <span>{formatNumber(post.metrics.shares)}</span>
            </div>
            <div className={styles.tooltipRow}>
              <span>觸及</span>
              <span>{formatNumber(post.metrics.reach)}</span>
            </div>
            <div className={styles.tooltipRow}>
              <span>點擊</span>
              <span>{formatNumber(post.metrics.clicks)}</span>
            </div>
            {post.metrics.reactions && (
              <div className={styles.tooltipReactions}>
                <span>愛心 {post.metrics.reactions.love}</span>
                <span>哇 {post.metrics.reactions.wow}</span>
                <span>哈 {post.metrics.reactions.haha}</span>
                <span>嗚 {post.metrics.reactions.sad}</span>
                <span>怒 {post.metrics.reactions.angry}</span>
              </div>
            )}
          </div>
        );
      case 'date':
        return (
          <div className={styles.tooltipMeta}>
            <div className={styles.tooltipRow}>
              <span>發布時間</span>
              <span>{formatDate(post.publishedAt, 'full')}</span>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  className={`${styles.th} ${col.sortable ? styles.sortable : ''} ${sortBy === col.key ? styles.sorted : ''}`}
                  style={{ width: col.width }}
                  onClick={() => handleSort(col.key)}
                >
                  <span>{col.label}</span>
                  {col.sortable && (
                    <span className={styles.sortIcon}>
                      {sortBy === col.key ? (sortOrder === 'desc' ? '↓' : '↑') : '⇅'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {posts.map((post, index) => (
              <tr
                key={post.id}
                className={styles.tr}
                style={{ animationDelay: `${Math.min(index * 0.02, 0.5)}s` }}
              >
                <td
                  className={styles.td}
                  onMouseEnter={(e) => handleCellMouseEnter(post, 'content', e)}
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                >
                  <a
                    href={post.permalink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.contentLink}
                  >
                    {post.contentPreview}
                  </a>
                </td>
                <td
                  className={styles.td}
                  onMouseEnter={(e) => handleCellMouseEnter(post, 'date', e)}
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                >
                  <span className={styles.date}>{formatDate(post.publishedAt, 'short')}</span>
                </td>
                <td className={styles.td}>
                  <span
                    className={styles.tag}
                    style={{ backgroundColor: (ACTION_COLORS[post.actionType] || '#64748b') + '22', color: ACTION_COLORS[post.actionType] || '#64748b' }}
                  >
                    {post.actionType}
                  </span>
                </td>
                <td className={styles.td}>
                  <span
                    className={styles.tag}
                    style={{ backgroundColor: (TOPIC_COLORS[post.topic] || '#64748b') + '22', color: TOPIC_COLORS[post.topic] || '#64748b' }}
                  >
                    {post.topic}
                  </span>
                </td>
                <td
                  className={styles.td}
                  onMouseEnter={(e) => handleCellMouseEnter(post, 'engagement', e)}
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                >
                  <span className={`${styles.metric} ${styles.engagement}`}>
                    {formatPercent(post.computed.engagementRate)}
                  </span>
                </td>
                <td
                  className={styles.td}
                  onMouseEnter={(e) => handleCellMouseEnter(post, 'reach', e)}
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                >
                  <span className={styles.metric}>{formatNumber(post.metrics.reach)}</span>
                </td>
                <td
                  className={styles.td}
                  onMouseEnter={(e) => handleCellMouseEnter(post, 'shares', e)}
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                >
                  <span className={styles.metric}>{formatNumber(post.metrics.shares)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <div
          className={styles.tooltip}
          style={{ left: tooltipPos.x, top: tooltipPos.y }}
        >
          {renderTooltipContent()}
        </div>
      )}
    </div>
  );
}
