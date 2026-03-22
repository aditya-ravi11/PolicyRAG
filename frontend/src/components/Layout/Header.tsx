import React, { useMemo, useState, useRef, useEffect } from 'react';
import type { ModelInfo } from '../../types';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

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
  const { theme, toggleTheme } = useTheme();
  const { user, signOut } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const isHealthy = Object.values(health).some((v) => v === true);

  // Close user menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

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
  const userInitial = user?.email?.charAt(0).toUpperCase() || '?';

  return (
    <header className="h-14 bg-white dark:bg-surface-900 border-b border-surface-200 dark:border-surface-700/50 flex items-center justify-between px-4 shrink-0">
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
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
          <h1 className="text-base font-semibold text-surface-900 dark:text-surface-100 leading-tight">
            PolicyRAG
          </h1>
          <p className="text-[10px] text-surface-500 leading-tight">
            SEC Filing Intelligence
          </p>
        </div>
      </div>

      {/* Center: Model Selector */}
      <div className="flex items-center gap-3" data-tour="model-selector">
        <label className="text-xs text-surface-500 dark:text-surface-400 font-medium">Model:</label>
        <select
          className="bg-surface-50 dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg px-3 py-1.5 text-sm text-surface-800 dark:text-surface-200 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 min-w-[220px]"
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

      {/* Right: Health + Theme Toggle + User Menu */}
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            isHealthy ? 'bg-emerald-400' : 'bg-red-400'
          }`}
        />
        <span className="text-xs text-surface-500 dark:text-surface-400">
          {isHealthy ? 'Connected' : 'Disconnected'}
        </span>
        {onReplayTour && (
          <button
            onClick={onReplayTour}
            className="ml-1 w-6 h-6 rounded-full bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 dark:hover:bg-surface-700 flex items-center justify-center text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 transition-colors text-xs font-bold"
            title="Replay onboarding tour"
          >
            ?
          </button>
        )}

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="ml-1 w-8 h-8 rounded-lg bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 dark:hover:bg-surface-700 flex items-center justify-center text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 transition-colors"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>

        {/* User menu */}
        {user && (
          <div className="relative ml-1" ref={menuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="w-8 h-8 rounded-full bg-brand-600 text-white text-sm font-semibold flex items-center justify-center hover:bg-brand-500 transition-colors"
              title={user.email || 'User menu'}
            >
              {userInitial}
            </button>
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg shadow-lg z-50 py-1">
                <div className="px-4 py-2 border-b border-surface-200 dark:border-surface-700">
                  <p className="text-xs text-surface-500 dark:text-surface-400 truncate">{user.email}</p>
                </div>
                <button
                  onClick={() => { signOut(); setShowUserMenu(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
