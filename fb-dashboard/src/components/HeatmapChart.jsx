import { useMemo, useState } from 'react';
import { formatPercent } from '../utils/formatters';
import styles from './HeatmapChart.module.css';

const WEEKDAYS = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

// Minimum post count threshold for a cell to be considered significant
const MIN_POST_THRESHOLD = 2;

export default function HeatmapChart({ heatmapData, onClick }) {
  const [filterLowData, setFilterLowData] = useState(true);

  const { cells, maxER, totalPosts } = useMemo(() => {
    if (!heatmapData || !heatmapData.length) {
      return { cells: [], maxER: 0, totalPosts: 0 };
    }

    const cellMap = new Map();
    heatmapData.forEach(d => {
      cellMap.set(`${d.weekday}-${d.hour}`, d);
    });

    // Calculate max ER only from significant cells (above threshold)
    let max = 0;
    let total = 0;
    heatmapData.forEach(d => {
      total += d.count || 0;
      // Only consider cells above threshold for max calculation if filtering is enabled
      if (!filterLowData || d.count >= MIN_POST_THRESHOLD) {
        if (d.avgER > max) max = d.avgER;
      }
    });

    const cells = [];
    for (let weekday = 0; weekday < 7; weekday++) {
      for (let hour = 0; hour < 24; hour++) {
        const data = cellMap.get(`${weekday}-${hour}`) || {
          weekday,
          hour,
          count: 0,
          avgER: 0
        };
        cells.push(data);
      }
    }

    return { cells, maxER: max, totalPosts: total };
  }, [heatmapData, filterLowData]);

  const getColor = (value, count) => {
    // No data
    if (count === 0) return 'rgba(148, 163, 184, 0.1)';
    // Below threshold (if filtering is enabled)
    if (filterLowData && count < MIN_POST_THRESHOLD) return 'rgba(148, 163, 184, 0.15)';
    // Has data but avgER is 0
    if (value === 0) return 'rgba(34, 197, 94, 0.35)';
    // Normal: gradient based on avgER
    const intensity = Math.min(value / maxER, 1);
    return `rgba(34, 197, 94, ${0.35 + intensity * 0.55})`;
  };

  const handleCellClick = (cell) => {
    if (onClick && cell.count > 0) {
      // Include weekdayName for filtering
      onClick({
        weekday: cell.weekday,
        weekdayName: WEEKDAYS[cell.weekday],
        hour: cell.hour
      });
    }
  };

  const isClickable = (cell) => {
    if (!filterLowData) return cell.count > 0;
    return cell.count >= MIN_POST_THRESHOLD;
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>發文時段熱力圖</h3>
        <div className={styles.controls}>
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={filterLowData}
              onChange={(e) => setFilterLowData(e.target.checked)}
            />
            <span className={styles.checkmark} />
            <span>隱藏低數據時段 (&lt;{MIN_POST_THRESHOLD}篇)</span>
          </label>
          <div className={styles.legend}>
            <span className={styles.legendLabel}>低</span>
            <div className={styles.legendGradient} />
            <span className={styles.legendLabel}>高</span>
          </div>
        </div>
      </div>

      <div className={styles.heatmapWrapper}>
        {/* Hour labels */}
        <div className={styles.hourLabels}>
          <div className={styles.cornerSpacer} />
          {HOURS.filter((_, i) => i % 3 === 0).map(hour => (
            <span key={hour} className={styles.hourLabel}>
              {hour.toString().padStart(2, '0')}
            </span>
          ))}
        </div>

        {/* Grid */}
        <div className={styles.gridContainer}>
          {WEEKDAYS.map((day, weekdayIndex) => (
            <div key={day} className={styles.row}>
              <span className={styles.weekdayLabel}>{day}</span>
              <div className={styles.cells}>
                {HOURS.map(hour => {
                  const cell = cells.find(c => c.weekday === weekdayIndex && c.hour === hour);
                  const clickable = isClickable(cell);
                  const dimmed = filterLowData && cell?.count > 0 && cell.count < MIN_POST_THRESHOLD;
                  return (
                    <div
                      key={`${weekdayIndex}-${hour}`}
                      className={`${styles.cell} ${clickable ? styles.active : ''} ${dimmed ? styles.dimmed : ''}`}
                      style={{ backgroundColor: getColor(cell?.avgER || 0, cell?.count || 0) }}
                      onClick={() => clickable && handleCellClick(cell)}
                      title={cell ? `${day} ${hour}:00\n互動率: ${formatPercent(cell.avgER)}\n貼文數: ${cell.count}` : ''}
                    >
                      {cell?.count > 0 && !dimmed && (
                        <span className={styles.cellCount}>{cell.count}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className={styles.hint}>數字為貼文數量 · 顏色深淺表示平均互動率 · 點擊篩選該時段貼文</p>
    </div>
  );
}
