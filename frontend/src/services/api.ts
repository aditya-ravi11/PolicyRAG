import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  CompareQueryResponse,
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

// Query
export async function queryDocuments(request: QueryRequest): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', request);
  return data;
}

export async function compareQuery(request: QueryRequest): Promise<CompareQueryResponse> {
  const { data } = await api.post<CompareQueryResponse>('/query/compare', request);
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
