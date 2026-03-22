import React, { useRef, useEffect } from 'react';
import type { Message, Document, CompareQueryResponse } from '../../types';
import MessageBubble from './MessageBubble';
import QueryInput from './QueryInput';
import StreamingIndicator from './StreamingIndicator';
import CompareToggle from '../Compare/CompareToggle';
import ComparisonView from '../Compare/ComparisonView';

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
  error?: string | null;
  onSendQuery: (query: string, docIds?: string[]) => void;
  onRetry?: () => void;
  documents: Document[];
  selectedDocIds: string[];
  onClearChat: () => void;
  compareMode?: boolean;
  onToggleCompare?: () => void;
  compareResult?: CompareQueryResponse | null;
}

const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isLoading,
  error,
  onSendQuery,
  onRetry,
  documents,
  selectedDocIds,
  onClearChat,
  compareMode,
  onToggleCompare,
  compareResult,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-surface-50 dark:bg-surface-950/50">
      {/* Chat header */}
      <div className="panel-header shrink-0">
        <h2 className="text-sm font-semibold text-surface-800 dark:text-surface-200">Chat</h2>
        <div className="flex items-center gap-3">
          {onToggleCompare && (
            <CompareToggle
              compareMode={!!compareMode}
              onToggle={onToggleCompare}
            />
          )}
          {(messages.length > 0 || compareResult) && (
            <button
              onClick={onClearChat}
              className="text-xs text-surface-500 hover:text-surface-600 dark:hover:text-surface-300 transition-colors"
            >
              Clear chat
            </button>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-4 mt-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-red-300">{error}</span>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-xs text-red-400 hover:text-red-300 font-medium ml-3 shrink-0"
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* Messages / Comparison area */}
      <div className="flex-1 overflow-y-auto px-6 py-4" data-tour="chat-messages">
        {compareMode && compareResult && !isLoading ? (
          <ComparisonView result={compareResult} />
        ) : isLoading && compareMode ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
              <p className="text-sm text-surface-500 dark:text-surface-400">Running comparison...</p>
              <p className="text-xs text-surface-500 mt-1">This may take a minute</p>
            </div>
          </div>
        ) : messages.length === 0 && !isLoading ? (
          <div className="h-full flex items-center justify-center animate-fade-in">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 mx-auto mb-4 bg-brand-500/10 dark:bg-brand-500/15 rounded-2xl flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-brand-500 dark:text-brand-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-surface-700 dark:text-surface-200 mb-2">
                {compareMode ? 'Compare Vanilla RAG vs PolicyRAG' : 'Ask about SEC Filings'}
              </h3>
              <p className="text-sm text-surface-500 dark:text-surface-400 mb-6">
                {compareMode
                  ? 'Ask a question to see a side-by-side comparison of vanilla RAG vs PolicyRAG with citations and trust scores.'
                  : 'Upload documents or fetch from EDGAR, then ask questions. Answers include citations and trust evaluation scores.'}
              </p>
              <div className="space-y-2">
                {[
                  'What are the key risk factors in the latest 10-K?',
                  'How did revenue change year-over-year?',
                  "What is management's outlook for next quarter?",
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => onSendQuery(example)}
                    className="w-full text-left px-4 py-2.5 bg-surface-100 dark:bg-surface-800/50 hover:bg-brand-500/10 dark:hover:bg-brand-500/10 border border-surface-200 dark:border-surface-700/50 hover:border-brand-500/30 dark:hover:border-brand-500/30 rounded-lg text-sm text-surface-600 dark:text-surface-400 hover:text-brand-700 dark:hover:text-brand-300 transition-all animate-fade-in-up"
                    style={{ animationDelay: `${i * 100}ms`, opacity: 0 }}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <StreamingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <QueryInput
        onSubmit={onSendQuery}
        isLoading={isLoading}
        documents={documents}
        selectedDocIds={selectedDocIds}
      />
    </div>
  );
};

export default ChatContainer;
