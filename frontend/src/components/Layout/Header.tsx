import React, { useMemo } from 'react';
import type { ModelInfo } from '../../types';

interface HeaderProps {
  models: ModelInfo[];
  activeProvider: string;
  activeModel: string;
  health: Record<string, boolean>;
  onSwitchModel: (provider: string, model: string) => void;
  isSwitching: boolean;
  onReplayTour?: () => void;
}

const TIER_LABELS: Record<string, { label: string; className: string }> = {
  groq: { label: 'FREE', className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
  gemini: { label: 'FREE', className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
  ollama: { label: 'LOCAL', className: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  openai: { label: 'PAID', className: 'bg-red-500/20 text-red-400 border-red-500/30' },
};

const Header: React.FC<HeaderProps> = ({
  models,
  activeProvider,
  activeModel,
  health,
  onSwitchModel,
  isSwitching,
  onReplayTour,
}) => {
  const isHealthy = Object.values(health).some((v) => v === true);

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const [provider, model] = e.target.value.split('::');
    if (provider && model) {
      onSwitchModel(provider, model);
    }
  };

  // Group models by provider
  const grouped = useMemo(() => {
    const groups: Record<string, ModelInfo[]> = {};
    for (const m of models) {
      if (!groups[m.provider]) groups[m.provider] = [];
      groups[m.provider].push(m);
    }
    return groups;
  }, [models]);

  const activeTier = TIER_LABELS[activeProvider];

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-700/50 flex items-center justify-between px-4 shrink-0">
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <svg
            className="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>
        <div>
          <h1 className="text-base font-semibold text-slate-100 leading-tight">
            PolicyRAG
          </h1>
          <p className="text-[10px] text-slate-500 leading-tight">
            SEC Filing Intelligence
          </p>
        </div>
      </div>

      {/* Center: Model Selector */}
      <div className="flex items-center gap-3" data-tour="model-selector">
        <label className="text-xs text-slate-400 font-medium">Model:</label>
        <select
          className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 min-w-[220px]"
          value={`${activeProvider}::${activeModel}`}
          onChange={handleModelChange}
          disabled={isSwitching}
        >
          {models.length === 0 && (
            <option value={`${activeProvider}::${activeModel}`}>
              {activeProvider ? `${activeProvider} / ${activeModel}` : 'No models available'}
            </option>
          )}
          {Object.entries(grouped).map(([provider, providerModels]) => (
            <optgroup key={provider} label={`${provider.toUpperCase()} ${TIER_LABELS[provider]?.label ? `(${TIER_LABELS[provider].label})` : ''}`}>
              {providerModels.map((m) => (
                <option
                  key={`${m.provider}::${m.model}`}
                  value={`${m.provider}::${m.model}`}
                  disabled={!m.available}
                >
                  {m.model}
                  {!m.available ? ' (unavailable)' : ''}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        {activeTier && (
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${activeTier.className}`}>
            {activeTier.label}
          </span>
        )}
        {isSwitching && (
          <span className="text-xs text-amber-400 animate-pulse">
            Switching...
          </span>
        )}
      </div>

      {/* Right: Health Indicator + Help */}
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            isHealthy ? 'bg-emerald-400' : 'bg-red-400'
          }`}
        />
        <span className="text-xs text-slate-400">
          {isHealthy ? 'Connected' : 'Disconnected'}
        </span>
        {onReplayTour && (
          <button
            onClick={onReplayTour}
            className="ml-2 w-6 h-6 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors text-xs font-bold"
            title="Replay onboarding tour"
          >
            ?
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;
