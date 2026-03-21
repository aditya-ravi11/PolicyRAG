from policyrag.core.citation_extractor import extract_citations
from policyrag.core.retriever import RetrievedChunk


def _make_source_map():
    return {
        1: RetrievedChunk(chunk_id="c1", text="Revenue was $383B", score=0.9, metadata={"doc_id": "d1", "section": "Business"}),
        2: RetrievedChunk(chunk_id="c2", text="Services grew 9%", score=0.8, metadata={"doc_id": "d1", "section": "MD&A"}),
        3: RetrievedChunk(chunk_id="c3", text="Cost of sales was $214B", score=0.7, metadata={"doc_id": "d1", "section": "Financials"}),
    }


def test_basic_citation_extraction():
    answer = "Apple's revenue was $383B [1]. Services grew 9% [2]."
    result = extract_citations(answer, _make_source_map())
    assert len(result.citations) == 2
    assert result.citations[0].index == 1
    assert result.citations[1].index == 2


def test_multiple_citations_in_sentence():
    answer = "Revenue details show $383B [1] with cost of $214B [3]."
    result = extract_citations(answer, _make_source_map())
    assert len(result.citations) == 2
    indices = {c.index for c in result.citations}
    assert indices == {1, 3}


def test_no_citations():
    answer = "Apple had significant revenue growth."
    result = extract_citations(answer, _make_source_map())
    assert len(result.citations) == 0
    assert result.citation_coverage == 0.0


def test_invalid_citation_number_ignored():
    answer = "Revenue was high [1]. Some claim [99]."
    result = extract_citations(answer, _make_source_map())
    assert len(result.citations) == 1
    assert result.citations[0].index == 1


def test_citation_coverage():
    answer = "Revenue was $383B [1]. Services grew [2]. Cost was high."
    result = extract_citations(answer, _make_source_map())
    assert result.citation_coverage > 0


def test_source_chunks_include_all():
    answer = "Revenue was $383B [1]."
    result = extract_citations(answer, _make_source_map())
    # Should have all 3 source chunks (1 cited + 2 uncited)
    assert len(result.source_chunks) == 3


def test_repeated_citation():
    answer = "Revenue [1] was high. Again revenue [1] confirmed."
    result = extract_citations(answer, _make_source_map())
    assert len(result.citations) == 1  # deduplicated


def test_malformed_marker_ignored():
    answer = "Revenue was high [abc]. Services grew [2]."
    result = extract_citations(answer, _make_source_map())
    assert len(result.citations) == 1
    assert result.citations[0].index == 2
