import React from 'react';
import ReactMarkdown from 'react-markdown';
import { parseCitations } from '../../utils/citationParser';

interface CitedAnswerProps {
  text: string;
}

const CitedAnswer: React.FC<CitedAnswerProps> = ({ text }) => {
  const segments = parseCitations(text);

  const handleCitationClick = (index: number) => {
    window.dispatchEvent(
      new CustomEvent('citation-click', { detail: { citationIndex: index } })
    );
  };

  return (
    <div className="text-sm text-slate-200 leading-relaxed prose prose-invert prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:text-slate-200 prose-strong:text-slate-100">
      {segments.map((segment, i) => {
        if (segment.type === 'citation' && segment.citationIndex !== undefined) {
          return (
            <button
              key={i}
              onClick={() => handleCitationClick(segment.citationIndex!)}
              className="citation-badge"
              title={`View source ${segment.citationIndex}`}
            >
              {segment.citationIndex}
            </button>
          );
        }
        return (
          <ReactMarkdown
            key={i}
            components={{
              // Render paragraphs as spans to avoid block-level nesting issues
              p: ({ children }) => <span>{children}</span>,
            }}
          >
            {segment.content}
          </ReactMarkdown>
        );
      })}
    </div>
  );
};

export default CitedAnswer;
