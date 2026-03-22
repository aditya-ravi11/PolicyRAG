import React from 'react';
import type { AnalyticsData, CompareData, EvalHistory } from '../../types';
import ScoreChart from './ScoreChart';
import ModelComparison from './ModelComparison';
import { formatDate, scoreColor, formatScore } from '../../utils/formatters';

interface EvalDashboardProps {
  analytics: AnalyticsData | null;
  comparison: CompareData | null;
  history: EvalHistory[];
  isLoading: boolean;
  onClose: () => void;
  onRefresh: () => void;
}

const EvalDashboard: React.FC<EvalDashboardProps> = ({
  analytics,
  comparison,
  history,
  isLoading,
  onClose,
  onRefresh,
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[85vh] bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-200 dark:border-surface-700/50 shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-surface-900 dark:text-surface-100">
              Evaluation Dashboard
            </h2>
            <p className="text-xs text-surface-500 mt-0.5">
              Quality metrics and provider comparison
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="btn-secondary flex items-center gap-1.5"
            >
              <svg
                className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-surface-200 dark:hover:bg-surface-800 flex items-center justify-center text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoading && !analytics ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              {analytics && (
                <div>
                  <h3 className="text-sm font-semibold text-surface-800 dark:text-surface-200 mb-3">
                    Overall Metrics
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                    <StatCard
                      label="Total Queries"
                      value={String(analytics.total_queries || 0)}
                      color="text-brand-500 dark:text-brand-400"
                    />
                    <StatCard
                      label="Avg Trust Score"
                      value={formatScore(analytics.avg_trust_score)}
                      color={scoreColor(analytics.avg_trust_score)}
                    />
                    <StatCard
                      label="Avg Faithfulness"
                      value={formatScore(analytics.avg_faithfulness)}
                      color={scoreColor(analytics.avg_faithfulness)}
                    />
                    <StatCard
                      label="Avg Hallucination"
                      value={formatScore(analytics.avg_hallucination)}
                      color={scoreColor(
                        analytics.avg_hallucination !== undefined
                          ? 1 - analytics.avg_hallucination
                          : undefined
                      )}
                    />
                  </div>

                  {/* Score Distribution */}
                  <div className="card p-4">
                    <ScoreChart
                      title="Average Score Distribution"
                      scores={[
                        { label: 'Faithfulness', value: analytics.avg_faithfulness },
                        { label: 'Citation Precision', value: analytics.avg_citation_precision },
                        { label: 'Citation Recall', value: analytics.avg_citation_recall },
                        { label: 'Context Relevance', value: analytics.avg_context_relevance },
                        { label: 'Trust Score', value: analytics.avg_trust_score },
                      ]}
                    />
                  </div>
                </div>
              )}

              {/* Provider Comparison */}
              {comparison && <ModelComparison comparison={comparison} />}

              {/* Recent Evaluations Table */}
              {history.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-surface-800 dark:text-surface-200 mb-3">
                    Recent Evaluations
                  </h3>
                  <div className="card overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-surface-200 dark:border-surface-700/50 text-surface-500 dark:text-surface-400">
                            <th className="text-left px-4 py-2.5 font-medium">Query</th>
                            <th className="text-left px-3 py-2.5 font-medium">Provider</th>
                            <th className="text-center px-3 py-2.5 font-medium">Faith.</th>
                            <th className="text-center px-3 py-2.5 font-medium">Halluc.</th>
                            <th className="text-center px-3 py-2.5 font-medium">Cit. Prec.</th>
                            <th className="text-center px-3 py-2.5 font-medium">Trust</th>
                            <th className="text-right px-4 py-2.5 font-medium">Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {history.slice(0, 20).map((entry) => (
                            <tr
                              key={entry.id}
                              className="border-b border-surface-200 dark:border-surface-800/50 hover:bg-surface-100 dark:hover:bg-surface-800/20"
                            >
                              <td className="px-4 py-2.5 text-surface-600 dark:text-surface-300 max-w-[200px] truncate">
                                {entry.query_text}
                              </td>
                              <td className="px-3 py-2.5 text-surface-500 dark:text-surface-400 font-mono">
                                {entry.provider}
                              </td>
                              <td className={`px-3 py-2.5 text-center font-mono ${scoreColor(entry.faithfulness_score)}`}>
                                {formatScore(entry.faithfulness_score)}
                              </td>
                              <td className={`px-3 py-2.5 text-center font-mono ${scoreColor(entry.hallucination_score !== undefined ? 1 - entry.hallucination_score : undefined)}`}>
                                {formatScore(entry.hallucination_score)}
                              </td>
                              <td className={`px-3 py-2.5 text-center font-mono ${scoreColor(entry.citation_precision)}`}>
                                {formatScore(entry.citation_precision)}
                              </td>
                              <td className={`px-3 py-2.5 text-center font-mono ${scoreColor(entry.overall_trust_score)}`}>
                                {formatScore(entry.overall_trust_score)}
                              </td>
                              <td className="px-4 py-2.5 text-right text-surface-500">
                                {formatDate(entry.created_at)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Empty state */}
              {!analytics && history.length === 0 && (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 text-surface-300 dark:text-surface-700 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <p className="text-sm text-surface-500">
                    No evaluation data yet. Start asking questions to build evaluation history.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// Internal stat card component
function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="card p-3">
      <div className="text-[10px] text-surface-500 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-xl font-bold font-mono ${color}`}>{value}</div>
    </div>
  );
}

export default EvalDashboard;
