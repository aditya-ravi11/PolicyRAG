from dataclasses import dataclass

from policyrag.core.retriever import RetrievedChunk


@dataclass
class ContextResult:
    formatted_text: str
    source_map: dict[int, RetrievedChunk]
    chunks_used: int


def _text_overlap(a: str, b: str) -> float:
    """Compute approximate text overlap ratio between two strings."""
    if not a or not b:
        return 0.0
    shorter = min(len(a), len(b))
    if shorter == 0:
        return 0.0
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    overlap = len(words_a & words_b)
    return overlap / min(len(words_a), len(words_b))


def build_context(
    chunks: list[RetrievedChunk],
    max_tokens: int = 4000,
    overlap_threshold: float = 0.5,
) -> ContextResult:
    """Deduplicate, sort, number, and format context chunks."""
    # Deduplicate overlapping chunks
    deduped = []
    for chunk in chunks:
        is_dup = False
        for existing in deduped:
            if _text_overlap(chunk.text, existing.text) > overlap_threshold:
                if chunk.score > existing.score:
                    deduped.remove(existing)
                    deduped.append(chunk)
                is_dup = True
                break
        if not is_dup:
            deduped.append(chunk)

    # Sort by relevance score descending
    deduped.sort(key=lambda c: c.score, reverse=True)

    # Build numbered context with metadata headers
    source_map: dict[int, RetrievedChunk] = {}
    parts = []
    total_chars = 0
    char_limit = max_tokens * 4  # rough chars-to-tokens

    for i, chunk in enumerate(deduped, 1):
        meta = chunk.metadata
        header_parts = []
        if meta.get("company"):
            header_parts.append(meta["company"])
        if meta.get("section"):
            header_parts.append(meta["section"])
        if meta.get("page_num"):
            header_parts.append(f"Page {meta['page_num']}")

        header = " | ".join(header_parts) if header_parts else f"Chunk {i}"
        block = f"[{i}] ({header})\n{chunk.text}"

        if total_chars + len(block) > char_limit:
            break

        parts.append(block)
        source_map[i] = chunk
        total_chars += len(block)

    formatted = "\n\n".join(parts)
    return ContextResult(formatted_text=formatted, source_map=source_map, chunks_used=len(source_map))
