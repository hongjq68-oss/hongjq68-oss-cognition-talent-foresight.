import { useState } from "react";
import clsx from "clsx";
import { useApp } from "../state";
import { Card, Details, EvidenceBadge, PageHeader, POOL, Sensitivity, Takeaway, useShowMore } from "../components/ui";
import type { Org, PoolType } from "../types";

function OrgCard({ o, capName }: { o: Org; capName: (id: string) => string }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-slate-900">{o.name}</span>
        <Sensitivity s={o.sensitivity} note={o.sensitivity_note} />
        <span className="ml-auto text-[11px] text-slate-400">{o.markets.join(" · ")}</span>
      </div>
      <p className="mt-1 line-clamp-2 text-xs text-slate-600">{o.why_relevant}</p>
      <Details className="mt-1.5">
        <div className="space-y-1 text-xs text-slate-500">
          <div><b>Value to Cognition:</b> {o.value_to_cognition}</div>
          <div><b>Teams:</b> {o.teams.join("; ")}</div>
          <div><b>Search hints:</b> {o.starting_titles.join(", ")}</div>
          {o.capabilities && <div className="flex flex-wrap gap-1">{o.capabilities.map((c) => <span key={c} className="chip bg-slate-100 text-slate-600">{capName(c)}</span>)}</div>}
          {o.sensitivity !== "none" && <p className="rounded bg-rose-50 p-2 text-[11px] text-rose-700">{o.sensitivity_note}</p>}
        </div>
      </Details>
    </div>
  );
}

function PoolColumn({ g, capName }: { g: { pool_type: PoolType; label: string; organisations: Org[] }; capName: (id: string) => string }) {
  const [shown, more] = useShowMore(g.organisations, 3);
  return (
    <div className="space-y-3">
      <div className={`rounded-md px-2 py-1 text-xs font-semibold ${POOL[g.pool_type].cls}`}>{g.label}</div>
      {g.organisations.length === 0 && <div className="text-xs text-slate-400">No mapped organisations in these markets.</div>}
      {shown.map((o) => <OrgCard key={o.id} o={o} capName={capName} />)}
      {more}
    </div>
  );
}

export default function Ecosystem() {
  const { analysis: a } = useApp();
  const capName = (id: string) => a!.capabilities.find((c) => c.id === id)?.name || id;
  const caps = a!.capabilities.filter((c) => a!.capability_pools[c.id]);
  const [cap, setCap] = useState<string>("all");
  const pools = cap === "all" ? null : a!.capability_pools[cap];
  const direct = a!.ecosystem.find((g) => g.pool_type === "direct")?.effort_share || 0;
  const top = [...a!.ecosystem].sort((x, y) => y.effort_share - x.effort_share)[0];
  return (
    <div className="space-y-5">
      <PageHeader letter="D" title="Talent Map" question="Where does this talent work today?">
        <EvidenceBadge c="market_intel" />
      </PageHeader>
      <Takeaway title={`Look beyond AI competitors: ${Math.round((1 - direct) * 100)}% of search effort goes to other talent pools.`}>
        Largest pool: {POOL[top.pool_type].label} ({Math.round(top.effort_share * 100)}%). Red flags mark Cognition customers, partners and competitors, so approach those carefully.
      </Takeaway>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-slate-500">View by capability:</span>
        <select className="input max-w-sm" value={cap} onChange={(e) => setCap(e.target.value)}>
          <option value="all">All capabilities</option>
          {caps.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>
      {!pools && (
        <Card title="Where to spend search effort">
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
          <PoolColumn key={g.pool_type + cap} g={g} capName={capName} />
        ))}
      </div>
    </div>
  );
}
