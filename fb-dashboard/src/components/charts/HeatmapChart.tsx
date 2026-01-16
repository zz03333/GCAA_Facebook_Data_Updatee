/**
 * HeatmapChart Component - Grid visualization for patterns
 */

import { WEEKDAY_NAMES } from '@/utils/constants';
import { getHeatmapColor } from '@/utils/colors';
import { formatNumber, formatPercent } from '@/utils/formatters';

interface HeatmapCell {
  weekday: number;
  hour: number;
  count: number;
  avgER?: number;
  [key: string]: string | number | undefined;
}

interface HeatmapChartProps {
  data: HeatmapCell[];
  valueKey?: 'count' | 'avgER';
  showLabels?: boolean;
  height?: number;
  className?: string;
}

export function HeatmapChart({
  data,
  valueKey = 'count',
  showLabels = false,
  height = 280,
  className = '',
}: HeatmapChartProps) {
  if (!data || data.length === 0) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        style={{ height }}
      >
        <p className="text-muted text-sm">暫無資料</p>
      </div>
    );
  }

  // Build a lookup map for quick access
  const cellMap = new Map<string, HeatmapCell>();
  data.forEach((cell) => {
    cellMap.set(`${cell.weekday}-${cell.hour}`, cell);
  });

  // Find max value for color normalization
  const maxValue = Math.max(...data.map((cell) => cell[valueKey] || 0));

  // Generate hours (0-23) and weekdays (0-6)
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const weekdays = Array.from({ length: 7 }, (_, i) => i);

  const valueFormatter = valueKey === 'avgER' ? formatPercent : formatNumber;

  return (
    <div className={className}>
      <div
        className="overflow-x-auto"
        style={{ height: showLabels ? height + 30 : height }}
      >
        <div className="min-w-[600px]">
          {/* Hour labels */}
          <div className="flex mb-1">
            <div className="w-12 flex-shrink-0" /> {/* Spacer for weekday labels */}
            {hours.map((hour) => (
              <div
                key={hour}
                className="flex-1 text-center text-[10px] text-muted"
              >
                {hour % 3 === 0 ? `${hour}` : ''}
              </div>
            ))}
          </div>

          {/* Grid */}
          {weekdays.map((weekday) => (
            <div key={weekday} className="flex mb-0.5">
              {/* Weekday label */}
              <div className="w-12 flex-shrink-0 flex items-center justify-end pr-2">
                <span className="text-xs text-muted">{WEEKDAY_NAMES[weekday]}</span>
              </div>

              {/* Cells */}
              {hours.map((hour) => {
                const cell = cellMap.get(`${weekday}-${hour}`);
                const value = cell?.[valueKey] || 0;
                const bgColor = getHeatmapColor(value as number, maxValue);

                return (
                  <div
                    key={hour}
                    className="flex-1 aspect-square m-0.5 rounded-sm relative group cursor-pointer transition-transform hover:scale-110 hover:z-10"
                    style={{ backgroundColor: bgColor }}
                    title={`${WEEKDAY_NAMES[weekday]} ${hour}:00 - ${valueFormatter(value as number)}`}
                  >
                    {/* Tooltip on hover */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20">
                      <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg whitespace-nowrap">
                        <p className="text-xs text-muted">
                          {WEEKDAY_NAMES[weekday]} {hour}:00
                        </p>
                        <p className="text-sm font-semibold text-bright">
                          {valueFormatter(value as number)}
                        </p>
                        {cell?.count !== undefined && valueKey !== 'count' && (
                          <p className="text-xs text-muted">
                            {cell.count} 則貼文
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Optional value label */}
                    {showLabels && value > 0 && (
                      <span className="absolute inset-0 flex items-center justify-center text-[8px] font-medium text-bright/80">
                        {Math.round(value as number)}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

          {/* Legend */}
          <div className="flex items-center justify-end mt-4 gap-2">
            <span className="text-xs text-muted">低</span>
            <div className="flex">
              {[0.2, 0.4, 0.6, 0.8, 1].map((intensity, i) => (
                <div
                  key={i}
                  className="w-5 h-3"
                  style={{ backgroundColor: getHeatmapColor(intensity * maxValue, maxValue) }}
                />
              ))}
            </div>
            <span className="text-xs text-muted">高</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * CrossAnalysisHeatmap - For action type x topic analysis
 */
interface CrossAnalysisCellData {
  actionType: string;
  topic: string;
  postCount: number;
  avgER: number;
  countIntensity?: number;
  erIntensity?: number;
}

interface CrossAnalysisHeatmapProps {
  data: {
    cells: CrossAnalysisCellData[];
    actionTypes: string[];
    topics: string[];
  };
  valueKey?: 'postCount' | 'avgER';
  height?: number;
  className?: string;
}

export function CrossAnalysisHeatmap({
  data,
  valueKey = 'avgER',
  height = 400,
  className = '',
}: CrossAnalysisHeatmapProps) {
  if (!data.cells || data.cells.length === 0) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        style={{ height }}
      >
        <p className="text-muted text-sm">暫無資料</p>
      </div>
    );
  }

  const { cells, actionTypes, topics } = data;

  // Build lookup map
  const cellMap = new Map<string, CrossAnalysisCellData>();
  cells.forEach((cell) => {
    cellMap.set(`${cell.actionType}-${cell.topic}`, cell);
  });

  // Find max value
  const maxValue = Math.max(...cells.map((c) => c[valueKey] || 0));

  // Using inline formatters for CrossAnalysisHeatmap

  return (
    <div className={`overflow-x-auto ${className}`}>
      <div className="min-w-[500px]">
        {/* Header row with topic names */}
        <div className="flex mb-2">
          <div className="w-28 flex-shrink-0" /> {/* Spacer */}
          {topics.map((topic) => (
            <div
              key={topic}
              className="flex-1 text-center text-xs text-muted px-1 truncate"
              title={topic}
            >
              {topic.length > 6 ? topic.slice(0, 6) + '...' : topic}
            </div>
          ))}
        </div>

        {/* Data rows */}
        {actionTypes.map((actionType) => (
          <div key={actionType} className="flex mb-1">
            {/* Row label */}
            <div className="w-28 flex-shrink-0 flex items-center pr-2">
              <span className="text-xs text-muted truncate" title={actionType}>
                {actionType}
              </span>
            </div>

            {/* Cells */}
            {topics.map((topic) => {
              const cell = cellMap.get(`${actionType}-${topic}`);
              const value = cell?.[valueKey] || 0;
              const intensity = valueKey === 'avgER' ? cell?.erIntensity : cell?.countIntensity;
              const bgColor = getHeatmapColor(
                intensity !== undefined ? intensity * maxValue : value,
                maxValue
              );

              return (
                <div
                  key={topic}
                  className="flex-1 h-10 m-0.5 rounded-sm relative group cursor-pointer transition-transform hover:scale-105 hover:z-10"
                  style={{ backgroundColor: cell ? bgColor : 'rgba(100, 116, 139, 0.1)' }}
                >
                  {/* Cell content */}
                  {cell && (
                    <span className="absolute inset-0 flex items-center justify-center text-[10px] font-medium text-bright/80">
                      {valueKey === 'avgER' ? cell.avgER.toFixed(1) : cell.postCount}
                    </span>
                  )}

                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20">
                    <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg whitespace-nowrap">
                      <p className="text-xs text-muted mb-1">
                        {actionType} × {topic}
                      </p>
                      {cell ? (
                        <>
                          <p className="text-sm font-semibold text-bright">
                            互動率: {formatPercent(cell.avgER)}
                          </p>
                          <p className="text-xs text-muted">
                            {cell.postCount} 則貼文
                          </p>
                        </>
                      ) : (
                        <p className="text-xs text-muted">無資料</p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ))}

        {/* Legend */}
        <div className="flex items-center justify-end mt-4 gap-2">
          <span className="text-xs text-muted">低{valueKey === 'avgER' ? '互動' : '數量'}</span>
          <div className="flex">
            {[0.2, 0.4, 0.6, 0.8, 1].map((intensity, i) => (
              <div
                key={i}
                className="w-5 h-3"
                style={{ backgroundColor: getHeatmapColor(intensity * maxValue, maxValue) }}
              />
            ))}
          </div>
          <span className="text-xs text-muted">高{valueKey === 'avgER' ? '互動' : '數量'}</span>
        </div>
      </div>
    </div>
  );
}
