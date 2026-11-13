import { Fragment, useState } from "react";
import clsx from "clsx";
import { useApp } from "../state";
import { CLASSIFICATION, ClassBadge, Card, EvidenceBadge, PageHeader } from "../components/ui";
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
        <div className="mt-2 text-xs text-slate-500">Delivery tendency: <b>{c.delivery_tendency}</b> · scarcity {c.scarcity}/5 · lead time ~{c.lead_weeks} wks</div>
      </div>
      <div>
        <div className="label">Why the engine predicts this</div>
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
        <div className="label">Confidence: {c.confidence}</div>
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
  return (
    <div className="space-y-6">
      <PageHeader letter="C" title="Capability Forecast" question="Which capabilities will the business need — now, in 6, 12 and 24 months?">
        <EvidenceBadge c="prediction" />
      </PageHeader>
      <div className="grid gap-3 md:grid-cols-5">
        {(Object.keys(CLASSIFICATION) as Classification[]).map((k) => (
          <button key={k} onClick={() => setCls(cls === k ? "all" : k)} className={clsx("card p-3 text-left transition", cls === k && "ring-2 ring-brand-500")}>
            <ClassBadge c={k} />
            <div className="mt-2 text-2xl font-semibold">{counts[k] || 0}</div>
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        {CATS.map((c) => (
          <button key={c} onClick={() => setCat(c)} className={clsx("btn !py-1.5 capitalize", cat === c ? "bg-ink-900 text-white" : "btn-secondary")}>{c}</button>
        ))}
      </div>
      <Card title="Demand heatmap" subtitle="Relative demand (0–100) by horizon. Click a row for the reasoning. Start-search date = need-by date − estimated lead time; red = already past, so the search is late.">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="py-2">Capability</th><th>Category</th>
              {H.map((h) => <th key={h} className="w-16 text-center">{h}</th>)}
              <th>Forecast</th><th>Need by</th><th>Start search by</th><th>Conf.</th>
            </tr>
          </thead>
          <tbody>
            {caps.map((c) => (
              <Fragment key={c.id}>
                <tr onClick={() => setOpen(open === c.id ? null : c.id)} className="cursor-pointer border-t border-slate-100 hover:bg-slate-50">
                  <td className="py-2 font-medium text-slate-800">{c.name}</td>
                  <td className="capitalize text-slate-500">{c.category}</td>
                  {H.map((h) => <td key={h} className="px-0.5"><div className={clsx("rounded py-1 text-center text-xs font-medium", heat(c.demand[h]))}>{Math.round(c.demand[h])}</div></td>)}
                  <td><ClassBadge c={c.classification} /></td>
                  <td className="text-slate-600">{c.need_by || "—"}</td>
                  <td className={clsx(c.classification === "immediate" ? "font-semibold text-rose-700" : "text-slate-600")}>{c.start_search_by || "—"}</td>
                  <td className="capitalize text-slate-600">{c.confidence}</td>
                </tr>
                {open === c.id && <tr><td colSpan={10}><Detail c={c} /></td></tr>}
              </Fragment>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
