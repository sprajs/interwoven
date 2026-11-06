import type { EvidenceStrength, NodeKind } from '../data/types.ts'

/** The same marks the chart draws: a drop of ink for technology, an open ring for science. */
export function Mark({ kind, color = 'currentColor', size = 10, strength = 'direct' }: { kind: NodeKind; color?: string; size?: number; strength?: EvidenceStrength }) {
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
  return <span className="inline-flex items-center gap-1 border-b border-dotted border-rule text-[13px] italic leading-snug text-ink-3">
    <Mark kind="science" strength={strength} size={9} />{strength === 'awareness_proxy' ? 'Awareness proxy' : 'Scoped inference'}
  </span>
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
