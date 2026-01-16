/**
 * GCAA Dashboard - Color Definitions
 */

// Base colors
export const COLORS = {
  primary: '#22c55e',
  secondary: '#06b6d4',
  tertiary: '#8b5cf6',
  warning: '#f59e0b',
  danger: '#ef4444',
  pink: '#ec4899',
  slate: '#64748b',
  blue: '#3b82f6',
  lime: '#84cc16',
  orange: '#f97316',
} as const;

// Action type color mapping
export const ACTION_COLORS: Record<string, string> = {
  '行動號召': '#ef4444',
  '定期活動': '#8b5cf6',
  '記者會': '#ec4899',
  '聲明稿': '#f59e0b',
  '新聞觀點': '#06b6d4',
  '投書': '#22c55e',
  '報告發布': '#3b82f6',
  '擺攤資訊': '#84cc16',
  '科普/Podcast': '#f97316',
  '其他行動 (無關鍵字匹配)': '#64748b',
  '其他': '#64748b',
};

// Topic color mapping
export const TOPIC_COLORS: Record<string, string> = {
  '核能發電': '#ef4444',
  '氣候問題': '#3b82f6',
  '淨零政策': '#22c55e',
  '產業分析': '#f59e0b',
  '能源發展': '#8b5cf6',
  '其他議題': '#06b6d4',
  '其他議題 (無關鍵字匹配)': '#64748b',
  '其他': '#64748b',
};

// Performance tier colors
export const TIER_COLORS: Record<string, string> = {
  viral: '#ef4444',
  high: '#22c55e',
  average: '#f59e0b',
  low: '#64748b',
};

// Quadrant colors
export const QUADRANT_COLORS: Record<string, string> = {
  'high-reach-high-er': '#22c55e',
  'high-reach-low-er': '#f59e0b',
  'low-reach-high-er': '#3b82f6',
  'low-reach-low-er': '#64748b',
};

// Chart color palette for sequential data
export const CHART_PALETTE = [
  '#22c55e',
  '#06b6d4',
  '#8b5cf6',
  '#f59e0b',
  '#ef4444',
  '#ec4899',
  '#3b82f6',
  '#84cc16',
  '#f97316',
  '#64748b',
];

/**
 * Get color for action type with fallback
 */
export function getActionTypeColor(actionType: string): string {
  return ACTION_COLORS[actionType] || COLORS.slate;
}

/**
 * Get color for topic with fallback
 */
export function getTopicColor(topic: string): string {
  return TOPIC_COLORS[topic] || COLORS.slate;
}

/**
 * Get color for performance tier with fallback
 */
export function getTierColor(tier: string): string {
  return TIER_COLORS[tier] || COLORS.slate;
}

/**
 * Get color for quadrant with fallback
 */
export function getQuadrantColor(quadrant: string): string {
  return QUADRANT_COLORS[quadrant] || COLORS.slate;
}

/**
 * Generate gradient colors for bar charts
 * Creates colors with decreasing opacity for visual hierarchy
 */
export function generateGradientColors(baseColor: string, count: number): string[] {
  const colors: string[] = [];
  const opacities = [1, 0.85, 0.7, 0.55, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1];

  for (let i = 0; i < count; i++) {
    const opacity = opacities[Math.min(i, opacities.length - 1)] ?? 0.1;
    colors.push(hexToRgba(baseColor, opacity));
  }

  return colors;
}

/**
 * Convert hex color to rgba
 */
export function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Get heatmap color based on value intensity
 */
export function getHeatmapColor(value: number, maxValue: number): string {
  if (value === 0 || maxValue === 0) return 'rgba(100, 116, 139, 0.3)'; // Gray for no data

  const intensity = Math.min(value / maxValue, 1);
  const minOpacity = 0.2;
  const maxOpacity = 1;
  const opacity = minOpacity + intensity * (maxOpacity - minOpacity);

  return hexToRgba(COLORS.primary, opacity);
}
