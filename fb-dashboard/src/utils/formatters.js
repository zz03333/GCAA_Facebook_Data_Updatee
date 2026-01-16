export function formatNumber(num) {
  if (num === null || num === undefined) return '-';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toLocaleString('zh-TW');
}

export function formatPercent(num, decimals = 2) {
  if (num === null || num === undefined) return '-';
  return num.toFixed(decimals) + '%';
}

export function formatDate(dateStr, format = 'short') {
  if (!dateStr) return '-';
  const date = new Date(dateStr);

  if (format === 'short') {
    return date.toLocaleDateString('zh-TW', { month: 'numeric', day: 'numeric' });
  }
  if (format === 'medium') {
    return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
  }
  if (format === 'long') {
    return date.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric' });
  }
  if (format === 'full') {
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  return dateStr;
}

export function formatRelativeTime(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '昨天';
  if (diffDays < 7) return `${diffDays} 天前`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} 週前`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} 個月前`;
  return `${Math.floor(diffDays / 365)} 年前`;
}

// Chart colors
export const COLORS = {
  primary: '#22c55e',
  secondary: '#06b6d4',
  tertiary: '#8b5cf6',
  warning: '#f59e0b',
  danger: '#ef4444',
  pink: '#ec4899',
  slate: '#64748b'
};

export const ACTION_COLORS = {
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
  '其他': '#64748b'
};

export const TOPIC_COLORS = {
  '核能發電': '#ef4444',
  '氣候問題': '#3b82f6',
  '淨零政策': '#22c55e',
  '產業分析': '#f59e0b',
  '能源發展': '#8b5cf6',
  '其他議題': '#06b6d4',
  '其他議題 (無關鍵字匹配)': '#64748b',
  '其他': '#64748b'
};

// Aggregate data by date range
export function aggregateByDateRange(daily, weeks, dateRange = null) {
  if (!daily || !daily.length) return [];

  let data = [...daily];

  // Custom date range filter
  if (weeks === 'custom' && dateRange) {
    if (dateRange.start) {
      data = data.filter(d => d.date >= dateRange.start);
    }
    if (dateRange.end) {
      data = data.filter(d => d.date <= dateRange.end);
    }
  } else if (weeks !== 'all') {
    const numWeeks = parseInt(weeks);
    if (!isNaN(numWeeks)) {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - numWeeks * 7);
      const cutoffStr = cutoffDate.toISOString().slice(0, 10);
      data = data.filter(d => d.date >= cutoffStr);
    }
  }

  // Filter out entries with null/undefined date and sort oldest to newest for charts
  return data
    .filter(d => d.date != null)
    .sort((a, b) => (a.date || '').localeCompare(b.date || ''));
}

// Calculate comparison data (7 days ago)
export function getComparisonData(daily, offset = 7) {
  if (!daily || !daily.length) return [];

  // Filter out entries with null date first
  const validDaily = daily.filter(d => d.date != null);

  return validDaily.map(d => {
    const targetDate = new Date(d.date);
    targetDate.setDate(targetDate.getDate() - offset);
    const targetStr = targetDate.toISOString().slice(0, 10);
    const comparison = validDaily.find(x => x.date === targetStr);
    return {
      ...d,
      comparison
    };
  });
}
