import type { Analysis, Meta, Overrides, Report } from "./types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || r.statusText);
  }
  const ct = r.headers.get("content-type") || "";
  return (ct.includes("json") ? r.json() : r.text()) as Promise<T>;
}

const post = <T,>(path: string, body: unknown) => req<T>(path, { method: "POST", body: JSON.stringify(body) });

export const builderApi = {
  overview: () => req<import("./types").BuilderOverview>("/api/builders"),
  investigate: (b: Record<string, unknown>) => post<import("./types").InvestigateResult>("/api/builders/investigate", b),
  runMonitor: (id: string) => post<{ new: number; builders: number; items_found: number; sources: Record<string, { ok: boolean; items?: number; error?: string }> }>(`/api/builders/monitors/${id}/run`, {}),
  createMonitor: (b: Record<string, unknown>) => post<{ id: string }>("/api/builders/monitors", b),
  decide: (id: string, decision: string, market?: string, pool_type?: string) => post<{ candidate_id?: string }>(`/api/builders/leads/${encodeURIComponent(id)}`, { decision, market, pool_type }),
};

export const api = {
  meta: () => req<Meta>("/api/meta"),
  analysis: (o: Overrides) => post<Analysis>("/api/analysis", o),
  report: (o: Overrides) => post<Report>("/api/report", o),
  reportMd: (o: Overrides) => post<string>("/api/report.md", o),
  review: (id: string, decision: string, note?: string) => post(`/api/evidence/${id}/review`, { decision, note }),
  profile: (id: string, profile_url: string) => post(`/api/candidates/${id}/profile`, { profile_url }),
  status: (id: string, status: string, note?: string) => post(`/api/candidates/${id}/status`, { status, note }),
  refresh: () => post<Record<string, { ok: boolean; items?: number; error?: string }>>("/api/refresh", {}),
  reset: () => post("/api/reset", {}),
};
