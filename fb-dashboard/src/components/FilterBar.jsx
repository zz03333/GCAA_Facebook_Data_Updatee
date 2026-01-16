import { useState } from 'react';
import styles from './FilterBar.module.css';

const TIME_RANGES = [
  { value: '1', label: '1 週' },
  { value: '2', label: '2 週' },
  { value: '4', label: '1 個月' },
  { value: '12', label: '3 個月' },
  { value: '26', label: '6 個月' },
  { value: '52', label: '1 年' },
  { value: 'all', label: '全部' },
  { value: 'custom', label: '自訂' }
];

export default function FilterBar({
  timeRange,
  onTimeRangeChange,
  dateRange,
  onDateRangeChange,
  actionTypes = [],
  topics = [],
  selectedActionType,
  onActionTypeChange,
  selectedTopic,
  onTopicChange,
  search,
  onSearchChange,
  showSearch = false,
  showFilters = false
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(timeRange === 'custom');

  return (
    <div className={styles.container}>
      <div className={styles.mainRow}>
        {/* Time Range Pills */}
        <div className={styles.timeRangeGroup}>
          <span className={styles.label}>時間範圍</span>
          <div className={styles.pills}>
            {TIME_RANGES.map(opt => (
              <button
                key={opt.value}
                className={`${styles.pill} ${timeRange === opt.value || (opt.value === 'custom' && showDatePicker) ? styles.active : ''}`}
                onClick={() => {
                  if (opt.value === 'custom') {
                    setShowDatePicker(true);
                    onTimeRangeChange('custom');
                  } else {
                    setShowDatePicker(false);
                    onTimeRangeChange(opt.value);
                  }
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Custom Date Range Picker */}
        {showDatePicker && (
          <div className={styles.datePickerGroup}>
            <label className={styles.dateField}>
              <span className={styles.dateLabel}>起始</span>
              <input
                type="date"
                value={dateRange?.start || ''}
                onChange={(e) => onDateRangeChange?.({
                  start: e.target.value,
                  end: dateRange?.end || ''
                })}
                className={styles.dateInput}
              />
            </label>
            <span className={styles.dateSeparator}>~</span>
            <label className={styles.dateField}>
              <span className={styles.dateLabel}>結束</span>
              <input
                type="date"
                value={dateRange?.end || ''}
                onChange={(e) => onDateRangeChange?.({
                  start: dateRange?.start || '',
                  end: e.target.value
                })}
                className={styles.dateInput}
              />
            </label>
          </div>
        )}

        {/* Search and Filters Toggle */}
        {(showSearch || showFilters) && (
          <div className={styles.actions}>
            {showSearch && (
              <div className={styles.searchWrapper}>
                <svg className={styles.searchIcon} viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <input
                  type="text"
                  placeholder="搜尋內容或標籤..."
                  value={search || ''}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className={styles.searchInput}
                />
                {search && (
                  <button
                    className={styles.clearBtn}
                    onClick={() => onSearchChange('')}
                  >
                    ✕
                  </button>
                )}
              </div>
            )}
            {showFilters && (
              <button
                className={`${styles.filterToggle} ${isExpanded ? styles.active : ''}`}
                onClick={() => setIsExpanded(!isExpanded)}
              >
                <span>篩選</span>
                <span className={styles.filterIcon}>{isExpanded ? '▲' : '▼'}</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Expanded Filters */}
      {showFilters && isExpanded && (
        <div className={styles.expandedFilters}>
          <label className={styles.filterGroup}>
            <span className={styles.filterLabel}>行動類型</span>
            <select
              value={selectedActionType || 'all'}
              onChange={(e) => onActionTypeChange(e.target.value)}
              className={styles.select}
            >
              <option value="all">全部</option>
              {actionTypes.map(a => (
                <option key={a.name} value={a.name}>{a.name} ({a.count})</option>
              ))}
            </select>
          </label>

          <label className={styles.filterGroup}>
            <span className={styles.filterLabel}>議題</span>
            <select
              value={selectedTopic || 'all'}
              onChange={(e) => onTopicChange(e.target.value)}
              className={styles.select}
            >
              <option value="all">全部</option>
              {topics.map(t => (
                <option key={t.name} value={t.name}>{t.name} ({t.count})</option>
              ))}
            </select>
          </label>

          {(selectedActionType !== 'all' || selectedTopic !== 'all') && (
            <button
              className={styles.clearFilters}
              onClick={() => {
                onActionTypeChange('all');
                onTopicChange('all');
              }}
            >
              清除篩選
            </button>
          )}
        </div>
      )}
    </div>
  );
}
