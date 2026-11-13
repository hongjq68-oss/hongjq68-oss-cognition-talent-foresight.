import { useEffect, useState } from "react";
import { useApp } from "../state";
import { api } from "../api";
import { Card, ClassBadge, Details, EvidenceBadge, List, MARKET_NAMES, PageHeader, Takeaway } from "../components/ui";
import type { Analysis } from "../types";

function Slider({ label, value, onChange, max = 1, step = 0.05 }: { label: string; value: number; onChange: (v: number) => void; max?: number; step?: number }) {
  return (
    <label className="block">
      <div className="flex justify-between text-xs text-slate-600"><span>{label}</span><span className="font-mono">{value.toFixed(2)}</span></div>
      <input type="range" min={0} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-brand-600" />
    </label>
  );
}

export default function Planner() {
  const { analysis: a, meta, setOverrides, overrides } = useApp();
  const base = a!.scenario;
  const [name, setName] = useState(base.name);
  const [segW, setSegW] = useState<Record<string, number>>({});
  const [mktW, setMktW] = useState<Record<string, number>>({});
  const [baseline, setBaseline] = useState<Analysis | null>(null);

  useEffect(() => {
    setSegW(Object.fromEntries(meta!.segments.map((s) => [s.id, base.segment_weights[s.id] || 0])));
    setMktW(Object.fromEntries(meta!.markets.map((m) => [m, base.market_weights[m] || 0])));
    setName(base.name);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base]);

  useEffect(() => {
    const id = overrides.scenario_id;
    if (id) api.analysis({ scenario_id: id }).then(setBaseline);
  }, [overrides.scenario_id]);

  const apply = () => setOverrides({ scenario_id: overrides.scenario_id, name: name === base.name ? `${base.name} (adjusted)` : name, segment_weights: segW, market_weights: mktW });
  const b = Object.fromEntries((baseline?.capabilities || []).map((c) => [c.id, c]));
  const deltas = a!.capabilities.map((c) => ({ c, d: c.peak - (b[c.id]?.peak ?? 0), was: b[c.id]?.classification })).filter((x) => Math.abs(x.d) > 0.5 || (x.was && x.was !== x.c.classification)).sort((x, y) => Math.abs(y.d) - Math.abs(x.d)).slice(0, 10);
  const up = deltas.filter((x) => x.d > 0.5).length, down = deltas.filter((x) => x.d < -0.5).length;

  return (
    <div className="space-y-5">
      <PageHeader title="Scenario Planner" question="Move the sliders to see how hiring needs change."><EvidenceBadge c="hypothesis" /></PageHeader>
      <Takeaway title={deltas.length ? `Your changes move ${deltas.length} capabilities: ${up} up, ${down} down.` : "No changes yet. Adjust the sliders, then click Recompute."} />
      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Adjust the scenario" subtitle="0 = ignore · 1 = full focus">
          <label className="label">Scenario name</label>
          <input className="input mb-4" value={name} onChange={(e) => setName(e.target.value)} />
          <div className="label">Customer segments</div>
          <div className="space-y-2">{meta!.segments.map((s) => <Slider key={s.id} label={s.name} value={segW[s.id] || 0} onChange={(v) => setSegW({ ...segW, [s.id]: v })} />)}</div>
          <div className="label mt-4">Markets</div>
          <div className="space-y-2">{meta!.markets.map((m) => <Slider key={m} label={MARKET_NAMES[m]} value={mktW[m] || 0} onChange={(v) => setMktW({ ...mktW, [m]: v })} />)}</div>
          <button className="btn-primary mt-5 w-full" onClick={apply}>Recompute forecast</button>
        </Card>
        <div className="space-y-6 lg:col-span-2">
          <Card title={a!.scenario.name} subtitle={a!.scenario.hypothesis}>
            <Details label="Risks, alternatives and assumptions">
            <div className="grid gap-4 md:grid-cols-3">
              <div><div className="label">Business changes</div><List items={a!.scenario.business_changes} /></div>
              <div><div className="label">What could derail it</div><List items={a!.scenario.derailers} /></div>
              <div><div className="label">Alternative talent strategies</div><List items={a!.scenario.alternatives} /></div>
            </div>
            {a!.scenario.assumptions.length > 0 && <div className="mt-4"><div className="label">Assumptions</div><List items={a!.scenario.assumptions} /></div>}
            </Details>
          </Card>
          <Card title="What changed vs the preset">
            {deltas.length === 0 ? <div className="text-sm text-slate-500">Nothing yet.</div> : <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500"><th className="py-1">Capability</th><th>Demand</th><th>Change</th><th>Forecast</th><th>Start search</th></tr></thead>
              <tbody>
                {deltas.map(({ c, d, was }) => (
                  <tr key={c.id} className="border-t border-slate-100">
                    <td className="py-1.5">{c.name}</td><td>{c.peak.toFixed(0)}</td>
                    <td className={d > 0.5 ? "text-emerald-700" : d < -0.5 ? "text-rose-700" : "text-slate-400"}>{d > 0 ? "+" : ""}{d.toFixed(1)}</td>
                    <td><ClassBadge c={c.classification} />{was && was !== c.classification && <span className="ml-1 text-[11px] text-slate-400">was {was}</span>}</td>
                    <td className="text-slate-600">{c.start_search_by || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>}
          </Card>
        </div>
      </div>
    </div>
  );
}
