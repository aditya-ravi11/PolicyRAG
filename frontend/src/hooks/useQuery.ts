import { useState, useCallback } from 'react';
import type { Message, QueryResponse } from '../types';
import { queryDocuments } from '../services/api';
import { generateId } from '../utils/formatters';

export function useQuery() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeResponse, setActiveResponse] = useState<QueryResponse | null>(null);

  const sendQuery = useCallback(
    async (
      query: string,
      documentIds?: string[],
      provider?: string,
      model?: string
    ) => {
      setError(null);

      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: query,
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await queryDocuments({
          query,
          document_ids: documentIds,
          provider,
          model,
          no_cache: false,
        });

        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: response.answer,
          response,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setActiveResponse(response);

        return response;
      } catch (err: unknown) {
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
        setIsLoading(false);
      }
    },
    []
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setActiveResponse(null);
    setError(null);
  }, []);

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
