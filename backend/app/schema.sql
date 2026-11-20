-- Cognition Talent Foresight — SQLite schema.
-- Every analytical row carries an evidence_class so the UI can separate
-- verified facts from market intelligence, hypotheses, predictions and recommendations.

CREATE TABLE IF NOT EXISTS sources (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  url           TEXT,
  publisher     TEXT NOT NULL,
  published_on  TEXT,
  retrieved_on  TEXT,
  source_type   TEXT NOT NULL CHECK (source_type IN ('company_blog','job_board','press','analyst','internal','synthetic'))
);

CREATE TABLE IF NOT EXISTS signals (
  id             TEXT PRIMARY KEY,
  kind           TEXT NOT NULL,          -- product | customer | partnership | expansion | leadership | funding | acquisition | hiring | competitor | regulatory
  title          TEXT NOT NULL,
  summary        TEXT NOT NULL,
  happened_on    TEXT,
  regions        TEXT NOT NULL DEFAULT '[]',  -- JSON list of market codes
  segment_ids    TEXT NOT NULL DEFAULT '[]',  -- JSON list
  source_id      TEXT REFERENCES sources(id),
  evidence_class TEXT NOT NULL CHECK (evidence_class IN ('verified_fact','market_intel','hypothesis','prediction','recommendation')),
  curated        INTEGER NOT NULL DEFAULT 0   -- 1 = analyst-reviewed, 0 = auto-ingested
);

CREATE TABLE IF NOT EXISTS job_postings (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  department    TEXT,
  team          TEXT,
  location      TEXT,
  market        TEXT,
  published_on  TEXT,
  url           TEXT,
  retrieved_on  TEXT,
  active        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS segments (
  id   TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  data TEXT NOT NULL                     -- JSON: goals, challenges, barriers, systems, stakeholders, deployment_requirements, ...
);

CREATE TABLE IF NOT EXISTS capabilities (
  id                 TEXT PRIMARY KEY,
  name               TEXT NOT NULL,
  category           TEXT NOT NULL CHECK (category IN ('technical','commercial','delivery','transformation','entrepreneurial')),
  description        TEXT NOT NULL,
  scarcity           INTEGER NOT NULL CHECK (scarcity BETWEEN 1 AND 5),
  base_lead_weeks    INTEGER NOT NULL,
  delivery_tendency  TEXT NOT NULL CHECK (delivery_tendency IN ('hire','develop','partner')),
  evidence_phrases   TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS customer_problems (
  id                TEXT PRIMARY KEY,
  segment_id        TEXT NOT NULL REFERENCES segments(id),
  name              TEXT NOT NULL,
  description       TEXT NOT NULL,
  severity          REAL NOT NULL,         -- 0..1 business cost / urgency
  complexity        INTEGER NOT NULL,      -- 1..5 technical complexity
  pattern           TEXT NOT NULL CHECK (pattern IN ('customer_specific','industry_pattern')),
  horizon_profile   TEXT NOT NULL,         -- JSON [now, 6m, 12m, 24m] intensity
  cognition_use_cases TEXT NOT NULL DEFAULT '[]',
  adoption_barriers TEXT NOT NULL DEFAULT '[]',
  signal_ids        TEXT NOT NULL DEFAULT '[]',
  evidence_class    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_capabilities (
  problem_id    TEXT NOT NULL REFERENCES customer_problems(id),
  capability_id TEXT NOT NULL REFERENCES capabilities(id),
  weight        REAL NOT NULL,
  rationale     TEXT,
  PRIMARY KEY (problem_id, capability_id)
);

CREATE TABLE IF NOT EXISTS organisations (
  id               TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  pool_type        TEXT NOT NULL CHECK (pool_type IN ('direct','adjacent','customer_side','consulting','founder')),
  markets          TEXT NOT NULL DEFAULT '[]',
  segment_ids      TEXT NOT NULL DEFAULT '[]',
  capability_ids   TEXT NOT NULL DEFAULT '[]',
  why_relevant     TEXT NOT NULL,
  teams            TEXT NOT NULL DEFAULT '[]',
  starting_titles  TEXT NOT NULL DEFAULT '[]',
  value_to_cognition TEXT NOT NULL,
  sensitivity      TEXT NOT NULL DEFAULT 'none' CHECK (sensitivity IN ('none','customer','partner','competitor')),
  sensitivity_note TEXT,
  signal_ids       TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS archetypes (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  summary       TEXT NOT NULL,
  capability_weights TEXT NOT NULL,      -- JSON {capability_id: weight}
  unconventional_backgrounds TEXT NOT NULL DEFAULT '[]',
  assessment    TEXT NOT NULL DEFAULT '[]',
  posting_keywords TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS scenarios (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  data        TEXT NOT NULL                -- JSON: hypothesis, drivers, weights, boosts, changes, derailers
);

CREATE TABLE IF NOT EXISTS candidates (
  id                 TEXT PRIMARY KEY,
  display_name       TEXT NOT NULL,
  synthetic          INTEGER NOT NULL DEFAULT 1,
  headline           TEXT NOT NULL,
  employer_descriptor TEXT NOT NULL,
  profile_url        TEXT,
  pool_type          TEXT NOT NULL,
  market             TEXT NOT NULL,
  background         TEXT NOT NULL,
  learning_needs     TEXT NOT NULL DEFAULT '[]',
  status             TEXT NOT NULL DEFAULT 'discovered'
                     CHECK (status IN ('discovered','evidence_review','verified','ready_for_ats','parked')),
  notes              TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS candidate_evidence (
  id             TEXT PRIMARY KEY,
  candidate_id   TEXT NOT NULL REFERENCES candidates(id),
  claim          TEXT NOT NULL,          -- what they built or delivered
  problem_solved TEXT NOT NULL,
  capability_ids TEXT NOT NULL,
  evidence_type  TEXT NOT NULL CHECK (evidence_type IN ('public_artifact','talk','publication','open_source','news','profile_self_reported','title_only','patent')),
  source_url     TEXT,
  source_date    TEXT,
  verification   TEXT NOT NULL DEFAULT 'unverified' CHECK (verification IN ('unverified','verified','rejected'))
);

CREATE TABLE IF NOT EXISTS evidence_reviews (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id  TEXT NOT NULL REFERENCES candidate_evidence(id),
  decision     TEXT NOT NULL,
  note         TEXT,
  reviewer     TEXT NOT NULL,
  reviewed_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  at         TEXT NOT NULL,
  actor      TEXT NOT NULL,
  action     TEXT NOT NULL,
  detail     TEXT
);

CREATE TABLE IF NOT EXISTS refresh_runs (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  at         TEXT NOT NULL,
  connector  TEXT NOT NULL,
  ok         INTEGER NOT NULL,
  new_items  INTEGER NOT NULL DEFAULT 0,
  message    TEXT
);

-- Builder Evidence Agent: discovery monitors and the leads they surface (unpromoted leads expire)
CREATE TABLE IF NOT EXISTS monitors (
  id             TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  capability_id  TEXT NOT NULL REFERENCES capabilities(id),
  market         TEXT,
  queries        TEXT NOT NULL,          -- {"github": "...", "hn": "...", "devto": "...", "arxiv": "..."}
  active         INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT NOT NULL,
  last_run_at    TEXT
);

CREATE TABLE IF NOT EXISTS leads (
  id               TEXT PRIMARY KEY,
  monitor_id       TEXT NOT NULL REFERENCES monitors(id),
  person_key       TEXT NOT NULL,
  display_name     TEXT NOT NULL,
  source           TEXT NOT NULL,
  profile_url      TEXT,
  location         TEXT,
  company          TEXT,
  bio              TEXT,
  market_verified  INTEGER NOT NULL DEFAULT 0,
  evidence         TEXT NOT NULL,
  capability_ids   TEXT NOT NULL,
  first_seen       TEXT NOT NULL,
  last_seen        TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','promoted','dismissed')),
  candidate_id     TEXT REFERENCES candidates(id),
  expires_at       TEXT
);

CREATE TABLE IF NOT EXISTS builder_runs (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  at       TEXT NOT NULL,
  kind     TEXT NOT NULL,
  target   TEXT NOT NULL,
  sources  TEXT NOT NULL,
  items    INTEGER NOT NULL,
  added    INTEGER NOT NULL
);

-- Companies the engine can run for. Cognition is hand-curated; others are built from public sources.
CREATE TABLE IF NOT EXISTS companies (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  website       TEXT,
  careers_url   TEXT,
  board         TEXT,                     -- JSON {"provider": "...", "slug": "..."}
  blog_feed     TEXT,
  description   TEXT,
  curated       INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL,
  refreshed_at  TEXT,
  gaps          TEXT NOT NULL DEFAULT '[]'
);
