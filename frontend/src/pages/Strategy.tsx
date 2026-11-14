import { useState } from "react";
import clsx from "clsx";
import { Briefcase, Copy, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useApp } from "../state";
import { Card, ClassBadge, EvidenceBadge, List, PageHeader, PoolBadge, Score, Tabs, Takeaway, useShowMore } from "../components/ui";
import type { ShortlistEntry } from "../types";

const STATUS_LABEL: Record<string, string> = { discovered: "Discovered", evidence_review: "In review", verified: "Verified", ready_for_ats: "Ready for ATS" };
const tier = (v: number) => (v >= 65 ? "Strong" : v >= 45 ? "Possible" : "Stretch");

function Shortlist({ items }: { items: ShortlistEntry[] }) {
  if (!items.length) return <div className="text-sm text-slate-500">No candidate has evidence for this role yet. Use the search strings to find people.</div>;
  return (
    <div className="divide-y divide-slate-100">
      {items.map((x, i) => (
        <Link key={x.candidate_id} to={`/candidates?c=${x.candidate_id}`} className="flex items-center gap-3 py-2.5 hover:bg-slate-50">
          <span className="w-4 text-xs text-slate-400">{i + 1}</span>
          <Score value={x.score} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-slate-900">{x.display_name}</span>
              <PoolBadge p={x.pool_type} />
              <span className="text-xs text-slate-400">{x.market} · {tier(x.score)} fit</span>
            </div>
            <div className="truncate text-xs text-slate-500">{x.employer_descriptor}</div>
            <div className="mt-0.5 truncate text-xs text-slate-600">
              <span className="text-emerald-700">✓ {x.strengths.join(" · ")}</span>
              {x.gaps.length > 0 && <span className="ml-2 text-amber-700">• check {x.gaps.join(", ")}</span>}
            </div>
          </div>
          <div className="shrink-0 text-right text-[11px] text-slate-500">
            <div className="font-medium text-slate-700">{STATUS_LABEL[x.status] || x.status}</div>
            <div>{x.verified_evidence} verified</div>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
        </Link>
      ))}
    </div>
  );
}

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
              {ar.name} <span className="text-xs opacity-70">· {s.shortlist.length} matches</span>
            </button>
          );
        })}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
        <Card title={arch.name} subtitle={arch.summary}>

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
          <Card title={`Auto-shortlist (${st.shortlist.length})`} subtitle="Top matches by evidence of what they built. Suggestions only; a recruiter verifies before anyone is contacted." right={<EvidenceBadge c="recommendation" />}>
            <Shortlist items={st.shortlist} />
          </Card>
        </div>
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
