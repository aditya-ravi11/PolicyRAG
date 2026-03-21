import React from 'react';
import type { EvaluationScores, QueryMetadata } from '../../types';
import ProgressBar from '../common/ProgressBar';
import Tooltip from '../common/Tooltip';
import { formatLatency, scoreColor } from '../../utils/formatters';

interface TrustScoreCardProps {
  evaluation: EvaluationScores;
  metadata?: QueryMetadata;
}

const TrustScoreCard: React.FC<TrustScoreCardProps> = ({ evaluation, metadata }) => {
  const trustScore = evaluation.overall_trust_score;

  return (
    <div className="mt-3 p-3 bg-slate-800/60 border border-slate-700/40 rounded-lg">
      {/* Trust Score Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className="text-xs font-semibold text-slate-300">Trust Evaluation</span>
        </div>
        {trustScore !== undefined && trustScore !== null && (
          <Tooltip content="Overall trust score combining all metrics">
            <span className={`text-lg font-bold font-mono ${scoreColor(trustScore)}`}>
              {Math.round(trustScore * 100)}%
            </span>
          </Tooltip>
        )}
      </div>

      {/* Score Bars */}
      <div className="space-y-2">
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
      </div>

      {/* Metadata footer */}
      {metadata && (
        <div className="mt-3 pt-2 border-t border-slate-700/30 flex items-center gap-4 text-[10px] text-slate-500">
          <span>
            {metadata.provider}/{metadata.model}
          </span>
          <span>{metadata.num_chunks_retrieved} chunks</span>
          <span>Retrieval: {formatLatency(metadata.latency_retrieval_ms)}</span>
          <span>Gen: {formatLatency(metadata.latency_generation_ms)}</span>
        </div>
      )}
    </div>
  );
};

export default TrustScoreCard;
