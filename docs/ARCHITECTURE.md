# Architecture

## Modules (backend/app/engine)

1. **kb.py**: loads the knowledge base from SQLite. `cite()` resolves a signal to its title, URL, date and evidence class.
2. **forecast.py**
   - `resolve_scenario()` merges a preset with user overrides.
   - `business_radar()` and `hiring_signals()` read the public signals and the Ashby roles.
   - `rank_problems()` computes a relevance score for each problem: segment weight × severity × number of supporting signals.
   - `capability_forecast()` sums problem demand by horizon (using each problem's horizon profile and a ramp for the scenario) plus the go-to-market needs of each segment, the scenario's capability boosts, and current public hiring. The result is normalised to 0–100.
   - `classify()` places each capability in one of five classes: immediate, emerging, strategic, develop internally, or via partners. It uses peak horizon, scarcity and how the capability tends to be delivered.
   - Start-search date = need-by date − lead time. Lead time is the base lead time scaled by scarcity.
3. **pools.py**: maps each capability to organisations in all 5 pool types, filtered by market and segment. Search effort is split across the pools: direct AI competitors 10%, and the rest goes to the non-direct pools. Builds search strings for approved channels only.
4. **candidates.py**: computes capability strength as Σ(evidence-type weight × verification weight), capped at 1. Fit = Σ(archetype capability weight × strength) × market fit.
   - Title-only evidence weighs 0. Unverified evidence weighs 0.5. Rejected evidence weighs 0.
   - The status machine enforces the Verified and Ready-for-ATS gates.
   - Also generates validation questions.
5. **journey.py**: turns the analysis into the 5-step hiring plan shown first in the app (Business goal → Key hires → Where to hire → Talent map → Shortlist).
   - Each scenario gets a plain-language goal and success outcomes (`GOALS`).
   - Key hires are the top 6 role types, with timing from their most urgent skill and live Ashby openings.
   - Talent map: role type × country. Talent depth is estimated from tracked companies in that country (exact market counts fully, APAC/global presence counts 0.5) weighted by how much their skills overlap the role, normalised to 0–100. It is market insight, not a headcount.
   - Country priority = 50% goal weight + 50% talent depth; the top 3 countries in the goal are recommended. Target companies exclude direct AI competitors.
   - Shortlist: pipeline candidates ranked by 0.8 × past-work fit (title-only still scores 0), plus +10 for a top-2 country, +6 for a targeted talent area and +4 for a target company; Find-builders leads matched on skills. Suggestions only.
6. **analysis.py**: runs the full chain for one scenario.
7. **report.py**: builds the 11-section executive report. Every line carries an evidence class and its citations.
8. **company.py** (any company): `build()` creates a company pack from public sources and `infer_goals()` proposes goals from it.
   - Jobs: tries Ashby, Greenhouse, Lever and SmartRecruiters by name slug, or uses a pasted careers-board URL (`connectors/company.py`).
   - Signals: the company's own RSS/Atom feed (pasted or auto-discovered from the website), Hacker News stories (Algolia, 15+ points, 24 months) and the Wikipedia summary. Google News is not used.
   - Each APAC job is mapped to a generic role type (`seed/generic.py`) by the longest matching title keyword. Goals are weighted by the role mix, APAC hiring by country and theme keywords in the news. They are stored as scenarios with `inferred=1`, and the app labels them as suggestions to confirm with the business.
   - Customer / partner / competitor flags are not guessed for added companies; all organisations are neutral.
   - Inferred plans mark a key hire "Start now" when it has 2+ live postings in the goal countries.

### Company isolation

`signals`, `sources`, `job_postings`, `scenarios`, `archetypes`, `segments` and `customer_problems` carry `company_id`. Cognition keeps its curated rows (`cognition`); added companies own their jobs, signals, sources and scenarios and share the generic library (`*`) for segments, problems and role types. Capabilities, organisations and the candidate pipeline are shared. Rebuilding a company replaces its rows; `DELETE /api/companies/{id}` removes them and refuses curated companies.

## Source integrations

| Source | Method | Status |
|---|---|---|
| Cognition blog | Public HTML index | Live (`POST /api/refresh`) |
| Cognition jobs | Ashby public posting API | Live |
| Other companies' jobs | Ashby, Greenhouse, Lever, SmartRecruiters public posting APIs | Live (`POST /api/companies`) |
| Other companies' news | Own RSS/Atom feed, Hacker News (Algolia), Wikipedia REST summary | Live |
| Press / newsroom | RSS or public pages | Phase 2 |
| GitHub | Official REST API (`GITHUB_TOKEN` optional; anonymous is 60 req/h) | Live, Builder Evidence |
| Hacker News, dev.to, arXiv, Hugging Face, npm, RSS | Public APIs/feeds, no key | Live, Builder Evidence |
| Patents, launch and demo pages | Recruiter-pasted public URL; page title/description metadata only | Live, Builder Evidence |
| Product Hunt, YouTube, patent search | Need API keys | Not integrated |
| Talks / blogs / case studies | Licensed search API (SerpAPI or Bing) | Phase 3 |
| LinkedIn | **Not integrated.** Recruiters use licensed tools manually | Excluded |
| LLM summarisation | Optional; must cite stored sources and must never create candidate facts | Phase 3 |

## Security & privacy

- Store only public, job-relevant evidence about people. Each item keeps its source link and date.
- Production requirements:
  - SSO and role-based access
  - Retention and deletion under PDPA/GDPR
  - Encryption at rest
  - The audit log kept as the system of record for recruiter decisions
- Sensitivity flags on organisations (customer, partner, competitor) must be checked before anyone is approached.
- Seeded people are synthetic. The Builder Evidence Agent stores real public work evidence (titles, links, dates, public profile URL, location and company as published) and never reads emails or contact details. Leads not added to Candidates expire after 30 days; every run, promotion and dismissal is in the audit log.
- Builder evidence is generated by rules (keyword-to-capability mapping), not an LLM, enters as `unverified`, and must pass the recruiter verification gate before ATS export.

## Roadmap

- **Phase 0–1 (this prototype):** schema, knowledge base, engine, dashboard, 6 scenarios, verification workflow, report, tests.
- **Phase 2:** scheduled refresh; hiring-trend deltas between job snapshots; new blog posts flagged for analyst tagging.
- **Phase 3:** discovery through the GitHub API and a licensed search API, reusing TalentScout connectors; optional LLM summaries with citations.
- **Phase 4:** SSO, data retention, and ATS integration through the ATS's official API.
