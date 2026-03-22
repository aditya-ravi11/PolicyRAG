import asyncio
import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from sentence_transformers import CrossEncoder

from policyrag.config import settings
from policyrag.core.retriever import RetrievedChunk
from policyrag.llm.base import BaseLLMProvider
from policyrag.llm.prompts import CLAIM_DECOMPOSITION_PROMPT

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_nli_model() -> CrossEncoder:
    return CrossEncoder(settings.NLI_MODEL)


@dataclass
class FaithfulnessResult:
    score: float
    num_claims: int
    num_faithful: int
    claims: list[str]
    claim_verdicts: list[bool]


def _check_entailment_per_chunk(claims: list[str], context_texts: list[str]) -> list[bool]:
    """Check if each claim is entailed by ANY individual context chunk (max entailment).

    For each claim, we check it against every chunk independently and take the max.
    This prevents long-context dilution where concatenating all chunks causes NLI to miss evidence.
    """
    nli = _get_nli_model()
    if not claims or not context_texts:
        return [False] * len(claims)

    # Build all (chunk, claim) pairs for batch prediction
    pairs = []
    pair_index_map: list[tuple[int, int]] = []  # (claim_idx, chunk_idx)
    for ci, claim in enumerate(claims):
        for chi, chunk_text in enumerate(context_texts):
            pairs.append((chunk_text, claim))
            pair_index_map.append((ci, chi))

    if not pairs:
        return [False] * len(claims)

    # Batch NLI inference
    scores = nli.predict(pairs)

    # For each claim, check if ANY chunk entails it
    claim_entailed = [False] * len(claims)
    for i, score_set in enumerate(scores):
        ci, _ = pair_index_map[i]
        if hasattr(score_set, "__len__"):
            is_entailed = int(score_set.argmax()) == 2  # entailment label
        else:
            is_entailed = float(score_set) > 0.5
        if is_entailed:
            claim_entailed[ci] = True

    return claim_entailed


async def evaluate_faithfulness(
    answer: str,
    context_chunks: list[RetrievedChunk],
    llm: BaseLLMProvider,
) -> FaithfulnessResult:
    """Two-step faithfulness: decompose claims, then NLI check each against individual chunks."""
    # Step 1: Decompose answer into claims
    prompt = CLAIM_DECOMPOSITION_PROMPT.format(answer=answer)
    response = await llm.generate(prompt)

    claims = []
    for line in response.content.strip().split("\n"):
        line = line.strip()
        # Remove numbering
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        if cleaned and len(cleaned) > 10:
            claims.append(cleaned)

    if not claims:
        return FaithfulnessResult(score=1.0, num_claims=0, num_faithful=0, claims=[], claim_verdicts=[])

    # Step 2: Per-chunk NLI check (max entailment across chunks)
    context_texts = [c.text for c in context_chunks]
    loop = asyncio.get_event_loop()
    verdicts = await loop.run_in_executor(None, _check_entailment_per_chunk, claims, context_texts)

    num_faithful = sum(verdicts)
    score = num_faithful / len(claims) if claims else 1.0

    return FaithfulnessResult(
        score=score,
        num_claims=len(claims),
        num_faithful=num_faithful,
        claims=claims,
        claim_verdicts=verdicts,
    )
