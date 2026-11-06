import type { DateKind, EntryBasis, EvidenceStrength } from '../data/types.ts'

export function entryReasonLabel(basis: EntryBasis | undefined, eventType?: string, kind?: DateKind, label?: string, strength?: EvidenceStrength): string {
  if (strength === 'scoped_inference') {
    if (kind === 'known_by') return `${basis === 'practical_use' ? 'Use' : 'Availability'} contextually inferred by ${label?.replace(/^By /, '') ?? 'the stated upper limit'}`
    return `${basis === 'practical_use' ? 'Use' : 'Availability'} inferred from the stated context`
  }
  if (kind === 'known_by' && basis === 'practical_use') return `In use by ${label?.replace(/^By /, '') ?? 'the stated upper date limit'}`
  if (kind === 'known_by' && (basis === 'commercial_availability' || basis === 'first_commercial_availability')) return `Available for purchase by ${label?.replace(/^By /, '') ?? 'the stated upper date limit'}`
  switch (basis) {
    case 'first_commercial_availability': return 'First commercially available'
    case 'commercial_availability': return 'Available for purchase'
    case 'practical_use': return 'Documented in use'
    case 'adoption': return 'Adoption documented'
    case 'public_availability': return 'Publicly released or accessible'
    case 'recognition': return 'Recognition documented'
    case 'public_awareness': return `${eventType === 'presentation' ? 'Presentation' : eventType === 'public_disclosure' ? 'Public disclosure' : 'Publication'} used as an awareness estimate`
    default: return 'Community entry awaiting research'
  }
}

export const evidenceLabel = (strength: EvidenceStrength | undefined) =>
  strength === 'direct' ? 'Direct evidence' : strength === 'scoped_inference' ? 'Scoped contextual inference' : strength === 'awareness_proxy' ? 'Awareness proxy' : 'Not yet assessed'

export function dateLimitNote(kind: DateKind | undefined): string {
  return kind === 'known_by' ? 'The mark is an upper date limit for the earliest evidenced record. Earlier history remains unresolved.'
    : kind === 'known_from' ? 'This is a lower date limit only. It establishes neither continuing use nor a later endpoint.' : ''
}
