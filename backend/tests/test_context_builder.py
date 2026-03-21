from policyrag.core.context_builder import build_context, _text_overlap
from policyrag.core.retriever import RetrievedChunk


_DISTINCT_TEXTS = [
    "Apple reported total revenue of $383 billion for the fiscal year ending September 2023.",
    "The services segment generated $85 billion, representing a 9% year-over-year increase.",
    "Cost of goods sold decreased to $214 billion driven by supply chain improvements.",
    "Research and development expenses totaled $29.9 billion, an increase of 14% annually.",
    "iPhone sales accounted for approximately 52% of total company revenue this quarter.",
]


def _make_chunks(n=3):
    return [
        RetrievedChunk(
            chunk_id=f"c{i}",
            text=_DISTINCT_TEXTS[i % len(_DISTINCT_TEXTS)],
            score=0.9 - i * 0.1,
            metadata={"doc_id": "d1", "section": f"Section {i}", "page_num": i, "company": "Apple"},
        )
        for i in range(n)
    ]


def test_basic_context_build():
    chunks = _make_chunks(3)
    result = build_context(chunks)
    assert result.chunks_used == 3
    assert "[1]" in result.formatted_text
    assert "[2]" in result.formatted_text
    assert "[3]" in result.formatted_text


def test_source_map_populated():
    chunks = _make_chunks(2)
    result = build_context(chunks)
    assert 1 in result.source_map
    assert 2 in result.source_map


def test_deduplication():
    chunks = [
        RetrievedChunk(chunk_id="c1", text="Same text about revenue", score=0.9, metadata={}),
        RetrievedChunk(chunk_id="c2", text="Same text about revenue", score=0.8, metadata={}),
    ]
    result = build_context(chunks)
    assert result.chunks_used == 1


def test_ordering_by_score():
    chunks = [
        RetrievedChunk(chunk_id="c1", text="Low score chunk A", score=0.5, metadata={}),
        RetrievedChunk(chunk_id="c2", text="High score chunk B", score=0.9, metadata={}),
    ]
    result = build_context(chunks)
    assert result.formatted_text.index("[1]") < result.formatted_text.index("[2]")
    assert result.source_map[1].score > result.source_map[2].score


def test_truncation():
    chunks = _make_chunks(50)
    result = build_context(chunks, max_tokens=100)
    assert result.chunks_used < 50


def test_metadata_headers():
    chunks = [
        RetrievedChunk(
            chunk_id="c1", text="Content", score=0.9,
            metadata={"company": "Apple", "section": "Business", "page_num": 5},
        )
    ]
    result = build_context(chunks)
    assert "Apple" in result.formatted_text
    assert "Business" in result.formatted_text
    assert "Page 5" in result.formatted_text


def test_text_overlap_identical():
    assert _text_overlap("hello world", "hello world") == 1.0


def test_text_overlap_none():
    assert _text_overlap("hello world", "foo bar baz") == 0.0


def test_text_overlap_empty():
    assert _text_overlap("", "hello") == 0.0
