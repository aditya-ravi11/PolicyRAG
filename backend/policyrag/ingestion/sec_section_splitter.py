import re
from dataclasses import dataclass


@dataclass
class Section:
    name: str
    start_idx: int
    end_idx: int
    text: str


# SEC 10-K item patterns, tolerant of format variations
SECTION_PATTERNS = [
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*1A[\.\s\-\u2014:]*\s*Risk\s*Factors", "Item 1A - Risk Factors"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*1B[\.\s\-\u2014:]*", "Item 1B"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*1[\.\s\-\u2014:]*\s*Business", "Item 1 - Business"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*2[\.\s\-\u2014:]*\s*Properties", "Item 2 - Properties"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*3[\.\s\-\u2014:]*", "Item 3"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*4[\.\s\-\u2014:]*", "Item 4"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*5[\.\s\-\u2014:]*", "Item 5"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*6[\.\s\-\u2014:]*", "Item 6"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*7A[\.\s\-\u2014:]*", "Item 7A"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*7[\.\s\-\u2014:]*\s*Management", "Item 7 - MD&A"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*7[\.\s\-\u2014:]*(?!A)", "Item 7 - MD&A"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*8[\.\s\-\u2014:]*\s*Financial\s*Statements", "Item 8 - Financial Statements"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*9A[\.\s\-\u2014:]*", "Item 9A"),
    (r"(?i)(?:^|\n)\s*(?:ITEM|Item)\s*9[\.\s\-\u2014:]*", "Item 9"),
]


def split_sections(full_text: str) -> list[Section]:
    """Split SEC filing text into sections based on Item headers."""
    matches = []
    for pattern, name in SECTION_PATTERNS:
        for m in re.finditer(pattern, full_text):
            matches.append((m.start(), name))

    if not matches:
        return [Section(name="Full Document", start_idx=0, end_idx=len(full_text), text=full_text)]

    matches.sort(key=lambda x: x[0])

    # Deduplicate: keep first occurrence of each section name
    seen = set()
    unique_matches = []
    for start, name in matches:
        if name not in seen:
            seen.add(name)
            unique_matches.append((start, name))
    matches = unique_matches

    sections = []
    for i, (start, name) in enumerate(matches):
        end = matches[i + 1][0] if i + 1 < len(matches) else len(full_text)
        text = full_text[start:end].strip()
        if text:
            sections.append(Section(name=name, start_idx=start, end_idx=end, text=text))

    return sections
