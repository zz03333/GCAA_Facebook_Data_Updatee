/**
 * ScatterPlot Component - Quadrant analysis visualization
 */

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
  ZAxis,
} from 'recharts';
import { formatNumber, formatPercent } from '@/utils/formatters';
import { COLORS, getQuadrantColor } from '@/utils/colors';

interface ScatterDataPoint {
  x: number;
  y: number;
  name?: string;
  id?: string;
  category?: string;
  quadrant?: string;
  size?: number;
  [key: string]: string | number | undefined;
}

interface ScatterPlotProps {
  data: ScatterDataPoint[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  xAxisFormatter?: (value: number) => string;
  yAxisFormatter?: (value: number) => string;
  showQuadrants?: boolean;
  medianX?: number;
  medianY?: number;
  height?: number;
  colorByQuadrant?: boolean;
  onPointClick?: (point: ScatterDataPoint) => void;
  className?: string;
}

const QUADRANT_LABELS = {
  'high-reach-high-er': '明星內容',
  'high-reach-low-er': '潛力內容',
  'low-reach-high-er': '利基內容',
  'low-reach-low-er': '常態內容',
};

export function ScatterPlot({
  data,
  xAxisLabel = '觸及人數',
  yAxisLabel = '互動率 (%)',
  xAxisFormatter = formatNumber,
  yAxisFormatter = (v) => formatPercent(v),
  showQuadrants = true,
  medianX,
  medianY,
  height = 400,
  colorByQuadrant = true,
  onPointClick,
  className = '',
}: ScatterPlotProps) {
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

  // Calculate medians if not provided
  const sortedX = data.map((d) => d.x).sort((a, b) => a - b);
  const sortedY = data.map((d) => d.y).sort((a, b) => a - b);
  const calcMedianX = medianX ?? sortedX[Math.floor(data.length / 2)] ?? 0;
  const calcMedianY = medianY ?? sortedY[Math.floor(data.length / 2)] ?? 0;

  // Assign quadrant to each point
  const dataWithQuadrant = data.map((point) => {
    const isHighX = point.x >= calcMedianX;
    const isHighY = point.y >= calcMedianY;
    let quadrant: string;

    if (isHighX && isHighY) quadrant = 'high-reach-high-er';
    else if (isHighX && !isHighY) quadrant = 'high-reach-low-er';
    else if (!isHighX && isHighY) quadrant = 'low-reach-high-er';
    else quadrant = 'low-reach-low-er';

    return { ...point, quadrant: point.quadrant || quadrant };
  });

  // Get point color based on quadrant
  const getPointColor = (point: ScatterDataPoint) => {
    if (!colorByQuadrant) return COLORS.primary;
    return getQuadrantColor(point.quadrant || 'low-reach-low-er');
  };

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 60 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(100, 116, 139, 0.1)"
          />
          <XAxis
            type="number"
            dataKey="x"
            name={xAxisLabel}
            tickFormatter={xAxisFormatter}
            stroke="var(--color-muted)"
            fontSize={11}
            tickLine={false}
            label={{
              value: xAxisLabel,
              position: 'bottom',
              fill: 'var(--color-muted)',
              fontSize: 12,
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={yAxisLabel}
            tickFormatter={yAxisFormatter}
            stroke="var(--color-muted)"
            fontSize={11}
            tickLine={false}
            label={{
              value: yAxisLabel,
              angle: -90,
              position: 'insideLeft',
              fill: 'var(--color-muted)',
              fontSize: 12,
            }}
          />
          <ZAxis type="number" dataKey="size" range={[30, 200]} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null;
              const point = payload[0].payload as ScatterDataPoint;
              return (
                <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg max-w-xs">
                  {point.name && (
                    <p className="text-xs text-bright font-medium mb-1 line-clamp-2">
                      {point.name}
                    </p>
                  )}
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    <span className="text-muted">{xAxisLabel}:</span>
                    <span className="text-bright font-medium">
                      {xAxisFormatter(point.x)}
                    </span>
                    <span className="text-muted">{yAxisLabel}:</span>
                    <span className="text-bright font-medium">
                      {yAxisFormatter(point.y)}
                    </span>
                  </div>
                  {point.quadrant && (
                    <div
                      className="mt-2 text-xs px-2 py-1 rounded inline-block"
                      style={{
                        backgroundColor: getPointColor(point) + '20',
                        color: getPointColor(point),
                      }}
                    >
                      {QUADRANT_LABELS[point.quadrant as keyof typeof QUADRANT_LABELS] || point.quadrant}
                    </div>
                  )}
                </div>
              );
            }}
          />
          {/* Reference lines for quadrant divisions */}
          {showQuadrants && (
            <>
              <ReferenceLine
                x={calcMedianX}
                stroke="var(--color-muted)"
                strokeDasharray="5 5"
                strokeOpacity={0.5}
              />
              <ReferenceLine
                y={calcMedianY}
                stroke="var(--color-muted)"
                strokeDasharray="5 5"
                strokeOpacity={0.5}
              />
            </>
          )}
          <Scatter
            data={dataWithQuadrant}
            onClick={onPointClick ? (data) => onPointClick(data) : undefined}
            style={{ cursor: onPointClick ? 'pointer' : 'default' }}
          >
            {dataWithQuadrant.map((point, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getPointColor(point)}
                fillOpacity={0.7}
                stroke={getPointColor(point)}
                strokeWidth={1}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Quadrant Legend */}
      {showQuadrants && (
        <div className="flex flex-wrap justify-center gap-4 mt-4">
          {Object.entries(QUADRANT_LABELS).map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getQuadrantColor(key) }}
              />
              <span className="text-xs text-muted">{label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
