import React, { useState } from 'react';
import type { Document } from '../../types';
import DocumentList from '../Documents/DocumentList';
import DocumentUpload from '../Documents/DocumentUpload';

interface SidebarProps {
  documents: Document[];
  selectedDocIds: string[];
  onToggleDoc: (id: string) => void;
  onUpload: (file: File) => Promise<unknown>;
  onFetchEdgar: (ticker: string, filingType: string) => Promise<unknown>;
  onDelete: (id: string) => void;
  onOpenEval: () => void;
  isUploading: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocIds,
  onToggleDoc,
  onUpload,
  onFetchEdgar,
  onDelete,
  onOpenEval,
  isUploading,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  if (isCollapsed) {
    return (
      <div className="w-12 bg-white dark:bg-surface-900 border-r border-surface-200 dark:border-surface-700/50 flex flex-col items-center py-3 shrink-0">
        <button
          onClick={() => setIsCollapsed(false)}
          className="w-8 h-8 rounded-lg bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 dark:hover:bg-surface-700 flex items-center justify-center text-surface-500 dark:text-surface-400 hover:text-surface-800 dark:hover:text-surface-200 transition-colors"
          title="Expand sidebar"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <div className="mt-4 flex flex-col gap-2">
          <button
            onClick={() => { setIsCollapsed(false); setShowUpload(true); }}
            className="w-8 h-8 rounded-lg bg-brand-600/20 hover:bg-brand-600/30 flex items-center justify-center text-brand-500 dark:text-brand-400 transition-colors"
            title="Upload document"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          <button
            onClick={onOpenEval}
            className="w-8 h-8 rounded-lg bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 dark:hover:bg-surface-700 flex items-center justify-center text-surface-500 dark:text-surface-400 hover:text-surface-800 dark:hover:text-surface-200 transition-colors"
            title="Evaluation dashboard"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </button>
        </div>
        <div className="mt-3 text-xs text-surface-500 font-mono">
          {documents.length}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="w-[250px] bg-white dark:bg-surface-900 border-r border-surface-200 dark:border-surface-700/50 flex flex-col shrink-0 overflow-hidden" data-tour="document-sidebar">
        {/* Header */}
        <div className="panel-header">
          <h2 className="text-sm font-semibold text-surface-800 dark:text-surface-200">Documents</h2>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowUpload(true)}
              className="w-7 h-7 rounded-md bg-brand-600 hover:bg-brand-500 flex items-center justify-center text-white transition-colors"
              title="Upload document"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={() => setIsCollapsed(true)}
              className="w-7 h-7 rounded-md hover:bg-surface-200 dark:hover:bg-surface-800 flex items-center justify-center text-surface-500 dark:text-surface-400 hover:text-surface-800 dark:hover:text-surface-200 transition-colors"
              title="Collapse sidebar"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>
        </div>

        {/* Document List */}
        <div className="flex-1 overflow-y-auto">
          {documents.length === 0 ? (
            <div className="p-6 text-center animate-fade-in">
              <div className="w-12 h-12 mx-auto mb-3 bg-brand-500/10 dark:bg-brand-500/15 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-brand-500 dark:text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 3v5a1 1 0 001 1h5" />
                </svg>
              </div>
              <p className="text-sm text-surface-500 dark:text-surface-400 mb-3">
                Upload a PDF filing or fetch from EDGAR to get started
              </p>
              <button
                onClick={() => setShowUpload(true)}
                className="text-brand-500 dark:text-brand-400 hover:text-brand-400 dark:hover:text-brand-300 text-sm font-medium transition-colors"
              >
                Add your first document
              </button>
            </div>
          ) : (
            <DocumentList
              documents={documents}
              selectedDocIds={selectedDocIds}
              onToggleDoc={onToggleDoc}
              onDelete={onDelete}
            />
          )}
        </div>

        {/* Footer: Eval Dashboard Link */}
        <div className="border-t border-surface-200 dark:border-surface-700/50 p-3">
          <button
            onClick={onOpenEval}
            data-tour="eval-button"
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-200 dark:hover:bg-surface-800 text-surface-500 dark:text-surface-400 hover:text-surface-800 dark:hover:text-surface-200 transition-colors text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Evaluation Dashboard
          </button>
        </div>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <DocumentUpload
          onClose={() => setShowUpload(false)}
          onUpload={onUpload}
          onFetchEdgar={onFetchEdgar}
          isUploading={isUploading}
        />
      )}
    </>
  );
};

export default Sidebar;
