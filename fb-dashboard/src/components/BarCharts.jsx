import { useRef, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip
} from 'chart.js';
import { formatPercent, formatNumber } from '../utils/formatters';
import styles from './BarCharts.module.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip);

// Available metrics for bar charts
const METRIC_OPTIONS = [
  { value: 'avgER', label: '平均互動率', format: 'percent' },
  { value: 'avgReach', label: '平均觸及', format: 'number' },
  { value: 'count', label: '貼文數', format: 'number' }
];

// Generate gradient colors based on metric values (sorted by intensity)
function generateGradientColors(baseColor, data, metricKey) {
  const hex = baseColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Get max value for normalization
  const values = data.map(d => d[metricKey] || 0);
  const maxValue = Math.max(...values, 1);

  // Generate colors based on value intensity
  return data.map(d => {
    const value = d[metricKey] || 0;
    const intensity = value / maxValue;
    // Higher value = more opaque (0.4 to 1.0 range)
    const alpha = 0.4 + intensity * 0.6;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  });
}

function HorizontalBarChart({ data, baseColor, title, onClick }) {
  const chartRef = useRef(null);
  const [selectedMetric, setSelectedMetric] = useState('avgER');

  if (!data || !data.length) return null;

  const metricConfig = METRIC_OPTIONS.find(m => m.value === selectedMetric);
  const labels = data.map(d => d.name);
  const values = data.map(d => d[selectedMetric] || 0);
  const colors = generateGradientColors(baseColor, data, selectedMetric);

  // Get max value for legend scale
  const maxValue = Math.max(...values, 1);

  const formatValue = (val) => {
    if (metricConfig?.format === 'percent') return formatPercent(val);
    return formatNumber(val);
  };

  const chartData = {
    labels,
    datasets: [{
      data: values,
      backgroundColor: colors,
      borderColor: colors.map(c => c.replace(/[\d.]+\)$/, '1)')),
      borderWidth: 1,
      borderRadius: 4,
      barThickness: 24
    }]
  };

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    onClick: (event, elements) => {
      if (elements.length > 0 && onClick) {
        const index = elements[0].index;
        onClick(data[index].name);
      }
    },
    plugins: {
      legend: { display: false },
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
          title: (items) => items[0]?.label || '',
          label: (context) => {
            const index = context.dataIndex;
            const item = data[index];
            return [
              `${metricConfig?.label || selectedMetric}: ${formatValue(values[index])}`,
              `平均觸及: ${formatNumber(item.avgReach || 0)}`,
              `貼文數: ${item.count} 篇`
            ];
          }
        }
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
          callback: (val) => {
            if (metricConfig?.format === 'percent') return val + '%';
            return formatNumber(val);
          }
        },
        beginAtZero: true
      },
      y: {
        grid: { display: false },
        ticks: {
          color: '#e2e8f0',
          font: { family: 'DM Sans', size: 12, weight: '500' },
          padding: 8
        }
      }
    }
  };

  // Parse base color for legend gradient
  const hex = baseColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <h3 className={styles.chartTitle}>{title}</h3>
        <select
          className={styles.metricSelect}
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value)}
        >
          {METRIC_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
      <div className={styles.chartContainer} style={{ height: Math.max(data.length * 44, 200) }}>
        <Bar ref={chartRef} data={chartData} options={options} />
      </div>
      <div className={styles.legendRow}>
        <span className={styles.legendLabel}>低</span>
        <div
          className={styles.legendGradient}
          style={{
            background: `linear-gradient(to right, rgba(${r},${g},${b},0.4), rgba(${r},${g},${b},1))`
          }}
        />
        <span className={styles.legendLabel}>高</span>
        <span className={styles.legendValue}>{metricConfig?.label}</span>
      </div>
      <p className={styles.hint}>點擊篩選貼文</p>
    </div>
  );
}

export function ActionTypeChart({ data, onClick }) {
  return (
    <HorizontalBarChart
      data={data}
      baseColor="#22c55e"
      title="行動類型表現"
      onClick={onClick}
    />
  );
}

export function TopicChart({ data, onClick }) {
  return (
    <HorizontalBarChart
      data={data}
      baseColor="#06b6d4"
      title="議題表現"
      onClick={onClick}
    />
  );
}
