import re
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)


@dataclass
class Section:
    name: str
    start_idx: int
    end_idx: int
    text: str


# SEC 10-K item patterns — match body headings, not TOC entries.
# Body headings typically have the item text on the SAME line or right after,
# and are NOT followed by just a page number on the next line.
SECTION_PATTERNS = [
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*1A[\.\s\-\u2014:]+Risk\s*Factors", "Item 1A - Risk Factors"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*1B[\.\s\-\u2014:]+(?:Unresolved|Cybersecurity)", "Item 1B"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*1C[\.\s\-\u2014:]+Cybersecurity", "Item 1C - Cybersecurity"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*1[\.\s\-\u2014:]+Business", "Item 1 - Business"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*2[\.\s\-\u2014:]+Properties", "Item 2 - Properties"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*3[\.\s\-\u2014:]+Legal\s*Proceedings", "Item 3 - Legal Proceedings"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*4[\.\s\-\u2014:]+Mine\s*Safety", "Item 4"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*5[\.\s\-\u2014:]+Market", "Item 5"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*6[\.\s\-\u2014:]", "Item 6"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*7A[\.\s\-\u2014:]+(?:Quantitative|Market\s*Risk)", "Item 7A"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*7[\.\s\-\u2014:]+Management", "Item 7 - MD&A"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*8[\.\s\-\u2014:]+Financial\s*Statements", "Item 8 - Financial Statements"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*9A[\.\s\-\u2014:]+Controls", "Item 9A"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*9[\.\s\-\u2014:]+Changes\s*in", "Item 9"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*10[\.\s\-\u2014:]+Directors", "Item 10"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*11[\.\s\-\u2014:]+Executive\s*Compensation", "Item 11"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*12[\.\s\-\u2014:]+Security\s*Ownership", "Item 12"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*13[\.\s\-\u2014:]+Certain\s*Relationships", "Item 13"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*14[\.\s\-\u2014:]+Principal\s*Accountant", "Item 14"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*15[\.\s\-\u2014:]+Exhibit", "Item 15"),
]

# Heuristic: TOC entries have the item title on a separate line followed by a page
# number (1-3 digits alone on the next line). Body headings have the title inline
# with the item number and are followed by substantive content.
_TOC_LINE_PATTERN = re.compile(
    r"^(?:ITEM|Item)\s*\d+[A-C]?[\.\s\-\u2014:]*\s*$"  # Item number alone on line
)
_PAGE_NUMBER_AFTER = re.compile(r"^\s*\d{1,3}\s*$")  # Just a page number on next line


_DOT_LEADER_RE = re.compile(r"\.{3,}\s*\d{1,3}\s*$")
_PROSE_WORD_RE = re.compile(r"[a-z]{2,}\s+[a-z]{2,}\s+[a-z]{2,}")


def _is_toc_entry(full_text: str, match_start: int) -> bool:
    """Heuristic: Check if this match is a Table of Contents entry rather than a body heading.

    TOC entries have page-number lines (bare digits or dot-leader patterns) nearby
    and no real prose.  Body headings are followed by paragraph text — sentences
    that start lowercase, contain ". " mid-line, or have 3+ consecutive lowercase words.

    Long section titles (80+ chars) are NOT treated as prose.
    """
    lookahead = full_text[match_start:match_start + 400]
    lines = lookahead.split("\n")

    page_number_count = 0
    prose_line_count = 0
    for line in lines[1:10]:  # Check next 9 lines after the match line
        stripped = line.strip()
        if not stripped:
            continue
        # Page number: standalone 1-3 digits, or dot-leader pattern like "....42"
        if (len(stripped) <= 3 and stripped.isdigit()) or _DOT_LEADER_RE.search(stripped):
            page_number_count += 1
        # Prose detection: lines that are clearly body paragraphs, not titles
        elif (
            (stripped[0].islower()) or  # starts lowercase — sentence continuation
            ('". ' in stripped or ". " in stripped and len(stripped) > 60) or  # mid-sentence period
            _PROSE_WORD_RE.search(stripped)  # 3+ consecutive lowercase words
        ):
            prose_line_count += 1

    # Strong TOC signal: multiple page numbers nearby
    if page_number_count >= 2:
        return True
    # Weak TOC signal: one page number and zero prose
    if page_number_count >= 1 and prose_line_count == 0:
        return True

    return False


def split_sections(full_text: str) -> list[Section]:
    """Split SEC filing text into sections based on Item headers.

    Uses heuristics to skip Table of Contents entries and only match
    actual body section headings.
    """
    matches = []
    for pattern, name in SECTION_PATTERNS:
        for m in re.finditer(pattern, full_text):
            # Skip TOC entries
            if _is_toc_entry(full_text, m.start()):
                continue
            matches.append((m.start(), name))

    if not matches:
        # Fallback: if no body headings found, treat entire text as one section
        # but skip obvious TOC (first ~10% of document is usually TOC/cover)
        logger.warning("No section headings found in document body; using full document")
        return [Section(name="Full Document", start_idx=0, end_idx=len(full_text), text=full_text)]

    matches.sort(key=lambda x: x[0])

    # Deduplicate: keep LAST occurrence of each section name.
    # Body headings always appear after TOC entries, so last wins.
    seen = {}
    for start, name in matches:
        seen[name] = (start, name)  # last occurrence wins
    matches = sorted(seen.values(), key=lambda x: x[0])

    # Build sections with text between consecutive headings
    sections = []
    for i, (start, name) in enumerate(matches):
        end = matches[i + 1][0] if i + 1 < len(matches) else len(full_text)
        text = full_text[start:end].strip()
        if text:
            sections.append(Section(name=name, start_idx=start, end_idx=end, text=text))

    logger.info(
        f"Split document into {len(sections)} sections: {[s.name for s in sections]}"
    )
    return sections
