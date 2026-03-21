import { useState, useEffect, useCallback } from 'react';
import type { ModelInfo } from '../types';
import {
  getModels,
  getActiveModel,
  switchModel as switchModelApi,
  getModelHealth,
} from '../services/api';

const STORAGE_KEY = 'policyrag_active_model';

function loadSavedModel(): { provider: string; model: string } | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch {}
  return null;
}

function saveModel(provider: string, model: string) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ provider, model }));
  } catch {}
}

export function useModels() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [activeProvider, setActiveProvider] = useState<string>('');
  const [activeModel, setActiveModelState] = useState<string>('');
  const [health, setHealth] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [modelList, active, healthData] = await Promise.all([
        getModels().catch(() => []),
        getActiveModel().catch(() => ({ provider: '', model: '' })),
        getModelHealth().catch(() => ({})),
      ]);
      setModels(Array.isArray(modelList) ? modelList : []);

      // Prefer localStorage saved model, then server active
      const saved = loadSavedModel();
      const provider = saved?.provider || active.provider || '';
      const model = saved?.model || active.model || '';
      setActiveProvider(provider);
      setActiveModelState(model);

      // If we restored from localStorage, sync to server
      if (saved && (saved.provider !== active.provider || saved.model !== active.model)) {
        switchModelApi(saved.provider, saved.model).catch(() => {});
      }

      setHealth(healthData || {});
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load models';
      setError(msg);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const switchModel = useCallback(
    async (provider: string, model: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await switchModelApi(provider, model);
        setActiveProvider(provider);
        setActiveModelState(model);
        saveModel(provider, model);
        await refresh();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to switch model';
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [refresh]
  );

  return {
    models,
    activeProvider,
    activeModel,
    health,
    isLoading,
    error,
    switchModel,
    refresh,
  };
}
