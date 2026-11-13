import { useState } from "react";
import clsx from "clsx";
import { useApp } from "../state";
import { Bar, Card, Cite, Details, EvidenceBadge, List, PageHeader, Takeaway, useShowMore } from "../components/ui";

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
  const [shown, more] = useShowMore(problems, 5);
  const top = a!.problems[0];
  return (
    <div className="space-y-5">
      <PageHeader letter="B" title="Customer Problems" question="Which customers drive growth, and what do they need solved?" />
      {top && <Takeaway title={`Biggest opportunity: ${top.name}`}>{top.segment}. {top.capabilities.length} capabilities are needed to deliver it.</Takeaway>}
      <div className="flex flex-wrap gap-2">
        {[{ id: "all", name: "All" }, ...segs].map((x) => (
          <button key={x.id} onClick={() => setSeg(x.id)} className={clsx("btn !py-1.5", seg === x.id ? "bg-ink-900 text-white" : "btn-secondary")}>
            {x.name}{x.id !== "all" && <span className="ml-1 text-xs opacity-70">×{a!.scenario.segment_weights[x.id]}</span>}
          </button>
        ))}
      </div>
      {s && (
        <Card title={`About ${s.name}`} right={<EvidenceBadge c="market_intel" />}>
          {s.data.cognition_needs && <><div className="label">What Cognition needs to win</div><List items={s.data.cognition_needs} /></>}
          <Details label="Full segment profile" className="mt-3">
            <div className="grid gap-5 md:grid-cols-3">
              {FIELDS.filter(([k]) => k !== "cognition_needs").map(([k, label]) => s.data[k] && (
                <div key={k}><div className="label">{label}</div><List items={s.data[k]} /></div>
              ))}
            </div>
          </Details>
        </Card>
      )}
      <div className="space-y-3">
        {shown.map((p, i) => (
          <Card key={p.id}>
            <div className="flex flex-wrap items-start gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400">#{i + 1}</span>
                  <span className="chip bg-slate-100 text-slate-600">{p.segment}</span>
                  <span className={clsx("chip", p.pattern === "industry_pattern" ? "bg-indigo-50 text-indigo-700" : "bg-amber-50 text-amber-800")}>
                    {p.pattern === "industry_pattern" ? "Industry-wide pattern" : "Customer-specific"}
                  </span>
                  <EvidenceBadge c={p.evidence_class} />
                </div>
                <h3 className="mt-2 text-base font-semibold text-slate-900">{p.name}</h3>
                <p className="mt-1 line-clamp-2 text-sm text-slate-600">{p.description}</p>
                <div className="mt-2 flex flex-wrap gap-1">{p.capabilities.map((c) => <span key={c.id} className="chip bg-brand-50 text-brand-700">{c.name}</span>)}</div>
              </div>
              <div className="w-48 shrink-0">
                <div className="flex justify-between text-xs text-slate-500"><span>Relevance</span><span className="font-medium text-slate-800">{p.relevance.toFixed(2)}</span></div>
                <Bar value={(100 * p.relevance) / max} />
                <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-slate-500">
                  <span>Severity {p.severity}</span><span>Complexity {p.complexity}/5</span>
                </div>
              </div>
            </div>
            <Details className="mt-3">
            <p className="mb-3 text-xs text-slate-500">{p.why}</p>
            <div className="grid gap-4 md:grid-cols-3">
              <div><div className="label">How Cognition could help</div><List items={p.cognition_use_cases} /></div>
              <div><div className="label">Adoption barriers</div><List items={p.adoption_barriers} /></div>
              <div>
                <div className="label">Why each capability</div>
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
            </Details>
            {p.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-100 pt-3">{p.citations.map((c) => <Cite key={c.id} c={c} />)}</div>
            )}
          </Card>
        ))}
        {more}
      </div>
    </div>
  );
}
