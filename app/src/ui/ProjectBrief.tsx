import { useRef } from 'react'

/** A concise entry point to the shared project brief, not a separate research policy. */
export function ProjectBrief() {
  const dialog = useRef<HTMLDialogElement>(null)
  return (
    <>
      <button className="project-button" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}>Project</button>
      <dialog ref={dialog} className="project-dialog" aria-labelledby="project-title" onKeyDown={(event) => {
        // Escape closes the dialog without also clearing the selected discovery.
        if (event.key === 'Escape') event.stopPropagation()
      }}>
        <div className="project-dialog-header">
          <div>
            <span className="project-eyebrow">The project</span>
            <h2 id="project-title">A tech tree of human civilisation</h2>
          </div>
          <button className="project-close" aria-label="Close project brief" onClick={() => dialog.current?.close()}>×</button>
        </div>
        <p>Interwoven traces discoveries, inventions and practices through an evidence-backed network: what they depended on, what they made possible, and what evidence helps explain why they emerged there and then.</p>
        <h3>Follow the branches</h3>
        <p>Research starts with varied breakthroughs and works backwards through supported prerequisites, while checking what happened afterwards. Independent reinventions, local adaptations, lost or abandoned branches and revivals belong here too. A missing link is a research gap, not proof of absence or loss.</p>
        <h3>Evidence and review</h3>
        <p>Open a discovery to inspect its sources and uncertainty. A description mentioning an event does not replace a supported dated event: researchers compare the actual event type, subject, date and scope before accepting or rejecting an extension.</p>
        <p>Routine admission review is a separate review by Terra High (<code>gpt-6.1-terra</code>, effort <code>high</code>) against original evidence; consequential unresolved disputes can receive targeted escalation. Uncertain claims remain explicit, and a researcher cannot approve their own additions.</p>
        <a href="https://github.com/sprajs/interwoven/blob/main/docs/project-brief.md" target="_blank" rel="noreferrer">Read the full project brief ↗</a>
      </dialog>
    </>
  )
}
