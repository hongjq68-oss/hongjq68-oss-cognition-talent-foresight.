import { useState } from "react";
import clsx from "clsx";
import { Briefcase, Copy } from "lucide-react";
import { useApp } from "../state";
import { Card, ClassBadge, EvidenceBadge, List, PageHeader } from "../components/ui";

export default function Strategy() {
  const { analysis: a } = useApp();
  const [sel, setSel] = useState(a!.strategies[0]?.archetype_id);
  const arch = a!.archetypes.find((x) => x.id === sel)!;
  const st = a!.strategies.find((x) => x.archetype_id === sel)!;
  const timeline = a!.capabilities.filter((c) => c.start_search_by).sort((x, y) => (x.start_search_by! < y.start_search_by! ? -1 : 1));
  const later = a!.capabilities.filter((c) => !c.start_search_by && c.classification === "strategic").slice(0, 6);
  return (
    <div className="space-y-6">
      <PageHeader letter="F" title="Hiring Strategy Generator" question="Which archetypes to hire, where to look, how to search, and when to start.">
        <EvidenceBadge c="recommendation" />
      </PageHeader>
      <div className="flex flex-wrap gap-2">
        {a!.strategies.map((s) => {
          const ar = a!.archetypes.find((x) => x.id === s.archetype_id)!;
          return (
            <button key={s.archetype_id} onClick={() => setSel(s.archetype_id)} className={clsx("btn !py-1.5", sel === s.archetype_id ? "bg-ink-900 text-white" : "btn-secondary")}>
              {ar.name} <span className="text-xs opacity-70">{ar.score.toFixed(0)}</span>
            </button>
          );
        })}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2" title={arch.name} subtitle={arch.summary}>
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <div className="label">Capability profile (not a title)</div>
              {arch.capabilities.map((c) => (
                <div key={c.id} className="flex items-baseline justify-between gap-3 py-0.5 text-sm"><span className="text-slate-700">{c.name}</span><span className="shrink-0 whitespace-nowrap text-xs text-slate-400">weight {c.weight} · demand {Math.round(c.demand)}</span></div>
              ))}
            </div>
            <div>
              <div className="label">Unconventional backgrounds to consider</div>
              <List items={arch.unconventional_backgrounds} />
              <div className="label mt-4">Suggested assessment</div>
              <List items={arch.assessment} />
            </div>
          </div>
          <div className="mt-6">
            <div className="label">Capability-based search strings</div>
            <div className="space-y-3">
              {st.queries.map((q) => (
                <div key={q.source} className="rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700">{q.source}
                    <button className="btn-ghost !p-1" onClick={() => navigator.clipboard?.writeText(q.query)} title="Copy"><Copy className="h-3.5 w-3.5" /></button>
                  </div>
                  <code className="mt-1 block whitespace-pre-wrap break-words rounded bg-slate-50 p-2 text-xs text-slate-700">{q.query}</code>
                  <div className="mt-1 text-xs text-slate-500">{q.note}</div>
                </div>
              ))}
            </div>
          </div>
        </Card>
        <div className="space-y-6">
          <Card title="Look for evidence of">
            <div className="flex flex-wrap gap-1">{st.evidence_to_look_for.map((e) => <span key={e} className="chip bg-emerald-50 text-emerald-700">{e}</span>)}</div>
          </Card>
          <Card title="Start with these organisations" subtitle="Non-direct pools first"><List items={st.target_organisations} /></Card>
          <Card title="Avoid"><List items={st.avoid} /></Card>
          <Card title="Matching open Cognition roles" right={<EvidenceBadge c="verified_fact" />}>
            {arch.open_roles.length === 0 ? <div className="text-xs text-slate-500">No open role yet — this is pipeline-building ahead of a requisition.</div> :
              arch.open_roles.map((r) => <a key={r.url} href={r.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-xs text-brand-700 hover:underline"><Briefcase className="h-3 w-3" />{r.title}</a>)}
          </Card>
        </div>
      </div>
      <Card title="Hiring timeline" subtitle="Start-search dates derived from need-by horizon minus scarcity-adjusted lead time" right={<EvidenceBadge c="prediction" />}>
        <div className="space-y-2">
          {timeline.map((c) => (
            <div key={c.id} className="grid grid-cols-12 items-center gap-2 text-sm">
              <div className="col-span-2 font-mono text-xs text-slate-600">{c.start_search_by}</div>
              <div className="col-span-4 font-medium text-slate-800">{c.name}</div>
              <div className="col-span-2"><ClassBadge c={c.classification} /></div>
              <div className="col-span-4 text-xs text-slate-500">capability needed by {c.need_by} · ~{c.lead_weeks} wks lead · scarcity {c.scarcity}/5</div>
            </div>
          ))}
          {later.map((c) => (
            <div key={c.id} className="grid grid-cols-12 items-center gap-2 text-sm opacity-70">
              <div className="col-span-2 font-mono text-xs text-slate-400">monitor</div>
              <div className="col-span-4 text-slate-700">{c.name}</div>
              <div className="col-span-2"><ClassBadge c={c.classification} /></div>
              <div className="col-span-4 text-xs text-slate-500">build relationships; no requisition expected yet</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
