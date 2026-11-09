import { useEffect, useId, useRef, type ReactNode } from 'react'
import { create } from 'zustand'

/** Which menu is open. Only one can be, and pointing at another while one is open moves to it. */
const useOpenMenu = create<{ open: string | null; set(open: string | null): void }>((set) => ({ open: null, set: (open) => set({ open }) }))

interface MenuProps {
  /** What the choice is about, such as "Time". */
  label: string
  /** The current choice in a word or two, shown on the button. */
  value: string
  /** Which edge of the button the list lines up with. */
  align?: 'left' | 'right'
  /** Open upward, for a button at the bottom of the page. */
  up?: boolean
  children: ReactNode
}

/**
 * A button that states the current choice and opens a short list of the alternatives. The page
 * shows the state; the options appear only when asked for.
 */
export function Menu({ label, value, align = 'left', up = false, children }: MenuProps) {
  const id = useId()
  const open = useOpenMenu((s) => s.open === id)
  const anyOpen = useOpenMenu((s) => s.open !== null)
  const set = useOpenMenu((s) => s.set)
  const root = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) return
    const onDown = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) set(null)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') set(null)
    }
    window.addEventListener('pointerdown', onDown)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('pointerdown', onDown)
      window.removeEventListener('keydown', onKey)
    }
  }, [open, set])

  return (
    <div className="menu" ref={root}>
      <button className="menu-button" aria-haspopup="true" aria-expanded={open} onClick={() => set(open ? null : id)} onPointerEnter={() => anyOpen && !open && set(id)}>
        <span className="menu-label">{label}</span>
        <span className="menu-value">{value}</span>
        <svg width="9" height="6" viewBox="0 0 9 6" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M1 1l3.5 3.5L8 1" />
        </svg>
      </button>
      {open && (
        <div className="menu-list" role="menu" data-align={align} data-up={up}>
          {children}
        </div>
      )}
    </div>
  )
}

interface OptionProps {
  name: string
  hint?: string
  /** Whether it is the current choice, or switched on. */
  on: boolean
  /** One of several: choosing it closes the list. Otherwise it is a switch, and the list stays open. */
  single?: boolean
  /** A swatch of colour before the name. */
  color?: string
  /** A figure at the right, such as how many discoveries it covers. */
  count?: number
  onChoose(): void
  onAlone?(): void
}

/** One row of a menu: a choice among several, or a switch. */
export function Option({ name, hint, on, single = false, color, count, onChoose, onAlone }: OptionProps) {
  const close = useOpenMenu((s) => s.set)
  return (
    <button
      className="menu-option"
      role={single ? 'menuitemradio' : 'menuitemcheckbox'}
      aria-checked={on}
      onClick={() => {
        onChoose()
        if (single) close(null)
      }}
      onDoubleClick={onAlone}
    >
      <span className="menu-mark" data-single={single} data-on={on} style={color && on ? { background: color, borderColor: color } : undefined} />
      <span className="menu-text">
        <span className="menu-name">{name}</span>
        {hint && <span className="menu-hint">{hint}</span>}
      </span>
      {count !== undefined && <span className="menu-count">{count}</span>}
    </button>
  )
}

export function MenuHeading({ children }: { children: ReactNode }) {
  return <div className="menu-heading">{children}</div>
}
