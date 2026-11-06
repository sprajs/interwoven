import type { EvidenceStrength, NodeKind } from '../data/types.ts'

/** Sizes at which a mark stands as tall as the lowercase of the text beside it. */
export const MARK_SIZE = { body: 8, note: 7 } as const

/** The same marks the chart draws: a drop of ink for technology, an open ring for science. */
export function Mark({ kind, color = 'currentColor', size = MARK_SIZE.body, strength = 'direct' }: { kind: NodeKind; color?: string; size?: number; strength?: EvidenceStrength }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden className="shrink-0">
      {strength === 'awareness_proxy'
        ? <path d="M6 1L11 6 6 11 1 6Z" fill="none" stroke={color} strokeWidth="1.4" />
        : strength === 'scoped_inference'
          ? <circle cx="6" cy="6" r="4.4" fill="none" stroke={color} strokeWidth="1.4" strokeDasharray="3 2" />
          : kind === 'technology' ? <circle cx="6" cy="6" r="5" fill={color} /> : <circle cx="6" cy="6" r="4.2" fill="none" stroke={color} strokeWidth="1.8" />}
    </svg>
  )
}

export function EvidenceBadge({ strength }: { strength?: EvidenceStrength }) {
  if (!strength || strength === 'direct') return null
  return <span className="note inline-flex items-center gap-1 whitespace-nowrap">
    <Mark kind="science" strength={strength} size={MARK_SIZE.note} />{strength === 'awareness_proxy' ? 'awareness proxy' : 'scoped inference'}
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

export function LooseMark() {
  return (
    <svg width="18" height="10" viewBox="0 0 18 10" aria-hidden>
      <path d="M3 8c2 0 5-1 8-5" stroke="currentColor" strokeWidth="0.75" fill="none" strokeLinecap="round" />
      <circle cx="3" cy="8" r="2" fill="currentColor" />
    </svg>
  )
}
