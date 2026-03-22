import React from 'react';
import type { CompareData } from '../../types';
import ScoreChart from './ScoreChart';

interface ModelComparisonProps {
  comparison: CompareData;
}

const ModelComparison: React.FC<ModelComparisonProps> = ({ comparison }) => {
  if (!comparison?.providers || comparison.providers.length === 0) {
    return (
      <div className="card p-4 text-center text-sm text-surface-500">
        No comparison data available. Run queries with different providers to compare.
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-surface-800 dark:text-surface-200 mb-4">
        Provider Comparison
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {comparison.providers.map((provider) => (
          <div key={`${provider.provider}-${provider.model}`} className="card p-4">
            {/* Provider header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="text-sm font-semibold text-surface-800 dark:text-surface-200">
                  {provider.provider}
                </h4>
                <p className="text-xs text-surface-500 font-mono">{provider.model}</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold font-mono text-brand-500 dark:text-brand-400">
                  {Math.round((provider.avg_trust_score || 0) * 100)}%
                </div>
                <p className="text-[10px] text-surface-500">Trust Score</p>
              </div>
            </div>

            {/* Scores */}
            <ScoreChart
              scores={[
                { label: 'Faithfulness', value: provider.avg_faithfulness },
                { label: 'Hallucination (inv)', value: provider.avg_hallucination !== undefined ? 1 - provider.avg_hallucination : undefined },
                { label: 'Citation Precision', value: provider.avg_citation_precision },
                { label: 'Citation Recall', value: provider.avg_citation_recall },
                { label: 'Trust Score', value: provider.avg_trust_score },
              ]}
            />

            {/* Query count */}
            <div className="mt-3 pt-3 border-t border-surface-200 dark:border-surface-700/30 text-[10px] text-surface-500">
              Based on {provider.query_count} queries
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ModelComparison;
