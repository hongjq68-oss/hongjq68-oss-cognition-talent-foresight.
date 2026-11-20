"""Executive Talent Strategy report: 11 sections, every item tagged with an evidence class and citations."""
from .forecast import CLASS_LABELS
from .pools import POOL_LABELS

EVIDENCE_LABELS = {"verified_fact": "Verified fact", "market_intel": "Market intelligence", "hypothesis": "Strategic hypothesis",
                   "prediction": "Engine prediction", "recommendation": "Recruiter recommendation"}


def _i(text, cls, cites=()):
    return {"text": text, "evidence_class": cls, "citations": list(cites)}


def build(a: dict) -> dict:
    sc, caps, probs = a["scenario"], a["capabilities"], a["problems"]
    cn = a.get("company_name", "Cognition")
    top_caps = caps[:10]
    immediate = [c for c in caps if c["classification"] == "immediate"]
    emerging = [c for c in caps if c["classification"] == "emerging"]
    strategic = [c for c in caps if c["classification"] == "strategic"]
    develop = [c for c in caps if c["classification"] == "develop"][:5]
    partner = [c for c in caps if c["classification"] == "partner"][:5]
    hiring = a["radar"]["hiring"]
    sections = [
        ("Business goal", [_i(sc["hypothesis"], "hypothesis")] + [_i(x, "hypothesis") for x in sc["business_changes"]]),
        ("Why we think this", [_i(f"{d['title']} — {d['summary']}", d["evidence_class"], [d]) for d in a["radar"]["drivers"]]
         + [_i(f"{cn} lists {hiring['in_scenario_markets']} open roles in the scenario markets ({', '.join(f'{m}: {n}' for m, n in hiring['by_market'].items())}).",
               "verified_fact", [hiring["source"]])]),
        ("Customer problems", [_i(f"{p['segment']}: {p['name']} — {p['description']}", p["evidence_class"], p["citations"]) for p in probs[:7]]),
        ("Skills we need", [_i(f"{c['name']} ({c['category']}) — {c['classification_label']}; peak demand {c['peak']:.0f}/100, "
                                        f"scarcity {c['scarcity']}/5, lead time ~{c['lead_weeks']} weeks, confidence {c['confidence']}.", "prediction") for c in top_caps]),
        ("Key hires", [_i(f"{x['name']} — {x['summary']} (demand score {x['score']:.0f}; "
                                  f"{len(x['open_roles'])} matching open {cn} roles)", "recommendation",
                                  [{"title": r["title"], "url": r["url"], "date": r["published_on"], "evidence_class": "verified_fact"} for r in x["open_roles"][:3]])
                               for x in a["archetypes"][:6]]),
        ("Less obvious places to find people", [_i(f"{g['label']}: " + "; ".join(o["name"] for o in g["organisations"][:5]), "market_intel")
                                            for g in a["ecosystem"] if g["pool_type"] != "direct"]
         + [_i(f"{x['name']}: " + "; ".join(x["unconventional_backgrounds"]), "recommendation") for x in a["archetypes"][:3]]),
        ("Where to hire", [_i(f"{o['name']} ({POOL_LABELS[o['pool_type']]}) — {o['value_to_cognition']}"
                                               + (f" ⚠ {o['sensitivity_note']}" if o["sensitivity"] != "none" else ""), "market_intel")
                                            for o in sorted([o for g in a["ecosystem"] for o in g["organisations"]], key=lambda o: -o["score"])[:10]]
         + [_i("Market priority: " + ", ".join(f"{m} ({w:g})" for m, w in sorted(sc["market_weights"].items(), key=lambda kv: -kv[1])), "hypothesis")]),
        ("How to find people", [_i(f"{s['focus_capabilities'][0]}: look for " + ", ".join(s["evidence_to_look_for"][:5])
                                                    + f". Start with {', '.join(s['target_organisations'][:4])}.", "recommendation") for s in a["strategies"][:4]]
         + [_i(f"{c['display_name']} (demo profile) — {c['best_fit']['archetype']}, fit {c['best_fit']['score']:.0f}. {c['transferability']}", "recommendation")
            for c in a["candidates"][:5]]),
        ("Hiring timeline", [_i(f"{c['name']}: start search by {c['start_search_by']} to have this skill by {c['need_by']} ({CLASS_LABELS[c['classification']]}).", "prediction")
                             for c in (immediate + emerging)[:10] if c["start_search_by"]]
         + [_i(f"{c['name']}: strategic — build pipeline and relationships; no requisition yet.", "prediction") for c in strategic[:3]]
         + [_i(f"{c['name']}: develop internally through enablement rather than external hiring.", "recommendation") for c in develop]
         + [_i(f"{c['name']}: likely delivered through partners (SI / hyperscaler).", "recommendation") for c in partner]),
        ("Risks and assumptions", [_i(x, "hypothesis") for x in sc["derailers"]] + [_i("Assumption: " + x, "hypothesis") for x in sc.get("assumptions", [])]
         + [_i("Alternative: " + x, "hypothesis") for x in sc["alternatives"]]
         + [_i("All candidate profiles in this prototype are synthetic. Organisation talent pools are analyst hypotheses to validate.", "hypothesis")]),
        ("Recommended next actions for the recruiter", [
            _i(f"Open pipeline-building for {', '.join(c['name'] for c in immediate[:3]) or 'the top emerging skills'} this month.", "recommendation"),
            _i(f"Validate the top {min(5, len(a['candidates']))} shortlisted people's past work before anyone is contacted.", "recommendation"),
            _i("Agree a relationship policy with account and alliance teams for customer/partner organisations flagged ⚠.", "recommendation"),
            _i("Run the skill-based searches above; log every source used.", "recommendation"),
            _i("Brief the hiring manager on the forecast and confirm which skills to hire, train or get through partners.", "recommendation"),
        ]),
    ]
    return {"title": f"Executive Talent Strategy — {sc['name']}", "scenario_id": sc["id"],
            "sections": [{"number": i + 1, "title": t, "items": items} for i, (t, items) in enumerate(sections)],
            "evidence_labels": EVIDENCE_LABELS}


def to_markdown(r: dict) -> str:
    lines = [f"# {r['title']}", "", "_Evidence key: " + "; ".join(f"[{v}]" for v in r["evidence_labels"].values()) + "_", ""]
    for s in r["sections"]:
        lines += [f"## {s['number']}. {s['title']}", ""]
        for it in s["items"]:
            cites = "; ".join(f"[{c['title']}]({c['url']}) ({c.get('date') or 'n.d.'})" if c.get("url") else f"{c['title']} (source needed)"
                              for c in it["citations"])
            lines.append(f"- **[{r['evidence_labels'][it['evidence_class']]}]** {it['text']}" + (f" — {cites}" if cites else ""))
        lines.append("")
    return "\n".join(lines)
