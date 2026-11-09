import { useLayoutEffect, useRef, useState } from 'react'
import { shortDate } from '../lib/text.ts'
import { useApp, useDimension, useModel } from '../store.ts'

/** A card beside whatever discovery the pointer is on, in any view. */
export function Tooltip() {
  const model = useModel()
  const hover = useApp((s) => s.hover)
  const dimension = useDimension()
  const ref = useRef<HTMLDivElement | null>(null)
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null)
  const entry = hover ? model.byId.get(hover.id) : undefined

  useLayoutEffect(() => {
    if (!hover || !ref.current) return setPosition(null)
    const box = ref.current.getBoundingClientRect()
    let left = hover.x + 14
    if (left + box.width > window.innerWidth - 8) left = hover.x - box.width - 14
    let top = hover.y - box.height - 10
    if (top < 8) top = hover.y + 22
    setPosition({ left: Math.max(8, left), top })
  }, [hover])

  if (!hover || !entry) return null
  const category = dimension.categories.find((c) => c.id === dimension.of(entry))
  const place = entry.at ? model.bundle.places[entry.at.place]?.name : undefined
  return (
    <div ref={ref} className="tooltip" role="tooltip" style={position ? position : { left: 0, top: 0, visibility: 'hidden' }}>
      <h4>{entry.name}</h4>
      <div className="meta">
        {entry.date ? shortDate(entry.date.label) : 'No date established'}
        {place ? ` · ${place}` : ''}
      </div>
      {entry.summary && <p>{entry.summary}</p>}
      <p className="meta">
        <i className="swatch" style={{ background: category?.color }} />
        {model.fieldNames.get(entry.domain)}
      </p>
    </div>
  )
}
