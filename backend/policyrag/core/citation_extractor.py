import logging
import re
from dataclasses import dataclass, field

import nltk

from policyrag.core.retriever import RetrievedChunk
from policyrag.schemas.citation import Citation, SourceChunk

logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(r"\[(\d+)\]")

# Ensure punkt tokenizer is available
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


@dataclass
class ExtractionResult:
    citations: list[Citation]
    source_chunks: list[SourceChunk]
    citation_coverage: float
    uncited_sentences: list[str]
    invalid_citations: list[int] = field(default_factory=list)


def _chunk_to_source(chunk: RetrievedChunk) -> SourceChunk:
    return SourceChunk(
        chunk_id=chunk.chunk_id,
        text=chunk.text,
        document_id=chunk.metadata.get("doc_id"),
        section=chunk.metadata.get("section"),
        page_num=chunk.metadata.get("page_num"),
        relevance_score=chunk.score,
        company=chunk.metadata.get("company"),
        filing_type=chunk.metadata.get("filing_type"),
    )


def extract_citations(
    answer: str,
    source_map: dict[int, RetrievedChunk],
) -> ExtractionResult:
    """Parse [N] markers from LLM output and map to source chunks."""
    # Find all citation numbers
    cited_numbers = set()
    invalid_citations: list[int] = []
    for match in CITATION_PATTERN.finditer(answer):
        num = int(match.group(1))
        if num in source_map:
            cited_numbers.add(num)
        else:
            invalid_citations.append(num)

    if invalid_citations:
        logger.warning(
            f"Invalid citation references (out of range): {sorted(set(invalid_citations))}",
            extra={"stage": "citation_extraction", "invalid_citations": sorted(set(invalid_citations))},
        )

    # Build citation objects
    citations = []
    source_chunks = []
    seen_chunks = set()

    for num in sorted(cited_numbers):
        chunk = source_map[num]
        source = _chunk_to_source(chunk)
        citations.append(Citation(index=num, chunk=source))

        if chunk.chunk_id not in seen_chunks:
            source_chunks.append(source)
            seen_chunks.add(chunk.chunk_id)

    # Add uncited source chunks
    for num, chunk in sorted(source_map.items()):
        if chunk.chunk_id not in seen_chunks:
            source_chunks.append(_chunk_to_source(chunk))
            seen_chunks.add(chunk.chunk_id)

    # Identify uncited sentences using nltk sentence tokenizer
    sentences = nltk.sent_tokenize(answer)
    uncited = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not CITATION_PATTERN.search(sentence) and len(sentence) > 20:
            uncited.append(sentence)

    total_sentences = len([s for s in sentences if len(s.strip()) > 20])
    cited_sentences = total_sentences - len(uncited)
    coverage = cited_sentences / total_sentences if total_sentences > 0 else 0.0

    return ExtractionResult(
        citations=citations,
        source_chunks=source_chunks,
        citation_coverage=coverage,
        uncited_sentences=uncited,
        invalid_citations=sorted(set(invalid_citations)),
    )
