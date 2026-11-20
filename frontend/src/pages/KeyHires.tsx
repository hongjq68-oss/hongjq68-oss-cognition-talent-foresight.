import { ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { useApp } from "../state";
import { Card, Details, Takeaway } from "../components/ui";
import { NextStep, StepHeader, WhenChip } from "../components/journey";

export default function KeyHires() {
  const { analysis: a } = useApp();
  const j = a!.journey;
  const now = j.hires.filter((h) => h.when.tone === "now");
  return (
    <div className="space-y-5">
      <StepHeader step={2} title="Key hires" question={`The roles we need to hit: ${j.goal.title}.`} />
      <Takeaway title={`${now.length} hires to start now: ${now.slice(0, 3).map((h) => h.name).join(", ")}${now.length > 3 ? "…" : ""}`}>
        Ranked by how much each role moves the goal. Roles marked "Start now" take longer to fill than we have.
      </Takeaway>
      <div className="space-y-3">
        {j.hires.map((h, i) => (
          <Card key={h.archetype_id}>
            <div className="flex flex-wrap items-start gap-4">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-ink-900 text-sm font-bold text-white">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base font-semibold text-slate-900">{h.name}</h2>
                  <WhenChip w={h.when} />
                </div>
                <p className="mt-0.5 text-sm text-slate-600">{h.summary}</p>
                {h.why && <p className="mt-1 text-sm text-slate-800"><span className="font-medium">Why it matters: </span>{h.why}.</p>}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {h.must_have.map((m) => <span key={m} className="chip bg-slate-100 text-slate-700">{m}</span>)}
                </div>
              </div>
              <div className="w-44 shrink-0 space-y-1 text-right text-xs text-slate-500">
                <div className="text-2xl font-semibold text-slate-900">{h.open_roles || "—"}</div>
                <div>{h.open_roles ? "open roles today" : "not posted yet"}</div>
                <div>Best in: <span className="font-medium text-slate-700">{h.where.slice(0, 2).map((w) => w.name).join(", ")}</span></div>
                {h.when.start_by && <div>Start search by {h.when.start_by}</div>}
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between gap-3">
              {h.open_role_links.length > 0 ? (
                <Details label="See open roles">
                  <div className="space-y-1">
                    {h.open_role_links.map((r) => (
                      <a key={r.url} href={r.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-xs text-brand-700 hover:underline">
                        <ExternalLink className="h-3 w-3" /> {r.title} · {r.market}
                      </a>
                    ))}
                  </div>
                </Details>
              ) : <span />}
              <Link to={`/where?role=${h.archetype_id}`} className="text-xs font-medium text-brand-700 hover:underline">Where to hire →</Link>
            </div>
          </Card>
        ))}
      </div>
      <NextStep step={2} />
    </div>
  );
}
