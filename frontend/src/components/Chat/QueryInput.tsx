import React, { useState, useRef, useEffect } from 'react';
import type { Document } from '../../types';

interface QueryInputProps {
  onSubmit: (query: string, docIds?: string[]) => void;
  isLoading: boolean;
  documents: Document[];
  selectedDocIds: string[];
}

const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  isLoading,
  documents,
  selectedDocIds,
}) => {
  const [query, setQuery] = useState('');
  const [showDocSelector, setShowDocSelector] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [query]);

  const handleSubmit = () => {
    const trimmed = query.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed, selectedDocIds.length > 0 ? selectedDocIds : undefined);
    setQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const readyDocs = documents.filter(
    (d) => d.status === 'READY' || d.status === 'ready'
  );

  return (
    <div className="border-t border-surface-200 dark:border-surface-700/50 bg-white/80 dark:bg-surface-900/80 backdrop-blur-sm p-4" data-tour="chat-input">
      {/* Document selector dropdown */}
      {showDocSelector && readyDocs.length > 0 && (
        <div className="mb-3 p-2 bg-surface-50 dark:bg-surface-800 border border-surface-300 dark:border-surface-700 rounded-lg max-h-32 overflow-y-auto">
          <div className="text-[10px] text-surface-500 uppercase tracking-wider mb-1.5 px-1">
            Filter by document
          </div>
          {readyDocs.map((doc) => (
            <label
              key={doc.id}
              className="flex items-center gap-2 px-2 py-1 rounded hover:bg-surface-200 dark:hover:bg-surface-700/50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedDocIds.includes(doc.id)}
                readOnly
                className="rounded border-surface-300 dark:border-surface-600 bg-surface-200 dark:bg-surface-700 text-brand-500 focus:ring-brand-500/50"
              />
              <span className="text-xs text-surface-600 dark:text-surface-300 truncate">
                {doc.company || doc.filename}
                {doc.filing_type && (
                  <span className="ml-1 text-surface-500 uppercase">
                    ({doc.filing_type})
                  </span>
                )}
              </span>
            </label>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="flex items-end gap-2">
        {/* Document filter toggle */}
        {readyDocs.length > 0 && (
          <button
            onClick={() => setShowDocSelector(!showDocSelector)}
            className={`relative shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-colors ${
              showDocSelector || selectedDocIds.length > 0
                ? 'bg-brand-600/20 text-brand-500 dark:text-brand-400 border border-brand-500/30'
                : 'bg-surface-50 dark:bg-surface-800 text-surface-500 dark:text-surface-400 hover:text-surface-800 dark:hover:text-surface-200 border border-surface-300 dark:border-surface-700'
            }`}
            title="Filter by document"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            {selectedDocIds.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-brand-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {selectedDocIds.length}
              </span>
            )}
          </button>
        )}

        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about SEC filings..."
            disabled={isLoading}
            rows={1}
            className="w-full px-4 py-2.5 bg-surface-50 dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-xl text-sm text-surface-900 dark:text-surface-100 placeholder-surface-400 dark:placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 resize-none transition-colors disabled:opacity-50"
          />
        </div>

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || isLoading}
          className="shrink-0 w-9 h-9 bg-brand-600 hover:bg-brand-500 disabled:bg-surface-300 dark:disabled:bg-surface-700 disabled:text-surface-500 text-white rounded-xl flex items-center justify-center transition-colors"
          title="Send query"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
          </svg>
        </button>
      </div>

      {/* Selected docs indicator */}
      {selectedDocIds.length > 0 && (
        <div className="mt-2 text-[10px] text-surface-500">
          Querying {selectedDocIds.length} selected document{selectedDocIds.length > 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

export default QueryInput;
