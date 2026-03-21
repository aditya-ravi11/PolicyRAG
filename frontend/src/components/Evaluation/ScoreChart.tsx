import React from 'react';
import { scoreBarColor, formatScore } from '../../utils/formatters';

interface ScoreChartProps {
  scores: { label: string; value: number | undefined | null }[];
  title?: string;
}

const ScoreChart: React.FC<ScoreChartProps> = ({ scores, title }) => {
  return (
    <div>
      {title && (
        <h4 className="text-xs font-semibold text-slate-300 mb-3 uppercase tracking-wider">
          {title}
        </h4>
      )}
      <div className="space-y-3">
        {scores.map(({ label, value }) => {
          const safeValue = value !== undefined && value !== null ? value : 0;
          const pct = Math.round(safeValue * 100);
          const barColor = scoreBarColor(value);

          return (
            <div key={label}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">{label}</span>
                <span className="text-xs font-mono text-slate-300">
                  {value !== undefined && value !== null ? formatScore(value) : 'N/A'}
                </span>
              </div>
              <div className="w-full h-2.5 bg-slate-700/50 rounded-full overflow-hidden">
                <div
                  className={`h-2.5 ${barColor} rounded-full transition-all duration-700 ease-out`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ScoreChart;
