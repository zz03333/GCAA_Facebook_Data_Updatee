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

// Metric configurations with colors matching KPICards
const METRIC_CONFIG = {
  postCount: {
    label: '總貼文數',
    format: 'number',
    color: '#22c55e',  // primary green
    colorLight: 'rgba(34, 197, 94, 0.1)'
  },
  avgEngagementRate: {
    label: '平均互動率',
    format: 'percent',
    color: '#06b6d4',  // secondary cyan
    colorLight: 'rgba(6, 182, 212, 0.1)'
  },
  totalReach: {
    label: '總觸及',
    format: 'number',
    color: '#8b5cf6',  // tertiary purple
    colorLight: 'rgba(139, 92, 246, 0.1)'
  },
  totalShares: {
    label: '總分享',
    format: 'number',
    color: '#f59e0b',  // warning amber
    colorLight: 'rgba(245, 158, 11, 0.1)'
  }
};

const WEEKDAY_NAMES = ['週日', '週一', '週二', '週三', '週四', '週五', '週六'];

export default function TrendChart({ daily, timeRange, dateRange, selectedMetrics, onMetricChange, onDateClick }) {
  const chartRef = useRef(null);
  // Support array of selected metrics (max 2)
  const [metrics, setMetrics] = useState(selectedMetrics || ['avgEngagementRate']);
  const [showComparison, setShowComparison] = useState(true);

  // 當外部 selectedMetrics 改變時，更新內部狀態
  useEffect(() => {
    if (selectedMetrics && selectedMetrics.length > 0) {
      setMetrics(selectedMetrics);
    }
  }, [selectedMetrics]);

  const filteredData = aggregateByDateRange(daily, timeRange, dateRange);

  // Get 7-day offset data for comparison (returns data from 7 days before)
  const getComparisonData = (metricKey, index) => {
    const offsetIndex = index - 7;
    if (offsetIndex >= 0 && filteredData[offsetIndex]) {
      return {
        value: filteredData[offsetIndex][metricKey],
        date: filteredData[offsetIndex].date
      };
    }
    return { value: null, date: null };
  };

  const labels = filteredData.map(d => formatDate(d.date, 'short'));

  // Format value based on metric type
  const formatValue = (val, metricKey) => {
    if (val === null || val === undefined) return '-';
    const config = METRIC_CONFIG[metricKey];
    if (config?.format === 'percent') return formatPercent(val);
    return formatNumber(val);
  };

  // Get weekday name from date string
  const getWeekdayFromDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return WEEKDAY_NAMES[date.getDay()];
  };

  // Build datasets for each selected metric (max 2)
  const buildDatasets = () => {
    const datasets = [];

    // Primary metrics (selected via KPI buttons)
    metrics.forEach((metricKey, idx) => {
      const config = METRIC_CONFIG[metricKey];
      if (!config) return;

      const data = filteredData.map(d => d[metricKey]);
      datasets.push({
        label: config.label,
        data,
        borderColor: config.color,
        backgroundColor: idx === 0 ? config.colorLight : 'transparent',
        borderWidth: 2.5,
        fill: idx === 0,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointBackgroundColor: config.color,
        pointBorderColor: '#0a1018',
        pointBorderWidth: 2,
        yAxisID: idx === 0 ? 'y' : 'y1',
        metricKey
      });

      // Add comparison line if enabled
      if (showComparison) {
        const compData = filteredData.map((_, i) => getComparisonData(metricKey, i).value);
        datasets.push({
          label: `${config.label} (7天前)`,
          data: compData,
          borderColor: config.color,
          borderWidth: 1.5,
          borderDash: [5, 5],
          fill: false,
          tension: 0.35,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointBackgroundColor: config.color,
          yAxisID: idx === 0 ? 'y' : 'y1',
          metricKey,
          isComparison: true,
          opacity: 0.5
        });
      }
    });

    return datasets;
  };

  const chartData = {
    labels,
    datasets: buildDatasets()
  };

  // Check if we need dual y-axis
  const needsDualAxis = metrics.length === 2;
  const primaryMetric = metrics[0];
  const secondaryMetric = metrics[1];

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    onClick: (event, elements) => {
      if (elements.length > 0 && onDateClick) {
        const element = elements[0];
        const datasetIndex = element.datasetIndex;
        const dataIndex = element.index;
        const dataset = chartData.datasets[datasetIndex];

        // If clicking on comparison line, get the 7-day-ago date
        if (dataset.isComparison) {
          const compData = getComparisonData(dataset.metricKey, dataIndex);
          if (compData.date) {
            onDateClick(compData.date);
          }
        } else if (filteredData[dataIndex]) {
          onDateClick(filteredData[dataIndex].date);
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
          pointStyle: 'line',
          filter: (legendItem) => {
            // Hide comparison lines from legend (they share same color)
            return !legendItem.text.includes('(7天前)');
          }
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
              const currentDate = filteredData[index].date;
              const weekday = getWeekdayFromDate(currentDate);
              return `${formatDate(currentDate, 'long')} (${weekday})`;
            }
            return '';
          },
          label: (context) => {
            const value = context.raw;
            if (value === null) return null;

            const dataset = context.dataset;
            const metricKey = dataset.metricKey;
            const config = METRIC_CONFIG[metricKey];

            if (dataset.isComparison) {
              // Show actual date for comparison data
              const compData = getComparisonData(metricKey, context.dataIndex);
              if (compData.date) {
                const compWeekday = getWeekdayFromDate(compData.date);
                return `${config.label}: ${formatValue(value, metricKey)} [${formatDate(compData.date, 'short')} ${compWeekday}]`;
              }
              return null;
            }

            return `${config.label}: ${formatValue(value, metricKey)}`;
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
        type: 'linear',
        display: true,
        position: 'left',
        grid: {
          color: 'rgba(148, 163, 184, 0.06)',
          drawBorder: false
        },
        ticks: {
          color: METRIC_CONFIG[primaryMetric]?.color || '#64748b',
          font: { family: 'DM Sans', size: 11 },
          callback: (value) => formatValue(value, primaryMetric)
        },
        beginAtZero: true
      },
      ...(needsDualAxis ? {
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: {
            drawOnChartArea: false
          },
          ticks: {
            color: METRIC_CONFIG[secondaryMetric]?.color || '#64748b',
            font: { family: 'DM Sans', size: 11 },
            callback: (value) => formatValue(value, secondaryMetric)
          },
          beginAtZero: true
        }
      } : {})
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>趨勢分析</h3>
        <div className={styles.controls}>
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
