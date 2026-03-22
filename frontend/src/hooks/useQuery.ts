import { useState, useCallback, useRef, useEffect } from 'react';
import type { Message, QueryResponse } from '../types';
import { queryDocuments, pollEvaluation } from '../services/api';
import { generateId } from '../utils/formatters';

const EVAL_POLL_INTERVAL_MS = 3000;
const EVAL_POLL_TIMEOUT_MS = 120000;

export function useQuery() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeResponse, setActiveResponse] = useState<QueryResponse | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const evalPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup eval polling
  const stopEvalPolling = useCallback(() => {
    if (evalPollRef.current) {
      clearInterval(evalPollRef.current);
      evalPollRef.current = null;
    }
  }, []);

  // Cancel in-flight request and polling on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      stopEvalPolling();
    };
  }, [stopEvalPolling]);

  const startEvalPolling = useCallback(
    (queryId: string, assistantMessageId: string) => {
      stopEvalPolling();
      const startTime = Date.now();

      evalPollRef.current = setInterval(async () => {
        // Timeout after 120s
        if (Date.now() - startTime > EVAL_POLL_TIMEOUT_MS) {
          stopEvalPolling();
          return;
        }

        try {
          const result = await pollEvaluation(queryId);
          if (result.status === 'completed' && result.evaluation) {
            stopEvalPolling();

            // Update the assistant message's response with evaluation scores
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id !== assistantMessageId || !msg.response) return msg;
                return {
                  ...msg,
                  response: {
                    ...msg.response,
                    evaluation: result.evaluation!,
                    evaluation_status: 'completed' as const,
                    metadata: {
                      ...msg.response.metadata,
                      latency_evaluation_ms: result.latency_evaluation_ms ?? 0,
                    },
                  },
                };
              })
            );

            // Update activeResponse too
            setActiveResponse((prev) => {
              if (!prev || prev.query_id !== queryId) return prev;
              return {
                ...prev,
                evaluation: result.evaluation!,
                evaluation_status: 'completed' as const,
                metadata: {
                  ...prev.metadata,
                  latency_evaluation_ms: result.latency_evaluation_ms ?? 0,
                },
              };
            });
          }
        } catch {
          // Silently ignore poll errors — evaluation may still be processing
        }
      }, EVAL_POLL_INTERVAL_MS);
    },
    [stopEvalPolling]
  );

  const sendQuery = useCallback(
    async (
      query: string,
      documentIds?: string[],
      provider?: string,
      model?: string
    ) => {
      // Cancel any previous in-flight request and polling
      abortControllerRef.current?.abort();
      stopEvalPolling();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setError(null);

      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: query,
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await queryDocuments(
          {
            query,
            document_ids: documentIds,
            provider,
            model,
            no_cache: false,
          },
          controller.signal,
        );

        if (controller.signal.aborted) return null;

        const assistantMessageId = generateId();
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: response.answer,
          response,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setActiveResponse(response);

        // If evaluation is pending, start polling
        if (response.evaluation_status === 'pending') {
          startEvalPolling(response.query_id, assistantMessageId);
        }

        return response;
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          return null;
        }
        let errorMessage = 'Failed to get response';
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosErr = err as { response?: { data?: { detail?: string } } };
          errorMessage = axiosErr.response?.data?.detail || (err instanceof Error ? err.message : errorMessage);
        } else if (err instanceof Error) {
          errorMessage = err.message;
        }
        setError(errorMessage);

        const errorAssistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: `Error: ${errorMessage}. Please try again.`,
        };
        setMessages((prev) => [...prev, errorAssistantMessage]);
        return null;
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    },
    [startEvalPolling, stopEvalPolling]
  );

  const clearMessages = useCallback(() => {
    abortControllerRef.current?.abort();
    stopEvalPolling();
    setMessages([]);
    setActiveResponse(null);
    setError(null);
  }, [stopEvalPolling]);

  return {
    messages,
    isLoading,
    error,
    activeResponse,
    sendQuery,
    clearMessages,
    setActiveResponse,
  };
}
