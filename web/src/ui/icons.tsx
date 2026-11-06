import type { NodeKind } from '../data/types.ts'

/** The same marks the chart draws: a drop of ink for technology, an open ring for science. */
export function Mark({ kind, color = 'currentColor', size = 10 }: { kind: NodeKind; color?: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden className="shrink-0">
      {kind === 'technology' ? <circle cx="6" cy="6" r="5" fill={color} /> : <circle cx="6" cy="6" r="4.2" fill="none" stroke={color} strokeWidth="1.8" />}
    </svg>
  )
}

export function CloseButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button onClick={onClick} aria-label={label} className="-mr-1 p-1 text-ink-3 transition-colors hover:text-ink">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" aria-hidden>
        <path d="M2.5 2.5l9 9M11.5 2.5l-9 9" />
      </svg>
    </button>
  )
}
