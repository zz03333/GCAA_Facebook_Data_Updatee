import { useMemo } from 'react';
import { formatPercent } from '../utils/formatters';
import styles from './HeatmapChart.module.css';

const WEEKDAYS = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function HeatmapChart({ heatmapData, onClick }) {
  const { cells, maxER } = useMemo(() => {
    if (!heatmapData || !heatmapData.length) {
      return { cells: [], maxER: 0 };
    }

    const cellMap = new Map();
    heatmapData.forEach(d => {
      cellMap.set(`${d.weekday}-${d.hour}`, d);
    });

    let max = 0;
    heatmapData.forEach(d => {
      if (d.avgER > max) max = d.avgER;
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

    return { cells, maxER: max };
  }, [heatmapData]);

  const getColor = (value, hasData) => {
    // 無資料的格子用灰色
    if (!hasData) return 'rgba(148, 163, 184, 0.1)';
    // 有資料但 avgER 為 0 用較淺的綠色
    if (value === 0) return 'rgba(34, 197, 94, 0.35)';
    // 有資料的格子根據 avgER 深淺變化，使用更寬的範圍讓所有資料點可見
    const intensity = Math.min(value / maxER, 1);
    return `rgba(34, 197, 94, ${0.35 + intensity * 0.55})`;
  };

  const handleCellClick = (cell) => {
    if (onClick && cell.count > 0) {
      onClick({ weekday: cell.weekday, hour: cell.hour });
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>發文時段熱力圖</h3>
        <div className={styles.legend}>
          <span className={styles.legendLabel}>低</span>
          <div className={styles.legendGradient} />
          <span className={styles.legendLabel}>高</span>
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
                  return (
                    <div
                      key={`${weekdayIndex}-${hour}`}
                      className={`${styles.cell} ${cell?.count > 0 ? styles.active : ''}`}
                      style={{ backgroundColor: getColor(cell?.avgER || 0, cell?.count > 0) }}
                      onClick={() => handleCellClick(cell)}
                      title={cell ? `${day} ${hour}:00\n互動率: ${formatPercent(cell.avgER)}\n貼文數: ${cell.count}` : ''}
                    >
                      {cell?.count > 0 && (
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

      <p className={styles.hint}>數字為貼文數量 · 顏色深淺表示平均互動率</p>
    </div>
  );
}
