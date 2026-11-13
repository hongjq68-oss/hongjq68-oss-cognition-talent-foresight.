import { useState } from "react";
import clsx from "clsx";
import { Check, X, RotateCcw, ExternalLink } from "lucide-react";
import { api } from "../api";
import { useApp } from "../state";
import { Bar, Card, EvidenceBadge, MARKET_NAMES, PageHeader, PoolBadge } from "../components/ui";
import type { Candidate } from "../types";

const STATUS: Record<string, { label: string; cls: string; next: string[] }> = {
  discovered: { label: "Discovered", cls: "bg-slate-100 text-slate-700", next: ["evidence_review", "parked"] },
  evidence_review: { label: "Evidence review", cls: "bg-amber-50 text-amber-800", next: ["verified", "parked"] },
  verified: { label: "Verified", cls: "bg-emerald-50 text-emerald-700", next: ["ready_for_ats", "evidence_review", "parked"] },
  ready_for_ats: { label: "Ready for ATS", cls: "bg-brand-50 text-brand-700", next: ["verified", "parked"] },
  parked: { label: "Parked", cls: "bg-slate-100 text-slate-500", next: ["discovered"] },
};
const ETYPE: Record<string, string> = {
  public_artifact: "Public artifact", open_source: "Open source", publication: "Publication", talk: "Talk",
  news: "News / press", profile_self_reported: "Self-reported", title_only: "Title only (scores 0)",
};

function Detail({ c, onChange }: { c: Candidate; onChange: () => void }) {
  const [err, setErr] = useState<string | null>(null);
  const act = async (fn: () => Promise<unknown>) => {
    try { await fn(); setErr(null); onChange(); } catch (e) { setErr(String((e as Error).message)); }
  };
  const f = c.best_fit;
  return (
    <div className="space-y-5">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold">{c.display_name}</h2>
          {c.synthetic ? <span className="chip bg-fuchsia-50 text-fuchsia-700">Synthetic profile</span> : null}
          <span className={clsx("chip", STATUS[c.status].cls)}>{STATUS[c.status].label}</span>
        </div>
        <div className="text-sm text-slate-600">{c.headline} · {c.employer_descriptor} · {MARKET_NAMES[c.market] || c.market}</div>
        <p className="mt-2 text-sm text-slate-600">{c.background}</p>
      </div>
      <div className="rounded-lg bg-slate-50 p-3">
        <div className="flex items-center justify-between text-sm"><span>Potential role: <b>{f.archetype}</b></span><span className="font-semibold">{f.score.toFixed(0)}/100</span></div>
        <div className="mt-1 text-xs text-slate-500">Evidence fit {(f.evidence_fit * 100).toFixed(0)}% · market fit {f.market_fit} · also: {c.alternative_fits.map((x) => `${x.archetype} (${x.score.toFixed(0)})`).join(", ")}</div>
        <p className="mt-2 text-sm text-slate-700"><b>Why it transfers:</b> {c.transferability}</p>
      </div>
      <div>
        <div className="label">Evidence — what they built or delivered</div>
        <p className="mb-2 text-xs text-slate-500">Only recruiter-verified evidence counts fully; unverified counts half; title-only and rejected count zero.</p>
        <div className="space-y-2">
          {c.evidence.map((e) => (
            <div key={e.id} className={clsx("rounded-lg border p-3", e.verification === "verified" ? "border-emerald-200 bg-emerald-50/40" : e.verification === "rejected" ? "border-rose-200 bg-rose-50/40 opacity-70" : "border-slate-200")}>
              <div className="flex items-center gap-2">
                <span className="chip bg-white text-slate-600 ring-1 ring-slate-200">{ETYPE[e.evidence_type]}</span>
                <span className="text-xs capitalize text-slate-500">{e.verification}</span>
                <span className="ml-auto text-xs text-slate-400">{e.source_date || "undated"}</span>
              </div>
              <div className="mt-1 text-sm font-medium text-slate-800">{e.claim}</div>
              <div className="text-xs text-slate-500">Problem solved: {e.problem_solved}</div>
              <div className="mt-1 flex flex-wrap items-center gap-1">
                {e.capability_ids.map((x) => <span key={x} className="chip bg-slate-100 text-slate-600">{x.replace(/_/g, " ")}</span>)}
                {e.source_url ? <a href={e.source_url} target="_blank" rel="noreferrer" className="text-xs text-brand-700"><ExternalLink className="inline h-3 w-3" /> source</a>
                  : <span className="text-xs text-amber-700">No source link (synthetic) — add one before verifying in production</span>}
              </div>
              <div className="mt-2 flex gap-2">
                <button className="btn-secondary !px-2 !py-1 text-xs" onClick={() => act(() => api.review(e.id, "verified"))}><Check className="h-3 w-3" /> Verify</button>
                <button className="btn-secondary !px-2 !py-1 text-xs" onClick={() => act(() => api.review(e.id, "rejected"))}><X className="h-3 w-3" /> Reject</button>
                {e.verification !== "unverified" && <button className="btn-ghost !px-2 !py-1 text-xs" onClick={() => act(() => api.review(e.id, "unverified"))}><RotateCcw className="h-3 w-3" /> Reset</button>}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div><div className="label">Demonstrated capabilities</div>
          {f.demonstrated.map((d) => <div key={d.id} className="mb-1 text-sm"><div className="flex justify-between"><span>{d.name}</span><span className="text-xs text-slate-400">{d.strength}</span></div><Bar value={d.strength * 100} className="bg-emerald-500" /></div>)}
        </div>
        <div><div className="label">What they need to learn / missing information</div>
          <ul className="list-disc pl-4 text-sm text-slate-600">{[...c.learning_needs, ...c.missing_information.map((m) => `No evidence yet: ${m}`)].map((x) => <li key={x}>{x}</li>)}</ul>
        </div>
      </div>
      <div><div className="label">Recruiter validation questions</div>
        <ol className="list-decimal space-y-1 pl-4 text-sm text-slate-600">{c.validation_questions.map((q) => <li key={q}>{q}</li>)}</ol>
      </div>
      <div className="border-t border-slate-200 pt-3">
        <div className="label">Pipeline status (recruiter decision)</div>
        <div className="flex flex-wrap gap-2">
          {STATUS[c.status].next.map((s) => <button key={s} className="btn-secondary !py-1.5 text-xs" onClick={() => act(() => api.status(c.id, s))}>Move to {STATUS[s].label}</button>)}
        </div>
        {err && <p className="mt-2 text-xs text-rose-600">{err}</p>}
        <p className="mt-2 text-[11px] text-slate-400">Moving to Verified needs ≥2 verified evidence items; Ready for ATS needs every item reviewed. The app never contacts candidates.</p>
      </div>
    </div>
  );
}

export default function Candidates() {
  const { analysis: a, reload } = useApp();
  const [sel, setSel] = useState<string>(a!.candidates[0]?.id);
  const c = a!.candidates.find((x) => x.id === sel);
  return (
    <div className="space-y-6">
      <PageHeader letter="E" title="Candidate Discovery" question="Who has demonstrably solved these problems — and what do we still need to verify?">
        <div className="flex items-center gap-2"><EvidenceBadge c="recommendation" /><a className="btn-secondary !py-1.5 text-xs" href="/api/ats-export?format=csv">Export Ready-for-ATS (CSV)</a></div>
      </PageHeader>
      <div className="rounded-lg border border-fuchsia-200 bg-fuchsia-50 px-4 py-2 text-xs text-fuchsia-800">
        All people below are <b>synthetic</b> prototype profiles with generic employer descriptions. In production, profiles come only from approved public sources and every claim carries a source link.
      </div>
      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2 !p-0" >
          <div className="divide-y divide-slate-100">
            {a!.candidates.map((x) => (
              <button key={x.id} onClick={() => setSel(x.id)} className={clsx("w-full p-4 text-left hover:bg-slate-50", sel === x.id && "bg-brand-50/60")}>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900">{x.display_name}</span>
                  <PoolBadge p={x.pool_type} />
                  <span className={clsx("chip", STATUS[x.status].cls)}>{STATUS[x.status].label}</span>
                  <span className="ml-auto text-sm font-semibold">{x.best_fit.score.toFixed(0)}</span>
                </div>
                <div className="mt-0.5 text-xs text-slate-500">{x.headline} · {x.market} → {x.best_fit.archetype}</div>
                <div className="mt-1.5"><Bar value={x.best_fit.score} /></div>
              </button>
            ))}
          </div>
        </Card>
        <Card className="lg:col-span-3">{c ? <Detail c={c} onChange={reload} /> : <div className="text-sm text-slate-500">Select a profile</div>}</Card>
      </div>
    </div>
  );
}
