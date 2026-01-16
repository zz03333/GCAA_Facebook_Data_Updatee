/**
 * GCAA Dashboard - Formatting Utilities
 */

type DateFormat = 'short' | 'medium' | 'long' | 'full';

/**
 * Format a number with K/M suffixes for large values
 */
export function formatNumber(num: number | null | undefined): string {
  if (num === null || num === undefined) return '-';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toLocaleString('zh-TW');
}

/**
 * Format a number as a percentage
 */
export function formatPercent(num: number | null | undefined, decimals = 2): string {
  if (num === null || num === undefined) return '-';
  return num.toFixed(decimals) + '%';
}

/**
 * Format currency (TWD)
 */
export function formatCurrency(num: number | null | undefined): string {
  if (num === null || num === undefined) return '-';
  return 'NT$' + num.toLocaleString('zh-TW', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

/**
 * Format a date string
 */
export function formatDate(dateStr: string | null | undefined, format: DateFormat = 'short'): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);

  if (isNaN(date.getTime())) return '-';

  switch (format) {
    case 'short':
      return date.toLocaleDateString('zh-TW', { month: 'numeric', day: 'numeric' });
    case 'medium':
      return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
    case 'long':
      return date.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric' });
    case 'full':
      return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    default:
      return dateStr;
  }
}

/**
 * Format a date as relative time (e.g., "2 days ago")
 */
export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '昨天';
  if (diffDays < 7) return `${diffDays} 天前`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} 週前`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} 個月前`;
  return `${Math.floor(diffDays / 365)} 年前`;
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Format time slot to Chinese
 */
export function formatTimeSlot(slot: string): string {
  const timeSlotMap: Record<string, string> = {
    morning: '早上 (6-12點)',
    noon: '中午 (12-15點)',
    afternoon: '下午 (15-18點)',
    evening: '晚上 (18-23點)',
    night: '深夜 (23-6點)',
  };
  return timeSlotMap[slot] || slot;
}

/**
 * Format day of week to Chinese
 */
export function formatDayOfWeek(dayIndex: number): string {
  const days = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];
  return days[dayIndex] || '';
}

/**
 * Format performance tier to Chinese
 */
export function formatPerformanceTier(tier: string): string {
  const tierMap: Record<string, string> = {
    viral: '熱門',
    high: '優質',
    average: '一般',
    low: '低表現',
  };
  return tierMap[tier] || tier;
}

/**
 * Get date range based on time range selection
 */
export function getDateRangeFromTimeRange(timeRange: string): { start: string; end: string } | null {
  if (timeRange === 'all' || timeRange === 'custom') return null;

  const weeks = parseInt(timeRange);
  if (isNaN(weeks)) return null;

  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - weeks * 7);

  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}
