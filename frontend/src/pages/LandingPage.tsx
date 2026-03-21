import React from 'react';
import { useNavigate } from 'react-router-dom';
import ComparisonView from '../components/Compare/ComparisonView';
import { COMPARISON_EXAMPLES } from '../data/comparisonExamples';

const DEMO_QUESTIONS = [
  'What are the key risk factors in the latest 10-K?',
  'How did revenue change year-over-year?',
  "What is management's outlook for next quarter?",
];

const FEATURES = [
  {
    title: 'Cited Answers',
    description: 'Every claim is backed by specific source chunks with [N] citations you can verify.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    title: 'Trust Scoring',
    description: 'Every response gets a faithfulness, hallucination, and citation-precision score.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    title: 'Compare Mode',
    description: 'See side-by-side how PolicyRAG improves over vanilla RAG with guardrails.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
      </svg>
    ),
  },
];

const STEPS = [
  { step: '1', title: 'Upload', description: 'Upload SEC filings (PDF) or fetch directly from EDGAR' },
  { step: '2', title: 'Ask', description: 'Ask natural language questions about the filings' },
  { step: '3', title: 'Verify', description: 'Review cited sources and trust scores for every answer' },
];

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleDemoQuestion = (question: string) => {
    navigate('/chat', { state: { prefillQuery: question } });
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Nav */}
      <nav className="border-b border-slate-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <span className="text-lg font-semibold">PolicyRAG</span>
          </div>
          <button
            onClick={() => navigate('/chat')}
            className="btn-primary"
          >
            Start Analyzing
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 py-20 md:py-32">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            SEC Filing Intelligence
            <br />
            You Can Trust
          </h1>
          <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            Ask questions about SEC filings and get answers with citations,
            hallucination detection, and trust scores — powered by free LLMs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate('/chat')}
              className="btn-primary text-base px-8 py-3"
            >
              Start Analyzing
            </button>
            <a
              href="#features"
              className="btn-secondary text-base px-8 py-3 text-center"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-16 bg-slate-950/50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-12">
            Why PolicyRAG?
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-6">
                <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center text-blue-400 mb-4">
                  {f.icon}
                </div>
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-6 py-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {STEPS.map((s) => (
              <div key={s.step} className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white text-lg font-bold mx-auto mb-4">
                  {s.step}
                </div>
                <h3 className="text-lg font-semibold mb-2">{s.title}</h3>
                <p className="text-sm text-slate-400">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Questions */}
      <section className="px-6 py-16 bg-slate-950/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">
            Try a Question
          </h2>
          <p className="text-sm text-slate-400 text-center mb-8">
            Click any question below to jump into the chat and see PolicyRAG in action.
          </p>
          <div className="space-y-3">
            {DEMO_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => handleDemoQuestion(q)}
                className="w-full text-left px-6 py-4 card hover:border-blue-500/50 transition-all text-slate-300 hover:text-slate-100"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* See the Difference */}
      <section className="px-6 py-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">
            See the Difference
          </h2>
          <p className="text-sm text-slate-400 text-center mb-8">
            Vanilla RAG vs PolicyRAG — notice the citations, trust scores, and guardrails.
          </p>
          <div className="card p-4">
            <ComparisonView result={COMPARISON_EXAMPLES[0]} />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 px-6 py-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <div className="w-5 h-5 bg-blue-600 rounded flex items-center justify-center">
              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            PolicyRAG — Trustworthy SEC Filing Intelligence
          </div>
          <div className="text-xs text-slate-600">
            Built with Groq, Sentence Transformers, and ChromaDB
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
