import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import clsx from "clsx";
import { Check, X, RotateCcw, ExternalLink, Download, Info, Building2, Pencil, Briefcase, RefreshCw } from "lucide-react";
import { api } from "../api";
import { useApp } from "../state";
import { Card, Details, MARKET_NAMES, PageHeader, PoolBadge, Score, Stat, Tabs } from "../components/ui";
import type { Candidate, OpenJob } from "../types";

const host = (u: string) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; } };

function ProfileLink({ c, onChange }: { c: Candidate; onChange: () => void }) {
  const [edit, setEdit] = useState(false);
  const [val, setVal] = useState(c.profile_url || "");
  const [err, setErr] = useState<string | null>(null);
  const save = async () => {
    try { await api.profile(c.id, val); setEdit(false); setErr(null); onChange(); }
    catch (e) { setErr(String((e as Error).message)); }
  };
  if (edit) return (
    <div className="mt-1">
      <div className="flex gap-1">
        <input autoFocus value={val} onChange={(e) => setVal(e.target.value)} placeholder="https://… public profile a recruiter has checked"
          className="min-w-0 flex-1 rounded-md border border-slate-300 px-2 py-1 text-xs" onKeyDown={(e) => e.key === "Enter" && save()} />
        <button className="btn-primary !px-2 !py-1 text-xs" onClick={save}>Save</button>
        <button className="btn-ghost !px-2 !py-1 text-xs" onClick={() => { setEdit(false); setVal(c.profile_url || ""); setErr(null); }}>Cancel</button>
      </div>
      {err && <p className="mt-1 text-xs text-rose-600">{err}</p>}
    </div>
  );
  return (
    <div className="mt-1 flex items-center gap-2 text-xs">
      {c.profile_url
        ? <a href={c.profile_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-medium text-brand-700 hover:underline"><ExternalLink className="h-3 w-3" /> {host(c.profile_url)}</a>
        : <span className="text-slate-400">No profile link{c.synthetic ? " (synthetic profile)" : ""}</span>}
      <button className="inline-flex items-center gap-0.5 text-slate-500 hover:text-brand-700" onClick={() => setEdit(true)}><Pencil className="h-3 w-3" /> {c.profile_url ? "Edit" : "Add link"}</button>
    </div>
  );
}

function JobGroup({ j, cands, sel, onSelect }: { j: OpenJob; cands: Candidate[]; sel: string; onSelect: (id: string) => void }) {
  const [all, setAll] = useState(false);
  const byId = new Map(cands.map((x) => [x.id, x]));
  const items = j.matches.filter((m) => byId.has(m.candidate_id));
  const shown = all ? items : items.slice(0, 3);
  return (
    <div>
      <div className="flex items-start gap-2 border-y border-slate-100 bg-slate-50 px-3 py-2">
        <Briefcase className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-500" />
        <div className="min-w-0 flex-1">
          <a href={j.url} target="_blank" rel="noreferrer" className="text-xs font-semibold text-slate-800 hover:text-brand-700 hover:underline">{j.title} <ExternalLink className="inline h-3 w-3" /></a>
          <div className="truncate text-[11px] text-slate-500">
            {j.location}{j.department ? ` · ${j.department}` : ""}
            {j.profile && <> · scored as <span className="text-slate-700">{j.profile.name}</span>{j.profile.basis === "inferred" && " (inferred)"}</>}
          </div>
        </div>
        <span className="chip shrink-0 bg-white text-slate-600">{items.length} {items.length === 1 ? "match" : "matches"}</span>
      </div>
      {j.note && <div className="px-3 py-2 text-[11px] text-slate-400">{j.note}</div>}
      {!j.note && !items.length && <div className="px-3 py-2 text-[11px] text-slate-400">No candidate with relevant evidence yet.</div>}
      <div className="divide-y divide-slate-100">
        {shown.map((m) => <Row key={m.candidate_id} x={byId.get(m.candidate_id)!} selected={sel === m.candidate_id} onSelect={() => onSelect(m.candidate_id)}
          score={m.score} role={m.strengths.length ? `✓ ${m.strengths.join(" · ")}` : byId.get(m.candidate_id)!.headline} />)}
      </div>
      {items.length > 3 && <button onClick={() => setAll(!all)} className="w-full px-3 py-1.5 text-left text-[11px] font-medium text-brand-700 hover:underline">{all ? "Show top 3" : `Show all ${items.length}`}</button>}
    </div>
  );
}

function Row({ x, selected, onSelect, score, role }: { x: Candidate; selected: boolean; onSelect: () => void; score: number; role: string }) {
  return (
    <div className={clsx("flex items-center gap-2 pr-3 hover:bg-slate-50", selected && "bg-brand-50/60")}>
      <button onClick={onSelect} className="flex min-w-0 flex-1 items-center gap-3 p-3 text-left">
        <Score value={score} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2"><span className="truncate text-sm font-semibold text-slate-900">{x.display_name}</span><PoolBadge p={x.pool_type} /></div>
          <div className="flex items-center gap-1 truncate text-xs text-slate-600"><Building2 className="h-3 w-3 shrink-0 text-slate-400" /><span className="truncate">{x.employer_descriptor}</span></div>
          <div className="truncate text-xs text-slate-500">{role} · {x.market}</div>
        </div>
        <span className={clsx("chip shrink-0", STATUS[x.status].cls)}>{STATUS[x.status].label}</span>
      </button>
      {x.profile_url
        ? <a href={x.profile_url} target="_blank" rel="noreferrer" title={`Open profile (${host(x.profile_url)})`} aria-label={`Open ${x.display_name}'s profile`} className="shrink-0 rounded p-1 text-brand-700 hover:bg-brand-50"><ExternalLink className="h-4 w-4" /></a>
        : <span title="No profile link yet" className="shrink-0 p-1 text-slate-300"><ExternalLink className="h-4 w-4" /></span>}
    </div>
  );
}

const STATUS: Record<string, { label: string; cls: string; next: string[] }> = {
  discovered: { label: "Discovered", cls: "bg-slate-100 text-slate-700", next: ["evidence_review", "parked"] },
  evidence_review: { label: "Evidence review", cls: "bg-amber-50 text-amber-800", next: ["verified", "parked"] },
  verified: { label: "Verified", cls: "bg-emerald-50 text-emerald-700", next: ["ready_for_ats", "evidence_review", "parked"] },
  ready_for_ats: { label: "Ready for ATS", cls: "bg-brand-50 text-brand-700", next: ["verified", "parked"] },
  parked: { label: "Parked", cls: "bg-slate-100 text-slate-500", next: ["discovered"] },
};
const STEPS = ["discovered", "evidence_review", "verified", "ready_for_ats"];
const ETYPE: Record<string, string> = {
  public_artifact: "Public artifact", open_source: "Open source", publication: "Publication", talk: "Talk",
  news: "News", profile_self_reported: "Self-reported", title_only: "Title only · scores 0",
};
const VERIF: Record<string, string> = { verified: "text-emerald-700", rejected: "text-rose-600", unverified: "text-slate-400" };

function Stepper({ status }: { status: string }) {
  const i = STEPS.indexOf(status);
  return (
    <div className="flex items-center gap-1">
      {STEPS.map((s, k) => (
        <div key={s} className="flex items-center gap-1">
          <span className={clsx("rounded-full px-2 py-0.5 text-[11px] font-medium", k < i ? "bg-emerald-100 text-emerald-700" : k === i ? "bg-ink-900 text-white" : "bg-slate-100 text-slate-400")}>{STATUS[s].label}</span>
          {k < STEPS.length - 1 && <span className="h-px w-3 bg-slate-300" />}
        </div>
      ))}
      {status === "parked" && <span className="ml-2 chip bg-slate-100 text-slate-500">Parked</span>}
    </div>
  );
}

function Detail({ c, onChange }: { c: Candidate; onChange: () => void }) {
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<"evidence" | "fit" | "questions">("evidence");
  const act = async (fn: () => Promise<unknown>) => {
    try {
      const r = (await fn()) as { candidate_status?: string };
      const revoked = r?.candidate_status && c.status !== "discovered" && r.candidate_status !== c.status;
      setErr(revoked ? `Status moved back to ${STATUS[r.candidate_status!].label}: the evidence no longer meets the ${STATUS[c.status].label} requirements.` : null);
      onChange();
    } catch (e) { setErr(String((e as Error).message)); }
  };
  const f = c.best_fit;
  const verified = c.evidence.filter((e) => e.verification === "verified").length;
  const pending = c.evidence.filter((e) => e.verification === "unverified").length;
  const gaps = [...f.gaps.map((g) => g.name), ...c.learning_needs].slice(0, 3);
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-4">
        <Score value={f.score} size="lg" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold">{c.display_name}</h2>
            {c.synthetic ? <span className="chip bg-fuchsia-50 text-fuchsia-700">Synthetic</span> : null}
          </div>
          <div className="text-sm text-slate-600">{c.headline} · {MARKET_NAMES[c.market] || c.market}</div>
          <div className="mt-0.5 flex items-center gap-1 text-sm text-slate-700"><Building2 className="h-3.5 w-3.5 text-slate-400" /> {c.employer_descriptor}</div>
          <ProfileLink key={c.profile_url || ""} c={c} onChange={onChange} />
          <div className="mt-1 text-sm">Best role: <b>{f.archetype}</b></div>
          {c.best_job && (
            <div className="text-xs text-slate-500">Best open job: <a href={c.best_job.url} target="_blank" rel="noreferrer" className="font-semibold text-brand-700 hover:underline">{c.best_job.title}</a> · {c.best_job.market} ({c.best_job.score.toFixed(0)})</div>
          )}
        </div>
      </div>
      <Stepper status={c.status} />

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg bg-emerald-50/60 p-3">
          <div className="text-xs font-semibold text-emerald-800">Proven strengths</div>
          <ul className="mt-1 space-y-0.5 text-sm text-slate-700">{f.demonstrated.slice(0, 3).map((d) => <li key={d.id}>✓ {d.name}</li>)}
            {!f.demonstrated.length && <li className="text-slate-400">None proven yet</li>}</ul>
        </div>
        <div className="rounded-lg bg-amber-50/60 p-3">
          <div className="text-xs font-semibold text-amber-800">Gaps to check</div>
          <ul className="mt-1 space-y-0.5 text-sm text-slate-700">{gaps.map((g) => <li key={g}>• {g}</li>)}</ul>
        </div>
      </div>

      <div className={clsx("flex items-center justify-between rounded-lg px-3 py-2 text-sm", verified >= 2 ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-600")}>
        <span><b>{verified}</b> of {c.evidence.length} evidence items verified{pending ? ` · ${pending} to review` : ""}</span>
        <span className="text-xs">Need 2 to verify</span>
      </div>

      <Tabs value={tab} onChange={setTab} tabs={[
        { id: "evidence", label: `Evidence (${c.evidence.length})` },
        { id: "fit", label: "Why they fit" },
        { id: "questions", label: `Questions (${c.validation_questions.length})` },
      ]} />

      {tab === "evidence" && (
        <div className="space-y-2">
          {c.evidence.map((e) => (
            <div key={e.id} className={clsx("rounded-lg border p-3", e.verification === "verified" ? "border-emerald-200 bg-emerald-50/30" : e.verification === "rejected" ? "border-rose-200 bg-rose-50/30 opacity-70" : "border-slate-200")}>
              <div className="flex items-start gap-2">
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-slate-800">{e.claim}</div>
                  <div className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-slate-500">
                    <span>{ETYPE[e.evidence_type]}</span><span>·</span>
                    <span className={clsx("capitalize font-medium", VERIF[e.verification])}>{e.verification}</span>
                    {e.source_url && <a href={e.source_url} target="_blank" rel="noreferrer" className="text-brand-700"><ExternalLink className="inline h-3 w-3" /> source</a>}
                  </div>
                </div>
                <div className="flex shrink-0 gap-1">
                  <button title="Verify" aria-label="Verify" className={clsx("btn-secondary !px-2 !py-1 text-xs", e.verification === "verified" && "!bg-emerald-600 !text-white")} onClick={() => act(() => api.review(e.id, "verified"))}><Check className="h-3 w-3" /> Verify</button>
                  <button title="Reject" aria-label="Reject" className={clsx("btn-secondary !px-2 !py-1 text-xs", e.verification === "rejected" && "!bg-rose-600 !text-white")} onClick={() => act(() => api.review(e.id, "rejected"))}><X className="h-3 w-3" /> Reject</button>
                  {e.verification !== "unverified" && <button title="Reset" aria-label="Reset" className="btn-ghost !px-2 !py-1 text-xs" onClick={() => act(() => api.review(e.id, "unverified"))}><RotateCcw className="h-3 w-3" /> Reset</button>}
                </div>
              </div>
              <Details label="More" className="mt-1">
                <div className="space-y-1 text-xs text-slate-500">
                  <div><b>Problem solved:</b> {e.problem_solved}</div>
                  <div className="flex flex-wrap gap-1">{e.capability_ids.map((x) => <span key={x} className="chip bg-slate-100 text-slate-600">{x.replace(/_/g, " ")}</span>)}</div>
                  <div>{e.source_date || "Undated"}{!e.source_url && " · no source link (synthetic)"}</div>
                </div>
              </Details>
            </div>
          ))}
        </div>
      )}
      {tab === "fit" && (
        <div className="space-y-3 text-sm text-slate-700">
          <p>{c.transferability}</p>
          <div className="text-xs text-slate-500">Evidence fit {(f.evidence_fit * 100).toFixed(0)}% · Market fit {f.market_fit}</div>
          {c.alternative_fits.length > 0 && <div className="text-xs text-slate-500">Also fits: {c.alternative_fits.map((x) => `${x.archetype} (${x.score.toFixed(0)})`).join(", ")}</div>}
          <Details label="Background">
            <p className="text-sm text-slate-600">{c.background}</p>
            {c.missing_information.length > 0 && <p className="mt-2 text-xs text-slate-500">No evidence yet: {c.missing_information.join(", ")}</p>}
          </Details>
        </div>
      )}
      {tab === "questions" && (
        <ol className="list-decimal space-y-1.5 pl-5 text-sm text-slate-700">{c.validation_questions.map((q) => <li key={q}>{q}</li>)}</ol>
      )}

      <div className="border-t border-slate-200 pt-3">
        <div className="flex flex-wrap gap-2">
          {STATUS[c.status].next.map((s, i) => (
            <button key={s} className={clsx(i === 0 ? "btn-primary" : "btn-secondary", "!py-1.5 text-xs")} onClick={() => act(() => api.status(c.id, s))}>Move to {STATUS[s].label}</button>
          ))}
        </div>
        {err && <p className="mt-2 text-xs text-rose-600">{err}</p>}
      </div>
    </div>
  );
}

export default function Candidates() {
  const { analysis: a, reload } = useApp();
  const [params] = useSearchParams();
  const [sel, setSel] = useState<string>(params.get("c") || a!.candidates[0]?.id);
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"fit" | "roles">("fit");
  const list = a!.candidates.filter((x) => !q || STATUS[x.status].label === q);
  const [mkt, setMkt] = useState("");
  const jobs = a!.open_jobs.filter((j) => !mkt || j.market === mkt);
  const markets = [...new Set(a!.open_jobs.map((j) => j.market))];
  const pulled = a!.open_jobs.map((j) => j.retrieved_on).filter(Boolean).sort().pop();
  const [refreshing, setRefreshing] = useState(false);
  const refresh = async () => { setRefreshing(true); try { await api.refresh(); await reload(); } finally { setRefreshing(false); } };
  const c = a!.candidates.find((x) => x.id === sel);
  const count = (s: string) => a!.candidates.filter((x) => x.status === s).length;
  const strong = a!.candidates.filter((x) => x.best_fit.score >= 65).length;
  return (
    <div className="space-y-5">
      <PageHeader letter="E" title="Candidates" question="People who have already solved these problems.">
        <a className="btn-secondary !py-1.5 text-xs" href="/api/ats-export?format=csv"><Download className="h-3.5 w-3.5" /> Export Ready-for-ATS</a>
      </PageHeader>
      <div className="grid gap-3 sm:grid-cols-4">
        <Stat label="Shortlisted" value={a!.candidates.length} />
        <Stat label="Strong fit (65+)" value={strong} />
        <Stat label="In review" value={count("evidence_review")} />
        <Stat label="Ready for ATS" value={count("ready_for_ats")} />
      </div>
      <div className="flex items-center gap-2 text-xs text-fuchsia-800"><Info className="h-3.5 w-3.5" /> Demo profiles are synthetic. Scores count only evidence of what someone built; job titles score zero.</div>
      <div className="grid gap-5 lg:grid-cols-5">
        <Card className="lg:col-span-2 !p-0">
          <div className="flex items-center gap-2 border-b border-slate-100 px-3 pt-3 text-xs text-slate-500">
            Sort by
            {([["fit", "Best fit"], ["roles", "Open jobs"]] as const).map(([k, l]) => (
              <button key={k} onClick={() => setSort(k)} className={clsx("chip", sort === k ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600")}>{l}</button>
            ))}
          </div>
          <div className="flex flex-wrap gap-1 border-b border-slate-100 p-3">
            {["", "Discovered", "Evidence review", "Verified", "Ready for ATS"].map((s) => (
              <button key={s} onClick={() => setQ(s)} className={clsx("chip", q === s ? "bg-ink-900 text-white" : "bg-slate-100 text-slate-600")}>{s || "All"}</button>
            ))}
          </div>
          {sort === "fit" ? (
            <div className="divide-y divide-slate-100">
              {list.map((x) => <Row key={x.id} x={x} selected={sel === x.id} onSelect={() => setSel(x.id)} score={x.best_fit.score} role={x.best_fit.archetype} />)}
              {!list.length && <div className="p-4 text-sm text-slate-400">No candidates in this stage</div>}
            </div>
          ) : (
            <div>
              <div className="flex flex-wrap items-center gap-1 px-3 py-2 text-[11px] text-slate-500">
                <span>{a!.open_jobs.length} live APAC jobs from Cognition's Ashby board{pulled ? ` · pulled ${pulled.slice(0, 10)}` : ""}</span>
                <button onClick={refresh} disabled={refreshing} className="inline-flex items-center gap-0.5 text-brand-700 hover:underline"><RefreshCw className={clsx("h-3 w-3", refreshing && "animate-spin")} /> Refresh</button>
              </div>
              <div className="flex flex-wrap gap-1 px-3 pb-2">
                {["", ...markets].map((m) => (
                  <button key={m} onClick={() => setMkt(m)} className={clsx("chip", mkt === m ? "bg-ink-900 text-white" : "bg-slate-100 text-slate-600")}>
                    {m ? `${MARKET_NAMES[m] || m} (${a!.open_jobs.filter((j) => j.market === m).length})` : "All markets"}
                  </button>
                ))}
              </div>
              {jobs.map((j) => <JobGroup key={j.id} j={j} cands={list} sel={sel} onSelect={setSel} />)}
            </div>
          )}
        </Card>
        <Card className="lg:col-span-3">{c ? <Detail key={c.id} c={c} onChange={reload} /> : <div className="text-sm text-slate-500">Select a candidate</div>}</Card>
      </div>
    </div>
  );
}
