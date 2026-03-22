"""Financial query expansion for SEC filing retrieval.

Expands user queries with SEC-specific synonyms to improve recall.
E.g., users say "revenue" but 10-Ks say "net sales".
"""

import logging
import re

logger = logging.getLogger(__name__)

FINANCIAL_SYNONYMS: dict[str, list[str]] = {
    "revenue": ["net sales", "total net sales", "net revenue", "total revenue"],
    "profit": ["net income", "earnings", "net profit", "operating income"],
    "expenses": ["operating expenses", "total operating expenses", "SG&A", "cost of sales"],
    "debt": ["long-term debt", "total debt", "notes payable", "borrowings", "term debt"],
    "cash": ["cash and cash equivalents", "cash position", "liquidity"],
    "growth": ["year-over-year", "YoY", "increase", "compared to prior year", "change"],
    "r&d": ["research and development", "R&D expenses", "R&D spending"],
    "margin": ["gross margin", "operating margin", "profit margin"],
    "dividend": ["dividends declared", "dividends per share", "cash dividends"],
    "buyback": ["share repurchase", "stock repurchase", "repurchased shares"],
    "earnings per share": ["EPS", "diluted earnings per share", "basic earnings per share"],
    "assets": ["total assets", "current assets", "noncurrent assets"],
    "liabilities": ["total liabilities", "current liabilities", "noncurrent liabilities"],
    "guidance": ["outlook", "forward-looking", "expects", "anticipates", "projects"],
    "risk": ["risk factors", "risks and uncertainties", "material adverse"],
}


def expand_query(query: str) -> str:
    """Expand a user query with financial synonyms for better SEC filing retrieval.

    Returns the original query with appended synonym terms if any matches are found.
    """
    query_lower = query.lower()
    expansions: list[str] = []

    for term, synonyms in FINANCIAL_SYNONYMS.items():
        # Check if the term appears in the query (word boundary aware)
        if re.search(rf"\b{re.escape(term)}\b", query_lower):
            expansions.extend(synonyms)

    if expansions:
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for exp in expansions:
            if exp.lower() not in seen and exp.lower() not in query_lower:
                seen.add(exp.lower())
                unique.append(exp)

        if unique:
            expanded = f"{query} ({', '.join(unique[:8])})"
            logger.info(
                f"Query expanded: '{query}' -> '{expanded}'",
                extra={"stage": "query_expansion", "num_expansions": len(unique)},
            )
            return expanded

    return query
