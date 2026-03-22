import axios from 'axios';
import { supabase, isSupabaseConfigured } from '../lib/supabase';
import type {
  QueryRequest,
  QueryResponse,
  CompareQueryResponse,
  EvaluationPollResponse,
  Document,
  EvalHistory,
  AnalyticsData,
  CompareData,
  ModelInfo,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
});

// Request interceptor: attach Supabase JWT (only when auth is configured)
api.interceptors.request.use(async (config) => {
  if (!isSupabaseConfigured) return config;
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
  } catch {
    // If session fetch fails, proceed without token
  }
  return config;
});

// Response interceptor: handle 401 by refreshing token (with dedup)
let isRefreshing = false;
let refreshSubscribers: Array<(token: string | null) => void> = [];

function onRefreshed(token: string | null) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!isSupabaseConfigured) return Promise.reject(error);
    const originalConfig = error.config;

    if (error.response?.status === 401 && !originalConfig._retry) {
      originalConfig._retry = true;

      if (isRefreshing) {
        // Queue this request until the refresh completes
        return new Promise((resolve, reject) => {
          refreshSubscribers.push((token) => {
            if (token) {
              originalConfig.headers.Authorization = `Bearer ${token}`;
              resolve(api.request(originalConfig));
            } else {
              reject(error);
            }
          });
        });
      }

      isRefreshing = true;
      try {
        const { error: refreshError } = await supabase.auth.refreshSession();
        if (refreshError) {
          onRefreshed(null);
          window.location.href = '/login';
          return Promise.reject(error);
        }
        const { data: { session } } = await supabase.auth.getSession();
        const newToken = session?.access_token || null;
        onRefreshed(newToken);
        if (newToken) {
          originalConfig.headers.Authorization = `Bearer ${newToken}`;
          return api.request(originalConfig);
        }
      } catch {
        onRefreshed(null);
        window.location.href = '/login';
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// Query
export async function queryDocuments(request: QueryRequest, signal?: AbortSignal): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', request, { signal });
  return data;
}

export async function compareQuery(request: QueryRequest): Promise<CompareQueryResponse> {
  const { data } = await api.post<CompareQueryResponse>('/query/compare', request);
  return data;
}

export async function pollEvaluation(queryId: string): Promise<EvaluationPollResponse> {
  const { data } = await api.get<EvaluationPollResponse>(`/query/${queryId}/evaluation`);
  return data;
}

// Documents
export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<Document>('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return data;
}

export async function fetchEdgar(ticker: string, filingType: string): Promise<Document> {
  const { data } = await api.post<Document>('/documents/edgar', {
    ticker,
    filing_type: filingType,
  });
  return data;
}

export async function getDocuments(): Promise<Document[]> {
  const { data } = await api.get<Document[]>('/documents');
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}

export async function getDocumentChunks(id: string): Promise<unknown[]> {
  const { data } = await api.get(`/documents/${id}/chunks`);
  return data;
}

// Evaluation
export async function getEvaluations(): Promise<EvalHistory[]> {
  const { data } = await api.get<EvalHistory[]>('/evaluation/history');
  return data;
}

export async function getAnalytics(): Promise<AnalyticsData> {
  const { data } = await api.get<AnalyticsData>('/evaluation/analytics');
  return data;
}

export async function getCompareProviders(): Promise<CompareData> {
  const { data } = await api.get<CompareData>('/evaluation/compare');
  return data;
}

// Models
export async function getModels(): Promise<ModelInfo[]> {
  const { data } = await api.get<ModelInfo[]>('/models');
  return data;
}

export async function getActiveModel(): Promise<{ provider: string; model: string }> {
  const { data } = await api.get<{ provider: string; model: string }>('/models/active');
  return data;
}

export async function switchModel(provider: string, model: string): Promise<void> {
  await api.post(`/models/switch?provider=${encodeURIComponent(provider)}&model=${encodeURIComponent(model)}`);
}

export async function getModelHealth(): Promise<Record<string, boolean>> {
  const { data } = await api.get<Record<string, boolean>>('/models/health');
  return data;
}

export default api;
