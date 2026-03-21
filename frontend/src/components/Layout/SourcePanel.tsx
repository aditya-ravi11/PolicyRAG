import React, { useEffect, useRef, useState } from 'react';
import type { Citation, SourceChunk } from '../../types';
import Tooltip from '../common/Tooltip';
import { scoreBarColor, formatScore } from '../../utils/formatters';

interface SourcePanelProps {
  citations: Citation[];
  sourceChunks: SourceChunk[];
}

const SourcePanel: React.FC<SourcePanelProps> = ({ citations, sourceChunks }) => {
  const [highlightedIndex, setHighlightedIndex] = useState<number | null>(null);
  const chunkRefs = useRef<Record<number, HTMLDivElement | null>>({});

  // Listen for citation click events from CitedAnswer
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (typeof detail?.citationIndex === 'number') {
        const idx = detail.citationIndex;
        setHighlightedIndex(idx);
        const ref = chunkRefs.current[idx];
        if (ref) {
          ref.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        // Clear highlight after 3 seconds
        setTimeout(() => setHighlightedIndex(null), 3000);
      }
    };
    window.addEventListener('citation-click', handler);
    return () => window.removeEventListener('citation-click', handler);
  }, []);

  // Display citations if available, otherwise fall back to source_chunks
  const items: { index: number; chunk: SourceChunk; isFaithful?: boolean }[] =
    citations.length > 0
      ? citations.map((c) => ({
          index: c.index,
          chunk: c.chunk,
          isFaithful: c.is_faithful,
        }))
      : sourceChunks.map((chunk, i) => ({
          index: i + 1,
          chunk,
          isFaithful: undefined,
        }));

  if (items.length === 0) {
    return (
      <div className="w-[350px] bg-slate-900 border-l border-slate-700/50 flex flex-col shrink-0">
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-slate-200">Sources</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <svg className="w-12 h-12 text-slate-700 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <p className="text-sm text-slate-500">
              Ask a question to see source citations here.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-[350px] bg-slate-900 border-l border-slate-700/50 flex flex-col shrink-0 overflow-hidden" data-tour="source-panel">
      <div className="panel-header">
        <h2 className="text-sm font-semibold text-slate-200">Sources</h2>
        <span className="text-xs text-slate-500 font-mono">{items.length} cited</span>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {items.map((item) => (
          <div
            key={item.index}
            ref={(el) => { chunkRefs.current[item.index] = el; }}
            className={`p-3 rounded-lg border transition-all duration-300 ${
              highlightedIndex === item.index
                ? 'bg-blue-500/10 border-blue-500/40 ring-1 ring-blue-500/20'
                : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600/50'
            }`}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="citation-badge text-[10px]">{item.index}</span>
                {item.chunk.section && (
                  <span className="text-xs text-slate-400 truncate max-w-[180px]">
                    {item.chunk.section}
                  </span>
                )}
              </div>
              {item.isFaithful != null && (
                <Tooltip content={item.isFaithful ? 'Faithful citation' : 'Unfaithful citation'}>
                  <span className={`text-xs ${item.isFaithful ? 'text-emerald-400' : 'text-red-400'}`}>
                    {item.isFaithful ? 'Faithful' : 'Unfaithful'}
                  </span>
                </Tooltip>
              )}
            </div>

            {/* Text */}
            <p className="text-xs text-slate-300 leading-relaxed line-clamp-4 mb-2">
              {item.chunk.text}
            </p>

            {/* Metadata footer */}
            <div className="flex items-center gap-3 text-[10px] text-slate-500">
              {item.chunk.company && (
                <span>{item.chunk.company}</span>
              )}
              {item.chunk.filing_type && (
                <span className="uppercase">{item.chunk.filing_type}</span>
              )}
              {item.chunk.page_num !== undefined && item.chunk.page_num !== null && (
                <span>p.{item.chunk.page_num}</span>
              )}
            </div>

            {/* Relevance bar */}
            {item.chunk.relevance_score !== undefined && (
              <div className="mt-2">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-[10px] text-slate-500">Relevance</span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {formatScore(item.chunk.relevance_score)}
                  </span>
                </div>
                <div className="w-full h-1 bg-slate-700/50 rounded-full overflow-hidden">
                  <div
                    className={`h-1 rounded-full transition-all duration-500 ${scoreBarColor(item.chunk.relevance_score)}`}
                    style={{ width: `${Math.round(item.chunk.relevance_score * 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourcePanel;
