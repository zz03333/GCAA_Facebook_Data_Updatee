/**
 * BarChart Component - Horizontal and vertical bar charts with Recharts
 */

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { formatNumber } from '@/utils/formatters';
import { COLORS, generateGradientColors } from '@/utils/colors';

interface BarChartProps {
  data: Array<{
    name: string;
    value: number;
    color?: string;
    [key: string]: string | number | undefined;
  }>;
  dataKey?: string;
  nameKey?: string;
  color?: string;
  layout?: 'horizontal' | 'vertical';
  showGrid?: boolean;
  height?: number;
  valueFormatter?: (value: number) => string;
  className?: string;
  useGradient?: boolean;
}

export function BarChart({
  data,
  dataKey = 'value',
  nameKey = 'name',
  color = COLORS.primary,
  layout = 'vertical',
  showGrid = false,
  height = 300,
  valueFormatter = formatNumber,
  className = '',
  useGradient = true,
}: BarChartProps) {
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

  // Generate gradient colors if needed
  const gradientColors = useGradient ? generateGradientColors(color, data.length) : null;

  // For horizontal bars (vertical layout), we need to swap X and Y
  const isHorizontal = layout === 'horizontal';

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart
          data={data}
          layout={isHorizontal ? 'vertical' : 'horizontal'}
          margin={{ top: 10, right: 30, left: isHorizontal ? 80 : 10, bottom: 10 }}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(100, 116, 139, 0.1)"
              horizontal={!isHorizontal}
              vertical={isHorizontal}
            />
          )}
          {isHorizontal ? (
            <>
              <XAxis
                type="number"
                tickFormatter={valueFormatter}
                stroke="var(--color-muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                type="category"
                dataKey={nameKey}
                stroke="var(--color-muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={70}
              />
            </>
          ) : (
            <>
              <XAxis
                type="category"
                dataKey={nameKey}
                stroke="var(--color-muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                interval={0}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                type="number"
                tickFormatter={valueFormatter}
                stroke="var(--color-muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
            </>
          )}
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null;
              const item = payload[0].payload;
              return (
                <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg">
                  <p className="text-xs text-muted mb-1">{item[nameKey]}</p>
                  <p className="text-sm font-semibold text-bright">
                    {valueFormatter(item[dataKey] as number)}
                  </p>
                </div>
              );
            }}
            cursor={{ fill: 'rgba(100, 116, 139, 0.1)' }}
          />
          <Bar
            dataKey={dataKey}
            radius={[4, 4, 4, 4]}
            maxBarSize={40}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || (gradientColors ? gradientColors[index] : color)}
              />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Stacked bar chart for comparing multiple categories
 */
interface StackedBarChartProps {
  data: Array<Record<string, string | number>>;
  bars: Array<{
    dataKey: string;
    label: string;
    color: string;
  }>;
  xAxisKey?: string;
  showGrid?: boolean;
  height?: number;
  valueFormatter?: (value: number) => string;
  className?: string;
}

export function StackedBarChart({
  data,
  bars,
  xAxisKey = 'name',
  showGrid = false,
  height = 300,
  valueFormatter = formatNumber,
  className = '',
}: StackedBarChartProps) {
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
        <RechartsBarChart
          data={data}
          margin={{ top: 10, right: 10, left: 0, bottom: 10 }}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(100, 116, 139, 0.1)"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
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
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              return (
                <div className="bg-card border border-white/10 rounded-lg px-3 py-2 shadow-lg">
                  <p className="text-xs text-muted mb-2">{label}</p>
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
            cursor={{ fill: 'rgba(100, 116, 139, 0.1)' }}
          />
          {bars.map((bar) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              name={bar.label}
              stackId="stack"
              fill={bar.color}
              radius={[0, 0, 0, 0]}
            />
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}
