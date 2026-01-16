/**
 * Card Component - Base container with loading/error/empty states
 */

import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
  className?: string;
  headerAction?: ReactNode;
}

export function Card({
  title,
  subtitle,
  children,
  loading = false,
  error = null,
  empty = false,
  emptyMessage = '暫無資料',
  className = '',
  headerAction,
}: CardProps) {
  return (
    <div
      className={`bg-card rounded-lg border border-white/5 overflow-hidden ${className}`}
    >
      {/* Header */}
      {(title || headerAction) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          <div>
            {title && (
              <h3 className="text-bright font-semibold text-sm">{title}</h3>
            )}
            {subtitle && (
              <p className="text-muted text-xs mt-0.5">{subtitle}</p>
            )}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}

      {/* Content */}
      <div className="p-5">
        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error} />
        ) : empty ? (
          <EmptyState message={emptyMessage} />
        ) : (
          children
        )}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-col gap-3 animate-pulse">
      <div className="h-4 bg-surface rounded w-3/4" />
      <div className="h-4 bg-surface rounded w-1/2" />
      <div className="h-4 bg-surface rounded w-2/3" />
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="w-12 h-12 rounded-full bg-danger/10 flex items-center justify-center mb-3">
        <svg
          className="w-6 h-6 text-danger"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <p className="text-muted text-sm">{message}</p>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="w-12 h-12 rounded-full bg-surface flex items-center justify-center mb-3">
        <svg
          className="w-6 h-6 text-muted"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
      </div>
      <p className="text-muted text-sm">{message}</p>
    </div>
  );
}

export { LoadingState, ErrorState, EmptyState };
