/**
 * TrendLineChart Component - Time series visualization with Recharts
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { formatNumber, formatDate } from '@/utils/formatters';
import { COLORS } from '@/utils/colors';

interface TrendLineChartProps {
  data: Array<{
    date: string;
    value: number;
    [key: string]: string | number;
  }>;
  dataKey?: string;
  color?: string;
  showArea?: boolean;
  showGrid?: boolean;
  height?: number;
  valueFormatter?: (value: number) => string;
  xAxisFormatter?: (date: string) => string;
  className?: string;
}

export function TrendLineChart({
  data,
  dataKey = 'value',
  color = COLORS.primary,
  showArea = true,
  showGrid = true,
  height = 300,
  valueFormatter = formatNumber,
  xAxisFormatter = (date) => formatDate(date, 'short'),
  className = '',
}: TrendLineChartProps) {
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

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        {showArea ? (
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(100, 116, 139, 0.1)"
                vertical={false}
              />
            )}
            <XAxis
              dataKey="date"
              tickFormatter={xAxisFormatter}
              stroke="var(--color-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tickFormatter={valueFormatter}
              stroke="var(--color-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              width={50}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                return (
                  <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg">
                    <p className="text-xs text-muted mb-1">{formatDate(String(label), 'medium')}</p>
                    <p className="text-sm font-semibold text-bright">
                      {valueFormatter(payload[0].value as number)}
                    </p>
                  </div>
                );
              }}
            />
            <defs>
              <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke="none"
              fill={`url(#gradient-${dataKey})`}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: color, stroke: 'var(--color-abyss)', strokeWidth: 2 }}
            />
          </ComposedChart>
        ) : (
          <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(100, 116, 139, 0.1)"
                vertical={false}
              />
            )}
            <XAxis
              dataKey="date"
              tickFormatter={xAxisFormatter}
              stroke="var(--color-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tickFormatter={valueFormatter}
              stroke="var(--color-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              width={50}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                return (
                  <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg">
                    <p className="text-xs text-muted mb-1">{formatDate(String(label), 'medium')}</p>
                    <p className="text-sm font-semibold text-bright">
                      {valueFormatter(payload[0].value as number)}
                    </p>
                  </div>
                );
              }}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: color, stroke: 'var(--color-abyss)', strokeWidth: 2 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Multi-line chart for comparing multiple metrics
 */
interface MultiLineChartProps {
  data: Array<Record<string, string | number>>;
  lines: Array<{
    dataKey: string;
    label: string;
    color: string;
  }>;
  xAxisKey?: string;
  showGrid?: boolean;
  height?: number;
  valueFormatter?: (value: number) => string;
  xAxisFormatter?: (date: string) => string;
  className?: string;
}

export function MultiLineChart({
  data,
  lines,
  xAxisKey = 'date',
  showGrid = true,
  height = 300,
  valueFormatter = formatNumber,
  xAxisFormatter = (date) => formatDate(date, 'short'),
  className = '',
}: MultiLineChartProps) {
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

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(100, 116, 139, 0.1)"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            tickFormatter={xAxisFormatter}
            stroke="var(--color-muted)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tickFormatter={valueFormatter}
            stroke="var(--color-muted)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={50}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              return (
                <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg">
                  <p className="text-xs text-muted mb-2">
                    {formatDate(label as string, 'medium')}
                  </p>
                  {payload.map((entry, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: entry.color }}
                      />
                      <span className="text-xs text-muted">{entry.name}:</span>
                      <span className="text-sm font-semibold text-bright">
                        {valueFormatter(entry.value as number)}
                      </span>
                    </div>
                  ))}
                </div>
              );
            }}
          />
          {lines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.label}
              stroke={line.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: line.color, stroke: 'var(--color-abyss)', strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
