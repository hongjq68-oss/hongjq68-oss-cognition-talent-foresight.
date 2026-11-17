import clsx from "clsx";
import { ArrowRight, Check } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { HireWhen, KeyHire } from "../types";

export const STEPS = [
  { to: "/goal", label: "Business goal" },
  { to: "/hires", label: "Key hires" },
  { to: "/where", label: "Where to hire" },
  { to: "/map", label: "Talent map" },
  { to: "/shortlist", label: "Shortlist" },
];

export function StepHeader({ step, title, question, children }: { step: number; title: string; question: string; children?: ReactNode }) {
  return (
    <div className="mb-5 space-y-4">
      <ol className="flex flex-wrap items-center gap-1 text-xs">
        {STEPS.map((s, i) => (
          <li key={s.to} className="flex items-center gap-1">
            <Link to={s.to} className={clsx("flex items-center gap-1.5 rounded-full px-2.5 py-1",
              i + 1 === step ? "bg-ink-900 text-white" : i + 1 < step ? "bg-brand-50 text-brand-700" : "bg-slate-100 text-slate-500 hover:text-slate-800")}>
              <span className={clsx("grid h-4 w-4 place-items-center rounded-full text-[10px] font-bold", i + 1 === step ? "bg-white text-ink-900" : "bg-white/70")}>
                {i + 1 < step ? <Check className="h-3 w-3" /> : i + 1}
              </span>
              {s.label}
            </Link>
            {i < STEPS.length - 1 && <span className="text-slate-300">—</span>}
          </li>
        ))}
      </ol>
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{question}</p>
        </div>
        {children}
      </div>
    </div>
  );
}

export function NextStep({ step }: { step: number }) {
  const next = STEPS[step];
  if (!next) return null;
  return (
    <div className="flex justify-end">
      <Link to={next.to} className="btn bg-ink-900 text-white hover:bg-ink-800">
        Next: {next.label} <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}

const WHEN_CLS = { now: "bg-rose-50 text-rose-700 ring-rose-200", soon: "bg-amber-50 text-amber-800 ring-amber-200", later: "bg-slate-100 text-slate-600 ring-slate-300" };

export function WhenChip({ w }: { w: HireWhen }) {
  return <span className={clsx("chip ring-1 ring-inset whitespace-nowrap", WHEN_CLS[w.tone])}>{w.label}</span>;
}

export function RolePicker({ hires, value, onChange, count }: { hires: KeyHire[]; value: string; onChange: (id: string) => void; count?: (h: KeyHire) => ReactNode }) {
  return (
    <div className="flex flex-wrap gap-2">
      {hires.map((h) => (
        <button key={h.archetype_id} onClick={() => onChange(h.archetype_id)}
          className={clsx("btn !py-1.5", value === h.archetype_id ? "bg-ink-900 text-white" : "btn-secondary")}>
          {h.name}{count && <span className="text-xs opacity-70"> · {count(h)}</span>}
        </button>
      ))}
    </div>
  );
}

export function heatClass(v: number) {
  if (v >= 85) return "bg-brand-700 text-white";
  if (v >= 70) return "bg-brand-500 text-white";
  if (v >= 50) return "bg-brand-300 text-ink-900";
  if (v >= 30) return "bg-brand-100 text-ink-900";
  return "bg-slate-50 text-slate-500";
}

export const heatLabel = (v: number) => (v >= 85 ? "Very deep" : v >= 70 ? "Deep" : v >= 50 ? "Good" : v >= 30 ? "Some" : "Thin");
