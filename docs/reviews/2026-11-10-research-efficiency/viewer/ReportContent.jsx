import React from "react";
import { EvidenceChart, ReportSection, RichNarrative, useDataApp } from "../../data-app-public.jsx";
import sections from "./sections.json";

const previews = {
  "https://developers.openai.com/api/docs/pricing": { title: "Official OpenAI pricing", summary: "Published model input, cached-input and output rates. These support API-equivalent comparisons, not a reconstruction of subscription billing.", approvedForReport: true },
  "https://developers.openai.com/api/docs/guides/prompt-caching": { title: "Prompt caching", summary: "Explains stable-prefix reuse, cache reads and cache writes. High cache reuse does not by itself make a long multi-step workflow efficient.", approvedForReport: true },
  "https://developers.openai.com/api/docs/guides/cost-optimization": { title: "Cost optimization", summary: "Recommends reducing requests and token volume and choosing suitable smaller models; also describes asynchronous processing options.", approvedForReport: true },
  "https://developers.openai.com/api/docs/guides/evals": { title: "Working with evals", summary: "Describes evaluating model behavior on representative inputs with explicit criteria.", approvedForReport: true },
};

export function ReportContent() {
  const { reviewedRows, visible, appTitle } = useDataApp();
  const rows = reviewedRows("campaign_roles");
  const bindings = {1:"run_usage",2:"campaign_roles",3:"pipeline",4:"diagnostics",5:"checkpoints",7:"model_roles"};
  return <article className="report-content" aria-label="Research efficiency review">
    <header className="report-hero">
      <h1 data-data-app-title>{appTitle}</h1>
      <RichNarrative id="review:deck" className="report-deck" value="A bounded pipeline can preserve the evidence standard while removing expensive coordination, duplicate retrieval and premature detail. Review of the 9–10 November 2026 runs." />
    </header>
    {sections.map((section, index) => <React.Fragment key={section.id}>
      {visible(section.id) && (bindings[index] ? <ReportSection id={section.id} title={section.title} queryId={bindings[index]} sourceRows={reviewedRows(bindings[index])} showHeading={false}>
          <RichNarrative id={section.id+":body"} value={section.text} sourcePreviews={previews} />
        </ReportSection> : <section><RichNarrative id={section.id+":body"} value={section.text} sourcePreviews={previews} /></section>)}
      {index === 2 && <>
        {visible("campaign-role-cost") && <EvidenceChart id="campaign-role-cost" queryId="campaign_roles" title="Modeled token cost by role" description="Standard API equivalent USD; excludes tool charges and plan-specific billing. Not an invoice." spec={{type:"horizontalBar",x:"role",y:"standardApiUsd",currency:"USD",valueDecimals:2,stackable:false}} rows={rows} sourceRows={rows} height={320} />}
        {visible("campaign-role-input") && <EvidenceChart id="campaign-role-input" queryId="campaign_roles" title="Input token presentations by role" description="Millions of logged input tokens, including cached history. Compare with cost above: raw token volume alone misstates the opportunity." spec={{type:"horizontalBar",x:"role",y:"inputMillions",yLabel:"Million tokens",valueDecimals:2,stackable:false}} rows={rows} sourceRows={rows} height={320} />}
      </>}
    </React.Fragment>)}
  </article>;
}
