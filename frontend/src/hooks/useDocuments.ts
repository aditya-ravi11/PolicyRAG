import { useState, useEffect, useCallback, useRef } from 'react';
import type { Document } from '../types';
import {
  getDocuments,
  uploadDocument,
  deleteDocument,
  fetchEdgar,
} from '../services/api';

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const docs = await getDocuments();
      setDocuments(Array.isArray(docs) ? docs : []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load documents';
      setError(msg);
    }
  }, []);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll for status changes when any document is processing
  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.status === 'PROCESSING' || d.status === 'processing'
    );

    if (hasProcessing && !pollRef.current) {
      pollRef.current = setInterval(refresh, 3000);
    } else if (!hasProcessing && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [documents, refresh]);

  const upload = useCallback(
    async (file: File) => {
      setIsLoading(true);
      setError(null);
      try {
        const doc = await uploadDocument(file);
        await refresh();
        return doc;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        setError(msg);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [refresh]
  );

  const fetchFromEdgar = useCallback(
    async (ticker: string, filingType: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const doc = await fetchEdgar(ticker, filingType);
        await refresh();
        return doc;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'EDGAR fetch failed';
        setError(msg);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [refresh]
  );

  const remove = useCallback(
    async (id: string) => {
      try {
        await deleteDocument(id);
        setDocuments((prev) => prev.filter((d) => d.id !== id));
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Delete failed';
        setError(msg);
      }
    },
    []
  );

  return {
    documents,
    isLoading,
    error,
    upload,
    fetchFromEdgar,
    remove,
    refresh,
  };
}
