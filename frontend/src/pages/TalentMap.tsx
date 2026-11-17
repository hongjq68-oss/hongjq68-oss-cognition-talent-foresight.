import clsx from "clsx";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../state";
import { Card, PoolBadge, Sensitivity, Takeaway } from "../components/ui";
import { NextStep, StepHeader, heatClass, heatLabel } from "../components/journey";

export default function TalentMap() {
  const { analysis: a } = useApp();
  const m = a!.journey.map;
  const best = m.rows.flatMap((r) => r.cells.filter((c) => c.goal_weight > 0).map((c) => ({ r, c, p: c.supply * (0.5 + 0.5 * c.goal_weight) })))
    .sort((x, y) => y.p - x.p)[0];
  const [sel, setSel] = useState<{ role: string; market: string }>({ role: best?.r.archetype_id || m.rows[0].archetype_id, market: best?.c.market || "SG" });
  const row = m.rows.find((r) => r.archetype_id === sel.role)!;
  const cell = row.cells.find((c) => c.market === sel.market)!;
  const mkt = m.markets.find((x) => x.id === sel.market)!;
  return (
    <div className="space-y-5">
      <StepHeader step={4} title="Talent map" question="Where these people sit today, by role type and country. Darker means more talent." />
      {best && (
        <Takeaway title={`Richest spot for the goal: ${best.r.name} in ${m.markets.find((x) => x.id === best.c.market)?.name}`}>
          Click any square to see the companies and areas to look at.
        </Takeaway>
      )}
      <div className="grid gap-5 lg:grid-cols-5">
        <Card className="lg:col-span-3 overflow-x-auto">
          <table className="w-full border-separate border-spacing-1 text-sm">
            <thead>
              <tr>
                <th className="text-left text-xs font-medium text-slate-500">Role type</th>
                {m.markets.map((x) => (
                  <th key={x.id} className="text-center text-xs font-medium text-slate-600">
                    {x.name}
                    <div className="text-[10px] font-normal text-slate-400">{x.goal_weight >= 0.8 ? "★ goal focus" : x.goal_weight > 0 ? "in goal" : "not in goal"}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {m.rows.map((r) => (
                <tr key={r.archetype_id}>
                  <td className="max-w-[12rem] pr-2 text-xs font-medium text-slate-700">{r.name}</td>
                  {r.cells.map((c) => (
                    <td key={c.market}>
                      <button onClick={() => setSel({ role: r.archetype_id, market: c.market })}
                        className={clsx("h-14 w-full rounded-md text-xs font-semibold transition", heatClass(c.supply),
                          c.goal_weight === 0 && "opacity-40",
                          sel.role === r.archetype_id && sel.market === c.market && "ring-2 ring-ink-900 ring-offset-1")}>
                        {heatLabel(c.supply)}
                        {c.in_pipeline > 0 && <div className="text-[10px] font-normal opacity-80">{c.in_pipeline} in pipeline</div>}
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
            {[90, 75, 55, 35, 10].map((v) => <span key={v} className="flex items-center gap-1"><span className={clsx("h-3 w-3 rounded", heatClass(v))} />{heatLabel(v)}</span>)}
            <span className="ml-2">Faded = country not part of this goal</span>
          </div>
        </Card>
        <Card className="lg:col-span-2" title={`${row.name} · ${mkt.name}`} subtitle={`${heatLabel(cell.supply)} talent · ${cell.in_pipeline} already in our pipeline`}>
          <div className="label">Where they sit</div>
          <div className="mb-3 flex flex-wrap gap-1.5">
            {cell.areas.map((x) => <span key={x.pool_type} className="chip bg-slate-100 text-slate-700">{x.label} · {x.count}</span>)}
          </div>
          <div className="label">Companies to look at</div>
          <div className="space-y-1.5">
            {cell.companies.map((o) => (
              <div key={o.name} className="flex flex-wrap items-center gap-1.5 text-sm">
                <span className="text-slate-800">{o.name}</span>
                <PoolBadge p={o.pool_type} />
                {!o.local && <span className="text-[11px] text-slate-400">regional</span>}
                <Sensitivity s={o.sensitivity} note={null} />
              </div>
            ))}
            {!cell.companies.length && <div className="text-sm text-slate-500">No known companies here yet.</div>}
          </div>
          <Link to={`/shortlist?role=${row.archetype_id}`} className="mt-4 inline-block text-xs font-medium text-brand-700 hover:underline">See shortlist for this role →</Link>
        </Card>
      </div>
      <p className="text-xs text-slate-500">Talent depth is estimated from the companies in each country that build these skills (market insight, not a headcount).</p>
      <NextStep step={4} />
    </div>
  );
}
