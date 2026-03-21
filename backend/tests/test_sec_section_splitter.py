from policyrag.ingestion.sec_section_splitter import split_sections


def test_basic_section_split():
    text = """
ITEM 1. BUSINESS
Apple designs smartphones and computers.

ITEM 1A. RISK FACTORS
The company faces market risks.

ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
Revenue decreased 3% in 2023.
"""
    sections = split_sections(text)
    names = [s.name for s in sections]
    assert "Item 1 - Business" in names
    assert "Item 1A - Risk Factors" in names
    assert "Item 7 - MD&A" in names


def test_uppercase_items():
    text = """
ITEM 1. BUSINESS
Content here.
ITEM 7. MANAGEMENT'S DISCUSSION
More content.
"""
    sections = split_sections(text)
    assert len(sections) >= 2


def test_item_with_dash():
    text = """
Item 1 — Business
Content here.
Item 7 — Management's Discussion and Analysis
More content.
"""
    sections = split_sections(text)
    assert len(sections) >= 2


def test_item_with_period_only():
    text = """
Item 1. Business
Content.
Item 7. Management's Discussion and Analysis
More.
"""
    sections = split_sections(text)
    assert len(sections) >= 2


def test_no_sections():
    text = "This is a plain document with no SEC sections."
    sections = split_sections(text)
    assert len(sections) == 1
    assert sections[0].name == "Full Document"


def test_section_text_content():
    text = """
ITEM 1. BUSINESS
Apple designs smartphones.

ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
Revenue was $383B.
"""
    sections = split_sections(text)
    business = next(s for s in sections if "Business" in s.name)
    assert "smartphones" in business.text


def test_item_8_detection():
    text = """
ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA
Net sales: $383,285 million.
"""
    sections = split_sections(text)
    assert any("Financial Statements" in s.name for s in sections)


def test_item_with_colon():
    text = """
Item 1: Business
Company overview here.
Item 7: Revenue Discussion
Revenue decreased 3%.
"""
    sections = split_sections(text)
    names = [s.name for s in sections]
    assert "Item 1 - Business" in names
    assert "Item 7 - MD&A" in names
