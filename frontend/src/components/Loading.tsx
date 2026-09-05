/**
 * Loading placeholder. No spinners, no animated dots.
 * Uses gray bars to indicate that data is being fetched.
 */

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="space-y-2 py-4">
      <span className="sr-only">{label}</span>
      <div className="aeris-skeleton w-1/3" />
      <div className="aeris-skeleton w-2/3" />
      <div className="aeris-skeleton w-1/2" />
    </div>
  );
}
