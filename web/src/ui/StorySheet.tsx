import { motion } from 'motion/react'
import { useEffect, useMemo, useRef } from 'react'
import { storyIndex } from '../data/derive.ts'
import type { Model } from '../data/model.ts'
import { formatYear } from '../engine/time.ts'
import { openThread, stepStory, useApp } from '../store.ts'
import { CloseButton, Mark } from './icons.tsx'
import { COMPACT_WIDTH, SHEET_WIDTH } from './layout.ts'

const INDEX_LIMIT = 40

function inkOf(model: Model, i: number): string {
  return `rgb(${model.ink[i * 3]! * 255} ${model.ink[i * 3 + 1]! * 255} ${model.ink[i * 3 + 2]! * 255})`
}

function gapWords(years: number): string | null {
  const y = Math.round(years)
  if (y < 1) return null
  return y === 1 ? '1 year later' : `${y.toLocaleString('en-US')} years later`
}

/** Every thread worth reading on its own. */
function StoryList({ model }: { model: Model }) {
  const index = useMemo(() => storyIndex(model.nodes, model.edges).slice(0, INDEX_LIMIT), [model])
  return (
    <>
      <h2 className="text-[21px] font-medium leading-none">Stories</h2>
      <p className="caption mt-2 leading-snug">Each is a set of entries joined by links, laid out on its own in reading order. Or click any entry on the chart twice to follow what led to it and what it made possible.</p>
      <ol className="mt-3 border-t border-rule">
        {index.map((story) => {
          const first = model.nodes[story.first]!
          const last = model.nodes[story.last]!
          return (
            <li key={story.first} className="border-b border-rule/50">
              <button onClick={() => openThread(story.first)} className="group block w-full py-[6px] text-left">
                <span className={`block text-[16px] leading-tight group-hover:underline group-hover:decoration-[0.5px] group-hover:underline-offset-2 ${first.kind === 'science' ? 'italic' : ''}`}>{first.title}</span>
                <span className="mt-0.5 flex items-baseline justify-between gap-3 text-[14px] leading-tight text-ink-3">
                  <span className="min-w-0 truncate">to {last.title}</span>
                  <span className="shrink-0">
                    {formatYear(first.year)}, {story.size}
                  </span>
                </span>
              </button>
            </li>
          )
        })}
      </ol>
      {index.length === 0 && <p className="mt-3 text-[15px] italic text-ink-3">No threads of three or more entries yet.</p>}
    </>
  )
}

/** A followed thread as continuous reading, with the chart beside it. */
function StoryText({ model }: { model: Model }) {
  const story = useApp((s) => s.story)!
  const selected = useApp((s) => s.selected)
  const select = useApp((s) => s.select)
  const setStory = useApp((s) => s.setStory)
  const listRef = useRef<HTMLOListElement>(null)
  const compact = window.innerWidth < COMPACT_WIDTH

  useEffect(() => {
    listRef.current?.querySelector('[data-current="true"]')?.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
  }, [selected])

  const members = story.members
  const position = selected === null ? -1 : members.indexOf(selected)
  const firstYear = model.nodes[members[0]!]!.year
  const lastYear = model.nodes[members[members.length - 1]!]!.year
  const inStory = useMemo(() => new Set(members), [members])

  return (
    <>
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-[15px] text-ink-3">
          {formatYear(firstYear)} to {formatYear(lastYear)}, {members.length} entries
        </p>
        <CloseButton
          onClick={() => {
            setStory(null)
            select(null)
          }}
          label="Close this story"
        />
      </div>
      <h2 className="mt-0.5 text-[23px] font-medium leading-[1.1]">
        {story.focus !== null ? <>What led to and followed {model.nodes[story.focus]!.title}</> : <>From {model.nodes[members[0]!]!.title}</>}
      </h2>
      {story.truncated && <p className="caption mt-1 leading-snug">A long thread: this shows the nearest {members.length} entries.</p>}

      <div className="mt-2 flex items-center gap-3 text-[15px] text-ink-3">
        <button onClick={() => stepStory(-1)} disabled={position <= 0} className="hover:text-ink disabled:opacity-40" aria-label="Previous entry">
          ← Earlier
        </button>
        <span className="text-[14px]">{position >= 0 ? `${position + 1} of ${members.length}` : ''}</span>
        <button onClick={() => stepStory(1)} disabled={position >= members.length - 1} className="hover:text-ink disabled:opacity-40" aria-label="Next entry">
          Later →
        </button>
      </div>

      <ol ref={listRef} className="mt-2 border-t border-rule">
        {members.map((i, k) => {
          const node = model.nodes[i]!
          const current = i === selected
          if (compact && !current) return null
          const gap = k > 0 ? gapWords(node.year - model.nodes[members[k - 1]!]!.year) : null
          const incoming = model.edgesInto[i]!.filter((e) => inStory.has(e.source))
          return (
            <li key={i} data-current={current} className={`border-b border-rule/50 py-2 ${current ? '' : 'cursor-pointer'}`} onClick={() => select(i)}>
              {gap && <p className="mb-1 text-[13.5px] italic text-ink-3">{gap}</p>}
              <div className="flex items-baseline gap-2 text-[16.5px] leading-tight">
                <span className="grid w-2.5 shrink-0 translate-y-[1px] place-items-center self-center">
                  <Mark kind={node.kind} size={9} color={inkOf(model, i)} />
                </span>
                <span className={`min-w-0 flex-1 ${current ? 'font-medium' : ''} ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</span>
                <span className="shrink-0 text-[14px] text-ink-3">{node.date_label}</span>
              </div>
              {incoming.map((edge, n) => (
                <p key={`${edge.source}-${n}`} className={`mt-1 pl-[18px] text-[14.5px] leading-snug ${edge.tentative ? 'text-ink-3' : 'text-ink-2'}`}>
                  <span className="italic text-ink-3">{edge.link.relation}, from {model.nodes[edge.source]!.title}. </span>
                  {current && edge.link.statement}
                  {edge.tentative && <em> Awaiting review.</em>}
                </p>
              ))}
              {current && (
                <div className="mt-1.5 pl-[18px]">
                  <p className="text-[15.5px] leading-[1.3]">{node.summary}</p>
                  {node.note && <p className="mt-1 text-[15px] italic leading-snug text-ink-2">{node.note}</p>}
                  {node.uncertainty && <p className="mt-1 text-[14px] leading-snug text-ink-3">{node.uncertainty}</p>}
                  {!node.anchored && !model.synthetic && <p className="mt-1 text-[14px] italic leading-snug text-ink-3">The date is provisional: no anchor has been selected yet.</p>}
                </div>
              )}
            </li>
          )
        })}
      </ol>
    </>
  )
}

export function StorySheet() {
  const model = useApp((s) => s.model)
  const story = useApp((s) => s.story)
  if (!model) return null
  const compact = window.innerWidth < COMPACT_WIDTH
  return (
    <motion.aside
      key="story-sheet"
      initial={compact ? { y: 80, opacity: 0 } : { x: SHEET_WIDTH }}
      animate={compact ? { y: 0, opacity: 1 } : { x: 0 }}
      exit={compact ? { y: 80, opacity: 0 } : { x: SHEET_WIDTH }}
      transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
      style={{ width: compact ? undefined : SHEET_WIDTH }}
      className={`sheet thin-scroll select-text overflow-y-auto px-5 pb-6 pt-3 ${
        compact ? 'absolute inset-x-0 bottom-0 z-30 max-h-[48vh] border-t border-rule' : 'absolute bottom-0 right-0 top-[54px] z-20 border-l border-t border-rule'
      }`}
      aria-label="Story"
    >
      {story ? <StoryText model={model} /> : <StoryList model={model} />}
    </motion.aside>
  )
}
