import { useState } from "react";
import clsx from "clsx";
import { Briefcase, Copy } from "lucide-react";
import { useApp } from "../state";
import { Card, ClassBadge, EvidenceBadge, List, PageHeader, Tabs, Takeaway, useShowMore } from "../components/ui";

export default function Strategy() {
  const { analysis: a } = useApp();
  const [sel, setSel] = useState(a!.strategies[0]?.archetype_id);
  const arch = a!.archetypes.find((x) => x.id === sel)!;
  const st = a!.strategies.find((x) => x.archetype_id === sel)!;
  const timeline = a!.capabilities.filter((c) => c.start_search_by).sort((x, y) => (x.start_search_by! < y.start_search_by! ? -1 : 1));
  const later = a!.capabilities.filter((c) => !c.start_search_by && c.classification === "strategic").slice(0, 6);
  const [tab, setTab] = useState<"profile" | "search" | "where">("profile");
  const [shownTl, moreTl] = useShowMore(timeline, 6);
  const topArch = a!.archetypes.find((x) => x.id === a!.strategies[0]?.archetype_id);
  return (
    <div className="space-y-5">
      <PageHeader letter="F" title="Hiring Strategy" question="Who to hire, where to look and when to start.">
        <EvidenceBadge c="recommendation" />
      </PageHeader>
      <Takeaway title={`Top priority: ${topArch?.name}.${timeline[0] ? ` First search starts ${timeline[0].start_search_by}.` : ""}`}>
        {a!.strategies.length} role profiles ranked by forecast demand. Pick one to see who to look for and how to search.
      </Takeaway>
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

          <Tabs value={tab} onChange={setTab} tabs={[{ id: "profile", label: "Profile" }, { id: "search", label: "How to search" }, { id: "where", label: "Where to look" }]} />
          <div className="mt-4">
            {tab === "profile" && (
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <div className="label">Must-have capabilities</div>
                  {arch.capabilities.map((c) => (
                    <div key={c.id} className="py-0.5 text-sm text-slate-700">• {c.name}</div>
                  ))}
                </div>
                <div>
                  <div className="label">Look for evidence of</div>
                  <div className="flex flex-wrap gap-1">{st.evidence_to_look_for.map((e) => <span key={e} className="chip bg-emerald-50 text-emerald-700">{e}</span>)}</div>
                  <div className="label mt-4">How to assess</div>
                  <List items={arch.assessment} />
                </div>
              </div>
            )}
            {tab === "search" && (
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
            )}
            {tab === "where" && (
              <div className="grid gap-5 md:grid-cols-2">
                <div><div className="label">Start with</div><List items={st.target_organisations} /></div>
                <div>
                  <div className="label">Unusual backgrounds worth a look</div><List items={arch.unconventional_backgrounds} />
                  <div className="label mt-4">Avoid</div><List items={st.avoid} />
                </div>
              </div>
            )}
          </div>
        </Card>
        <div className="space-y-6">
          <Card title="Open Cognition roles" right={<EvidenceBadge c="verified_fact" />}>
            {arch.open_roles.length === 0 ? <div className="text-xs text-slate-500">No open role yet. Build the pipeline early.</div> :
              arch.open_roles.map((r) => <a key={r.url} href={r.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-xs text-brand-700 hover:underline"><Briefcase className="h-3 w-3" />{r.title}</a>)}
          </Card>
        </div>
      </div>
      <Card title="Hiring timeline" subtitle="When to start each search" right={<EvidenceBadge c="prediction" />}>
        <div className="space-y-2">
          {shownTl.map((c) => (
            <div key={c.id} className="grid grid-cols-12 items-center gap-2 text-sm">
              <div className="col-span-2 font-mono text-xs text-slate-600">{c.start_search_by}</div>
              <div className="col-span-4 font-medium text-slate-800">{c.name}</div>
              <div className="col-span-2"><ClassBadge c={c.classification} /></div>
              <div className="col-span-4 text-xs text-slate-500">{c.need_by && c.need_by > new Date().toISOString().slice(0, 10) ? `Needed by ${c.need_by}` : "Needed now"}</div>
            </div>
          ))}
          {later.map((c) => (
            <div key={c.id} className="grid grid-cols-12 items-center gap-2 text-sm opacity-70">
              <div className="col-span-2 font-mono text-xs text-slate-400">monitor</div>
              <div className="col-span-4 text-slate-700">{c.name}</div>
              <div className="col-span-2"><ClassBadge c={c.classification} /></div>
              <div className="col-span-4 text-xs text-slate-500">build relationships</div>
            </div>
          ))}
          {moreTl}
        </div>
      </Card>
    </div>
  );
}
