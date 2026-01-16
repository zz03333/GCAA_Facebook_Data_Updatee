import { useRef, useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { aggregateByDateRange, formatNumber, formatPercent, formatDate } from '../utils/formatters';
import styles from './TrendChart.module.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const METRIC_OPTIONS = [
  { value: 'avgEngagementRate', label: '互動率 (%)', format: 'percent' },
  { value: 'postCount', label: '貼文數', format: 'number' },
  { value: 'totalReach', label: '總觸及', format: 'number' },
  { value: 'totalEngagement', label: '總互動', format: 'number' },
  { value: 'totalShares', label: '總分享', format: 'number' }
];

export default function TrendChart({ daily, timeRange, dateRange, selectedMetric, onMetricChange, onDateClick }) {
  const chartRef = useRef(null);
  const [primaryMetric, setPrimaryMetric] = useState(selectedMetric || 'avgEngagementRate');
  const [showComparison, setShowComparison] = useState(true);

  // 當外部 selectedMetric 改變時，更新內部狀態
  useEffect(() => {
    if (selectedMetric) {
      setPrimaryMetric(selectedMetric);
    }
  }, [selectedMetric]);

  const filteredData = aggregateByDateRange(daily, timeRange, dateRange);

  // Get 7-day offset data for comparison
  const getComparisonValue = (index) => {
    const offsetIndex = index - 7;
    if (offsetIndex >= 0 && filteredData[offsetIndex]) {
      return filteredData[offsetIndex][primaryMetric];
    }
    return null;
  };

  const labels = filteredData.map(d => formatDate(d.date, 'short'));
  const primaryData = filteredData.map(d => d[primaryMetric]);
  const comparisonData = filteredData.map((_, i) => getComparisonValue(i));

  const metricConfig = METRIC_OPTIONS.find(m => m.value === primaryMetric);

  const formatValue = (val) => {
    if (val === null || val === undefined) return '-';
    if (metricConfig?.format === 'percent') return formatPercent(val);
    return formatNumber(val);
  };

  const chartData = {
    labels,
    datasets: [
      {
        label: metricConfig?.label || primaryMetric,
        data: primaryData,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointBackgroundColor: '#22c55e',
        pointBorderColor: '#0a1018',
        pointBorderWidth: 2
      },
      ...(showComparison ? [{
        label: '7天前',
        data: comparisonData,
        borderColor: 'rgba(148, 163, 184, 0.5)',
        borderWidth: 1.5,
        borderDash: [5, 5],
        fill: false,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointBackgroundColor: 'rgba(148, 163, 184, 0.5)'
      }] : [])
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    onClick: (event, elements) => {
      if (elements.length > 0 && onDateClick) {
        const index = elements[0].index;
        if (filteredData[index]) {
          onDateClick(filteredData[index].date);
        }
      }
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        align: 'end',
        labels: {
          boxWidth: 12,
          boxHeight: 2,
          padding: 20,
          color: '#94a3b8',
          font: { family: 'DM Sans', size: 12 },
          usePointStyle: true,
          pointStyle: 'line'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(22, 32, 48, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        borderColor: 'rgba(34, 197, 94, 0.3)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        titleFont: { family: 'Syne', weight: '600', size: 13 },
        bodyFont: { family: 'DM Sans', size: 12 },
        callbacks: {
          title: (items) => {
            const index = items[0]?.dataIndex;
            if (index !== undefined && filteredData[index]) {
              return formatDate(filteredData[index].date, 'long');
            }
            return '';
          },
          label: (context) => {
            const value = context.raw;
            if (value === null) return null;
            return `${context.dataset.label}: ${formatValue(value)}`;
          },
          footer: () => onDateClick ? '點擊查看當日貼文' : ''
        },
        footerColor: '#94a3b8',
        footerFont: { size: 11, style: 'italic' }
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(148, 163, 184, 0.06)',
          drawBorder: false
        },
        ticks: {
          color: '#64748b',
          font: { family: 'DM Sans', size: 11 },
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 12
        }
      },
      y: {
        grid: {
          color: 'rgba(148, 163, 184, 0.06)',
          drawBorder: false
        },
        ticks: {
          color: '#64748b',
          font: { family: 'DM Sans', size: 11 },
          callback: (value) => formatValue(value)
        },
        beginAtZero: true
      }
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>趨勢分析</h3>
        <div className={styles.controls}>
          <label className={styles.controlGroup}>
            <span className={styles.controlLabel}>指標</span>
            <select
              value={primaryMetric}
              onChange={(e) => {
                setPrimaryMetric(e.target.value);
                onMetricChange?.(e.target.value);
              }}
              className={styles.select}
            >
              {METRIC_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={showComparison}
              onChange={(e) => setShowComparison(e.target.checked)}
            />
            <span className={styles.checkmark} />
            <span>對比 7 天前</span>
          </label>
        </div>
      </div>
      <div className={styles.chartWrapper}>
        <Line ref={chartRef} data={chartData} options={options} />
      </div>
    </div>
  );
}
