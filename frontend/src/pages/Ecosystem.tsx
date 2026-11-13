import { useState } from "react";
import clsx from "clsx";
import { useApp } from "../state";
import { Card, EvidenceBadge, PageHeader, POOL, PoolBadge, Sensitivity } from "../components/ui";
import type { Org, PoolType } from "../types";

function OrgCard({ o, capName }: { o: Org; capName: (id: string) => string }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-slate-900">{o.name}</span>
        <Sensitivity s={o.sensitivity} note={o.sensitivity_note} />
        <span className="ml-auto text-[11px] text-slate-400">{o.markets.join(" · ")}</span>
      </div>
      <p className="mt-1 text-xs text-slate-600">{o.why_relevant}</p>
      <p className="mt-1 text-xs text-slate-500"><b>Value to Cognition:</b> {o.value_to_cognition}</p>
      <div className="mt-2 text-xs text-slate-500"><b>Teams:</b> {o.teams.join("; ")}</div>
      <div className="mt-1 text-xs text-slate-500"><b>Starting titles (search hints, not filters):</b> {o.starting_titles.join(", ")}</div>
      {o.capabilities && <div className="mt-2 flex flex-wrap gap-1">{o.capabilities.map((c) => <span key={c} className="chip bg-slate-100 text-slate-600">{capName(c)}</span>)}</div>}
      {o.sensitivity !== "none" && <p className="mt-2 rounded bg-rose-50 p-2 text-[11px] text-rose-700">{o.sensitivity_note}</p>}
    </div>
  );
}

export default function Ecosystem() {
  const { analysis: a } = useApp();
  const capName = (id: string) => a!.capabilities.find((c) => c.id === id)?.name || id;
  const caps = a!.capabilities.filter((c) => a!.capability_pools[c.id]);
  const [cap, setCap] = useState<string>("all");
  const pools = cap === "all" ? null : a!.capability_pools[cap];
  return (
    <div className="space-y-6">
      <PageHeader letter="D" title="Talent Ecosystem Map" question="Where does the talent with these capabilities exist today — beyond AI competitors?">
        <EvidenceBadge c="market_intel" />
      </PageHeader>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-slate-500">View by capability:</span>
        <select className="input max-w-sm" value={cap} onChange={(e) => setCap(e.target.value)}>
          <option value="all">All in-demand capabilities (ranked organisations)</option>
          {caps.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>
      {!pools && (
        <Card title="Recommended search-effort split" subtitle="Direct AI competitors are deliberately a small share: expensive, contested, and often the least transferable to regulated customers.">
          <div className="flex h-8 overflow-hidden rounded-lg">
            {a!.ecosystem.map((g) => (
              <div key={g.pool_type} className={clsx("grid place-items-center text-xs font-medium", POOL[g.pool_type].cls)} style={{ width: `${g.effort_share * 100}%` }}>
                {POOL[g.pool_type].short} {Math.round(g.effort_share * 100)}%
              </div>
            ))}
          </div>
        </Card>
      )}
      <div className="grid gap-4 xl:grid-cols-5 lg:grid-cols-3 md:grid-cols-2">
        {(pools ? (Object.keys(POOL) as PoolType[]).map((pt) => ({ pool_type: pt, label: POOL[pt].label, organisations: pools[pt].organisations }))
          : a!.ecosystem).map((g) => (
          <div key={g.pool_type} className="space-y-3">
            <div className="flex items-center gap-2"><PoolBadge p={g.pool_type} /><span className="text-xs font-semibold text-slate-700">{g.label}</span></div>
            {g.organisations.length === 0 && <div className="text-xs text-slate-400">No mapped organisations in these markets.</div>}
            {g.organisations.slice(0, pools ? 4 : 6).map((o) => <OrgCard key={o.id} o={o} capName={capName} />)}
          </div>
        ))}
      </div>
    </div>
  );
}
