import clsx from "clsx";
import { ExternalLink, AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";
import type { Citation, EvidenceClass, Classification, PoolType } from "../types";

export const EVIDENCE: Record<EvidenceClass, { label: string; cls: string }> = {
  verified_fact: { label: "Verified fact", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  market_intel: { label: "Market intelligence", cls: "bg-sky-50 text-sky-700 ring-sky-200" },
  hypothesis: { label: "Strategic hypothesis", cls: "bg-amber-50 text-amber-800 ring-amber-200" },
  prediction: { label: "Engine prediction", cls: "bg-violet-50 text-violet-700 ring-violet-200" },
  recommendation: { label: "Recruiter recommendation", cls: "bg-slate-100 text-slate-700 ring-slate-300" },
};

export function EvidenceBadge({ c }: { c: EvidenceClass }) {
  const e = EVIDENCE[c];
  return <span className={clsx("chip ring-1 ring-inset whitespace-nowrap", e.cls)}>{e.label}</span>;
}

export const CLASSIFICATION: Record<Classification, { label: string; cls: string }> = {
  immediate: { label: "Immediate hire", cls: "bg-rose-50 text-rose-700 ring-rose-200" },
  emerging: { label: "Emerging", cls: "bg-orange-50 text-orange-700 ring-orange-200" },
  strategic: { label: "Strategic future", cls: "bg-indigo-50 text-indigo-700 ring-indigo-200" },
  develop: { label: "Develop internally", cls: "bg-teal-50 text-teal-700 ring-teal-200" },
  partner: { label: "Via partners", cls: "bg-slate-100 text-slate-700 ring-slate-300" },
};

export function ClassBadge({ c }: { c: Classification }) {
  const e = CLASSIFICATION[c];
  return <span className={clsx("chip ring-1 ring-inset whitespace-nowrap", e.cls)}>{e.label}</span>;
}

export const POOL: Record<PoolType, { label: string; short: string; cls: string }> = {
  direct: { label: "Direct industry talent", short: "Direct", cls: "bg-slate-100 text-slate-700" },
  adjacent: { label: "Adjacent technology talent", short: "Adjacent tech", cls: "bg-sky-50 text-sky-700" },
  customer_side: { label: "Customer-side talent", short: "Customer-side", cls: "bg-emerald-50 text-emerald-700" },
  consulting: { label: "Consulting & implementation", short: "Consulting/SI", cls: "bg-amber-50 text-amber-800" },
  founder: { label: "Founders & independent builders", short: "Founders", cls: "bg-fuchsia-50 text-fuchsia-700" },
};

export function PoolBadge({ p }: { p: PoolType }) {
  return <span className={clsx("chip", POOL[p].cls)}>{POOL[p].short}</span>;
}

export function Cite({ c }: { c: Citation }) {
  if (!c.url)
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-700">
        <AlertTriangle className="h-3 w-3" /> source needed
      </span>
    );
  return (
    <a href={c.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-brand-700 hover:underline">
      <ExternalLink className="h-3 w-3" />
      <span className="truncate max-w-[22rem]">{c.title}</span>
      {c.date && <span className="text-slate-400">· {c.date}</span>}
    </a>
  );
}

export function Card({ title, subtitle, right, children, className }: { title?: ReactNode; subtitle?: ReactNode; right?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={clsx("card p-5", className)}>
      {(title || right) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="section-title">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ letter, title, question, children }: { letter?: string; title: string; question: string; children?: ReactNode }) {
  return (
    <div className="mb-6 flex items-end justify-between gap-4">
      <div>
        <div className="flex items-center gap-2">
          {letter && <span className="grid h-6 w-6 place-items-center rounded-md bg-ink-900 text-xs font-bold text-white">{letter}</span>}
          <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        </div>
        <p className="mt-1 text-sm text-slate-500">{question}</p>
      </div>
      {children}
    </div>
  );
}

export function Bar({ value, className }: { value: number; className?: string }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-slate-100">
      <div className={clsx("h-1.5 rounded-full", className || "bg-brand-500")} style={{ width: `${Math.max(2, Math.min(100, value))}%` }} />
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

export function Sensitivity({ s, note }: { s: string; note: string | null }) {
  if (s === "none") return null;
  const label = { customer: "Cognition customer", partner: "Cognition partner", competitor: "Competitor" }[s] || s;
  return (
    <span title={note || ""} className="chip bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200">
      <AlertTriangle className="h-3 w-3" /> {label}
    </span>
  );
}

export const MARKET_NAMES: Record<string, string> = { SG: "Singapore", AU: "Australia", JP: "Japan", IN: "India", KR: "South Korea" };

export function List({ items, className }: { items: string[]; className?: string }) {
  return (
    <ul className={clsx("space-y-1 text-sm text-slate-600", className)}>
      {items.map((x) => (
        <li key={x} className="flex gap-2"><span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-slate-400" />{x}</li>
      ))}
    </ul>
  );
}
