/**
 * KPICard Component - Animated number display for key metrics
 */

import { useEffect, useRef, useState } from 'react';
import { formatNumber, formatPercent, formatCurrency } from '@/utils/formatters';

interface KPICardProps {
  title: string;
  value: number;
  previousValue?: number;
  format?: 'number' | 'percent' | 'currency';
  decimals?: number;
  color?: 'primary' | 'secondary' | 'tertiary' | 'warning' | 'danger';
  icon?: React.ReactNode;
  selected?: boolean;
  onClick?: () => void;
  loading?: boolean;
  subtitle?: string;
}

const colorClasses = {
  primary: 'text-primary',
  secondary: 'text-secondary',
  tertiary: 'text-tertiary',
  warning: 'text-warning',
  danger: 'text-danger',
};

const bgClasses = {
  primary: 'bg-primary/10',
  secondary: 'bg-secondary/10',
  tertiary: 'bg-tertiary/10',
  warning: 'bg-warning/10',
  danger: 'bg-danger/10',
};

export function KPICard({
  title,
  value,
  previousValue,
  format = 'number',
  decimals = 2,
  color = 'primary',
  icon,
  selected = false,
  onClick,
  loading = false,
  subtitle,
}: KPICardProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const animationRef = useRef<number | undefined>(undefined);
  const startTimeRef = useRef<number | undefined>(undefined);

  // Animate value on change
  useEffect(() => {
    if (loading) return;

    const duration = 800;
    const startValue = displayValue;
    const endValue = value;

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);

      // Easing function (ease-out-cubic)
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = startValue + (endValue - startValue) * eased;

      setDisplayValue(current);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    startTimeRef.current = undefined;
    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [value, loading]);

  // Format the display value
  const formattedValue = (() => {
    switch (format) {
      case 'percent':
        return formatPercent(displayValue, decimals);
      case 'currency':
        return formatCurrency(displayValue);
      default:
        return formatNumber(Math.round(displayValue));
    }
  })();

  // Calculate change percentage
  const change =
    previousValue !== undefined && previousValue !== 0
      ? ((value - previousValue) / previousValue) * 100
      : null;

  const isPositive = change !== null && change >= 0;

  return (
    <div
      className={`
        relative p-5 rounded-lg border transition-all duration-200 cursor-pointer
        ${selected ? 'bg-card border-primary/30 shadow-glow-primary' : 'bg-card/50 border-white/5 hover:bg-card hover:border-white/10'}
        ${onClick ? 'cursor-pointer' : 'cursor-default'}
      `}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-muted text-xs font-medium uppercase tracking-wider">
          {title}
        </span>
        {icon && (
          <div className={`w-8 h-8 rounded-lg ${bgClasses[color]} flex items-center justify-center`}>
            <span className={colorClasses[color]}>{icon}</span>
          </div>
        )}
      </div>

      {/* Value */}
      {loading ? (
        <div className="h-9 w-24 bg-surface rounded animate-pulse" />
      ) : (
        <div className={`text-3xl font-bold ${colorClasses[color]} tabular-nums`}>
          {formattedValue}
        </div>
      )}

      {/* Subtitle or Change */}
      <div className="mt-2 flex items-center gap-2">
        {subtitle ? (
          <span className="text-muted text-xs">{subtitle}</span>
        ) : change !== null ? (
          <span
            className={`text-xs font-medium ${isPositive ? 'text-primary' : 'text-danger'}`}
          >
            {isPositive ? '↑' : '↓'} {Math.abs(change).toFixed(1)}%
          </span>
        ) : null}
      </div>

      {/* Selected indicator */}
      {selected && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-b" />
      )}
    </div>
  );
}

/**
 * MiniKPICard - Smaller version for inline use
 */
interface MiniKPICardProps {
  label: string;
  value: number | string;
  format?: 'number' | 'percent' | 'currency' | 'text';
  color?: 'primary' | 'secondary' | 'tertiary' | 'warning' | 'danger' | 'muted';
}

export function MiniKPICard({
  label,
  value,
  format = 'number',
  color = 'primary',
}: MiniKPICardProps) {
  const formattedValue = (() => {
    if (format === 'text' || typeof value === 'string') return value;
    switch (format) {
      case 'percent':
        return formatPercent(value as number);
      case 'currency':
        return formatCurrency(value as number);
      default:
        return formatNumber(value as number);
    }
  })();

  return (
    <div className="flex flex-col">
      <span className="text-muted text-xs">{label}</span>
      <span className={`text-lg font-semibold ${color === 'muted' ? 'text-muted' : colorClasses[color as keyof typeof colorClasses]}`}>
        {formattedValue}
      </span>
    </div>
  );
}
