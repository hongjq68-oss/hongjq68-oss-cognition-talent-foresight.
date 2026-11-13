import { Briefcase } from "lucide-react";
import { useApp } from "../state";
import { Card, Cite, Details, EvidenceBadge, MARKET_NAMES, PageHeader, Stat, List, Takeaway, useShowMore } from "../components/ui";
import type { Signal } from "../types";

function SignalRow({ s }: { s: Signal }) {
  return (
    <div className="border-b border-slate-100 py-2.5 last:border-0">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1 text-sm font-medium text-slate-900">{s.title}</div>
        <span className="shrink-0 text-xs text-slate-400">{s.date || "undated"}</span>
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <span className="chip bg-slate-100 text-slate-600 capitalize">{s.kind}</span>
        <EvidenceBadge c={s.evidence_class} />
        <Details label="Summary"><p className="text-sm text-slate-600">{s.summary}</p><div className="mt-1"><Cite c={s} /></div></Details>
      </div>
    </div>
  );
}

export default function Radar() {
  const { analysis: a } = useApp();
  const h = a!.radar.hiring;
  const sc = a!.scenario;
  const [drivers, moreDrivers] = useShowMore(a!.radar.drivers, 8);
  const [related, moreRelated] = useShowMore(a!.radar.related, 4);
  const roles = Object.values(h.by_archetype).flat().filter((r, i, arr) => arr.findIndex((x) => x.url === r.url) === i);
  const [shownRoles, moreRoles] = useShowMore(roles, 5);
  const topMarkets = Object.entries(sc.market_weights).sort((x, y) => y[1] - x[1]).filter(([, w]) => w > 0).slice(0, 3).map(([m]) => MARKET_NAMES[m] || m);
  return (
    <div className="space-y-5">
      <PageHeader letter="A" title="Growth Radar" question="Where is Cognition heading, and what's the evidence?" />
      <Takeaway title={`${a!.radar.drivers.length} public signals point to growth in ${topMarkets.join(", ")}.`}>
        Cognition already has {h.in_scenario_markets} open roles in these markets. Scenario: {sc.name} <span className="text-slate-400">(a hypothesis, not a stated plan)</span>
      </Takeaway>
      <div className="grid gap-3 md:grid-cols-4">
        <Stat label="Supporting signals" value={a!.radar.drivers.length} />
        <Stat label="Open roles (all)" value={h.total_open_roles} />
        <Stat label="Open roles in focus markets" value={h.in_scenario_markets} />
        <Stat label="Role types already hiring" value={Object.keys(h.by_archetype).length} />
      </div>
      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2" title="Signals behind this scenario" right={<Details label="What would change"><List items={sc.business_changes} /></Details>}>
          {drivers.map((s) => <SignalRow key={s.id} s={s} />)}
          {moreDrivers}
        </Card>
        <div className="space-y-5">
          <Card title="Open roles in focus markets" right={<EvidenceBadge c="verified_fact" />}>
            <div className="space-y-1 text-sm">
              {Object.entries(h.by_department).sort((x, y) => y[1] - x[1]).slice(0, 5).map(([d, n]) => (
                <div key={d} className="flex justify-between"><span className="text-slate-600">{d}</span><span className="font-medium">{n}</span></div>
              ))}
            </div>
            <div className="mt-3 space-y-1">
              {shownRoles.map((r) => (
                <a key={r.url} href={r.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-xs text-brand-700 hover:underline">
                  <Briefcase className="h-3 w-3 shrink-0" /> <span className="truncate">{r.title}</span> <span className="text-slate-400">· {r.market}</span>
                </a>
              ))}
              {moreRoles}
            </div>
            <div className="mt-3"><Cite c={h.source} /></div>
          </Card>
          <Card title="Related signals">
            {related.map((s) => <SignalRow key={s.id} s={s} />)}
            {moreRelated}
          </Card>
        </div>
      </div>
    </div>
  );
}
