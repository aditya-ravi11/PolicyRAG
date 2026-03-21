import { useState, useCallback } from 'react';
import type { CompareQueryResponse } from '../types';
import { compareQuery } from '../services/api';

export function useCompare() {
  const [compareMode, setCompareMode] = useState(false);
  const [compareResult, setCompareResult] = useState<CompareQueryResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendCompareQuery = useCallback(
    async (query: string, docIds?: string[], provider?: string, model?: string) => {
      setIsComparing(true);
      setError(null);
      try {
        const result = await compareQuery({
          query,
          document_ids: docIds,
          provider,
          model,
        });
        setCompareResult(result);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Comparison failed';
        setError(msg);
      } finally {
        setIsComparing(false);
      }
    },
    []
  );

  return {
    compareMode,
    setCompareMode,
    compareResult,
    isComparing,
    error,
    sendCompareQuery,
  };
}
