import React from 'react';
import Joyride, { CallBackProps, STATUS, Step } from 'react-joyride';

interface OnboardingTourProps {
  onFinish: () => void;
}

const STEPS: Step[] = [
  {
    target: '[data-tour="model-selector"]',
    content: 'Choose your LLM provider and model here. Groq and Gemini are free!',
    title: 'Model Selector',
    disableBeacon: true,
  },
  {
    target: '[data-tour="document-sidebar"]',
    content: 'Upload SEC filings (PDF) or fetch them directly from EDGAR. Select documents to scope your queries.',
    title: 'Document Sidebar',
  },
  {
    target: '[data-tour="chat-input"]',
    content: 'Type your question here. Ask about risk factors, revenue, management outlook, or any filing detail.',
    title: 'Ask Questions',
  },
  {
    target: '[data-tour="compare-toggle"]',
    content: 'Toggle Compare Mode to see PolicyRAG vs Vanilla RAG side-by-side with the same retrieval context.',
    title: 'Compare Mode',
  },
  {
    target: '[data-tour="chat-messages"]',
    content: 'Every answer includes a trust evaluation with color-coded confidence. Cited source chunks appear in the right panel.',
    title: 'Trust Scores & Citations',
  },
  {
    target: '[data-tour="eval-button"]',
    content: 'Open the evaluation dashboard to see aggregate trust scores, provider comparisons, and query history.',
    title: 'Evaluation Dashboard',
  },
];

const OnboardingTour: React.FC<OnboardingTourProps> = ({ onFinish }) => {
  const handleCallback = (data: CallBackProps) => {
    const { status } = data;
    if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
      onFinish();
    }
  };

  return (
    <Joyride
      steps={STEPS}
      continuous
      showSkipButton
      showProgress
      run
      callback={handleCallback}
      styles={{
        options: {
          backgroundColor: '#292524',
          textColor: '#e7e5e4',
          primaryColor: '#0d9488',
          arrowColor: '#292524',
          overlayColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 10000,
        },
        tooltip: {
          borderRadius: '12px',
          padding: '16px',
        },
        tooltipTitle: {
          fontSize: '16px',
          fontWeight: 600,
        },
        tooltipContent: {
          fontSize: '14px',
          lineHeight: '1.5',
        },
        buttonNext: {
          backgroundColor: '#0d9488',
          borderRadius: '8px',
          fontSize: '13px',
          padding: '8px 16px',
        },
        buttonBack: {
          color: '#a8a29e',
          fontSize: '13px',
        },
        buttonSkip: {
          color: '#78716c',
          fontSize: '13px',
        },
      }}
    />
  );
};

export default OnboardingTour;
