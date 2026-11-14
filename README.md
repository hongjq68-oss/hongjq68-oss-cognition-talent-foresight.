# Cognition Talent Foresight

A business-to-talent intelligence engine. It answers one question: *given where Cognition is going, what capabilities will the business need next, where does that talent exist today, and how do we reach those people before the rest of the market?*

This is not a sourcing tool, and it does not replace the ATS. It reasons through this chain:

```
business signal → customer problem → capability requirement → talent pool → candidate evidence → hiring strategy
```

Every output is tagged with one evidence class: **verified fact** (a dated public source, linked), **market intelligence**, **strategic hypothesis**, **engine prediction** or **recruiter recommendation**.

## Run

```bash
./start.sh            # builds the UI and serves UI + API on http://localhost:8010
```

Development mode:

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000     # API (seeds backend/data/foresight.db on first start)
cd frontend && npm install && npm run dev                # UI on :5173, proxies /api to :8000
```

Tests: `cd backend && .venv/bin/python -m pytest -q`

## What is in the prototype

| Area | Contents |
|---|---|
| A. Business Growth Radar | 29 dated signals from cognition.ai/blog, plus 114 live roles from Cognition's public Ashby board used as a hiring signal |
| B. Customer Opportunity | 7 segments and 21 customer problems, each with severity, complexity, use cases and adoption barriers |
| C. Capability Forecast | 36 capabilities in 5 categories. Demand for now/6/12/24 months, scarcity, lead time, need-by and start-search dates, 5 classifications, confidence |
| D. Talent Ecosystem | 50 organisations across 5 pool types (direct, adjacent, customer-side, consulting/SI, founders). Every capability is covered by all 5. Customers, partners and competitors are flagged |
| E. Candidate Discovery | 14 **synthetic** profiles. Fit is based on evidence: title-only evidence scores 0, unverified evidence counts half. Includes a recruiter verification workflow and audit log. "Open jobs" groups candidates under every live APAC posting on the Ashby board, scored against the role profile each posting maps to (recruiting roles are not scored) |
| F. Hiring Strategy | Archetypes (capability bundles), search strings for approved channels, target organisations, timeline |
| Scenario Planner | 6 preset scenarios (APAC banking is the default). You can reweight segments and markets |
| Executive Report | 11 sections, with evidence labels and citations. Exports to Markdown or print |

## Layout

```
backend/app/schema.sql        data model (sources, signals, job_postings, segments, customer_problems,
                              capabilities, problem_capabilities, organisations, archetypes, scenarios,
                              candidates, candidate_evidence, evidence_reviews, audit_log, refresh_runs)
backend/app/connectors/       cognition_blog.py, ashby.py (public sources only)
backend/app/seed/             curated knowledge base + snapshots/ of public sources
backend/app/engine/           kb, forecast, pools, candidates, analysis, report
backend/app/main.py           FastAPI routes (/api/...)
frontend/src/pages/           one page per dashboard section
docs/ARCHITECTURE.md          design, scoring, guardrails, roadmap
```

## Guardrails

- No scraping of LinkedIn or other restricted networks.
- No outreach and no hiring decisions. Every candidate status change is a recruiter action, and each one is written to the audit log.
- A profile needs at least 2 recruiter-verified evidence items to reach **Verified**. To reach **Ready for ATS**, every evidence item must be reviewed. The ATS export includes verified evidence only.
- Scenarios are hypotheses. They are not statements of Cognition's plans.
