export interface SourceChunk {
  chunk_id: string;
  text: string;
  document_id?: string;
  section?: string;
  page_num?: number;
  relevance_score: number;
  company?: string;
  filing_type?: string;
}

export interface Citation {
  index: number;
  chunk: SourceChunk;
  is_faithful?: boolean;
}

export interface EvaluationScores {
  faithfulness?: number;
  hallucination_score?: number;
  citation_precision?: number;
  citation_recall?: number;
  context_relevance?: number;
  completeness?: number;
  overall_trust_score?: number;
}

export interface QueryMetadata {
  provider: string;
  model: string;
  num_chunks_retrieved: number;
  latency_retrieval_ms: number;
  latency_generation_ms: number;
  latency_evaluation_ms: number;
}

export interface QueryResponse {
  query_id: string;
  query: string;
  answer: string;
  abstained?: boolean;
  citations: Citation[];
  source_chunks: SourceChunk[];
  evaluation: EvaluationScores;
  evaluation_status?: 'pending' | 'completed';
  metadata: QueryMetadata;
}

export interface EvaluationPollResponse {
  status: 'pending' | 'completed';
  evaluation?: EvaluationScores;
  latency_evaluation_ms?: number;
}

export interface QueryRequest {
  query: string;
  document_ids?: string[];
  provider?: string;
  model?: string;
  no_cache?: boolean;
}

export interface Document {
  id: string;
  filename: string;
  company?: string;
  filing_type?: string;
  filing_date?: string;
  ticker?: string;
  status: string;
  chunk_count: number;
  created_at: string;
}

export interface EvalHistory {
  id: string;
  query_id: string;
  query_text: string;
  answer_text: string;
  provider: string;
  model: string;
  faithfulness_score?: number;
  hallucination_score?: number;
  citation_precision?: number;
  citation_recall?: number;
  context_relevance?: number;
  overall_trust_score?: number;
  completeness_score?: number;
  created_at: string;
}

export interface ModelInfo {
  provider: string;
  model: string;
  available: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: QueryResponse;
}

export interface AnalyticsData {
  total_queries: number;
  avg_faithfulness: number;
  avg_hallucination: number;
  avg_citation_precision: number;
  avg_citation_recall: number;
  avg_context_relevance: number;
  avg_trust_score: number;
  provider_breakdown?: Record<string, {
    count: number;
    avg_faithfulness: number;
    avg_trust_score: number;
  }>;
}

export interface VanillaResponse {
  answer: string;
  latency_ms: number;
  provider: string;
  model: string;
}

export interface CompareQueryResponse {
  query: string;
  vanilla: VanillaResponse;
  policyrag: QueryResponse;
}

export interface CompareData {
  providers: {
    provider: string;
    model: string;
    avg_faithfulness: number;
    avg_hallucination: number;
    avg_citation_precision: number;
    avg_citation_recall: number;
    avg_trust_score: number;
    query_count: number;
  }[];
}
