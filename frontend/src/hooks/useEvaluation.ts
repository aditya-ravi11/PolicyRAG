import { useState, useEffect, useCallback } from 'react';
import type { EvalHistory, AnalyticsData, CompareData } from '../types';
import { getEvaluations, getAnalytics, getCompareProviders } from '../services/api';

export function useEvaluation() {
  const [history, setHistory] = useState<EvalHistory[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [comparison, setComparison] = useState<CompareData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [histData, analyticsData, compareData] = await Promise.all([
        getEvaluations().catch(() => []),
        getAnalytics().catch(() => null),
        getCompareProviders().catch(() => null),
      ]);
      setHistory(Array.isArray(histData) ? histData : []);
      setAnalytics(analyticsData);
      setComparison(compareData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load evaluations';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    history,
    analytics,
    comparison,
    isLoading,
    error,
    refresh: fetchAll,
  };
}
