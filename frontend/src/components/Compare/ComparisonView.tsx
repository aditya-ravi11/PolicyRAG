import React from 'react';
import ReactMarkdown from 'react-markdown';
import type { CompareQueryResponse } from '../../types';

interface ComparisonViewProps {
  result: CompareQueryResponse;
}

const ComparisonView: React.FC<ComparisonViewProps> = ({ result }) => {
  const { vanilla, policyrag } = result;
  const eval_ = policyrag.evaluation;

  const citationCount = policyrag.citations.length;
  const trustScore = eval_.overall_trust_score;
  const faithfulness = eval_.faithfulness;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Query bar */}
      <div className="px-4 py-2 bg-slate-800/50 border-b border-slate-700/30 text-sm text-slate-400 shrink-0">
        <span className="text-slate-500 mr-2">Query:</span>
        <span className="text-slate-200">{result.query}</span>
      </div>

      {/* Two-column comparison */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Vanilla RAG */}
        <div className="flex-1 flex flex-col border-r border-slate-700/30 overflow-hidden">
          <div className="px-4 py-2 bg-slate-700/30 border-b border-slate-700/30 shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Vanilla RAG
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-600/50 text-slate-400">
                No guardrails
              </span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 prose prose-invert prose-sm max-w-none prose-p:my-1.5 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:text-slate-200 prose-strong:text-slate-100">
            <ReactMarkdown>{vanilla.answer}</ReactMarkdown>
          </div>
          <div className="px-4 py-2 border-t border-slate-700/30 text-[10px] text-slate-500 shrink-0">
            {vanilla.latency_ms.toFixed(0)}ms
          </div>
        </div>

        {/* Right: PolicyRAG */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="px-4 py-2 bg-blue-600/10 border-b border-blue-500/20 shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                PolicyRAG
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                Citations + Trust Scores
              </span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 prose prose-invert prose-sm max-w-none prose-p:my-1.5 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:text-slate-200 prose-strong:text-slate-100">
            <ReactMarkdown>{policyrag.answer}</ReactMarkdown>
            {/* Inline citation badges */}
            {citationCount > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {policyrag.citations.map((c) => (
                  <span
                    key={c.index}
                    className={`citation-badge ${
                      c.is_faithful === false ? 'bg-red-500/20 text-red-400 border-red-500/30' : ''
                    }`}
                  >
                    [{c.index}]
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="px-4 py-2 border-t border-slate-700/30 text-[10px] text-slate-500 shrink-0">
            {policyrag.metadata.latency_generation_ms.toFixed(0)}ms
          </div>
        </div>
      </div>

      {/* Summary bar */}
      <div className="px-4 py-3 bg-slate-800/80 border-t border-slate-700/50 flex items-center justify-around shrink-0">
        <SummaryItem label="Citations" value={String(citationCount)} />
        <SummaryItem
          label="Trust Score"
          value={trustScore != null ? `${(trustScore * 100).toFixed(0)}%` : 'N/A'}
          color={trustScore != null && trustScore >= 0.7 ? 'text-emerald-400' : 'text-amber-400'}
        />
        <SummaryItem
          label="Faithfulness"
          value={faithfulness != null ? `${(faithfulness * 100).toFixed(0)}%` : 'N/A'}
          color={faithfulness != null && faithfulness >= 0.8 ? 'text-emerald-400' : 'text-amber-400'}
        />
        <SummaryItem
          label="Citation Precision"
          value={
            eval_.citation_precision != null
              ? `${(eval_.citation_precision * 100).toFixed(0)}%`
              : 'N/A'
          }
        />
      </div>
    </div>
  );
};

function SummaryItem({
  label,
  value,
  color = 'text-slate-200',
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="text-center">
      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">{label}</div>
      <div className={`text-sm font-semibold ${color}`}>{value}</div>
    </div>
  );
}

export default ComparisonView;
