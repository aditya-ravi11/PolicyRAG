import { useState, useEffect, useCallback, useRef } from 'react';
import type { Document } from '../types';
import {
  getDocuments,
  uploadDocument,
  deleteDocument,
  fetchEdgar,
} from '../services/api';

// Toast callback type — set externally by the component that provides toast context
let _toastCallback: ((msg: string) => void) | null = null;
export function setDocumentToastCallback(cb: (msg: string) => void) {
  _toastCallback = cb;
}

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevDocsRef = useRef<Document[]>([]);

  const refresh = useCallback(async () => {
    try {
      const docs = await getDocuments();
      const newDocs = Array.isArray(docs) ? docs : [];

      // Detect PROCESSING → READY transitions
      const prev = prevDocsRef.current;
      for (const doc of newDocs) {
        if (doc.status === 'READY' || doc.status === 'ready') {
          const prevDoc = prev.find((d) => d.id === doc.id);
          if (prevDoc && (prevDoc.status === 'PROCESSING' || prevDoc.status === 'processing')) {
            _toastCallback?.(`Document ready — ${doc.chunk_count} chunks indexed`);
          }
        }
      }

      prevDocsRef.current = newDocs;
      setDocuments(newDocs);
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
