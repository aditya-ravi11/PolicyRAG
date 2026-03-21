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
  onSendQuery: (query: string, docIds?: string[]) => void;
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
  onSendQuery,
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
    <div className="flex-1 flex flex-col min-w-0 bg-slate-950/50">
      {/* Chat header */}
      <div className="panel-header shrink-0">
        <h2 className="text-sm font-semibold text-slate-200">Chat</h2>
        <div className="flex items-center gap-3">
          {onToggleCompare && (
            <CompareToggle
              compareMode={!!compareMode}
              onToggle={onToggleCompare}
            />
          )}
          {messages.length > 0 && (
            <button
              onClick={onClearChat}
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              Clear chat
            </button>
          )}
        </div>
      </div>

      {/* Messages / Comparison area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {compareMode && compareResult && !isLoading ? (
          <ComparisonView result={compareResult} />
        ) : isLoading && compareMode ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
              <p className="text-sm text-slate-400">Running comparison...</p>
              <p className="text-xs text-slate-500 mt-1">This may take a minute</p>
            </div>
          </div>
        ) : messages.length === 0 && !isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 mx-auto mb-4 bg-slate-800 rounded-2xl flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-slate-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-300 mb-2">
                {compareMode ? 'Compare Vanilla RAG vs PolicyRAG' : 'Ask about SEC Filings'}
              </h3>
              <p className="text-sm text-slate-500 mb-6">
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
                    className="w-full text-left px-4 py-2.5 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600 rounded-lg text-sm text-slate-400 hover:text-slate-200 transition-all"
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
