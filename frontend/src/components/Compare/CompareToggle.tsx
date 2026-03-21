import React from 'react';

interface CompareToggleProps {
  compareMode: boolean;
  onToggle: () => void;
}

const CompareToggle: React.FC<CompareToggleProps> = ({ compareMode, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
        compareMode
          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
          : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
      }`}
      title="Toggle comparison mode: Vanilla RAG vs PolicyRAG"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
      </svg>
      {compareMode ? 'Compare ON' : 'Compare'}
    </button>
  );
};

export default CompareToggle;
