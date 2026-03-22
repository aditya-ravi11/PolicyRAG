/**
 * Returns a Tailwind color class based on the score value.
 * Green for scores > 0.7, amber for > 0.4, red otherwise.
 */
export function scoreColor(score: number | undefined | null): string {
  if (score === undefined || score === null) return 'text-surface-500';
  if (score > 0.7) return 'text-emerald-400';
  if (score > 0.4) return 'text-amber-400';
  return 'text-red-400';
}

/**
 * Returns a Tailwind background color class for score bars.
 */
export function scoreBarColor(score: number | undefined | null): string {
  if (score === undefined || score === null) return 'bg-surface-600';
  if (score > 0.7) return 'bg-emerald-500';
  if (score > 0.4) return 'bg-amber-500';
  return 'bg-red-500';
}

/**
 * Returns a border color for score-based highlighting.
 */
export function scoreBorderColor(score: number | undefined | null): string {
  if (score === undefined || score === null) return 'border-surface-600';
  if (score > 0.7) return 'border-emerald-500/30';
  if (score > 0.4) return 'border-amber-500/30';
  return 'border-red-500/30';
}

/**
 * Format a date string for display.
 */
export function formatDate(dateStr: string | undefined | null): string {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format a latency value in milliseconds for display.
 */
export function formatLatency(ms: number | undefined | null): string {
  if (ms === undefined || ms === null) return 'N/A';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/**
 * Format a score as a percentage string.
 */
export function formatScore(score: number | undefined | null): string {
  if (score === undefined || score === null) return 'N/A';
  return `${(score * 100).toFixed(0)}%`;
}

/**
 * Generate a unique ID for messages.
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}
