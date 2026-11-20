import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";
import type { Analysis, Meta, Overrides } from "./types";

interface Ctx {
  meta: Meta | null;
  analysis: Analysis | null;
  overrides: Overrides;
  loading: boolean;
  error: string | null;
  company: string;
  setScenario: (id: string) => void;
  setCompany: (id: string) => void;
  setOverrides: (o: Overrides) => void;
  reload: () => Promise<void>;
  reloadMeta: () => Promise<void>;
}

const C = createContext<Ctx | null>(null);

export function AppState({ children }: { children: ReactNode }) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [company, setCompanyId] = useState<string>(() => localStorage.getItem("company") || "cognition");
  const [overrides, setOverridesRaw] = useState<Overrides>({ company, scenario_id: company === "cognition" ? "apac_banking" : `${company}:balanced` });
  const setOverrides = useCallback((o: Overrides) => setOverridesRaw({ ...o, company }), [company]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setAnalysis(await api.analysis(overrides));
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [overrides]);
  const reloadMeta = useCallback(async () => setMeta(await api.meta(company)), [company]);
  const setCompany = useCallback((id: string) => {
    localStorage.setItem("company", id);
    setCompanyId(id);
    setOverridesRaw({ company: id, scenario_id: id === "cognition" ? "apac_banking" : `${id}:balanced` });
  }, []);

  useEffect(() => {
    reloadMeta().catch((e) => (company !== "cognition" ? setCompany("cognition") : setError(String(e))));
  }, [reloadMeta, company, setCompany]);
  useEffect(() => { reload(); }, [reload]);

  return (
    <C.Provider value={{ meta, analysis, overrides, loading, error, reload, reloadMeta, setOverrides, company, setCompany,
      setScenario: (id) => setOverrides({ scenario_id: id }) }}>
      {children}
    </C.Provider>
  );
}

export function useApp() {
  const c = useContext(C);
  if (!c) throw new Error("useApp outside AppState");
  return c;
}

export const isCustom = (o: Overrides): boolean => !!(o.segment_weights || o.market_weights || o.capability_boosts || o.name);

export function useCompanyName(): string {
  return useApp().meta?.company?.name || "Cognition";
}
