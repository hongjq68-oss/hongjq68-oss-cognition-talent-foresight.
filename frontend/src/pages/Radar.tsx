import { Briefcase } from "lucide-react";
import { useApp } from "../state";
import { Card, Cite, EvidenceBadge, MARKET_NAMES, PageHeader, Stat, List } from "../components/ui";
import type { Signal } from "../types";

function SignalRow({ s }: { s: Signal }) {
  return (
    <div className="border-b border-slate-100 py-3 last:border-0">
      <div className="flex items-center gap-2">
        <span className="chip bg-slate-100 text-slate-600 capitalize">{s.kind}</span>
        <EvidenceBadge c={s.evidence_class} />
        <span className="ml-auto text-xs text-slate-400">{s.date || "undated"}</span>
      </div>
      <div className="mt-1.5 text-sm font-medium text-slate-900">{s.title}</div>
      <p className="mt-0.5 text-sm text-slate-600">{s.summary}</p>
      <div className="mt-1"><Cite c={s} /></div>
    </div>
  );
}

export default function Radar() {
  const { analysis: a } = useApp();
  if (!a) return null;
  const h = a.radar.hiring;
  const sc = a.scenario;
  return (
    <div className="space-y-6">
      <PageHeader letter="A" title="Business Growth Radar" question="Where is Cognition going, and what evidence says so?" />
      <Card title={sc.name} subtitle="Scenario hypothesis — a planning assumption, not a statement of Cognition's plans" right={<EvidenceBadge c="hypothesis" />}>
        <p className="text-sm text-slate-700">{sc.hypothesis}</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div><div className="label">What would change in the business</div><List items={sc.business_changes} /></div>
          <div><div className="label">Market weighting</div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(sc.market_weights).sort((x, y) => y[1] - x[1]).map(([m, w]) => (
                <span key={m} className="chip bg-brand-50 text-brand-700">{MARKET_NAMES[m] || m} · {w}</span>
              ))}
            </div>
          </div>
        </div>
      </Card>
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Driving public signals" value={a.radar.drivers.length} hint="Dated, linked Cognition sources" />
        <Stat label="Open Cognition roles (all)" value={h.total_open_roles} hint={`Ashby, retrieved ${h.source.date}`} />
        <Stat label="Open roles in scenario markets" value={h.in_scenario_markets} hint={Object.entries(h.by_market).map(([m, n]) => `${m} ${n}`).join(" · ")} />
        <Stat label="Archetypes Cognition is already hiring" value={Object.keys(h.by_archetype).length} hint="Hiring signal → demand now" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2" title="Signals driving this scenario" subtitle="Products, customers, partnerships, expansion, funding — paraphrased from the linked source">
          {a.radar.drivers.map((s) => <SignalRow key={s.id} s={s} />)}
        </Card>
        <div className="space-y-6">
          <Card title="Hiring signals" subtitle="Cognition's public job board, scenario markets" right={<EvidenceBadge c="verified_fact" />}>
            <div className="space-y-1.5 text-sm">
              {Object.entries(h.by_department).sort((x, y) => y[1] - x[1]).map(([d, n]) => (
                <div key={d} className="flex justify-between"><span className="text-slate-600">{d}</span><span className="font-medium">{n}</span></div>
              ))}
            </div>
            <div className="mt-4 space-y-1">
              {Object.values(h.by_archetype).flat().filter((r, i, arr) => arr.findIndex((x) => x.url === r.url) === i).slice(0, 12).map((r) => (
                <a key={r.url} href={r.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-xs text-brand-700 hover:underline">
                  <Briefcase className="h-3 w-3" /> {r.title} <span className="text-slate-400">· {r.market}</span>
                </a>
              ))}
            </div>
            <div className="mt-3"><Cite c={h.source} /></div>
          </Card>
          <Card title="Related signals" subtitle="Same segments & markets">
            <div className="max-h-[28rem] overflow-y-auto pr-1">{a.radar.related.map((s) => <SignalRow key={s.id} s={s} />)}</div>
          </Card>
        </div>
      </div>
    </div>
  );
}
