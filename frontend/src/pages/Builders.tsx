import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import clsx from "clsx";
import { ExternalLink, Play, Search, UserPlus, X } from "lucide-react";
import { builderApi } from "../api";
import { useApp } from "../state";
import { Card, Details, MARKET_NAMES, PageHeader, Stat, Tabs, Takeaway } from "../components/ui";
import type { BuilderOverview, InvestigateResult, Lead, SourceReport } from "../types";

const KIND: Record<string, string> = {
  repo: "Repo", package: "Package", model: "Model", launch: "Launch", demo: "Demo", article: "Writing", paper: "Paper", patent: "Patent",
};
const SRC: Record<string, string> = { github: "GitHub", hn: "Hacker News", devto: "dev.to", arxiv: "arXiv", huggingface: "Hugging Face", npm: "npm", rss: "Blog/RSS", web: "Web" };
const POOLS = [["founder", "Founder / builder"], ["adjacent", "Adjacent tech"], ["customer_side", "Customer-side"], ["consulting", "Consulting/SI"], ["direct", "Direct"]];
const ago = (s: string | null) => (s ? s.slice(0, 16).replace("T", " ") : "never");

function SourceResult({ r }: { r: SourceReport }) {
  return (
    <div className="flex flex-wrap gap-1">
      {Object.entries(r).map(([k, v]) => (
        <span key={k} title={v.error} className={clsx("chip", v.ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700")}>
          {SRC[k] || k}: {v.ok ? v.items : v.error?.slice(0, 40)}
        </span>
      ))}
    </div>
  );
}

function LeadCard({ l, caps, onDone }: { l: Lead; caps: Record<string, string>; onDone: (msg: string) => void }) {
  const [pool, setPool] = useState("founder");
  const [err, setErr] = useState<string | null>(null);
  const act = async (d: string) => {
    try { const r = await builderApi.decide(l.id, d, undefined, pool); onDone(d === "promote" ? `${l.display_name} added to Candidates (${r.candidate_id})` : `${l.display_name} dismissed`); }
    catch (e) { setErr((e as Error).message); }
  };
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-slate-900">{l.display_name}</span>
        <span className="chip bg-slate-100 text-slate-600">{SRC[l.source] || l.source}</span>
        {l.location ? <span className="text-xs text-slate-500">{l.location}</span> : <span className="text-xs text-amber-700">Location unknown</span>}
        {l.company && <span className="text-xs text-slate-500">· {l.company}</span>}
        {l.profile_url && <a href={l.profile_url} target="_blank" rel="noreferrer" className="text-xs text-brand-700 hover:underline"><ExternalLink className="inline h-3 w-3" /> profile</a>}
        <span className="ml-auto text-[11px] text-slate-400">first seen {l.first_seen.slice(0, 10)}</span>
      </div>
      <ul className="mt-2 space-y-1">
        {l.evidence.slice(0, 3).map((e) => (
          <li key={e.source_url} className="text-xs text-slate-700">
            <span className="chip mr-1 bg-brand-50 text-brand-700">{KIND[e.kind] || e.kind}</span>
            <a href={e.source_url} target="_blank" rel="noreferrer" className="hover:text-brand-700 hover:underline">{e.claim}</a>
            {e.source_date && <span className="text-slate-400"> · {e.source_date}</span>}
          </li>
        ))}
      </ul>
      {l.evidence.length > 3 && <div className="mt-1 text-[11px] text-slate-400">+{l.evidence.length - 3} more items</div>}
      <div className="mt-2 flex flex-wrap gap-1">{l.capability_ids.slice(0, 5).map((c) => <span key={c} className="chip bg-slate-100 text-slate-600">{caps[c] || c}</span>)}</div>
      <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-2">
        <select value={pool} onChange={(e) => setPool(e.target.value)} className="rounded-md border border-slate-300 px-1.5 py-1 text-xs">
          {POOLS.map(([v, lbl]) => <option key={v} value={v}>{lbl}</option>)}
        </select>
        <button className="btn-primary !px-2 !py-1 text-xs" onClick={() => act("promote")}><UserPlus className="h-3 w-3" /> Add to candidates</button>
        <button className="btn-ghost !px-2 !py-1 text-xs" onClick={() => act("dismiss")}><X className="h-3 w-3" /> Dismiss</button>
        {err && <span className="text-xs text-rose-600">{err}</span>}
      </div>
    </div>
  );
}

function Monitors({ o, caps, reload }: { o: BuilderOverview; caps: Record<string, string>; reload: () => Promise<void> }) {
  const [running, setRunning] = useState<string | null>(null);
  const [last, setLast] = useState<{ id: string; text: string; r: SourceReport } | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const { reload: reloadAnalysis } = useApp();
  const run = async (id: string) => {
    setRunning(id);
    try {
      const r = await builderApi.runMonitor(id);
      setLast({ id, text: `${r.new} new builders · ${r.builders} matched · ${r.items_found} public items scanned`, r: r.sources });
      await reload();
    } catch (e) { setLast({ id, text: (e as Error).message, r: {} }); } finally { setRunning(null); }
  };
  const leads = o.leads.filter((l) => !filter || l.monitor_id === filter);
  return (
    <div className="grid gap-5 lg:grid-cols-5">
      <Card className="lg:col-span-2" title="Monitors" subtitle={`Re-run every ${o.interval_hours}h automatically. Unreviewed leads are deleted after ${o.lead_ttl_days} days.`}>
        <div className="space-y-2">
          {o.monitors.map((m) => (
            <div key={m.id} className={clsx("rounded-lg border p-3", filter === m.id ? "border-brand-300 bg-brand-50/40" : "border-slate-200")}>
              <div className="flex items-start gap-2">
                <button onClick={() => setFilter(filter === m.id ? "" : m.id)} className="min-w-0 flex-1 text-left">
                  <div className="text-sm font-semibold text-slate-900">{m.name}</div>
                  <div className="text-[11px] text-slate-500">{caps[m.capability_id]} · {m.market ? MARKET_NAMES[m.market] : "All APAC"} · last run {ago(m.last_run_at)}</div>
                </button>
                <button className="btn-secondary !px-2 !py-1 text-xs" disabled={!!running} onClick={() => run(m.id)}>
                  <Play className={clsx("h-3 w-3", running === m.id && "animate-pulse")} /> {running === m.id ? "Running" : "Run"}
                </button>
              </div>
              <div className="mt-1 flex gap-3 text-[11px]">
                <span className="font-medium text-slate-700">{m.leads_open} to review</span>
                {m.leads_new_last_run > 0 && <span className="text-emerald-700">{m.leads_new_last_run} new last run</span>}
                {m.leads_promoted > 0 && <span className="text-slate-500">{m.leads_promoted} added</span>}
              </div>
              {last?.id === m.id && <div className="mt-2 space-y-1 text-[11px] text-slate-600"><div>{last.text}</div><SourceResult r={last.r} /></div>}
              <Details label="Searches" className="mt-1">
                <div className="space-y-0.5 text-[11px] text-slate-500">{Object.entries(m.queries).map(([k, v]) => <div key={k}><b>{SRC[k]}:</b> {v}</div>)}</div>
              </Details>
            </div>
          ))}
        </div>
      </Card>
      <Card className="lg:col-span-3" title={`Leads to review (${leads.length})`} subtitle="Builders found from public work. Suggestions only: nobody is contacted, and evidence enters unverified.">
        {flash && <div className="mb-2 rounded-md bg-emerald-50 px-3 py-2 text-xs text-emerald-800">{flash} · <Link to="/candidates" className="underline">open Candidates</Link></div>}
        <div className="space-y-2">
          {leads.map((l) => <LeadCard key={l.id} l={l} caps={caps} onDone={async (msg) => { setFlash(msg); await reload(); await reloadAnalysis(); }} />)}
          {!leads.length && <div className="text-sm text-slate-400">No leads yet. Run a monitor.</div>}
        </div>
      </Card>
    </div>
  );
}

function Investigate({ reload }: { reload: () => Promise<void> }) {
  const { analysis: a, reload: reloadAnalysis } = useApp();
  const [f, setF] = useState<Record<string, string>>({ candidate_id: "", display_name: "", market: "SG", pool_type: "founder" });
  const [links, setLinks] = useState("");
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<InvestigateResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const set = (k: string) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const go = async () => {
    setBusy(true); setErr(null); setRes(null);
    try {
      const body = { ...f, candidate_id: f.candidate_id || null, links: links.split(/\s+/).filter(Boolean) };
      setRes(await builderApi.investigate(body)); await reload(); await reloadAnalysis();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };
  const field = (k: string, label: string, ph: string) => (
    <label className="text-xs text-slate-600">{label}
      <input value={f[k] || ""} onChange={set(k)} placeholder={ph} className="mt-0.5 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
    </label>
  );
  return (
    <div className="grid gap-5 lg:grid-cols-5">
      <Card className="lg:col-span-3" title="Investigate a person" subtitle="Enter public handles. The agent collects what they built and attaches it as unverified evidence.">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-xs text-slate-600">Existing candidate
            <select value={f.candidate_id} onChange={set("candidate_id")} className="mt-0.5 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm">
              <option value="">New person</option>
              {a!.candidates.map((c) => <option key={c.id} value={c.id}>{c.display_name}</option>)}
            </select>
          </label>
          {!f.candidate_id && field("display_name", "Name", "e.g. Jane Tan")}
          {!f.candidate_id && (
            <div className="grid grid-cols-2 gap-2">
              <label className="text-xs text-slate-600">Market
                <select value={f.market} onChange={set("market")} className="mt-0.5 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm">
                  {Object.entries(MARKET_NAMES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-600">Pool
                <select value={f.pool_type} onChange={set("pool_type")} className="mt-0.5 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm">
                  {POOLS.map(([v, lbl]) => <option key={v} value={v}>{lbl}</option>)}
                </select>
              </label>
            </div>
          )}
          {field("github", "GitHub username", "repos, stars")}
          {field("hn", "Hacker News username", "Show HN launches")}
          {field("devto", "dev.to username", "technical writing")}
          {field("arxiv", "arXiv author name", "papers")}
          {field("huggingface", "Hugging Face user/org", "models & demo Spaces")}
          {field("npm", "npm username", "packages maintained")}
          {field("rss", "Blog RSS/Atom URL", "https://…/feed.xml")}
        </div>
        <label className="mt-3 block text-xs text-slate-600">Patent, launch or demo links (one per line)
          <textarea value={links} onChange={(e) => setLinks(e.target.value)} rows={3} placeholder="https://patents.google.com/patent/…&#10;https://www.producthunt.com/posts/…&#10;https://youtube.com/watch?v=…"
            className="mt-0.5 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
        </label>
        <div className="mt-3 flex items-center gap-2">
          <button className="btn-primary" onClick={go} disabled={busy}><Search className="h-4 w-4" /> {busy ? "Collecting…" : "Collect evidence"}</button>
          {err && <span className="text-xs text-rose-600">{err}</span>}
        </div>
      </Card>
      <Card className="lg:col-span-2" title="Result">
        {res ? (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-3 gap-2">
              <Stat label="Public items" value={res.items_found} />
              <Stat label="Mapped to capabilities" value={res.mapped} />
              <Stat label="Added (unverified)" value={res.added} />
            </div>
            <SourceResult r={res.sources} />
            {res.unmapped > 0 && <p className="text-xs text-slate-500">{res.unmapped} items didn't match any capability and were skipped.</p>}
            <Link to={`/candidates?c=${res.candidate_id}`} className="btn-secondary !py-1.5 text-xs">Review evidence in Candidates</Link>
          </div>
        ) : <p className="text-sm text-slate-500">Nothing collected yet.</p>}
      </Card>
    </div>
  );
}

export default function Builders() {
  const { meta } = useApp();
  const [o, setO] = useState<BuilderOverview | null>(null);
  const [tab, setTab] = useState<"monitors" | "investigate">("monitors");
  const reload = useCallback(async () => setO(await builderApi.overview()), []);
  useEffect(() => { reload(); }, [reload]);
  if (!o) return <div className="text-sm text-slate-500">Loading…</div>;
  const caps = Object.fromEntries((meta!.capabilities || []).map((c) => [c.id, c.name]));
  const fresh = o.monitors.reduce((n, m) => n + m.leads_new_last_run, 0);
  const off = Object.entries(o.sources).filter(([, v]) => !v.ready || v.note);
  return (
    <div className="space-y-5">
      <PageHeader letter="G" title="Builder Evidence" question="Find people by what they have built, not their job title." />
      <Takeaway title={`${o.leads.length} builders to review${fresh ? `, ${fresh} new since the last runs` : ""}`}>
        Evidence comes from GitHub, Show HN launches, dev.to, arXiv, Hugging Face, npm, blogs and pasted patent or demo links.
      </Takeaway>
      <div className="grid gap-3 sm:grid-cols-4">
        <Stat label="Monitors" value={o.monitors.length} />
        <Stat label="Leads to review" value={o.leads.length} />
        <Stat label="Added to candidates" value={o.monitors.reduce((n, m) => n + m.leads_promoted, 0)} />
        <Stat label="Last run" value={<span className="text-base">{ago(o.runs[0]?.at || null)}</span>} />
      </div>
      {off.length > 0 && (
        <Details label="Source limits">
          <ul className="space-y-0.5 text-xs text-slate-600">{off.map(([k, v]) => <li key={k}><b>{SRC[k] || k.replace("_", " ")}:</b> {v.note}</li>)}</ul>
        </Details>
      )}
      <Tabs value={tab} onChange={setTab} tabs={[{ id: "monitors", label: "Discovery monitoring" }, { id: "investigate", label: "Investigate a person" }]} />
      {tab === "monitors" ? <Monitors o={o} caps={caps} reload={reload} /> : <Investigate reload={reload} />}
    </div>
  );
}
