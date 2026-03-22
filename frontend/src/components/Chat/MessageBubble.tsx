import React from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../../types';
import CitedAnswer from './CitedAnswer';
import TrustScoreCard from './TrustScoreCard';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[70%] px-4 py-2.5 bg-brand-600 text-white rounded-2xl rounded-br-md">
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>
      </div>
    );
  }

  // Assistant message
  const response = message.response;
  const hasEvaluation =
    response?.evaluation &&
    Object.values(response.evaluation).some((v) => v !== undefined && v !== null);
  const evaluationPending = response?.evaluation_status === 'pending';
  const isAbstained = response?.abstained === true;

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%]">
        {/* Abstention badge */}
        {isAbstained && (
          <div className="mb-2 flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/10 border border-amber-500/30 rounded-full text-xs font-semibold text-amber-400">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              LOW CONFIDENCE — ABSTAINED
            </span>
          </div>
        )}

        {/* Answer with citations */}
        <div className={`px-4 py-3 rounded-2xl rounded-bl-md ${
          isAbstained
            ? 'bg-amber-500/5 border border-amber-500/20'
            : 'bg-surface-100 dark:bg-surface-800/40 border border-surface-200 dark:border-surface-700/30'
        }`}>
          {response && !isAbstained ? (
            <CitedAnswer text={message.content} />
          ) : (
            <div className="text-sm text-surface-800 dark:text-surface-200 leading-relaxed prose prose-invert prose-sm max-w-none prose-p:my-1.5 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:text-surface-800 dark:prose-headings:text-surface-200 prose-strong:text-surface-900 dark:prose-strong:text-surface-100">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Trust Score Card */}
        {(hasEvaluation || evaluationPending) && response && (
          <TrustScoreCard
            evaluation={response.evaluation}
            metadata={response.metadata}
            evaluationPending={evaluationPending}
          />
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
