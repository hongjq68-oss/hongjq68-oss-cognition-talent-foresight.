import { Fragment, useState } from "react";
import clsx from "clsx";
import { useApp } from "../state";
import { CLASSIFICATION, ClassBadge, Card, EvidenceBadge, PageHeader, Takeaway } from "../components/ui";
import type { Capability, Classification, Horizon } from "../types";

const H: Horizon[] = ["now", "6m", "12m", "24m"];
const CATS = ["all", "technical", "commercial", "delivery", "transformation", "entrepreneurial"];

function heat(v: number) {
  if (v >= 80) return "bg-brand-700 text-white";
  if (v >= 60) return "bg-brand-500 text-white";
  if (v >= 40) return "bg-brand-300 text-ink-900";
  if (v >= 20) return "bg-brand-100 text-ink-900";
  return "bg-slate-50 text-slate-400";
}

function Detail({ c }: { c: Capability }) {
  return (
    <div className="grid gap-4 bg-slate-50 p-4 text-sm md:grid-cols-3">
      <div>
        <div className="label">What it means</div>
        <p className="text-slate-600">{c.description}</p>
        <div className="mt-2 text-xs text-slate-500">Need by <b>{c.need_by || "—"}</b> · scarcity {c.scarcity}/5 · ~{c.lead_weeks} wks to hire · tends to be {c.delivery_tendency}</div>
      </div>
      <div>
        <div className="label">Why</div>
        <ul className="space-y-1">
          {c.drivers.map((d) => (
            <li key={d.type + d.id} className="flex justify-between gap-2 text-slate-600">
              <span><span className="chip mr-1 bg-white text-slate-500 ring-1 ring-slate-200">{d.type}</span>{d.label}</span>
              <span className="text-xs text-slate-400">+{d.contribution}</span>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <div className="label capitalize">{c.confidence} confidence</div>
        <ul className="list-disc space-y-1 pl-4 text-slate-600">{c.confidence_factors.map((f) => <li key={f}>{f}</li>)}</ul>
      </div>
    </div>
  );
}

export default function Forecast() {
  const { analysis: a } = useApp();
  const [cat, setCat] = useState("all");
  const [cls, setCls] = useState<Classification | "all">("all");
  const [open, setOpen] = useState<string | null>(null);
  const caps = a!.capabilities.filter((c) => (cat === "all" || c.category === cat) && (cls === "all" || c.classification === cls));
  const counts = a!.capabilities.reduce<Record<string, number>>((m, c) => ({ ...m, [c.classification]: (m[c.classification] || 0) + 1 }), {});
  const today = new Date().toISOString().slice(0, 10);
  const now = a!.capabilities.filter((c) => c.classification === "immediate").sort((x, y) => (x.start_search_by || "").localeCompare(y.start_search_by || ""));
  const late = now.filter((c) => c.start_search_by && c.start_search_by < today).length;
  return (
    <div className="space-y-5">
      <PageHeader letter="C" title="Capability Forecast" question="What skills will we need, and when?">
        <EvidenceBadge c="prediction" />
      </PageHeader>
      <Takeaway title={`Hire for ${now.length} capabilities now${late ? `: ${late} searches are already late` : ""}.`}>
        {counts.emerging || 0} more are emerging within 12 months, and {counts.strategic || 0} are longer-term bets.
      </Takeaway>
      {now.length > 0 && (
        <div className="grid gap-3 md:grid-cols-3">
          {now.slice(0, 3).map((c) => (
            <button key={c.id} onClick={() => setOpen(c.id)} className="card p-4 text-left hover:ring-2 hover:ring-brand-300">
              <div className="text-sm font-semibold text-slate-900">{c.name}</div>
              <div className={clsx("mt-1 text-xs", c.start_search_by && c.start_search_by < today ? "font-semibold text-rose-700" : "text-slate-500")}>
                Start search by {c.start_search_by}{c.start_search_by && c.start_search_by < today ? " (late)" : ""}
              </div>
              <div className="mt-1 text-xs text-slate-500">~{c.lead_weeks} weeks to hire · {c.confidence} confidence</div>
            </button>
          ))}
        </div>
      )}
      <div className="grid gap-3 md:grid-cols-5">
        {(Object.keys(CLASSIFICATION) as Classification[]).map((k) => (
          <button key={k} onClick={() => setCls(cls === k ? "all" : k)} className={clsx("card p-3 text-left transition", cls === k && "ring-2 ring-brand-500")}>
            <ClassBadge c={k} />
            <div className="mt-2 text-2xl font-semibold">{counts[k] || 0}</div>
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {CATS.map((c) => (
          <button key={c} onClick={() => setCat(c)} className={clsx("btn !py-1.5 capitalize", cat === c ? "bg-ink-900 text-white" : "btn-secondary")}>{c}</button>
        ))}
      </div>
      <Card title="Demand heatmap" subtitle="Demand 0–100 over time. Click a row to see why.">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="py-2">Capability</th>
              {H.map((h) => <th key={h} className="w-16 text-center">{h}</th>)}
              <th className="pl-3">Forecast</th><th>Start search</th>
            </tr>
          </thead>
          <tbody>
            {caps.map((c) => (
              <Fragment key={c.id}>
                <tr onClick={() => setOpen(open === c.id ? null : c.id)} className="cursor-pointer border-t border-slate-100 hover:bg-slate-50">
                  <td className="py-2 font-medium text-slate-800">{c.name}<div className="text-[11px] font-normal capitalize text-slate-400">{c.category}</div></td>
                  {H.map((h) => <td key={h} className="px-0.5"><div className={clsx("rounded py-1 text-center text-xs font-medium", heat(c.demand[h]))}>{Math.round(c.demand[h])}</div></td>)}
                  <td className="pl-3"><ClassBadge c={c.classification} /></td>
                  <td className={clsx("whitespace-nowrap", c.start_search_by && c.start_search_by < today ? "font-semibold text-rose-700" : "text-slate-600")}>{c.start_search_by || "—"}</td>
                </tr>
                {open === c.id && <tr><td colSpan={7}><Detail c={c} /></td></tr>}
              </Fragment>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
