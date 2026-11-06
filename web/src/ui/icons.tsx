import type { NodeType } from '../data/types.ts'

/** Matches the shapes the node shader draws for each type. */
export function ShapeIcon({ type, color = 'currentColor', size = 12 }: { type: NodeType; color?: string; size?: number }) {
  const common = { width: size, height: size, viewBox: '0 0 12 12', 'aria-hidden': true }
  switch (type) {
    case 'discovery':
      return <svg {...common}><circle cx="6" cy="6" r="4.5" fill={color} /></svg>
    case 'theory':
      return <svg {...common}><circle cx="6" cy="6" r="3.7" fill="none" stroke={color} strokeWidth="2" /></svg>
    case 'instrument':
      return <svg {...common}><rect x="1.8" y="1.8" width="8.4" height="8.4" rx="1.8" fill={color} /></svg>
    case 'invention':
      return <svg {...common}><path d="M6 .8 11.2 6 6 11.2.8 6Z" fill={color} /></svg>
    case 'system':
      return <svg {...common}><path d="M6 1 10.4 3.5v5L6 11 1.6 8.5v-5Z" fill={color} /></svg>
  }
}

export function Icon({ name, size = 16 }: { name: 'search' | 'filter' | 'close' | 'plus' | 'minus' | 'fit'; size?: number }) {
  const paths: Record<typeof name, string> = {
    search: 'M11 11l3 3M12 7A5 5 0 1 1 2 7a5 5 0 0 1 10 0Z',
    filter: 'M2 4h12M4.5 8h7M7 12h2',
    close: 'M4 4l8 8M12 4l-8 8',
    plus: 'M8 3v10M3 8h10',
    minus: 'M3 8h10',
    fit: 'M2.5 6V2.5H6M10 2.5h3.5V6M13.5 10v3.5H10M6 13.5H2.5V10',
  }
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={paths[name]} />
    </svg>
  )
}
