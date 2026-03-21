export interface ParsedSegment {
  type: 'text' | 'citation';
  content: string;
  citationIndex?: number;
}

/**
 * Parses text containing citation markers like [1], [2], etc.
 * Returns an array of segments that are either plain text or citation references.
 */
export function parseCitations(text: string): ParsedSegment[] {
  const segments: ParsedSegment[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    // Add text before the citation
    if (match.index > lastIndex) {
      segments.push({
        type: 'text',
        content: text.slice(lastIndex, match.index),
      });
    }

    // Add the citation
    const citationIndex = parseInt(match[1], 10);
    segments.push({
      type: 'citation',
      content: match[0],
      citationIndex,
    });

    lastIndex = regex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    segments.push({
      type: 'text',
      content: text.slice(lastIndex),
    });
  }

  return segments;
}

/**
 * Extracts all unique citation indices from text.
 */
export function extractCitationIndices(text: string): number[] {
  const regex = /\[(\d+)\]/g;
  const indices = new Set<number>();
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    indices.add(parseInt(match[1], 10));
  }

  return Array.from(indices).sort((a, b) => a - b);
}
