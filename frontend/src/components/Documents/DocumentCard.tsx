import React from 'react';
import type { Document } from '../../types';
import Badge from '../common/Badge';
import { formatDate } from '../../utils/formatters';

interface DocumentCardProps {
  document: Document;
  isSelected: boolean;
  onToggle: () => void;
  onDelete: () => void;
}

const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  isSelected,
  onToggle,
  onDelete,
}) => {
  return (
    <div
      className={`group px-3 py-2.5 border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-colors ${
        isSelected ? 'bg-blue-500/5 border-l-2 border-l-blue-500' : 'border-l-2 border-l-transparent'
      }`}
      onClick={onToggle}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {/* Company / Filename */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-slate-200 truncate">
              {document.company || document.filename}
            </span>
          </div>

          {/* Metadata row */}
          <div className="flex items-center gap-2 flex-wrap">
            {document.ticker && (
              <span className="text-[10px] font-mono text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded">
                {document.ticker}
              </span>
            )}
            {document.filing_type && (
              <span className="text-[10px] text-slate-500 uppercase">
                {document.filing_type}
              </span>
            )}
            {document.filing_date && (
              <span className="text-[10px] text-slate-500">
                {formatDate(document.filing_date)}
              </span>
            )}
            <span className="text-[10px] text-slate-600">
              {document.chunk_count} chunks
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <Badge status={document.status} />
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="w-6 h-6 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-500/20 flex items-center justify-center text-slate-500 hover:text-red-400 transition-all"
            title="Delete document"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentCard;
