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


def _check_entailment_sync(claims: list[str], context_texts: list[str]) -> list[bool]:
    """Check if each claim is entailed by any context chunk using NLI."""
    nli = _get_nli_model()
    verdicts = []
    combined_context = " ".join(context_texts)

    pairs = [(combined_context, claim) for claim in claims]
    if not pairs:
        return []

    # NLI labels: 0=contradiction, 1=neutral, 2=entailment
    scores = nli.predict(pairs)
    for score_set in scores:
        if hasattr(score_set, "__len__"):
            verdict = int(score_set.argmax()) == 2  # entailment
        else:
            verdict = float(score_set) > 0.5
        verdicts.append(verdict)

    return verdicts


async def evaluate_faithfulness(
    answer: str,
    context_chunks: list[RetrievedChunk],
    llm: BaseLLMProvider,
) -> FaithfulnessResult:
    """Two-step faithfulness: decompose claims, then NLI check each."""
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

    # Step 2: NLI check
    context_texts = [c.text for c in context_chunks]
    loop = asyncio.get_event_loop()
    verdicts = await loop.run_in_executor(None, _check_entailment_sync, claims, context_texts)

    num_faithful = sum(verdicts)
    score = num_faithful / len(claims) if claims else 1.0

    return FaithfulnessResult(
        score=score,
        num_claims=len(claims),
        num_faithful=num_faithful,
        claims=claims,
        claim_verdicts=verdicts,
    )
