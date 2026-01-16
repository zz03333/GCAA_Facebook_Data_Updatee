import { useRef } from 'react';
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

// 生成單色深淺變化的顏色（簡化為 4 個漸層階段）
function generateGradientColors(baseColor, count) {
  // 解析 RGB 顏色
  const hex = baseColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // 定義 4 個固定的漸層階段 (opacity)
  const opacityLevels = [1.0, 0.8, 0.6, 0.4];
  const brightnessLevels = [1.0, 0.8, 0.6, 0.4];

  const colors = [];
  for (let i = 0; i < count; i++) {
    // 將項目分配到 4 個漸層組中
    const groupIndex = Math.min(Math.floor((i / count) * 4), 3);
    const alpha = opacityLevels[groupIndex];
    const factor = brightnessLevels[groupIndex];

    const newR = Math.round(r * factor);
    const newG = Math.round(g * factor);
    const newB = Math.round(b * factor);
    colors.push(`rgba(${newR}, ${newG}, ${newB}, ${alpha})`);
  }
  return colors;
}

function HorizontalBarChart({ data, baseColor, title, onClick }) {
  const chartRef = useRef(null);

  if (!data || !data.length) return null;

  const labels = data.map(d => d.name);
  const values = data.map(d => d.avgER);
  const counts = data.map(d => d.count);
  const colors = generateGradientColors(baseColor, data.length);

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
            return [
              `平均互動率: ${formatPercent(values[index])}`,
              `貼文數: ${counts[index]} 篇`
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
          callback: (val) => val + '%'
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

  return (
    <div className={styles.chartCard}>
      <h3 className={styles.chartTitle}>{title}</h3>
      <div className={styles.chartContainer} style={{ height: Math.max(data.length * 44, 200) }}>
        <Bar ref={chartRef} data={chartData} options={options} />
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
