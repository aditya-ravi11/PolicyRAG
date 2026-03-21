import asyncio
import re
from functools import lru_cache

from sentence_transformers import CrossEncoder

from policyrag.config import settings
from policyrag.core.retriever import RetrievedChunk
from policyrag.schemas.citation import Citation


@lru_cache(maxsize=1)
def _get_nli_model() -> CrossEncoder:
    return CrossEncoder(settings.NLI_MODEL)


def _check_precision_sync(
    cited_pairs: list[tuple[str, str]],
) -> list[bool]:
    """Check if each cited sentence is entailed by its source chunk."""
    if not cited_pairs:
        return []
    nli = _get_nli_model()
    scores = nli.predict(cited_pairs)
    results = []
    for score_set in scores:
        if hasattr(score_set, "__len__"):
            results.append(int(score_set.argmax()) == 2)
        else:
            results.append(float(score_set) > 0.5)
    return results


async def evaluate_citation_metrics(
    answer: str,
    citations: list[Citation],
    source_map: dict[int, RetrievedChunk],
) -> tuple[float, float, dict[int, bool]]:
    """Returns (citation_precision, citation_recall, per_citation_faithful)."""
    # Split answer into sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
    citation_pattern = re.compile(r"\[(\d+)\]")

    # Citation precision: for each [N] in context, is the claim entailed?
    cited_pairs = []
    pair_citation_indices: list[int] = []
    for sentence in sentences:
        refs = citation_pattern.findall(sentence)
        clean_sentence = citation_pattern.sub("", sentence).strip()
        if not clean_sentence or len(clean_sentence) < 10:
            continue
        for ref in refs:
            num = int(ref)
            if num in source_map:
                cited_pairs.append((source_map[num].text, clean_sentence))
                pair_citation_indices.append(num)

    per_citation_faithful: dict[int, bool] = {}
    if cited_pairs:
        loop = asyncio.get_event_loop()
        precision_verdicts = await loop.run_in_executor(None, _check_precision_sync, cited_pairs)
        precision = sum(precision_verdicts) / len(precision_verdicts)

        # Map verdicts back to individual citation indices
        citation_verdicts: dict[int, list[bool]] = {}
        for idx, verdict in zip(pair_citation_indices, precision_verdicts):
            citation_verdicts.setdefault(idx, []).append(verdict)
        per_citation_faithful = {
            idx: all(verdicts) for idx, verdicts in citation_verdicts.items()
        }
    else:
        precision = 0.0

    # Citation recall: % of substantive sentences that have at least one citation
    substantive = [s for s in sentences if len(s.strip()) > 20]
    if not substantive:
        return precision, 1.0, per_citation_faithful

    cited_count = sum(1 for s in substantive if citation_pattern.search(s))
    recall = cited_count / len(substantive)

    return precision, recall, per_citation_faithful
