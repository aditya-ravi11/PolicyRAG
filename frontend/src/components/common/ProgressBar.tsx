import React from 'react';
import { scoreBarColor } from '../../utils/formatters';

interface ProgressBarProps {
  value: number | undefined | null;
  label?: string;
  showPercentage?: boolean;
  height?: string;
  className?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercentage = true,
  height = 'h-2',
  className = '',
}) => {
  const safeValue = value !== undefined && value !== null ? value : 0;
  const percentage = Math.round(safeValue * 100);
  const barColor = scoreBarColor(value);

  return (
    <div className={`w-full ${className}`}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between mb-1">
          {label && (
            <span className="text-xs text-surface-500 dark:text-surface-400 font-medium">{label}</span>
          )}
          {showPercentage && value !== undefined && value !== null && (
            <span className="text-xs font-mono text-surface-600 dark:text-surface-300">
              {percentage}%
            </span>
          )}
          {(value === undefined || value === null) && showPercentage && (
            <span className="text-xs text-surface-500">N/A</span>
          )}
        </div>
      )}
      <div className={`w-full ${height} bg-surface-200 dark:bg-surface-700/50 rounded-full overflow-hidden`}>
        <div
          className={`${height} ${barColor} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
