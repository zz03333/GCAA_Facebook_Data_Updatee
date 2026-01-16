import { useEffect, useRef, useState } from 'react';
import { formatNumber, formatPercent } from '../utils/formatters';
import styles from './KPICards.module.css';

function AnimatedNumber({ value, format = 'number', duration = 1000 }) {
  const [displayValue, setDisplayValue] = useState(0);
  const startTime = useRef(null);
  const frameRef = useRef(null);

  useEffect(() => {
    if (value === undefined || value === null) return;

    const target = typeof value === 'number' ? value : parseFloat(value) || 0;

    const animate = (timestamp) => {
      if (!startTime.current) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);

      // Easing function (easeOutExpo)
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setDisplayValue(target * eased);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    };

    startTime.current = null;
    frameRef.current = requestAnimationFrame(animate);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [value, duration]);

  if (format === 'percent') {
    return <span>{formatPercent(displayValue, 2)}</span>;
  }
  return <span>{formatNumber(Math.round(displayValue))}</span>;
}

// KPI 卡片與圖表指標的對應關係
const KPI_TO_METRIC = {
  '總貼文數': 'postCount',
  '平均互動率': 'avgEngagementRate',
  '總觸及': 'totalReach',
  '總分享': 'totalShares'
};

// Max number of metrics that can be selected simultaneously
const MAX_SELECTED_METRICS = 2;

export default function KPICards({ stats, daily, timeRange, dateRange, selectedMetrics = [], onMetricChange }) {
  // Calculate KPIs based on filtered data
  const filteredDaily = daily?.filter(d => {
    // Custom date range filter
    if (timeRange === 'custom' && dateRange) {
      if (dateRange.start && d.date < dateRange.start) return false;
      if (dateRange.end && d.date > dateRange.end) return false;
      return true;
    }
    if (timeRange === 'all') return true;
    const weeks = parseInt(timeRange);
    if (isNaN(weeks)) return true;
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - weeks * 7);
    return new Date(d.date) >= cutoffDate;
  }) || [];

  const totalPosts = filteredDaily.reduce((sum, d) => sum + d.postCount, 0);
  const totalReach = filteredDaily.reduce((sum, d) => sum + d.totalReach, 0);
  const totalShares = filteredDaily.reduce((sum, d) => sum + d.totalShares, 0);
  const avgER = filteredDaily.length > 0
    ? filteredDaily.reduce((sum, d) => sum + d.avgEngagementRate, 0) / filteredDaily.length
    : 0;

  const kpis = [
    {
      label: '總貼文數',
      value: totalPosts,
      format: 'number',
      color: 'primary'
    },
    {
      label: '平均互動率',
      value: avgER,
      format: 'percent',
      color: 'secondary'
    },
    {
      label: '總觸及',
      value: totalReach,
      format: 'number',
      color: 'tertiary'
    },
    {
      label: '總分享',
      value: totalShares,
      format: 'number',
      color: 'warning'
    }
  ];

  const handleCardClick = (kpiLabel) => {
    const metric = KPI_TO_METRIC[kpiLabel];
    if (!metric || !onMetricChange) return;

    const currentMetrics = Array.isArray(selectedMetrics) ? selectedMetrics : [];
    const isCurrentlySelected = currentMetrics.includes(metric);

    let newMetrics;
    if (isCurrentlySelected) {
      // Deselect: remove from array (but keep at least one selected)
      if (currentMetrics.length > 1) {
        newMetrics = currentMetrics.filter(m => m !== metric);
      } else {
        // Can't deselect the last one, do nothing
        return;
      }
    } else {
      // Select: add to array (max 2)
      if (currentMetrics.length >= MAX_SELECTED_METRICS) {
        // Replace the second one (keep first, replace second with new)
        newMetrics = [currentMetrics[0], metric];
      } else {
        newMetrics = [...currentMetrics, metric];
      }
    }

    onMetricChange(newMetrics);
  };

  // Get selection order (1 or 2) for badge display
  const getSelectionOrder = (metric) => {
    const idx = selectedMetrics.indexOf(metric);
    return idx >= 0 ? idx + 1 : 0;
  };

  return (
    <div className={styles.grid}>
      {kpis.map((kpi, index) => {
        const metric = KPI_TO_METRIC[kpi.label];
        const selectionOrder = getSelectionOrder(metric);
        const isSelected = selectionOrder > 0;
        return (
          <button
            key={kpi.label}
            className={`${styles.card} ${styles[kpi.color]} ${isSelected ? styles.selected : ''}`}
            style={{ animationDelay: `${index * 0.1}s` }}
            onClick={() => handleCardClick(kpi.label)}
            title={isSelected ? "點擊取消選取 (最多可選2項)" : "點擊選取此指標 (最多可選2項)"}
          >
            <div className={styles.cardHeader}>
              <span className={styles.label}>{kpi.label}</span>
              {isSelected && (
                <span className={styles.selectedBadge}>
                  {selectedMetrics.length > 1 ? `#${selectionOrder}` : '顯示中'}
                </span>
              )}
            </div>
            <div className={styles.value}>
              <AnimatedNumber value={kpi.value} format={kpi.format} />
            </div>
            <div className={styles.glow} />
          </button>
        );
      })}
    </div>
  );
}
