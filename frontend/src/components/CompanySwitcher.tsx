import { useEffect, useState } from "react";
import { Building2, Plus, X } from "lucide-react";
import { api } from "../api";
import { useApp } from "../state";
import type { Company } from "../types";

export function CompanySwitcher() {
  const { company, setCompany } = useApp();
  const [list, setList] = useState<Company[]>([]);
  const [open, setOpen] = useState(false);
  const load = () => api.companies().then(setList).catch(() => setList([]));
  useEffect(() => { load(); }, [company]);
  return (
    <div className="flex items-center gap-2">
      <Building2 className="h-4 w-4 text-slate-400" />
      <select className="input !w-auto" value={company} aria-label="Company"
        onChange={(e) => (e.target.value === "__add" ? setOpen(true) : setCompany(e.target.value))}>
        {list.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        <option value="__add">+ Add a company…</option>
      </select>
      {open && <AddCompany onClose={() => setOpen(false)} onDone={(id) => { setOpen(false); load(); setCompany(id); }} />}
    </div>
  );
}

function AddCompany({ onClose, onDone }: { onClose: () => void; onDone: (id: string) => void }) {
  const [f, setF] = useState({ name: "", website: "", careers_url: "", blog_url: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [done, setDone] = useState<Awaited<ReturnType<typeof api.addCompany>> | null>(null);
  const submit = async () => {
    setBusy(true); setErr(null);
    try {
      setDone(await api.addCompany(Object.fromEntries(Object.entries(f).filter(([, v]) => v.trim())) as typeof f));
    } catch (e) { setErr(String((e as Error).message || e)); } finally { setBusy(false); }
  };
  const field = (k: keyof typeof f, label: string, ph: string) => (
    <label className="block">
      <span className="label">{label}</span>
      <input className="input mt-1" value={f[k]} placeholder={ph} onChange={(e) => setF({ ...f, [k]: e.target.value })} />
    </label>
  );
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-ink-900/40 p-4" role="dialog" aria-label="Add a company">
      <div className="card w-full max-w-lg space-y-4 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Add a company</h2>
            <p className="text-sm text-slate-500">We read its public careers board, blog and news, then build the same 5-step hiring plan.</p>
          </div>
          <button className="text-slate-400 hover:text-slate-600" onClick={onClose} aria-label="Close"><X className="h-5 w-5" /></button>
        </div>
        {!done ? <>
          {field("name", "Company name", "e.g. Canva")}
          {field("website", "Website (optional)", "canva.com")}
          {field("careers_url", "Careers page (optional)", "jobs.ashbyhq.com/… or boards.greenhouse.io/…")}
          {field("blog_url", "Blog / news RSS feed (optional)", "canva.com/newsroom/rss")}
          <p className="text-xs text-slate-500">Public sources only: Ashby, Greenhouse, Lever and SmartRecruiters job boards, the company's own feed, Hacker News and Wikipedia.</p>
          {err && <p className="text-sm text-rose-600">{err}</p>}
          <div className="flex justify-end gap-2">
            <button className="btn-secondary" onClick={onClose}>Cancel</button>
            <button className="btn-primary" disabled={busy || !f.name.trim()} onClick={submit}>
              <Plus className="h-4 w-4" /> {busy ? "Reading public sources… (up to a minute)" : "Build hiring plan"}
            </button>
          </div>
        </> : <>
          <div className="grid grid-cols-3 gap-3 text-center">
            {[["Open jobs", done.jobs], ["In APAC", done.apac_jobs], ["News & posts", done.signals]].map(([l, v]) => (
              <div key={l} className="rounded-lg bg-slate-50 p-3"><div className="text-2xl font-semibold">{v}</div><div className="text-xs text-slate-500">{l}</div></div>
            ))}
          </div>
          <p className="text-sm">{done.goals} business goals suggested for {done.name}.</p>
          {done.gaps.length > 0 && <ul className="list-disc space-y-1 pl-5 text-sm text-amber-700">{done.gaps.map((g) => <li key={g}>{g}</li>)}</ul>}
          <div className="flex justify-end"><button className="btn-primary" onClick={() => onDone(done.id)}>Open {done.name}'s plan</button></div>
        </>}
      </div>
    </div>
  );
}
