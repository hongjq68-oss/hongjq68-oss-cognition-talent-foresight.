import clsx from "clsx";
import { Building2, Compass, FileText, Gauge, Layers, LineChart, Network, Radar, SlidersHorizontal, Users, RefreshCw, ScanSearch } from "lucide-react";
import Goal from "./pages/Goal";
import KeyHires from "./pages/KeyHires";
import WhereToHire from "./pages/WhereToHire";
import TalentMap from "./pages/TalentMap";
import Shortlist from "./pages/Shortlist";
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
import Builders from "./pages/Builders";
import Planner from "./pages/Planner";
import ReportPage from "./pages/Report";
import Architecture from "./pages/Architecture";

const PLAN = [
  { to: "/goal", label: "Business goal", letter: "1" },
  { to: "/hires", label: "Key hires", letter: "2" },
  { to: "/where", label: "Where to hire", letter: "3" },
  { to: "/map", label: "Talent map", letter: "4" },
  { to: "/shortlist", label: "Shortlist", letter: "5" },
];
const PEOPLE = [
  { to: "/candidates", label: "Candidates", icon: Users },
  { to: "/builders", label: "Find builders", icon: ScanSearch },
];
const MORE = [
  { to: "/radar", label: "Growth signals", icon: Radar },
  { to: "/customers", label: "Customer problems", icon: Building2 },
  { to: "/forecast", label: "Skills forecast", icon: LineChart },
  { to: "/ecosystem", label: "Talent sources", icon: Network },
  { to: "/strategy", label: "Sourcing playbook", icon: Compass },
  { to: "/planner", label: "What-if planner", icon: SlidersHorizontal },
  { to: "/report", label: "Executive summary", icon: FileText },
  { to: "/architecture", label: "How it works", icon: Layers },
];
const navCls = ({ isActive }: { isActive: boolean }) => clsx("flex items-center gap-3 rounded-lg px-3 py-2 text-sm", isActive ? "bg-ink-700 text-white" : "hover:bg-ink-800");
const Group = ({ label }: { label: string }) => <div className="px-3 pb-1 pt-4 text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</div>;

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
          <Group label="Hiring plan" />
          {PLAN.map((n) => (
            <NavLink key={n.to} to={n.to} className={navCls}>
              <span className="grid h-5 w-5 place-items-center rounded-full bg-ink-700 text-[10px] font-bold text-slate-200">{n.letter}</span>
              {n.label}
            </NavLink>
          ))}
          <Group label="People" />
          {PEOPLE.map((n) => <NavLink key={n.to} to={n.to} className={navCls}><n.icon className="h-4 w-4" /> {n.label}</NavLink>)}
          <Group label="More detail" />
          {MORE.map((n) => <NavLink key={n.to} to={n.to} className={navCls}><n.icon className="h-4 w-4" /> {n.label}</NavLink>)}
        </nav>
        <div className="mt-6 px-5 text-[11px] leading-relaxed text-slate-500">
          Demo candidates are made up. Uses public sources only. Nobody is contacted automatically and people make every hiring decision.
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-slate-200 bg-white/90 px-6 py-3 backdrop-blur">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Business goal</span>
          <select className="input max-w-xl" value={custom ? "custom" : overrides.scenario_id || ""} onChange={(e) => setScenario(e.target.value)}>
            {custom && <option value="custom">Custom: {analysis?.journey.goal.title}</option>}
            {meta?.scenarios.map((s) => <option key={s.id} value={s.id}>{s.goal}</option>)}
          </select>
          {loading && <span className="text-xs text-slate-400">Recomputing…</span>}
          {error && <span className="text-xs text-rose-600">{error}</span>}
          <div className="ml-auto flex items-center gap-3 text-xs text-slate-500">
            {meta && <span>{meta.counts.jobs} open roles · {meta.counts.organisations} companies tracked</span>}
            <button className="btn-secondary !py-1.5" onClick={refresh} disabled={refreshing} title="Pull the public Cognition blog index and job board">
              <RefreshCw className={clsx("h-3.5 w-3.5", refreshing && "animate-spin")} /> Refresh data
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">
          {analysis && meta ? (
            <Routes>
              <Route path="/" element={<Navigate to="/goal" replace />} />
              <Route path="/goal" element={<Goal />} />
              <Route path="/hires" element={<KeyHires />} />
              <Route path="/where" element={<WhereToHire />} />
              <Route path="/map" element={<TalentMap />} />
              <Route path="/shortlist" element={<Shortlist />} />
              <Route path="/radar" element={<Radar_ />} />
              <Route path="/customers" element={<Customers />} />
              <Route path="/forecast" element={<Forecast />} />
              <Route path="/ecosystem" element={<Ecosystem />} />
              <Route path="/candidates" element={<Candidates />} />
              <Route path="/strategy" element={<Strategy />} />
              <Route path="/builders" element={<Builders />} />
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
