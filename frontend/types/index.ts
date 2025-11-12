/**
 * Type definitions for RAG Pipeline API
 * Matches backend schema from api/main.py
 */

// API Request Types
export interface QueryRequest {
  query: string; // Renamed from "question"
  metadata_filters?: Record<string, unknown>; // Optional metadata filters
  experiment_variant?: 'baseline' | 'reranked' | 'hybrid' | null; // Optional A/B test variant
  max_results?: number; // Optional: default 5
  include_sources?: boolean; // Optional: default true
  temperature?: number; // Optional: 0.0-2.0
  max_tokens?: number; // Optional: 1-4000
}

// API Response Types
export interface QueryResponse {
  // New schema fields
  query_id?: string;
  answer: string;
  sources?: SourceMetadata[]; // Array of source documents with metadata
  experiment_variant?: string;
  confidence_score?: number;
  processing_time_ms?: number;
  token_count?: number;
  cost_usd?: number;
  evaluation_metrics?: RAGASMetrics; // Optional RAGAS metrics

  // Legacy fields (for backward compatibility during migration)
  contexts?: string[];
  scores?: Record<string, number>;
  latency_ms?: number;
  timing?: TimingMetrics;
  metadata?: SourceMetadata[];
}

export interface HealthResponse {
  status: string;
}

// Extended Types for Frontend Display
export interface SourceMetadata {
  id?: string;
  source?: string;
  title?: string;
  content?: string; // The actual text content of the source
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

// Metrics Context State
export interface MetricsState {
  queries: QueryResult[];
  cacheHits: number;
  cacheMisses: number;
  totalQueries: number;
  avgLatency: number;
  errorCount: number;
  lastUpdated: Date;
  totalTokens: number;
  totalCost: number;
}

// Historical Query Entry
export interface HistoricalQuery {
  id: string;
  query: string; // Renamed from "question" to match API schema
  question?: string; // Legacy field for backward compatibility
  result: QueryResult;
  timestamp: Date;
}
