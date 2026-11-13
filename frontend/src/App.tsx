import clsx from "clsx";
import { Building2, Compass, FileText, Gauge, Layers, LineChart, Network, Radar, SlidersHorizontal, Users, RefreshCw } from "lucide-react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";
import { api } from "./api";
import { AppState, isCustom, useApp } from "./state";
import Radar_ from "./pages/Radar";
import Customers from "./pages/Customers";
import Forecast from "./pages/Forecast";
import Ecosystem from "./pages/Ecosystem";
import Candidates from "./pages/Candidates";
import Strategy from "./pages/Strategy";
import Planner from "./pages/Planner";
import ReportPage from "./pages/Report";
import Architecture from "./pages/Architecture";

const NAV = [
  { to: "/radar", label: "Business Growth Radar", icon: Radar, letter: "A" },
  { to: "/customers", label: "Customer Opportunity", icon: Building2, letter: "B" },
  { to: "/forecast", label: "Capability Forecast", icon: LineChart, letter: "C" },
  { to: "/ecosystem", label: "Talent Ecosystem Map", icon: Network, letter: "D" },
  { to: "/candidates", label: "Candidate Discovery", icon: Users, letter: "E" },
  { to: "/strategy", label: "Hiring Strategy", icon: Compass, letter: "F" },
];
const NAV2 = [
  { to: "/planner", label: "Scenario Planner", icon: SlidersHorizontal },
  { to: "/report", label: "Executive Report", icon: FileText },
  { to: "/architecture", label: "Architecture & Data", icon: Layers },
];

function Shell() {
  const { meta, overrides, setScenario, loading, error, analysis, reload, reloadMeta } = useApp();
  const [refreshing, setRefreshing] = useState(false);
  const custom = isCustom(overrides);
  const refresh = async () => {
    setRefreshing(true);
    try { await api.refresh(); await reloadMeta(); await reload(); } finally { setRefreshing(false); }
  };
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 shrink-0 bg-ink-900 text-slate-300">
        <div className="flex items-center gap-2 px-5 py-5">
          <Gauge className="h-6 w-6 text-brand-300" />
          <div>
            <div className="text-sm font-semibold text-white">Talent Foresight</div>
            <div className="text-[11px] text-slate-400">Cognition · APAC talent intelligence</div>
          </div>
        </div>
        <nav className="space-y-0.5 px-3">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => clsx("flex items-center gap-3 rounded-lg px-3 py-2 text-sm", isActive ? "bg-ink-700 text-white" : "hover:bg-ink-800")}>
              <span className="grid h-5 w-5 place-items-center rounded bg-ink-700 text-[10px] font-bold text-slate-200">{n.letter}</span>
              {n.label}
            </NavLink>
          ))}
          <div className="my-3 border-t border-ink-700" />
          {NAV2.map((n) => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => clsx("flex items-center gap-3 rounded-lg px-3 py-2 text-sm", isActive ? "bg-ink-700 text-white" : "hover:bg-ink-800")}>
              <n.icon className="h-4 w-4" /> {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-6 px-5 text-[11px] leading-relaxed text-slate-500">
          Synthetic candidates. Public Cognition sources only. No automated outreach or hiring decisions.
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-slate-200 bg-white/90 px-6 py-3 backdrop-blur">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Scenario</span>
          <select className="input max-w-xl" value={custom ? "custom" : overrides.scenario_id || ""} onChange={(e) => setScenario(e.target.value)}>
            {custom && <option value="custom">Custom: {analysis?.scenario.name}</option>}
            {meta?.scenarios.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          {loading && <span className="text-xs text-slate-400">Recomputing…</span>}
          {error && <span className="text-xs text-rose-600">{error}</span>}
          <div className="ml-auto flex items-center gap-3 text-xs text-slate-500">
            {meta && <span>{meta.counts.signals} signals · {meta.counts.jobs} open roles · {meta.counts.organisations} orgs</span>}
            <button className="btn-secondary !py-1.5" onClick={refresh} disabled={refreshing} title="Pull the public Cognition blog index and job board">
              <RefreshCw className={clsx("h-3.5 w-3.5", refreshing && "animate-spin")} /> Refresh public sources
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">
          {analysis && meta ? (
            <Routes>
              <Route path="/" element={<Navigate to="/radar" replace />} />
              <Route path="/radar" element={<Radar_ />} />
              <Route path="/customers" element={<Customers />} />
              <Route path="/forecast" element={<Forecast />} />
              <Route path="/ecosystem" element={<Ecosystem />} />
              <Route path="/candidates" element={<Candidates />} />
              <Route path="/strategy" element={<Strategy />} />
              <Route path="/planner" element={<Planner />} />
              <Route path="/report" element={<ReportPage />} />
              <Route path="/architecture" element={<Architecture />} />
            </Routes>
          ) : (
            <div className="text-sm text-slate-500">{error || "Loading…"}</div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return <AppState><Shell /></AppState>;
}
