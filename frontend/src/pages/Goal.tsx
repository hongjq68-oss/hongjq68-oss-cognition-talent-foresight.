import clsx from "clsx";
import { Target } from "lucide-react";
import { useApp } from "../state";
import { Card, Cite, Details, List, Stat, Takeaway } from "../components/ui";
import { NextStep, StepHeader } from "../components/journey";

export default function Goal() {
  const { analysis: a, meta, overrides, setScenario } = useApp();
  const j = a!.journey;
  const now = j.hires.filter((h) => h.when.tone === "now");
  const open = j.hires.reduce((n, h) => n + h.open_roles, 0);
  return (
    <div className="space-y-5">
      <StepHeader step={1} title="Business goal" question="Start with what the business wants to achieve. Everything else follows from it." />
      <div className="grid gap-2 md:grid-cols-3">
        {meta!.scenarios.map((s) => (
          <button key={s.id} onClick={() => setScenario(s.id)}
            className={clsx("card flex items-start gap-2 p-3 text-left text-sm transition",
              overrides.scenario_id === s.id ? "ring-2 ring-brand-600" : "hover:ring-1 hover:ring-slate-300")}>
            <Target className={clsx("mt-0.5 h-4 w-4 shrink-0", overrides.scenario_id === s.id ? "text-brand-600" : "text-slate-400")} />
            <span className="font-medium text-slate-800">{s.goal}</span>
          </button>
        ))}
      </div>
      <Takeaway title={j.goal.title}>
        To hit this goal we need {j.hires.length} key hires. {now.length} of them should start now.
      </Takeaway>
      <div className="grid gap-3 md:grid-cols-4">
        <Stat label="Key hires" value={j.hires.length} hint="Roles that move the goal" />
        <Stat label="Start now" value={now.length} hint={now.length ? `First: ${now[0].name}` : "Nothing urgent"} />
        <Stat label="Open roles today" value={open} hint="Live on Cognition's job board" />
        <Stat label="Focus countries" value={j.goal.top_markets.length} hint={j.goal.top_markets.join(", ")} />
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <Card title="What success looks like">
          <List items={j.goal.outcomes} />
        </Card>
        <Card title="Customer problems we must solve">
          <List items={j.goal.customer_problems} />
        </Card>
      </div>
      <Card title="Why we think this">
        <p className="text-sm text-slate-600">{j.goal.story}</p>
        <div className="mt-3 space-y-1">
          {a!.radar.drivers.slice(0, 3).map((s) => <div key={s.id}><Cite c={s} /></div>)}
        </div>
        <Details className="mt-3" label="What changes in the business, and the risks">
          <div className="grid gap-4 md:grid-cols-2">
            <div><div className="label">What changes</div><List items={j.goal.what_changes} /></div>
            <div><div className="label">Risks if we hire late</div><List items={j.goal.risks} /></div>
          </div>
        </Details>
      </Card>
      <NextStep step={1} />
    </div>
  );
}
