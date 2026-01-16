/**
 * FilterBar Component - Date range and filter controls
 */

import { useState } from 'react';
import type { TimeRange, FilterState } from '@/types';
import { TIME_RANGE_OPTIONS } from '@/utils/constants';

interface FilterBarProps {
  filters: Partial<FilterState>;
  onFilterChange: (filters: Partial<FilterState>) => void;
  actionTypes?: string[];
  topics?: string[];
  showSearch?: boolean;
  showSort?: boolean;
  className?: string;
}

export function FilterBar({
  filters,
  onFilterChange,
  actionTypes = [],
  topics = [],
  showSearch = true,
  showSort = false,
  className = '',
}: FilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleTimeRangeChange = (timeRange: TimeRange) => {
    onFilterChange({ ...filters, timeRange });
  };

  const handleActionTypeChange = (actionType: string | null) => {
    onFilterChange({ ...filters, actionType });
  };

  const handleTopicChange = (topic: string | null) => {
    onFilterChange({ ...filters, topic });
  };

  const handleSearchChange = (search: string) => {
    onFilterChange({ ...filters, search });
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {/* Primary filters row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Time Range Pills */}
        <div className="flex items-center gap-1 bg-surface rounded-lg p-1">
          {TIME_RANGE_OPTIONS.filter(o => o.value !== 'custom').map((option) => (
            <button
              key={option.value}
              onClick={() => handleTimeRangeChange(option.value)}
              className={`
                px-3 py-1.5 rounded-md text-xs font-medium transition-all
                ${filters.timeRange === option.value
                  ? 'bg-primary text-abyss'
                  : 'text-muted hover:text-bright hover:bg-card'}
              `}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* Search */}
        {showSearch && (
          <div className="relative flex-1 min-w-[200px] max-w-[300px]">
            <input
              type="text"
              placeholder="搜尋貼文內容..."
              value={filters.search || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full px-4 py-2 pl-10 bg-surface border border-white/5 rounded-lg text-sm text-bright placeholder-muted focus:outline-none focus:border-primary/50"
            />
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        )}

        {/* Expand button for more filters */}
        {(actionTypes.length > 0 || topics.length > 0) && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1.5 px-3 py-2 text-xs text-muted hover:text-bright transition-colors"
          >
            <svg
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
            更多篩選
          </button>
        )}
      </div>

      {/* Expanded filters */}
      {isExpanded && (
        <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-white/5">
          {/* Action Type Filter */}
          {actionTypes.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted">行動類型:</span>
              <select
                value={filters.actionType || 'all'}
                onChange={(e) =>
                  handleActionTypeChange(e.target.value === 'all' ? null : e.target.value)
                }
                className="px-3 py-1.5 bg-surface border border-white/5 rounded-lg text-xs text-bright focus:outline-none focus:border-primary/50"
              >
                <option value="all">全部</option>
                {actionTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Topic Filter */}
          {topics.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted">議題:</span>
              <select
                value={filters.topic || 'all'}
                onChange={(e) =>
                  handleTopicChange(e.target.value === 'all' ? null : e.target.value)
                }
                className="px-3 py-1.5 bg-surface border border-white/5 rounded-lg text-xs text-bright focus:outline-none focus:border-primary/50"
              >
                <option value="all">全部</option>
                {topics.map((topic) => (
                  <option key={topic} value={topic}>
                    {topic}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Sort options */}
          {showSort && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted">排序:</span>
              <select
                value={filters.sortBy || 'date'}
                onChange={(e) =>
                  onFilterChange({
                    ...filters,
                    sortBy: e.target.value as FilterState['sortBy'],
                  })
                }
                className="px-3 py-1.5 bg-surface border border-white/5 rounded-lg text-xs text-bright focus:outline-none focus:border-primary/50"
              >
                <option value="date">日期</option>
                <option value="engagement">互動率</option>
                <option value="reach">觸及</option>
                <option value="shares">分享</option>
              </select>
              <button
                onClick={() =>
                  onFilterChange({
                    ...filters,
                    sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc',
                  })
                }
                className="p-1.5 bg-surface border border-white/5 rounded-lg hover:bg-card transition-colors"
              >
                <svg
                  className={`w-4 h-4 text-muted transition-transform ${filters.sortOrder === 'asc' ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
            </div>
          )}

          {/* Clear filters */}
          <button
            onClick={() =>
              onFilterChange({
                timeRange: '4',
                dateRange: { start: null, end: null },
                actionType: null,
                topic: null,
                search: '',
                sortBy: 'date',
                sortOrder: 'desc',
              })
            }
            className="text-xs text-muted hover:text-danger transition-colors"
          >
            清除篩選
          </button>
        </div>
      )}
    </div>
  );
}
