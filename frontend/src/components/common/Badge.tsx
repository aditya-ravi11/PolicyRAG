import React from 'react';

interface BadgeProps {
  status: string;
  className?: string;
}

const statusStyles: Record<string, string> = {
  READY: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  ready: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  PROCESSING: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  processing: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  FAILED: 'bg-red-500/15 text-red-400 border-red-500/30',
  failed: 'bg-red-500/15 text-red-400 border-red-500/30',
  PENDING: 'bg-surface-500/15 text-surface-400 border-surface-500/30',
  pending: 'bg-surface-500/15 text-surface-400 border-surface-500/30',
};

const Badge: React.FC<BadgeProps> = ({ status, className = '' }) => {
  const style =
    statusStyles[status] ||
    'bg-surface-500/15 text-surface-400 border-surface-500/30';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border ${style} ${className}`}
    >
      {status === 'PROCESSING' || status === 'processing' ? (
        <>
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse mr-1.5" />
          {status.toUpperCase()}
        </>
      ) : (
        status.toUpperCase()
      )}
    </span>
  );
};

export default Badge;
