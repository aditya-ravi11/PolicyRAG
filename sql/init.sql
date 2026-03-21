CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(500) NOT NULL,
    company VARCHAR(300),
    filing_type VARCHAR(50),
    filing_date DATE,
    cik VARCHAR(20),
    ticker VARCHAR(10),
    source_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PROCESSING',
    chunk_count INTEGER DEFAULT 0,
    file_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evaluation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL,
    query_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    faithfulness_score FLOAT,
    citation_precision FLOAT,
    citation_recall FLOAT,
    context_relevance FLOAT,
    hallucination_score FLOAT,
    completeness_score FLOAT,
    overall_trust_score FLOAT,
    num_claims INTEGER,
    num_faithful_claims INTEGER,
    num_chunks_retrieved INTEGER,
    latency_retrieval_ms FLOAT,
    latency_generation_ms FLOAT,
    latency_evaluation_ms FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS query_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL,
    citation_index INTEGER NOT NULL,
    chunk_id VARCHAR(200) NOT NULL,
    chunk_text TEXT NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    section VARCHAR(100),
    page_num INTEGER,
    relevance_score FLOAT,
    is_faithful BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_company ON documents(company);
CREATE INDEX IF NOT EXISTS idx_documents_ticker ON documents(ticker);
CREATE INDEX IF NOT EXISTS idx_evaluation_history_query_id ON evaluation_history(query_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_history_created_at ON evaluation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evaluation_history_provider ON evaluation_history(provider);
CREATE INDEX IF NOT EXISTS idx_query_citations_query_id ON query_citations(query_id);
