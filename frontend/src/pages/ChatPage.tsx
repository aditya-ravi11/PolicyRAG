import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Layout/Header';
import Sidebar from '../components/Layout/Sidebar';
import SourcePanel from '../components/Layout/SourcePanel';
import ChatContainer from '../components/Chat/ChatContainer';
import EvalDashboard from '../components/Evaluation/EvalDashboard';
import OnboardingTour from '../components/Onboarding/OnboardingTour';
import { useQuery } from '../hooks/useQuery';
import { useDocuments, setDocumentToastCallback } from '../hooks/useDocuments';
import { useModels } from '../hooks/useModels';
import { useEvaluation } from '../hooks/useEvaluation';
import { useCompare } from '../hooks/useCompare';
import { useToast } from '../contexts/ToastContext';
import type { Citation, SourceChunk } from '../types';

const ChatPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // State management via hooks
  const {
    messages,
    isLoading: isQuerying,
    error: queryError,
    activeResponse,
    sendQuery,
    clearMessages,
  } = useQuery();

  const {
    documents,
    isLoading: isDocLoading,
    upload,
    fetchFromEdgar,
    remove: removeDoc,
  } = useDocuments();

  const {
    models,
    activeProvider,
    activeModel,
    health,
    isLoading: isModelSwitching,
    switchModel,
  } = useModels();

  const {
    analytics,
    comparison,
    history: evalHistory,
    isLoading: isEvalLoading,
    refresh: refreshEval,
  } = useEvaluation();

  const {
    compareMode,
    setCompareMode,
    compareResult,
    isComparing,
    error: compareError,
    sendCompareQuery,
    clearCompare,
  } = useCompare();

  const { addToast } = useToast();

  // Wire toast for document processing transitions
  useEffect(() => {
    setDocumentToastCallback((msg: string) => addToast({ message: msg, type: 'success' }));
    return () => setDocumentToastCallback(() => {});
  }, [addToast]);

  // Local UI state
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [showEvalDashboard, setShowEvalDashboard] = useState(false);
  const [showTour, setShowTour] = useState(false);

  // Check first visit for onboarding
  useEffect(() => {
    const onboarded = localStorage.getItem('policyrag_onboarded');
    if (!onboarded) {
      setShowTour(true);
    }
  }, []);

  // Handle prefilled query from landing page
  useEffect(() => {
    const state = location.state as { prefillQuery?: string } | null;
    if (state?.prefillQuery) {
      sendQuery(state.prefillQuery, undefined, activeProvider || undefined, activeModel || undefined);
      // Clear the state so it doesn't re-fire
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state]); // eslint-disable-line react-hooks/exhaustive-deps

  // Toggle document selection
  const handleToggleDoc = useCallback((id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  }, []);

  // Send query with current model context
  const handleSendQuery = useCallback(
    (query: string, docIds?: string[]) => {
      if (compareMode) {
        sendCompareQuery(query, docIds, activeProvider || undefined, activeModel || undefined);
      } else {
        sendQuery(query, docIds, activeProvider || undefined, activeModel || undefined);
      }
    },
    [sendQuery, sendCompareQuery, compareMode, activeProvider, activeModel]
  );

  // Clear chat — clears both messages and compare result
  const handleClearChat = useCallback(() => {
    clearMessages();
    clearCompare();
  }, [clearMessages, clearCompare]);

  // Extract citations and source chunks from the active response
  const citations: Citation[] = activeResponse?.citations || [];
  const sourceChunks: SourceChunk[] = activeResponse?.source_chunks || [];
  const hasSourceData = citations.length > 0 || sourceChunks.length > 0;

  return (
    <div className="h-screen flex flex-col bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 overflow-hidden">
      {/* Top Header */}
      <Header
        models={models}
        activeProvider={activeProvider}
        activeModel={activeModel}
        health={health}
        onSwitchModel={switchModel}
        isSwitching={isModelSwitching}
        onReplayTour={() => setShowTour(true)}
      />

      {/* Main three-panel layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Document Sidebar */}
        <Sidebar
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggleDoc={handleToggleDoc}
          onUpload={upload}
          onFetchEdgar={fetchFromEdgar}
          onDelete={removeDoc}
          onOpenEval={() => {
            refreshEval();
            setShowEvalDashboard(true);
          }}
          isUploading={isDocLoading}
        />

        {/* Center: Chat */}
        <ChatContainer
          messages={messages}
          isLoading={isQuerying || isComparing}
          error={compareMode ? compareError : queryError}
          onSendQuery={handleSendQuery}
          documents={documents}
          selectedDocIds={selectedDocIds}
          onClearChat={handleClearChat}
          compareMode={compareMode}
          onToggleCompare={() => setCompareMode(!compareMode)}
          compareResult={compareResult}
        />

        {/* Right: Source Panel (conditional) */}
        {!compareMode && hasSourceData && (
          <SourcePanel citations={citations} sourceChunks={sourceChunks} />
        )}
      </div>

      {/* Evaluation Dashboard Modal */}
      {showEvalDashboard && (
        <EvalDashboard
          analytics={analytics}
          comparison={comparison}
          history={evalHistory}
          isLoading={isEvalLoading}
          onClose={() => setShowEvalDashboard(false)}
          onRefresh={refreshEval}
        />
      )}

      {/* Onboarding Tour */}
      {showTour && (
        <OnboardingTour
          onFinish={() => {
            setShowTour(false);
            localStorage.setItem('policyrag_onboarded', 'true');
          }}
        />
      )}
    </div>
  );
};

export default ChatPage;
