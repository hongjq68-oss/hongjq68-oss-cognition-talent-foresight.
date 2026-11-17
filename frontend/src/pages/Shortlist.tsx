import { ChevronRight, ExternalLink } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { useApp } from "../state";
import { Card, MARKET_NAMES, PoolBadge, Score, Takeaway } from "../components/ui";
import { RolePicker, StepHeader, WhenChip } from "../components/journey";

const STAGE: Record<string, string> = { discovered: "New", evidence_review: "Checking", verified: "Checked", ready_for_ats: "Ready for ATS", parked: "Parked" };

export default function Shortlist() {
  const { analysis: a } = useApp();
  const j = a!.journey;
  const [sp, setSp] = useSearchParams();
  const sel = j.hires.find((h) => h.archetype_id === sp.get("role")) || j.hires[0];
  return (
    <div className="space-y-5">
      <StepHeader step={5} title="Shortlist" question="People picked automatically for each key hire, using the countries and companies from the talent map." />
      <RolePicker hires={j.hires} value={sel.archetype_id} onChange={(id) => setSp({ role: id })} count={(h) => h.shortlist.length + h.builders.length} />
      <Takeaway title={sel.shortlist[0] ? `Top pick for ${sel.name}: ${sel.shortlist[0].display_name}` : `No one in the pipeline fits ${sel.name} yet`}>
        Ranked by proven skills, then by being in {sel.where.slice(0, 2).map((w) => w.name).join(" or ")} and coming from the right kind of company. Suggestions only: a recruiter checks each person before any contact.
      </Takeaway>
      <Card title={`From our pipeline · ${sel.shortlist.length}`} right={<WhenChip w={sel.when} />}>
        {!sel.shortlist.length && <div className="text-sm text-slate-500">Nobody yet. Try the new builders below or the companies on the talent map.</div>}
        <div className="divide-y divide-slate-100">
          {sel.shortlist.map((p, i) => (
            <Link key={p.candidate_id} to={`/candidates?c=${p.candidate_id}`} className="flex items-center gap-3 py-3 hover:bg-slate-50">
              <span className="w-4 text-xs text-slate-400">{i + 1}</span>
              <Score value={p.match} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900">{p.display_name}</span>
                  <PoolBadge p={p.pool_type} />
                  <span className="text-xs text-slate-400">{MARKET_NAMES[p.market] || p.market}</span>
                </div>
                <div className="truncate text-xs text-slate-500">{p.headline} · {p.employer_descriptor}</div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {p.reasons.map((r) => <span key={r} className="chip bg-emerald-50 text-emerald-700">{r}</span>)}
                  {p.gaps.length > 0 && <span className="chip bg-amber-50 text-amber-800">Check: {p.gaps.join(", ")}</span>}
                </div>
              </div>
              <div className="shrink-0 text-right text-[11px] text-slate-500">
                <div className="font-medium text-slate-700">{STAGE[p.status] || p.status}</div>
              </div>
              <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
            </Link>
          ))}
        </div>
      </Card>
      <Card title={`New builders found online · ${sel.builders.length}`} subtitle="People whose public work (code, launches, articles) matches this role. Not checked yet."
        right={<Link to="/builders" className="text-xs font-medium text-brand-700 hover:underline">Review in Find builders →</Link>}>
        {!sel.builders.length && <div className="text-sm text-slate-500">None yet. Search runs daily in Find builders.</div>}
        <div className="divide-y divide-slate-100">
          {sel.builders.map((b) => (
            <div key={b.lead_id} className="flex items-start gap-3 py-2.5">
              <Score value={b.match} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-semibold text-slate-900">{b.display_name}</span>
                  <span className="text-xs text-slate-400">{b.market ? MARKET_NAMES[b.market] : "Location unknown"} · via {b.source}</span>
                  {b.profile_url && <a href={b.profile_url} target="_blank" rel="noreferrer" className="text-brand-700"><ExternalLink className="h-3.5 w-3.5" /></a>}
                </div>
                {b.work.map((w) => <div key={w} className="truncate text-xs text-slate-600">{w}</div>)}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
