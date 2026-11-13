import { useEffect, useState } from "react";
import { Download, Printer } from "lucide-react";
import { api } from "../api";
import { useApp } from "../state";
import { Cite, EvidenceBadge, EVIDENCE } from "../components/ui";
import type { EvidenceClass, Report } from "../types";

export default function ReportPage() {
  const { overrides, analysis } = useApp();
  const [r, setR] = useState<Report | null>(null);
  useEffect(() => { api.report(overrides).then(setR); }, [overrides, analysis]);
  const download = async () => {
    const md = await api.reportMd(overrides);
    const url = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
    const el = Object.assign(document.createElement("a"), { href: url, download: `talent-strategy-${r?.scenario_id}.md` });
    el.click();
    URL.revokeObjectURL(url);
  };
  if (!r) return <div className="text-sm text-slate-500">Building report…</div>;
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Executive Talent Strategy</div>
          <h1 className="text-2xl font-semibold text-slate-900">{r.title.replace("Executive Talent Strategy — ", "")}</h1>
        </div>
        <div className="flex gap-2 print:hidden">
          <button className="btn-secondary" onClick={download}><Download className="h-4 w-4" /> Markdown</button>
          <button className="btn-secondary" onClick={() => window.print()}><Printer className="h-4 w-4" /> Print / PDF</button>
        </div>
      </div>
      <div className="card flex flex-wrap gap-2 p-3 text-xs text-slate-500">
        <span className="mr-1 font-medium">Evidence key:</span>
        {(Object.keys(EVIDENCE) as EvidenceClass[]).map((k) => <EvidenceBadge key={k} c={k} />)}
      </div>
      {r.sections.map((s) => (
        <section key={s.number} className="card p-5">
          <h2 className="mb-3 text-base font-semibold text-slate-900">{s.number}. {s.title}</h2>
          <ul className="space-y-2.5">
            {s.items.map((it, i) => (
              <li key={i} className="text-sm text-slate-700">
                <div className="flex gap-2"><span className="shrink-0"><EvidenceBadge c={it.evidence_class} /></span><span>{it.text}</span></div>
                {it.citations.length > 0 && <div className="ml-1 mt-1 flex flex-wrap gap-x-4">{it.citations.map((c, j) => <Cite key={j} c={c} />)}</div>}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
