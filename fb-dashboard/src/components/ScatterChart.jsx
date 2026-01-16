import { useRef, useState, useMemo } from 'react';
import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
} from 'chart.js';
import { ACTION_COLORS, TOPIC_COLORS, formatNumber, formatPercent } from '../utils/formatters';
import styles from './ScatterChart.module.css';

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);

const AXIS_OPTIONS = [
  { value: 'reach', label: '觸及人數', format: 'number' },
  { value: 'engagementRate', label: '互動率 (%)', format: 'percent' },
  { value: 'shares', label: '分享數', format: 'number' },
  { value: 'clicks', label: '點擊數', format: 'number' },
  { value: 'likes', label: '讚數', format: 'number' },
  { value: 'comments', label: '留言數', format: 'number' },
  { value: 'totalEngagement', label: '總互動', format: 'number' }
];

const COLOR_OPTIONS = [
  { value: 'actionType', label: '行動類型' },
  { value: 'topic', label: '議題' }
];

const SIZE_OPTIONS = [
  { value: 'totalEngagement', label: '總互動' },
  { value: 'reach', label: '觸及' },
  { value: 'shares', label: '分享' },
  { value: 'fixed', label: '固定大小' }
];

export default function ScatterChart({ posts, onPointClick }) {
  const chartRef = useRef(null);
  const [xAxis, setXAxis] = useState('reach');
  const [yAxis, setYAxis] = useState('engagementRate');
  const [colorBy, setColorBy] = useState('actionType');
  const [sizeBy, setSizeBy] = useState('totalEngagement');

  const getValue = (post, field) => {
    switch (field) {
      case 'reach': return post.metrics.reach;
      case 'shares': return post.metrics.shares;
      case 'clicks': return post.metrics.clicks;
      case 'likes': return post.metrics.likes;
      case 'comments': return post.metrics.comments;
      case 'engagementRate': return post.computed.engagementRate;
      case 'totalEngagement': return post.computed.totalEngagement;
      default: return 0;
    }
  };

  const getRadius = (post) => {
    if (sizeBy === 'fixed') return 6;
    const value = getValue(post, sizeBy);
    return Math.min(Math.max(Math.sqrt(value) * 0.5, 4), 30);
  };

  const getColor = (post) => {
    if (colorBy === 'actionType') {
      return ACTION_COLORS[post.actionType] || '#64748b';
    }
    return TOPIC_COLORS[post.topic] || '#64748b';
  };

  const chartData = useMemo(() => {
    if (!posts || !posts.length) return { datasets: [] };

    // Group by color category
    const groups = {};
    posts.forEach(post => {
      const category = colorBy === 'actionType' ? post.actionType : post.topic;
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push({
        x: getValue(post, xAxis),
        y: getValue(post, yAxis),
        r: getRadius(post),
        post
      });
    });

    const colorMap = colorBy === 'actionType' ? ACTION_COLORS : TOPIC_COLORS;

    return {
      datasets: Object.entries(groups).map(([category, data]) => ({
        label: category,
        data,
        backgroundColor: (colorMap[category] || '#64748b') + 'aa',
        borderColor: colorMap[category] || '#64748b',
        borderWidth: 1.5,
        pointRadius: data.map(d => d.r),
        pointHoverRadius: data.map(d => d.r + 3)
      }))
    };
  }, [posts, xAxis, yAxis, colorBy, sizeBy]);

  const xAxisConfig = AXIS_OPTIONS.find(a => a.value === xAxis);
  const yAxisConfig = AXIS_OPTIONS.find(a => a.value === yAxis);

  const formatAxisValue = (value, config) => {
    if (config?.format === 'percent') return formatPercent(value);
    return formatNumber(value);
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: (event, elements) => {
      if (elements.length > 0 && onPointClick) {
        const { datasetIndex, index } = elements[0];
        const point = chartData.datasets[datasetIndex].data[index];
        if (point?.post) {
          onPointClick(point.post);
        }
      }
    },
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          boxWidth: 12,
          padding: 16,
          color: '#94a3b8',
          font: { family: 'DM Sans', size: 11 },
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(22, 32, 48, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        borderColor: 'rgba(148, 163, 184, 0.2)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        titleFont: { family: 'Syne', weight: '600', size: 13 },
        bodyFont: { family: 'DM Sans', size: 12 },
        callbacks: {
          title: (items) => {
            const point = items[0]?.raw;
            if (point?.post) {
              return point.post.contentPreview?.slice(0, 40) + '...';
            }
            return '';
          },
          label: (context) => {
            const point = context.raw;
            if (!point?.post) return [];
            return [
              `${xAxisConfig?.label}: ${formatAxisValue(point.x, xAxisConfig)}`,
              `${yAxisConfig?.label}: ${formatAxisValue(point.y, yAxisConfig)}`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: xAxisConfig?.label || xAxis,
          color: '#64748b',
          font: { family: 'DM Sans', size: 12, weight: '500' }
        },
        grid: {
          color: 'rgba(148, 163, 184, 0.06)',
          drawBorder: false
        },
        ticks: {
          color: '#64748b',
          font: { family: 'DM Sans', size: 11 },
          callback: (val) => formatAxisValue(val, xAxisConfig)
        }
      },
      y: {
        title: {
          display: true,
          text: yAxisConfig?.label || yAxis,
          color: '#64748b',
          font: { family: 'DM Sans', size: 12, weight: '500' }
        },
        grid: {
          color: 'rgba(148, 163, 184, 0.06)',
          drawBorder: false
        },
        ticks: {
          color: '#64748b',
          font: { family: 'DM Sans', size: 11 },
          callback: (val) => formatAxisValue(val, yAxisConfig)
        },
        beginAtZero: true
      }
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>自訂散佈圖分析</h3>
      </div>

      <div className={styles.controls}>
        <label className={styles.controlGroup}>
          <span className={styles.controlLabel}>X 軸</span>
          <select value={xAxis} onChange={(e) => setXAxis(e.target.value)} className={styles.select}>
            {AXIS_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        <label className={styles.controlGroup}>
          <span className={styles.controlLabel}>Y 軸</span>
          <select value={yAxis} onChange={(e) => setYAxis(e.target.value)} className={styles.select}>
            {AXIS_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        <label className={styles.controlGroup}>
          <span className={styles.controlLabel}>顏色</span>
          <select value={colorBy} onChange={(e) => setColorBy(e.target.value)} className={styles.select}>
            {COLOR_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>

        <label className={styles.controlGroup}>
          <span className={styles.controlLabel}>大小</span>
          <select value={sizeBy} onChange={(e) => setSizeBy(e.target.value)} className={styles.select}>
            {SIZE_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className={styles.chartWrapper}>
        <Scatter ref={chartRef} data={chartData} options={options} />
      </div>
    </div>
  );
}
