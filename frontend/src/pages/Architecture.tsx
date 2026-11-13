import { ArrowRight } from "lucide-react";
import { useApp } from "../state";
import { Card, EVIDENCE, EvidenceBadge, List, PageHeader } from "../components/ui";
import type { EvidenceClass } from "../types";

const PIPELINE = [
  ["Business intelligence", "Cognition blog, job board, curated signals"],
  ["Customer problems", "7 segments × problems, severity, horizon profile"],
  ["Capability inference", "Problem → capability weights + GTM needs + hiring signals"],
  ["Prediction", "Now/6/12/24m demand, classification, confidence, lead time"],
  ["Talent pools", "5 pool types per capability, market & segment fit"],
  ["Candidate evidence", "Evidence-type × verification weighting"],
  ["Strategy & report", "Archetypes, search strings, timeline, 11-section report"],
];

const TABLES: [string, string][] = [
  ["sources", "Every URL used, with publisher, published and retrieved dates"],
  ["signals", "Business signals with evidence_class and source_id"],
  ["job_postings", "Public Cognition roles (Ashby) — hiring signal"],
  ["segments / customer_problems", "Segment profiles and the problems they need solved"],
  ["capabilities / problem_capabilities", "Taxonomy (5 categories) and weighted, explained mappings"],
  ["organisations", "Talent-pool organisations with sensitivity flags"],
  ["archetypes / scenarios", "Capability bundles and hypothetical growth scenarios"],
  ["candidates / candidate_evidence", "Profiles and individual evidence items with verification state"],
  ["evidence_reviews / audit_log", "Who verified what and when; every status change"],
  ["refresh_runs", "Connector run history"],
];

const SOURCES: [string, string, string][] = [
  ["Cognition blog index", "cognition.ai/blog (public HTML)", "Live in prototype"],
  ["Cognition job board", "Ashby public posting API", "Live in prototype"],
  ["Customer & partner press", "Public press releases / newsroom RSS", "Phase 2"],
  ["GitHub", "REST/GraphQL API with token, public data only", "Phase 3"],
  ["Web search for talks, blogs, case studies", "SerpAPI / Bing API (licensed)", "Phase 3"],
  ["LinkedIn", "Not integrated. Recruiters use licensed tools manually", "Excluded"],
  ["LLM summarisation", "Optional, must cite sources; never invents candidate facts", "Phase 3"],
];

export default function Architecture() {
  const { meta } = useApp();
  return (
    <div className="space-y-6">
      <PageHeader title="Architecture & Data" question="How the engine reasons, what it stores, and the guardrails it enforces." />
      <Card title="Reasoning chain" subtitle="Deterministic and explainable: every score in the UI shows its drivers">
        <div className="flex flex-wrap items-stretch gap-2">
          {PIPELINE.map(([t, d], i) => (
            <div key={t} className="flex items-center gap-2">
              <div className="w-40 rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="text-xs font-semibold text-slate-800">{i + 1}. {t}</div>
                <div className="mt-1 text-[11px] text-slate-500">{d}</div>
              </div>
              {i < PIPELINE.length - 1 && <ArrowRight className="h-4 w-4 text-slate-400" />}
            </div>
          ))}
        </div>
      </Card>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Data model (SQLite)" subtitle="backend/app/schema.sql">
          <table className="w-full text-sm">
            <tbody>{TABLES.map(([t, d]) => <tr key={t} className="border-t border-slate-100"><td className="py-1.5 pr-3 font-mono text-xs text-slate-800">{t}</td><td className="text-slate-600">{d}</td></tr>)}</tbody>
          </table>
        </Card>
        <Card title="Evidence classes" subtitle="Every analytical record and report line carries exactly one">
          <div className="space-y-2">
            {(Object.keys(EVIDENCE) as EvidenceClass[]).map((k) => (
              <div key={k} className="flex items-center gap-3 text-sm"><EvidenceBadge c={k} /><span className="text-slate-600">{{
                verified_fact: "Stated in a dated public source (linked).",
                market_intel: "Analyst knowledge about markets/organisations; validate before external use.",
                hypothesis: "Scenario assumption or inferred customer problem.",
                prediction: "Engine output (demand, timing, classification).",
                recommendation: "Suggested recruiter action. A human decides.",
              }[k]}</span></div>
            ))}
          </div>
        </Card>
        <Card title="Approved source integrations">
          <table className="w-full text-sm">
            <tbody>{SOURCES.map(([s, how, st]) => <tr key={s} className="border-t border-slate-100"><td className="py-1.5 pr-3 font-medium text-slate-800">{s}</td><td className="text-slate-600">{how}</td><td className="text-xs text-slate-500">{st}</td></tr>)}</tbody>
          </table>
          {meta?.last_refresh.length ? <div className="mt-3 text-xs text-slate-500">Last refresh: {meta.last_refresh.map((r) => `${r.connector} ${r.ok ? "ok" : "failed"} (${r.new_items}) at ${r.at}`).join(" · ")}</div> : <div className="mt-3 text-xs text-slate-500">Using snapshot from 2026-11-13; use "Refresh public sources" to pull live.</div>}
        </Card>
        <Card title="Security, privacy & guardrails">
          <List items={[
            "No scraping of restricted professional networks and no bypassing of access controls.",
            "No automatic outreach and no automatic hiring decisions. Every pipeline move is a recruiter action, written to the audit log.",
            "A title or employer name alone scores zero. Only evidence of what someone built or delivered counts.",
            "Moving a profile to Verified needs at least 2 recruiter-verified evidence items. Ready-for-ATS needs every item reviewed. The ATS export includes verified evidence only.",
            "Cognition customers, partners and competitors are flagged, so relationship policy can be applied before anyone is approached.",
            "Personal data: store only public, job-relevant evidence. Production needs PDPA/GDPR retention and deletion, SSO and role-based access.",
            "Prototype candidates are synthetic. No real person is profiled.",
          ]} />
        </Card>
      </div>
    </div>
  );
}
