RAG_SYSTEM_PROMPT = """You are a financial analyst assistant specializing in SEC filings analysis. You provide accurate, well-cited answers based solely on the provided context.

RULES:
1. Only use information from the provided context chunks
2. Cite your sources using [N] notation where N is the chunk number
3. If the context doesn't contain enough information, say so explicitly
4. Be precise with financial figures and dates
5. Never fabricate or hallucinate information not in the context"""

RAG_USER_TEMPLATE = """Context chunks from SEC filings:
{context}

Question: {query}

Provide a comprehensive answer citing specific chunks using [N] notation."""

VANILLA_RAG_SYSTEM_PROMPT = """You are a helpful assistant. Answer questions based on the provided context."""

VANILLA_RAG_PROMPT = """Answer the following question based on the provided context.

Context:
{context}

Question: {query}

Answer:"""

CLAIM_DECOMPOSITION_PROMPT = """Decompose the following answer into individual atomic claims. Each claim should be a single factual statement that can be independently verified.

Answer: {answer}

Return each claim on a separate line, numbered:
1. <claim>
2. <claim>
..."""

COMPLETENESS_EVALUATION_PROMPT = """Given the question and context, evaluate how completely the answer addresses the question.

Question: {query}
Context: {context}
Answer: {answer}

Rate completeness from 0.0 to 1.0:
- 1.0: Fully answers the question with all relevant details from context
- 0.7: Answers the main question but misses some details
- 0.4: Partially answers the question
- 0.1: Barely addresses the question

Return only a number between 0.0 and 1.0."""
