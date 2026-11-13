import { useState } from "react";
import clsx from "clsx";
import { useApp } from "../state";
import { Bar, Card, Cite, EvidenceBadge, List, PageHeader } from "../components/ui";

const FIELDS: [string, string][] = [
  ["goals", "Strategic goals"], ["challenges", "Operational challenges"], ["barriers", "Adoption barriers"],
  ["systems", "Legacy systems"], ["stakeholders", "Decision-makers & stakeholders"], ["deployment_requirements", "Deployment requirements"],
  ["cognition_needs", "What Cognition needs to win, deploy & expand"],
];

export default function Customers() {
  const { analysis: a } = useApp();
  const segs = Object.values(a!.segments);
  const [seg, setSeg] = useState<string>("all");
  const problems = a!.problems.filter((p) => seg === "all" || p.segment_id === seg);
  const max = Math.max(...a!.problems.map((p) => p.relevance), 1);
  const s = segs.find((x) => x.id === seg);
  return (
    <div className="space-y-6">
      <PageHeader letter="B" title="Customer Opportunity Intelligence" question="Which customers drive this growth, and what problems do they need Cognition to solve?" />
      <div className="flex flex-wrap gap-2">
        {[{ id: "all", name: "All segments in scenario" }, ...segs].map((x) => (
          <button key={x.id} onClick={() => setSeg(x.id)} className={clsx("btn !py-1.5", seg === x.id ? "bg-ink-900 text-white" : "btn-secondary")}>
            {x.name}{x.id !== "all" && <span className="ml-1 text-xs opacity-70">×{a!.scenario.segment_weights[x.id]}</span>}
          </button>
        ))}
      </div>
      {s && (
        <Card title={`${s.name} — segment profile`} right={<EvidenceBadge c="market_intel" />}>
          <div className="grid gap-5 md:grid-cols-3">
            {FIELDS.map(([k, label]) => s.data[k] && (
              <div key={k}><div className="label">{label}</div><List items={s.data[k]} /></div>
            ))}
          </div>
        </Card>
      )}
      <div className="space-y-4">
        {problems.map((p) => (
          <Card key={p.id}>
            <div className="flex flex-wrap items-start gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="chip bg-slate-100 text-slate-600">{p.segment}</span>
                  <span className={clsx("chip", p.pattern === "industry_pattern" ? "bg-indigo-50 text-indigo-700" : "bg-amber-50 text-amber-800")}>
                    {p.pattern === "industry_pattern" ? "Industry-wide pattern" : "Customer-specific"}
                  </span>
                  <EvidenceBadge c={p.evidence_class} />
                </div>
                <h3 className="mt-2 text-base font-semibold text-slate-900">{p.name}</h3>
                <p className="mt-1 text-sm text-slate-600">{p.description}</p>
              </div>
              <div className="w-48 shrink-0">
                <div className="flex justify-between text-xs text-slate-500"><span>Scenario relevance</span><span className="font-medium text-slate-800">{p.relevance.toFixed(2)}</span></div>
                <Bar value={(100 * p.relevance) / max} />
                <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-slate-500">
                  <span>Severity {p.severity}</span><span>Complexity {p.complexity}/5</span>
                </div>
                <div className="mt-1 text-[11px] text-slate-400">{p.why}</div>
              </div>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <div><div className="label">How Cognition could help</div><List items={p.cognition_use_cases} /></div>
              <div><div className="label">Adoption barriers</div><List items={p.adoption_barriers} /></div>
              <div>
                <div className="label">Capabilities required (inferred)</div>
                <div className="space-y-1">
                  {p.capabilities.map((c) => (
                    <div key={c.id} className="text-sm" title={c.rationale || ""}>
                      <span className="font-medium text-slate-800">{c.name}</span>
                      <span className="ml-1 text-xs text-slate-400">w{c.weight}</span>
                      {c.rationale && <div className="text-xs text-slate-500">{c.rationale}</div>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {p.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-100 pt-3">{p.citations.map((c) => <Cite key={c.id} c={c} />)}</div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
