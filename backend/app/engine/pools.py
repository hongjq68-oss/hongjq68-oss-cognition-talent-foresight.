"""Capability -> talent pools (5 pool types) and capability-led search strategies."""
from .kb import KB

POOL_TYPES = ["direct", "adjacent", "customer_side", "consulting", "founder"]
POOL_LABELS = {
    "direct": "Direct industry talent",
    "adjacent": "Adjacent technology talent",
    "customer_side": "Customer-side talent",
    "consulting": "Consulting & implementation talent",
    "founder": "Startup founders & independent builders",
}
# Proportion of the recommended search effort per pool type. Direct competitors are kept deliberately low.
POOL_EFFORT = {"direct": 0.10, "adjacent": 0.25, "customer_side": 0.25, "consulting": 0.20, "founder": 0.20}


def _market_fit(org: dict, markets: dict) -> float:
    best = max((markets.get(m, 0) for m in org["markets"]), default=0)
    if "GLOBAL" in org["markets"] or "APAC" in org["markets"]:
        best = max(best, 0.6)
    return best


def pools_for_capability(kb: KB, cap_id: str, sc: dict, per_type: int = 4) -> dict:
    markets = {m: w for m, w in sc["market_weights"].items() if w > 0}
    segs = sc["segment_weights"]
    out = {}
    for pt in POOL_TYPES:
        cands = []
        for o in kb.organisations:
            if o["pool_type"] != pt or cap_id not in o["capability_ids"]:
                continue
            mf = _market_fit(o, markets)
            if mf <= 0:
                continue
            sf = max((segs.get(s, 0) for s in o["segment_ids"]), default=0)
            score = round(0.6 * mf + 0.4 * sf, 3)
            cands.append(org_view(o) | {"score": score})
        out[pt] = {"label": POOL_LABELS[pt], "organisations": sorted(cands, key=lambda x: -x["score"])[:per_type]}
    return out


def org_view(o: dict) -> dict:
    return {k: o[k] for k in ("id", "name", "pool_type", "markets", "why_relevant", "teams", "starting_titles",
                              "value_to_cognition", "sensitivity", "sensitivity_note")} | {"evidence_class": "market_intel"}


def ecosystem(kb: KB, sc: dict, capabilities: list[dict], top_n: int = 12) -> list[dict]:
    """Organisations ranked by how many in-demand capabilities they can supply for this scenario."""
    markets = {m: w for m, w in sc["market_weights"].items() if w > 0}
    demand = {c["id"]: c["peak"] for c in capabilities}
    rows = []
    for o in kb.organisations:
        mf = _market_fit(o, markets)
        if mf <= 0:
            continue
        caps = [c for c in o["capability_ids"] if c in demand]
        cover = sum(demand[c] for c in caps) / 100
        if not caps:
            continue
        sf = max((sc["segment_weights"].get(s, 0) for s in o["segment_ids"]), default=0)
        rows.append(org_view(o) | {"score": round(cover * (0.5 + 0.5 * mf) * (0.6 + 0.4 * sf), 2),
                                   "capabilities": sorted(caps, key=lambda c: -demand[c])[:6]})
    rows.sort(key=lambda x: -x["score"])
    by_type = {pt: [r for r in rows if r["pool_type"] == pt][:top_n] for pt in POOL_TYPES}
    return [{"pool_type": pt, "label": POOL_LABELS[pt], "effort_share": POOL_EFFORT[pt], "organisations": by_type[pt]} for pt in POOL_TYPES]


def rank_archetypes(kb: KB, capabilities: list[dict], hiring: dict) -> list[dict]:
    cap = {c["id"]: c for c in capabilities}
    out = []
    for a in kb.archetypes.values():
        w = a["capability_weights"]
        total = sum(w.values())
        score = sum(wt * cap[c]["peak"] for c, wt in w.items() if c in cap) / total
        horizon = min((cap[c]["need_by"] for c, wt in w.items() if c in cap and wt >= 0.8 and cap[c]["need_by"]), default=None)
        out.append({
            "id": a["id"], "name": a["name"], "summary": a["summary"], "score": round(score, 1),
            "capabilities": [{"id": c, "name": kb.capabilities[c]["name"], "weight": wt,
                              "demand": cap[c]["peak"] if c in cap else 0} for c, wt in sorted(w.items(), key=lambda kv: -kv[1])],
            "unconventional_backgrounds": a["unconventional_backgrounds"], "assessment": a["assessment"],
            "open_roles": hiring["by_archetype"].get(a["id"], []), "need_by": horizon,
            "evidence_class": "recommendation",
        })
    return sorted(out, key=lambda x: -x["score"])


def search_strategy(kb: KB, archetype: dict, sc: dict, capabilities: list[dict]) -> dict:
    """Capability-based search strings for approved sources. Never title-only; never scrapes restricted networks."""
    cap_rank = {c["id"]: c["peak"] for c in capabilities}
    caps = sorted(archetype["capabilities"], key=lambda c: -(c["weight"] * cap_rank.get(c["id"], 0)))[:4]
    phrases = []
    for c in caps:
        phrases.append(kb.capabilities[c["id"]]["evidence_phrases"][:3])
    markets = [m for m, w in sorted(sc["market_weights"].items(), key=lambda kv: -kv[1]) if w >= 0.6]
    names = {"SG": "Singapore", "AU": "Australia OR Sydney OR Melbourne", "JP": "Japan OR Tokyo", "IN": "India OR Bengaluru OR Mumbai", "KR": "Korea OR Seoul"}
    geo = " OR ".join(names[m] for m in markets if m in names)
    grp = lambda ps: "(" + " OR ".join(f'"{p}"' for p in ps) + ")"
    core = " AND ".join(grp(p) for p in phrases[:2])
    pools = pools_for_capability(kb, caps[0]["id"], sc, per_type=3)
    target_orgs = [o["name"] for pt in POOL_TYPES if pt != "direct" for o in pools[pt]["organisations"]][:8]
    return {
        "archetype_id": archetype["id"],
        "focus_capabilities": [c["name"] for c in caps],
        "evidence_to_look_for": [p for ps in phrases for p in ps],
        "queries": [
            {"source": "GitHub (API, public repos & profiles)", "query": " ".join(phrases[0][:2]) + (f" location:{markets[0]}" if markets else ""),
             "note": "Look for maintained repos, merged PRs into enterprise-grade projects; ignore star counts."},
            {"source": "Conference talks & engineering blogs (web search)", "query": f"{core} (talk OR keynote OR \"case study\") ({geo})" if geo else core,
             "note": "Public talks/blogs show what someone actually built and the problem they solved."},
            {"source": "Press releases & customer case studies", "query": f"{grp(phrases[0])} (bank OR insurer) (\"led\" OR \"delivered\") ({geo})" if geo else grp(phrases[0]),
             "note": "Named project leads in announcements are strong public evidence."},
            {"source": "Recruiter's licensed tools (manual — e.g. LinkedIn Recruiter seat)", "query": core,
             "note": "Run manually under the platform's terms. This app does not scrape or automate restricted networks."},
        ],
        "target_organisations": target_orgs,
        "avoid": ["Searching on job titles alone", "Defaulting to direct AI competitors", "Approaching staff at named Cognition customers/partners without a relationship policy"],
        "evidence_class": "recommendation",
    }
