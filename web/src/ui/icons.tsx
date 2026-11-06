import type { EvidenceStrength, NodeKind } from '../data/types.ts'

/** Sizes at which a mark stands as tall as the lowercase of the text beside it. */
export const MARK_SIZE = { body: 8, note: 7 } as const

/** The same marks the chart draws: a solid square for technology, an open circle for science. */
export function Mark({ kind, color = 'currentColor', size = MARK_SIZE.body, strength = 'direct' }: { kind: NodeKind; color?: string; size?: number; strength?: EvidenceStrength }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden className="shrink-0">
      {strength === 'awareness_proxy' ? (
        <path d="M6 .8L11.2 6 6 11.2.8 6Z" fill="none" stroke={color} strokeWidth="1.6" />
      ) : strength === 'scoped_inference' ? (
        <path d="M1 4V1h3M8 1h3v3M11 8v3H8M4 11H1V8" fill="none" stroke={color} strokeWidth="1.6" />
      ) : kind === 'mathematics' ? (
        <path d="M6 .8L11.2 6 6 11.2.8 6Z" fill="none" stroke={color} strokeWidth="1.6" />
      ) : kind === 'practice' ? (
        <rect x="1" y="1" width="10" height="10" fill="none" stroke={color} strokeWidth="1.6" />
      ) : kind === 'technology' ? (
        <rect x="1" y="1" width="10" height="10" fill={color} />
      ) : (
        <circle cx="6" cy="6" r="4.6" fill="none" stroke={color} strokeWidth="1.8" />
      )}
    </svg>
  )
}

export function EvidenceBadge({ strength }: { strength?: EvidenceStrength }) {
  if (!strength || strength === 'direct') return null
  return <span className="note inline-flex items-center gap-1 border-b border-dotted border-rule">
    <Mark kind="science" strength={strength} size={MARK_SIZE.note} />{strength === 'awareness_proxy' ? 'Awareness proxy' : 'Scoped inference'}
  </span>
}

export function CloseButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button onClick={onClick} aria-label={label} className="-mr-1 p-1 text-ink-3 transition-colors hover:text-ink">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" aria-hidden>
        <path d="M2 2l8 8M10 2l-8 8" />
      </svg>
    </button>
  )
}

/** The little date-range and broken-link drawings used in keys. */
export function RangeMark() {
  return (
    <svg width="18" height="8" viewBox="0 0 18 8" aria-hidden>
      <path d="M1 1v6M17 1v6M1 4h16" stroke="currentColor" strokeWidth="0.75" fill="none" />
    </svg>
  )
}

export function BrokenMark() {
  return (
    <svg width="18" height="6" viewBox="0 0 18 6" aria-hidden>
      <path d="M1 3h4M7 3h4M13 3h4" stroke="currentColor" strokeWidth="1" fill="none" strokeLinecap="round" />
    </svg>
  )
}
