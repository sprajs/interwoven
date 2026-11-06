import { motion } from 'motion/react'
import { useEffect, useMemo, useRef } from 'react'
import { storyIndex } from '../data/derive.ts'
import type { Model } from '../data/model.ts'
import { formatYear } from '../engine/time.ts'
import { focusEntry, openThread, stepStory, useApp } from '../store.ts'
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
  const index = useMemo(() => storyIndex(model.nodes, model.edges, 2).slice(0, INDEX_LIMIT), [model])
  return (
    <>
      <h2 className="text-head">Stories</h2>
      <p className="note mt-1">Each is a set of placed entries joined by links, laid out on its own in reading order. Or click any entry on the chart twice to follow what led to it and what it made possible.</p>
      <ol className="mt-4 border-t border-rule">
        {index.map((story) => {
          const first = model.nodes[story.first]!
          const last = model.nodes[story.last]!
          return (
            <li key={story.first} className="border-b border-rule-soft">
              <button onClick={() => openThread(story.first)} className="group block w-full py-2 text-left">
                <span className={`link-hover block text-body ${first.kind === 'science' ? 'science' : ''}`}>{first.title}</span>
                <span className="note flex items-baseline justify-between gap-3">
                  <span className="min-w-0 truncate">to {last.title}</span>
                  <span className="shrink-0">
                    {formatYear(first.year)}, {story.size} entries
                  </span>
                </span>
              </button>
            </li>
          )
        })}
      </ol>
      {index.length === 0 && <p className="note mt-2">No threads are placed yet.</p>}
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
        <p className="note">
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
      <h2 className="text-head">{story.focus !== null ? <>What led to and followed {model.nodes[story.focus]!.title}</> : <>From {model.nodes[members[0]!]!.title}</>}</h2>
      {story.truncated && <p className="note mt-1">A long thread: this shows the nearest {members.length} entries.</p>}

      <div className="note mt-2 flex items-center gap-3">
        <button onClick={() => stepStory(-1)} disabled={position <= 0} className="hover:text-ink disabled:opacity-40" aria-label="Previous entry">
          ← Earlier
        </button>
        <span className="figures">{position >= 0 ? `${position + 1} of ${members.length}` : ''}</span>
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
          const waiting = model.links.filter((link) => (link.to === node.id && !model.indexById.has(link.from)) || (link.from === node.id && !model.indexById.has(link.to)))
          return (
            <li key={i} data-current={current} className={`border-b border-rule-soft py-2 ${current ? '' : 'cursor-pointer'}`} onClick={() => select(i)}>
              {gap && <p className="note mb-1">{gap}</p>}
              <div className="flex items-baseline gap-2 text-body">
                <span className="grid w-2 shrink-0 translate-y-px place-items-center self-center">
                  <Mark kind={node.kind} color={inkOf(model, i)} />
                </span>
                <span className={`min-w-0 flex-1 ${current ? 'text-ink' : 'text-ink-2'} ${node.kind === 'science' ? 'science' : ''}`}>{node.title}</span>
                <span className="note shrink-0">{node.date_label}</span>
              </div>
              {incoming.map((edge, n) => (
                <p key={`${edge.source}-${n}`} className="note mt-1 pl-4">
                  {edge.link.relation}, from {model.nodes[edge.source]!.title}.
                  {current && edge.link.statement && <span className="text-ink-2"> {edge.link.statement}</span>}
                  {edge.tentative && <span> Awaiting review.</span>}
                </p>
              ))}
              {current && (
                <div className="mt-2 pl-4">
                  <p className="text-body">{node.summary}</p>
                  {node.note && <p className="mt-1 text-body text-ink-2">{node.note}</p>}
                  {node.uncertainty && <p className="note mt-1">{node.uncertainty}</p>}
                  {waiting.length > 0 && (
                    <div className="mt-2">
                      <p className="note">Also linked, awaiting a date:</p>
                      <ul>
                        {waiting.map((link, n) => {
                          const other = model.entryById.get(link.to === node.id ? link.from : link.to)
                          if (!other) return null
                          return (
                            <li key={n}>
                              <button
                                onClick={(event) => {
                                  event.stopPropagation()
                                  focusEntry(other.id)
                                }}
                                className={`link-hover text-left text-note text-ink-2 ${other.kind === 'science' ? 'science' : ''}`}
                              >
                                {other.title}
                              </button>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )}
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
      initial={compact ? { y: 72, opacity: 0 } : { x: SHEET_WIDTH }}
      animate={compact ? { y: 0, opacity: 1 } : { x: 0 }}
      exit={compact ? { y: 72, opacity: 0 } : { x: SHEET_WIDTH }}
      transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
      style={{ width: compact ? undefined : SHEET_WIDTH }}
      className={`sheet thin-scroll select-text overflow-y-auto px-8 pb-8 pt-4 ${compact ? 'absolute inset-x-0 bottom-0 z-30 max-h-[48vh] border-t border-rule' : 'absolute bottom-0 right-0 top-18 z-20 border-l border-t border-rule'}`}
      aria-label="Story"
    >
      {story ? <StoryText model={model} /> : <StoryList model={model} />}
    </motion.aside>
  )
}
