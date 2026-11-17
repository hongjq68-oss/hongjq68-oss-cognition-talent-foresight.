import { useSearchParams } from "react-router-dom";
import { Link } from "react-router-dom";
import { useApp } from "../state";
import { Bar, Card, List, PoolBadge, Sensitivity, Takeaway } from "../components/ui";
import { NextStep, RolePicker, StepHeader, WhenChip, heatLabel } from "../components/journey";

export default function WhereToHire() {
  const { analysis: a } = useApp();
  const j = a!.journey;
  const [sp, setSp] = useSearchParams();
  const sel = j.hires.find((h) => h.archetype_id === sp.get("role")) || j.hires[0];
  const top = sel.where[0];
  return (
    <div className="space-y-5">
      <StepHeader step={3} title="Where to hire" question="The best countries for each key hire, and where these people work today." />
      <RolePicker hires={j.hires} value={sel.archetype_id} onChange={(id) => setSp({ role: id })} />
      <Takeaway title={`${sel.name}: hire in ${sel.where.slice(0, 2).map((w) => w.name).join(" and ")} first`}>
        {top?.name} has {heatLabel(top?.supply ?? 0).toLowerCase()} talent and matters most to the goal. Look in: {sel.areas.map((x) => x.label).join(", ")}.
      </Takeaway>
      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="Best countries" subtitle="Goal priority and talent depth combined" right={<WhenChip w={sel.when} />}>
          <div className="space-y-3">
            {sel.where.map((w, i) => (
              <div key={w.market}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-slate-800">{i + 1}. {w.name}</span>
                  <span className="text-xs text-slate-500">{heatLabel(w.supply)} talent{w.open_roles ? ` · ${w.open_roles} open` : ""}</span>
                </div>
                <Bar value={w.priority} className={i === 0 ? "bg-brand-600" : "bg-brand-300"} />
              </div>
            ))}
          </div>
        </Card>
        <Card title="Companies to look at" subtitle="Where people with these skills work today" className="lg:col-span-2">
          <div className="grid gap-2 sm:grid-cols-2">
            {sel.companies.map((o) => (
              <div key={o.name} className="rounded-lg border border-slate-200 p-2.5">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-sm font-medium text-slate-900">{o.name}</span>
                  <PoolBadge p={o.pool_type} />
                  <Sensitivity s={o.sensitivity} note={null} />
                </div>
                <div className="mt-0.5 text-xs text-slate-500">{o.market && `${o.local ? "" : "Regional · "}${o.market}`}{o.teams.length ? ` · Teams: ${o.teams.join(", ")}` : ""}</div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">Red tags mean a Cognition customer, partner or competitor: agree an approach before contacting their staff.</p>
        </Card>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <Card title="Areas to search">
          <List items={sel.areas.map((x) => x.label)} />
        </Card>
        <Card title="Also consider" subtitle="Less obvious backgrounds that often work">
          <List items={sel.also_consider} />
        </Card>
      </div>
      <div className="flex items-center justify-between">
        <Link to="/strategy" className="text-xs font-medium text-brand-700 hover:underline">Full sourcing playbook and search strings →</Link>
        <NextStep step={3} />
      </div>
    </div>
  );
}
