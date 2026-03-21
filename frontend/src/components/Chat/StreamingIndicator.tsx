import React from 'react';

const StreamingIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3">
      <div className="flex items-center gap-1">
        <span
          className="w-2 h-2 bg-blue-400 rounded-full animate-dot-pulse"
          style={{ animationDelay: '0s' }}
        />
        <span
          className="w-2 h-2 bg-blue-400 rounded-full animate-dot-pulse"
          style={{ animationDelay: '0.2s' }}
        />
        <span
          className="w-2 h-2 bg-blue-400 rounded-full animate-dot-pulse"
          style={{ animationDelay: '0.4s' }}
        />
      </div>
      <span className="text-xs text-slate-500 ml-2">Analyzing documents...</span>
    </div>
  );
};

export default StreamingIndicator;
