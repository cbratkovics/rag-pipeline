/**
 * Type definitions for RAG Pipeline API
 * Matches backend schema from api/main.py
 */

// API Request Types
export interface QueryRequest {
  question: string;
  k?: number; // Final number of documents to retrieve (default: 4)
  top_k_bm25?: number; // Number of BM25 results (default: 8)
  top_k_vec?: number; // Number of vector search results (default: 8)
  rrf_k?: number; // RRF K parameter for fusion (default: 60)
  provider?: 'stub' | 'openai'; // LLM provider (default: 'stub')
}

// API Response Types
export interface QueryResponse {
  answer: string;
  contexts: string[];
  scores: Record<string, number>;
  latency_ms: number;
  metadata?: SourceMetadata[];
  timing?: TimingMetrics;
}

export interface HealthResponse {
  status: string;
}

// Extended Types for Frontend Display
export interface SourceMetadata {
  id?: string;
  source?: string;
  title?: string;
  relevance_score?: number;
  retrieval_method?: 'bm25' | 'vector' | 'hybrid';
  snippet?: string;
}

export interface TimingMetrics {
  retrieval_ms?: number;
  generation_ms?: number;
  total_ms?: number;
}

// RAGAS Evaluation Metrics
export interface RAGASMetrics {
  context_relevancy?: number;
  answer_faithfulness?: number;
  answer_relevancy?: number;
  context_recall?: number;
  overall_score?: number;
}

// A/B Testing Types
export type ABVariant = 'auto' | 'baseline' | 'reranked' | 'hybrid';

export interface ABTestConfig {
  variant: ABVariant;
  experiment_id?: string;
}

// UI State Types
export interface QueryState {
  isLoading: boolean;
  error: string | null;
  data: QueryResponse | null;
}

export interface QueryParams {
  k: number;
  top_k_bm25: number;
  top_k_vec: number;
  rrf_k: number;
  provider: 'stub' | 'openai';
  temperature?: number;
  max_tokens?: number;
}

// Cost Estimation
export interface CostMetrics {
  token_count?: number;
  estimated_cost_usd?: number;
  model?: string;
}

// Complete Query Result (combines all data)
export interface QueryResult extends QueryResponse {
  ragas_metrics?: RAGASMetrics;
  cost_metrics?: CostMetrics;
  ab_config?: ABTestConfig;
  query_id?: string;
  timestamp?: string;
}

// Error Types
export interface APIError {
  message: string;
  status?: number;
  code?: string;
  details?: Record<string, unknown>;
}

// Utility Types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface ScoreData {
  hybrid?: number;
  bm25?: number;
  vector?: number;
}
