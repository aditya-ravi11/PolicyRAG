import React from 'react';
import type { EvaluationScores, QueryMetadata } from '../../types';
import ProgressBar from '../common/ProgressBar';
import Tooltip from '../common/Tooltip';
import { formatLatency, scoreColor } from '../../utils/formatters';

interface TrustScoreCardProps {
  evaluation: EvaluationScores;
  metadata?: QueryMetadata;
  evaluationPending?: boolean;
}

const SHIMMER_LABELS = [
  'Faithfulness',
  'Citation Precision',
  'Citation Recall',
  'Non-Hallucination',
  'Context Relevance',
  'Completeness',
];

const TrustScoreCard: React.FC<TrustScoreCardProps> = ({ evaluation, metadata, evaluationPending }) => {
  const trustScore = evaluation.overall_trust_score;

  const totalLatency = metadata
    ? metadata.latency_retrieval_ms + metadata.latency_generation_ms + metadata.latency_evaluation_ms
    : 0;

  return (
    <div className="mt-3 p-3 bg-surface-100 dark:bg-surface-800/60 border border-surface-200 dark:border-surface-700/40 rounded-lg">
      {/* Trust Score Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-surface-500 dark:text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          {evaluationPending ? (
            <span className="text-xs font-semibold text-surface-500 dark:text-surface-400 animate-pulse">Verifying answer...</span>
          ) : (
            <span className="text-xs font-semibold text-surface-600 dark:text-surface-300">Trust Evaluation</span>
          )}
        </div>
        {!evaluationPending && trustScore !== undefined && trustScore !== null && (
          <Tooltip content="Overall trust score combining all metrics">
            <span className={`text-lg font-bold font-mono ${scoreColor(trustScore)}`}>
              {Math.round(trustScore * 100)}%
            </span>
          </Tooltip>
        )}
      </div>

      {/* Score Bars or Shimmer Placeholders */}
      <div className="space-y-2">
        {evaluationPending ? (
          // Shimmer placeholder bars
          SHIMMER_LABELS.map((label) => (
            <div key={label} className="flex items-center gap-2">
              <span className="text-[10px] text-surface-500 w-24 shrink-0">{label}</span>
              <div className="flex-1 h-1.5 rounded-full bg-surface-200 dark:bg-surface-700/50 overflow-hidden">
                <div className="h-full w-[60%] rounded-full bg-surface-400 dark:bg-surface-600 animate-pulse" />
              </div>
            </div>
          ))
        ) : (
          <>
            {evaluation.faithfulness !== undefined && evaluation.faithfulness !== null && (
              <ProgressBar
                value={evaluation.faithfulness}
                label="Faithfulness"
                height="h-1.5"
              />
            )}
            {evaluation.citation_precision !== undefined && evaluation.citation_precision !== null && (
              <ProgressBar
                value={evaluation.citation_precision}
                label="Citation Precision"
                height="h-1.5"
              />
            )}
            {evaluation.citation_recall !== undefined && evaluation.citation_recall !== null && (
              <ProgressBar
                value={evaluation.citation_recall}
                label="Citation Recall"
                height="h-1.5"
              />
            )}
            {evaluation.hallucination_score !== undefined && evaluation.hallucination_score !== null && (
              <ProgressBar
                value={1 - evaluation.hallucination_score}
                label="Non-Hallucination"
                height="h-1.5"
              />
            )}
            {evaluation.context_relevance !== undefined && evaluation.context_relevance !== null && (
              <ProgressBar
                value={evaluation.context_relevance}
                label="Context Relevance"
                height="h-1.5"
              />
            )}
            {evaluation.completeness !== undefined && evaluation.completeness !== null && (
              <ProgressBar
                value={evaluation.completeness}
                label="Completeness"
                height="h-1.5"
              />
            )}
          </>
        )}
      </div>

      {/* Latency breakdown footer */}
      {metadata && (
        <div className="mt-3 pt-2 border-t border-surface-200 dark:border-surface-700/30">
          <div className="flex items-center gap-4 text-[10px] text-surface-500">
            <span>
              {metadata.provider}/{metadata.model}
            </span>
            <span>{metadata.num_chunks_retrieved} chunks</span>
          </div>
          <div className="flex items-center gap-1 mt-1.5">
            <Tooltip content={`Retrieval: ${formatLatency(metadata.latency_retrieval_ms)}`}>
              <div
                className="h-1.5 rounded-l bg-blue-500/60"
                style={{ width: `${totalLatency > 0 ? (metadata.latency_retrieval_ms / totalLatency) * 100 : 33}%` }}
              />
            </Tooltip>
            <Tooltip content={`Generation: ${formatLatency(metadata.latency_generation_ms)}`}>
              <div
                className="h-1.5 bg-emerald-500/60"
                style={{ width: `${totalLatency > 0 ? (metadata.latency_generation_ms / totalLatency) * 100 : 33}%` }}
              />
            </Tooltip>
            <Tooltip content={evaluationPending ? 'Evaluation: ...' : `Evaluation: ${formatLatency(metadata.latency_evaluation_ms)}`}>
              <div
                className={`h-1.5 rounded-r bg-amber-500/60 ${evaluationPending ? 'animate-pulse' : ''}`}
                style={{ width: `${totalLatency > 0 ? (metadata.latency_evaluation_ms / totalLatency) * 100 : 33}%` }}
              />
            </Tooltip>
          </div>
          <div className="flex items-center justify-between mt-1 text-[10px] text-surface-500">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500/60" />
                Retrieval {formatLatency(metadata.latency_retrieval_ms)}
              </span>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/60" />
                Gen {formatLatency(metadata.latency_generation_ms)}
              </span>
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500/60" />
                Eval {evaluationPending ? '...' : formatLatency(metadata.latency_evaluation_ms)}
              </span>
            </div>
            <span className="font-mono">
              {evaluationPending ? formatLatency(metadata.latency_retrieval_ms + metadata.latency_generation_ms) + '+' : formatLatency(totalLatency) + ' total'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrustScoreCard;
