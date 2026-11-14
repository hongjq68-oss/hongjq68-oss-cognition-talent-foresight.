export type EvidenceClass = "verified_fact" | "market_intel" | "hypothesis" | "prediction" | "recommendation";
export type Horizon = "now" | "6m" | "12m" | "24m";
export type PoolType = "direct" | "adjacent" | "customer_side" | "consulting" | "founder";

export interface Citation { id?: string; title: string; url: string | null; date: string | null; evidence_class: EvidenceClass; source_needed?: boolean }
export interface Signal extends Citation { summary: string; kind: string }

export interface Scenario {
  id: string; name: string; hypothesis: string; signal_ids: string[];
  segment_weights: Record<string, number>; market_weights: Record<string, number>;
  capability_boosts: Record<string, number>; extra_demand: Record<string, number>;
  business_changes: string[]; derailers: string[]; alternatives: string[]; assumptions: string[];
}

export interface Role { title: string; url: string; market: string; published_on: string }
export interface Hiring {
  total_open_roles: number; in_scenario_markets: number; by_department: Record<string, number>;
  by_market: Record<string, number>; by_archetype: Record<string, Role[]>; source: Citation;
}

export interface ProblemCap { id: string; name: string; weight: number; rationale: string | null }
export interface Problem {
  id: string; segment_id: string; segment: string; name: string; description: string; severity: number; complexity: number;
  pattern: "customer_specific" | "industry_pattern"; relevance: number; horizon_profile: number[];
  cognition_use_cases: string[]; adoption_barriers: string[]; evidence_class: EvidenceClass; citations: Citation[];
  capabilities: ProblemCap[]; why: string;
}

export type Classification = "immediate" | "emerging" | "strategic" | "develop" | "partner";
export interface Capability {
  id: string; name: string; category: string; description: string; demand: Record<Horizon, number>; peak: number;
  scarcity: number; lead_weeks: number; need_by: string | null; start_search_by: string | null;
  classification: Classification; classification_label: string; delivery_tendency: string;
  confidence: "low" | "medium" | "high"; confidence_factors: string[];
  drivers: { type: string; id: string; label: string; contribution: number }[]; hiring_signal_roles: number;
}

export interface Org {
  id: string; name: string; pool_type: PoolType; markets: string[]; why_relevant: string; teams: string[];
  starting_titles: string[]; value_to_cognition: string; sensitivity: "none" | "customer" | "partner" | "competitor";
  sensitivity_note: string | null; score: number; capabilities?: string[];
}
export interface PoolGroup { pool_type: PoolType; label: string; effort_share: number; organisations: Org[] }

export interface Archetype {
  id: string; name: string; summary: string; score: number;
  capabilities: { id: string; name: string; weight: number; demand: number }[];
  unconventional_backgrounds: string[]; assessment: string[]; open_roles: Role[]; need_by: string | null;
}

export interface Strategy {
  archetype_id: string; focus_capabilities: string[]; evidence_to_look_for: string[];
  queries: { source: string; query: string; note: string }[]; target_organisations: string[]; avoid: string[];
  shortlist: ShortlistEntry[];
}

export interface ShortlistEntry {
  candidate_id: string; display_name: string; headline: string; employer_descriptor: string; profile_url: string | null; market: string; pool_type: PoolType; status: string;
  score: number; strengths: string[]; gaps: string[]; verified_evidence: number;
}

export interface Evidence {
  id: string; claim: string; problem_solved: string; capability_ids: string[]; evidence_type: string;
  source_url: string | null; source_date: string | null; verification: "unverified" | "verified" | "rejected";
}
export interface Fit {
  archetype_id: string; archetype: string; score: number; evidence_fit: number; market_fit: number;
  demonstrated: { id: string; name: string; strength: number; evidence_id: string }[];
  gaps: { id: string; name: string; weight: number }[];
}
export interface BestJob { job_id: string; title: string; url: string; market: string; score: number }
export interface OpenJob {
  id: string; title: string; department: string | null; location: string; market: string; url: string;
  published_on: string | null; retrieved_on: string | null; regional: boolean; scenario_market_weight: number;
  profile: { id: string; name: string; basis: "role_profile" | "inferred" } | null; note: string | null;
  matches: { candidate_id: string; score: number; strengths: string[] }[];
}

export interface Candidate {
  id: string; display_name: string; synthetic: number; headline: string; employer_descriptor: string; profile_url: string | null;
  pool_type: PoolType; market: string; background: string; learning_needs: string[]; status: string; notes: string; evidence: Evidence[];
  best_fit: Fit; best_job: BestJob | null; alternative_fits: { archetype: string; score: number }[]; transferability: string;
  validation_questions: string[]; missing_information: string[];
}

export interface Segment { id: string; name: string; data: Record<string, string[]> }

export interface Analysis {
  scenario: Scenario; radar: { drivers: Signal[]; related: Signal[]; hiring: Hiring }; problems: Problem[];
  capabilities: Capability[]; archetypes: Archetype[]; ecosystem: PoolGroup[];
  capability_pools: Record<string, Record<PoolType, { label: string; organisations: Org[] }>>;
  strategies: Strategy[]; candidates: Candidate[]; open_jobs: OpenJob[]; segments: Record<string, Segment>;
}

export interface Meta {
  scenarios: { id: string; name: string; hypothesis: string }[];
  segments: { id: string; name: string }[];
  capabilities: { id: string; name: string; category: string; scarcity: number }[];
  markets: string[];
  counts: Record<string, number>;
  last_refresh: { at: string; connector: string; ok: number; new_items: number; message: string }[];
}

export interface ReportItem { text: string; evidence_class: EvidenceClass; citations: Citation[] }
export interface Report { title: string; scenario_id: string; sections: { number: number; title: string; items: ReportItem[] }[]; evidence_labels: Record<EvidenceClass, string> }

export interface Overrides {
  scenario_id: string | null; name?: string; hypothesis?: string;
  segment_weights?: Record<string, number>; market_weights?: Record<string, number>; capability_boosts?: Record<string, number>;
}
