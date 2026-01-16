import { useState, useMemo } from 'react';
import { useData, useFilteredData } from './hooks/useData';
import Header from './components/Header';
import FilterBar from './components/FilterBar';
import KPICards from './components/KPICards';
import TrendChart from './components/TrendChart';
import { ActionTypeChart, TopicChart } from './components/BarCharts';
import HeatmapChart from './components/HeatmapChart';
import PostsTable from './components/PostsTable';
import ScatterChart from './components/ScatterChart';
import ContentAnalysisPage from './components/ContentAnalysisPage';
import AdAnalyticsPage from './components/AdAnalyticsPage';
import styles from './App.module.css';

function LoadingScreen() {
  return (
    <div className={styles.loading}>
      <div className={styles.loadingContent}>
        <div className={styles.loadingSpinner} />
        <p>載入資料中...</p>
      </div>
    </div>
  );
}

function ErrorScreen({ message }) {
  return (
    <div className={styles.error}>
      <div className={styles.errorContent}>
        <svg className={styles.errorIcon} viewBox="0 0 24 24" width="48" height="48">
          <path fill="#f59e0b" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
        </svg>
        <h2>載入失敗</h2>
        <p>{message}</p>
        <button onClick={() => window.location.reload()} className={styles.retryBtn}>
          重新載入
        </button>
      </div>
    </div>
  );
}

function DashboardPage({ daily, stats, timeRange, dateRange, onTimeRangeChange, onDateRangeChange, onChartClick }) {
  // Support multi-select metrics (max 2)
  const [selectedMetrics, setSelectedMetrics] = useState(['avgEngagementRate']);

  return (
    <div className={styles.page}>
      <FilterBar
        timeRange={timeRange}
        onTimeRangeChange={onTimeRangeChange}
        dateRange={dateRange}
        onDateRangeChange={onDateRangeChange}
      />

      <KPICards
        stats={stats}
        daily={daily}
        timeRange={timeRange}
        dateRange={dateRange}
        selectedMetrics={selectedMetrics}
        onMetricChange={setSelectedMetrics}
      />

      {daily && daily.length > 0 ? (
        <TrendChart
          daily={daily}
          timeRange={timeRange}
          dateRange={dateRange}
          selectedMetrics={selectedMetrics}
          onMetricChange={setSelectedMetrics}
          onDateClick={(date) => onChartClick('date', date)}
        />
      ) : (
        <div className={styles.placeholder}>無趨勢資料</div>
      )}

      <div className={styles.chartRow}>
        {stats?.byActionType?.length > 0 ? (
          <ActionTypeChart
            data={stats.byActionType}
            onClick={(actionType) => onChartClick('actionType', actionType)}
          />
        ) : (
          <div className={styles.placeholder}>無行動類型資料</div>
        )}
        {stats?.byTopic?.length > 0 ? (
          <TopicChart
            data={stats.byTopic}
            onClick={(topic) => onChartClick('topic', topic)}
          />
        ) : (
          <div className={styles.placeholder}>無議題資料</div>
        )}
      </div>

      <HeatmapChart
        heatmapData={stats?.heatmap}
        onClick={(cell) => onChartClick('time', cell)}
      />
    </div>
  );
}

function ExplorerPage({ posts, stats, timeRange, dateRange, onTimeRangeChange, onDateRangeChange, presetFilter, onClearPresetFilter }) {
  const [filters, setFilters] = useState({
    timeRange,
    dateRange,
    actionType: 'all',
    topic: 'all',
    search: '',
    sortBy: 'date',
    sortOrder: 'desc',
    hour: null,
    weekday: null
  });

  // 處理預設篩選條件
  useMemo(() => {
    if (presetFilter) {
      const newFilters = { ...filters, timeRange, dateRange, hour: null, weekday: null };
      if (presetFilter.type === 'actionType') {
        newFilters.actionType = presetFilter.value;
      } else if (presetFilter.type === 'topic') {
        newFilters.topic = presetFilter.value;
      } else if (presetFilter.type === 'time') {
        // Heatmap click: filter by hour and weekday
        newFilters.hour = presetFilter.value.hour;
        newFilters.weekday = presetFilter.value.weekday;
      }
      setFilters(newFilters);
    } else {
      setFilters(f => ({ ...f, timeRange, dateRange, hour: null, weekday: null }));
    }
  }, [timeRange, dateRange, presetFilter]);

  const filteredPosts = useFilteredData(posts, filters);

  const handleSort = (key) => {
    setFilters(f => ({
      ...f,
      sortBy: key,
      sortOrder: f.sortBy === key && f.sortOrder === 'desc' ? 'asc' : 'desc'
    }));
  };

  const handleClearFilter = () => {
    setFilters(f => ({
      ...f,
      actionType: 'all',
      topic: 'all',
      hour: null,
      weekday: null
    }));
    onClearPresetFilter?.();
  };

  // 檢查是否有活動的篩選條件
  const hasActiveFilter = presetFilter || filters.actionType !== 'all' || filters.topic !== 'all' || filters.hour !== null;

  return (
    <div className={styles.page}>
      <FilterBar
        timeRange={filters.timeRange}
        onTimeRangeChange={(val) => {
          setFilters(f => ({ ...f, timeRange: val }));
          onTimeRangeChange(val);
          onClearPresetFilter?.();
        }}
        dateRange={filters.dateRange}
        onDateRangeChange={(val) => {
          setFilters(f => ({ ...f, dateRange: val }));
          onDateRangeChange(val);
        }}
        actionTypes={stats?.byActionType || []}
        topics={stats?.byTopic || []}
        selectedActionType={filters.actionType}
        onActionTypeChange={(val) => {
          setFilters(f => ({ ...f, actionType: val }));
          onClearPresetFilter?.();
        }}
        selectedTopic={filters.topic}
        onTopicChange={(val) => {
          setFilters(f => ({ ...f, topic: val }));
          onClearPresetFilter?.();
        }}
        search={filters.search}
        onSearchChange={(val) => setFilters(f => ({ ...f, search: val }))}
        showSearch={true}
        showFilters={true}
      />

      <div className={styles.resultsInfo}>
        <span className={styles.resultCount}>
          共 <strong>{filteredPosts.length}</strong> 篇貼文
        </span>
        {hasActiveFilter && (
          <button className={styles.clearFilterBtn} onClick={handleClearFilter}>
            清除篩選
          </button>
        )}
      </div>

      <PostsTable
        posts={filteredPosts}
        sortBy={filters.sortBy}
        sortOrder={filters.sortOrder}
        onSort={handleSort}
      />
    </div>
  );
}

function AnalyticsPage({ posts, timeRange, dateRange, onTimeRangeChange, onDateRangeChange }) {
  const [filters, setFilters] = useState({ timeRange, dateRange });

  useMemo(() => {
    setFilters(f => ({ ...f, timeRange, dateRange }));
  }, [timeRange, dateRange]);

  const filteredPosts = useFilteredData(posts, filters);

  const handlePointClick = (post) => {
    if (post?.permalink) {
      window.open(post.permalink, '_blank');
    }
  };

  return (
    <div className={styles.page}>
      <FilterBar
        timeRange={filters.timeRange}
        onTimeRangeChange={(val) => {
          setFilters(f => ({ ...f, timeRange: val }));
          onTimeRangeChange(val);
        }}
        dateRange={filters.dateRange}
        onDateRangeChange={(val) => {
          setFilters(f => ({ ...f, dateRange: val }));
          onDateRangeChange(val);
        }}
      />

      <ScatterChart
        posts={filteredPosts}
        onPointClick={handlePointClick}
      />
    </div>
  );
}

export default function App() {
  const { posts, daily, stats, loading, error } = useData();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [timeRange, setTimeRange] = useState('12');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [presetFilter, setPresetFilter] = useState(null);

  const handleChartClick = (type, value) => {
    // 設定預設篩選條件
    if (type === 'date') {
      // 點擊趨勢圖上的日期
      setTimeRange('custom');
      setDateRange({ start: value, end: value });
      setPresetFilter({ type: 'date', value });
    } else if (type === 'actionType') {
      // 點擊行動類型
      setPresetFilter({ type: 'actionType', value });
    } else if (type === 'topic') {
      // 點擊議題
      setPresetFilter({ type: 'topic', value });
    } else if (type === 'time') {
      // 點擊熱力圖時段
      setPresetFilter({ type: 'time', value });
    }
    // 跳轉到 explorer 頁面
    setActiveTab('explorer');
  };

  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen message={error} />;

  return (
    <div className={styles.app}>
      <Header
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onLogoClick={() => setActiveTab('dashboard')}
        />

      <main className={styles.main}>
        {activeTab === 'dashboard' && (
          <DashboardPage
            daily={daily}
            stats={stats}
            timeRange={timeRange}
            dateRange={dateRange}
            onTimeRangeChange={setTimeRange}
            onDateRangeChange={setDateRange}
            onChartClick={handleChartClick}
          />
        )}

        {activeTab === 'explorer' && (
          <ExplorerPage
            posts={posts}
            stats={stats}
            timeRange={timeRange}
            dateRange={dateRange}
            onTimeRangeChange={setTimeRange}
            onDateRangeChange={setDateRange}
            presetFilter={presetFilter}
            onClearPresetFilter={() => setPresetFilter(null)}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsPage
            posts={posts}
            timeRange={timeRange}
            dateRange={dateRange}
            onTimeRangeChange={setTimeRange}
            onDateRangeChange={setDateRange}
          />
        )}

        {activeTab === 'content' && (
          <ContentAnalysisPage />
        )}

        {activeTab === 'ads' && (
          <AdAnalyticsPage />
        )}
      </main>

      <footer className={styles.footer}>
        <p>
          資料更新：{stats?.lastUpdated ? new Date(stats.lastUpdated).toLocaleString('zh-TW') : '-'}
          {' · '}
          <a href="https://gcaa.org.tw" target="_blank" rel="noopener noreferrer">
            綠色公民行動聯盟
          </a>
          {' · '}
          <a href="https://litostswirrl.github.io/gcaa-dashboard/" target="_blank" rel="noopener noreferrer">
            原始模板
          </a>
        </p>
      </footer>
    </div>
  );
}
