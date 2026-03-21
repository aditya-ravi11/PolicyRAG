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
        <div className="max-w-[70%] px-4 py-2.5 bg-blue-600 text-white rounded-2xl rounded-br-md">
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

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%]">
        {/* Answer with citations */}
        <div className="px-4 py-3 bg-slate-800/40 border border-slate-700/30 rounded-2xl rounded-bl-md">
          {response ? (
            <CitedAnswer text={message.content} />
          ) : (
            <div className="text-sm text-slate-200 leading-relaxed prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:text-slate-200 prose-strong:text-slate-100">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Trust Score Card */}
        {hasEvaluation && response && (
          <TrustScoreCard
            evaluation={response.evaluation}
            metadata={response.metadata}
          />
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
