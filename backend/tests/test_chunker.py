from policyrag.ingestion.chunker import chunk_text


def test_basic_chunking():
    text = "A " * 500  # ~1000 chars
    chunks = chunk_text(text, doc_id="d1")
    assert len(chunks) >= 1


def test_chunk_metadata():
    text = "Revenue was significant. " * 50
    chunks = chunk_text(
        text, doc_id="d1", section="Business",
        page_num=3, company="Apple", filing_type="10-K",
    )
    assert len(chunks) >= 1
    meta = chunks[0].metadata
    assert meta["doc_id"] == "d1"
    assert meta["section"] == "Business"
    assert meta["page_num"] == 3
    assert meta["company"] == "Apple"
    assert meta["filing_type"] == "10-K"


def test_chunk_size_within_limits():
    text = "Word " * 2000
    chunks = chunk_text(text, doc_id="d1")
    for chunk in chunks:
        # Allow some tolerance for overlap
        assert len(chunk.text) <= 1200


def test_chunk_overlap():
    text = "Sentence number one. " * 100
    chunks = chunk_text(text, doc_id="d1")
    if len(chunks) >= 2:
        # Check there's some overlap between consecutive chunks
        text1 = chunks[0].text
        text2 = chunks[1].text
        words1 = set(text1.split()[-10:])
        words2 = set(text2.split()[:10])
        # With overlap=200, there should be shared words
        assert len(words1 & words2) > 0


def test_chunk_indices():
    text = "Long content. " * 200
    chunks = chunk_text(text, doc_id="d1")
    indices = [c.metadata["chunk_idx"] for c in chunks]
    assert indices == list(range(len(chunks)))


def test_short_text_single_chunk():
    text = "Short text."
    chunks = chunk_text(text, doc_id="d1")
    assert len(chunks) == 1
    assert chunks[0].text == "Short text."
