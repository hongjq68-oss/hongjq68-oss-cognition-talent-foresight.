"""Business signal -> customer problem -> capability demand -> horizon forecast.

All scoring is deterministic and returns its working so every number in the UI can be explained."""
from datetime import date, timedelta

from .kb import KB, cite

HORIZONS = ["now", "6m", "12m", "24m"]
HORIZON_WEEKS = [0, 26, 52, 104]
GTM_PROFILE = [0.8, 1.0, 1.0, 0.9]
GTM_SCALE = 1.6
EXTRA_PROFILE = [0.5, 1.0, 1.0, 0.8]
SCENARIO_RAMP = [0.55, 0.8, 1.0, 1.0]  # a scenario materialises over ~12 months
HIRING_PROFILE = [1.0, 0.8, 0.4, 0.2]  # open Cognition roles = demand that exists today
HIRING_UNIT = 0.18
NEED_THRESHOLD = 55.0
MARKET_LEAD_ADJ = {"JP": 6, "KR": 4}  # language / market-entry friction (assumption)

CLASS_LABELS = {
    "immediate": "Immediate hiring requirement",
    "emerging": "Emerging talent requirement",
    "strategic": "Strategic future capability",
    "develop": "Capability better developed internally",
    "partner": "Capability potentially delivered through partners",
}


def resolve_scenario(kb: KB, scenario_id: str | None = None, overrides: dict | None = None) -> dict:
    base = dict(kb.scenarios[scenario_id]["data"]) if scenario_id else {
        "hypothesis": "Custom scenario", "signal_ids": [], "segment_weights": {}, "market_weights": {},
        "capability_boosts": {}, "business_changes": [], "derailers": [], "alternatives": [], "extra_demand": {}, "assumptions": []}
    base["id"] = scenario_id or "custom"
    base["name"] = kb.scenarios[scenario_id]["name"] if scenario_id else (overrides or {}).get("name", "Custom scenario")
    for k, v in (overrides or {}).items():
        if k in ("segment_weights", "market_weights", "capability_boosts", "extra_demand") and isinstance(v, dict):
            base[k] = {**base.get(k, {}), **{a: float(b) for a, b in v.items()}}
        elif k in ("hypothesis",):
            base[k] = v
    return base


def business_radar(kb: KB, sc: dict) -> dict:
    segs = {s for s, w in sc["segment_weights"].items() if w > 0}
    markets = {m for m, w in sc["market_weights"].items() if w > 0}
    drivers = [cite(kb, s) | {"summary": kb.signals[s]["summary"], "kind": kb.signals[s]["kind"]} for s in sc["signal_ids"] if s in kb.signals]
    related = []
    for s in kb.signals.values():
        if s["id"] in sc["signal_ids"]:
            continue
        if set(s["segment_ids"]) & segs and (set(s["regions"]) & (markets | {"GLOBAL", "APAC"})):
            related.append(cite(kb, s["id"]) | {"summary": s["summary"], "kind": s["kind"]})
    related.sort(key=lambda x: x["date"] or "", reverse=True)
    hiring = hiring_signals(kb, markets)
    return {"drivers": drivers, "related": related, "hiring": hiring}


def hiring_signals(kb: KB, markets: set[str]) -> dict:
    """Public Cognition job postings in scenario markets, grouped by department and archetype."""
    in_market = [j for j in kb.jobs if j["market"] in markets]
    by_dept: dict[str, int] = {}
    for j in in_market:
        by_dept[j["department"] or "Other"] = by_dept.get(j["department"] or "Other", 0) + 1
    by_arch = {}
    for a in kb.archetypes.values():
        hits = [j for j in in_market if any(k.lower() in j["title"].lower() for k in a["posting_keywords"])]
        if hits:
            by_arch[a["id"]] = [{"title": j["title"], "url": j["url"], "market": j["market"], "published_on": j["published_on"]} for j in hits]
    by_market = {m: sum(1 for j in in_market if j["market"] == m) for m in sorted(markets)}
    return {"total_open_roles": len(kb.jobs), "in_scenario_markets": len(in_market), "by_department": by_dept,
            "by_market": by_market, "by_archetype": by_arch,
            "source": {"title": "Cognition public job board (Ashby)", "url": "https://jobs.ashbyhq.com/cognition",
                       "date": max((j["retrieved_on"] or "" for j in kb.jobs), default=None), "evidence_class": "verified_fact"}}


def rank_problems(kb: KB, sc: dict) -> list[dict]:
    out = []
    drivers = set(sc["signal_ids"])
    for p in kb.problems.values():
        w = sc["segment_weights"].get(p["segment_id"], 0)
        if w <= 0:
            continue
        support = [s for s in p["signal_ids"] if s in kb.signals]
        boost = 1 + 0.1 * min(len(support), 3) + 0.15 * len(drivers & set(support))
        relevance = round(p["severity"] * w * boost, 3)
        caps = sorted(kb.problem_caps.get(p["id"], {}).items(), key=lambda kv: -kv[1][0])
        out.append({
            "id": p["id"], "segment_id": p["segment_id"], "segment": kb.segments[p["segment_id"]]["name"],
            "name": p["name"], "description": p["description"], "severity": p["severity"], "complexity": p["complexity"],
            "pattern": p["pattern"], "relevance": relevance, "horizon_profile": p["horizon_profile"],
            "cognition_use_cases": p["cognition_use_cases"], "adoption_barriers": p["adoption_barriers"],
            "evidence_class": p["evidence_class"], "citations": [cite(kb, s) for s in support],
            "capabilities": [{"id": c, "name": kb.capabilities[c]["name"], "weight": wt, "rationale": why} for c, (wt, why) in caps],
            "why": f"Segment weight {w:g} × severity {p['severity']:g} × evidence boost {boost:.2f}",
        })
    return sorted(out, key=lambda x: -x["relevance"])


def capability_forecast(kb: KB, sc: dict, problems: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    raw: dict[str, list[float]] = {c: [0.0] * 4 for c in kb.capabilities}
    drivers: dict[str, list[dict]] = {c: [] for c in kb.capabilities}
    from ..seed.segments import SEGMENT_GTM  # static GTM weights per segment
    from ..seed.generic import THEME_GTM
    SEGMENT_GTM = SEGMENT_GTM | THEME_GTM

    for p in problems:
        for c in p["capabilities"]:
            for h in range(4):
                raw[c["id"]][h] += p["relevance"] * p["horizon_profile"][h] * c["weight"] * SCENARIO_RAMP[h]
            drivers[c["id"]].append({"type": "problem", "id": p["id"], "label": p["name"], "contribution": round(p["relevance"] * c["weight"], 3)})
    for seg, w in sc["segment_weights"].items():
        for cid, gw in SEGMENT_GTM.get(seg, {}).items():
            for h in range(4):
                raw[cid][h] += GTM_SCALE * w * gw * GTM_PROFILE[h] * SCENARIO_RAMP[h]
            drivers[cid].append({"type": "gtm", "id": seg, "label": f"Go-to-market in {kb.segments[seg]['name']}", "contribution": round(GTM_SCALE * w * gw, 3)})
    for cid, x in sc.get("extra_demand", {}).items():
        for h in range(4):
            raw[cid][h] += x * EXTRA_PROFILE[h]
        drivers[cid].append({"type": "scenario", "id": sc["id"], "label": "Scenario-specific demand", "contribution": x})
    markets = {m: w for m, w in sc["market_weights"].items() if w > 0}
    hiring = hiring_signals(kb, set(markets))
    for aid, roles in hiring["by_archetype"].items():
        n = min(len(roles), 4)
        for cid, wt in kb.archetypes[aid]["capability_weights"].items():
            if wt < 0.6:
                continue
            for h in range(4):
                raw[cid][h] += HIRING_UNIT * n * wt * HIRING_PROFILE[h]
            drivers[cid].append({"type": "hiring", "id": aid, "label": f"{len(roles)} open Cognition role(s): {kb.archetypes[aid]['name']}",
                                 "contribution": round(HIRING_UNIT * n * wt, 3)})
    for cid, b in sc.get("capability_boosts", {}).items():
        raw[cid] = [v * b for v in raw[cid]]

    peak = max((max(v) for v in raw.values()), default=1) or 1
    lead_adj = max((MARKET_LEAD_ADJ.get(m, 0) for m, w in markets.items() if w >= 0.7), default=0)
    out = []
    for cid, vals in raw.items():
        if max(vals) <= 0:
            continue
        cap = kb.capabilities[cid]
        demand = [round(100 * v / peak, 1) for v in vals]
        lead = cap["base_lead_weeks"] + (cap["scarcity"] - 3) * 2 + (lead_adj if cap["scarcity"] >= 4 else 0)
        need_idx = next((h for h, d in enumerate(demand) if d >= NEED_THRESHOLD), None)
        need_by = today + timedelta(weeks=HORIZON_WEEKS[need_idx]) if need_idx is not None else None
        start_by = need_by - timedelta(weeks=lead) if need_by else None
        cls = classify(cap, need_idx, start_by, today)
        support_arch = [a for a in kb.archetypes.values() if a["capability_weights"].get(cid, 0) >= 0.6 and a["id"] in hiring["by_archetype"]]
        conf, factors = confidence(drivers[cid], problems, support_arch, need_idx)
        out.append({
            "id": cid, "name": cap["name"], "category": cap["category"], "description": cap["description"],
            "demand": dict(zip(HORIZONS, demand)), "peak": max(demand), "scarcity": cap["scarcity"],
            "lead_weeks": lead, "need_by": need_by.isoformat() if need_by else None,
            "start_search_by": start_by.isoformat() if start_by else None,
            "classification": cls, "classification_label": CLASS_LABELS[cls], "delivery_tendency": cap["delivery_tendency"],
            "confidence": conf, "confidence_factors": factors,
            "drivers": sorted(drivers[cid], key=lambda d: -d["contribution"])[:6],
            "hiring_signal_roles": sum(len(hiring["by_archetype"][a["id"]]) for a in support_arch),
            "evidence_class": "prediction",
        })
    return sorted(out, key=lambda x: -x["peak"])


def classify(cap: dict, need_idx: int | None, start_by: date | None, today: date) -> str:
    if cap["delivery_tendency"] == "partner":
        return "partner"
    if cap["delivery_tendency"] == "develop" and cap["scarcity"] <= 3:
        return "develop"
    if need_idx is None:
        return "strategic"
    if start_by and start_by <= today + timedelta(weeks=4):
        return "immediate"
    if need_idx <= 2:
        return "emerging"
    return "strategic"


def confidence(drivers: list[dict], problems: list[dict], hiring_arch: list, need_idx: int | None) -> tuple[str, list[str]]:
    probs = {p["id"]: p for p in problems}
    linked = [probs[d["id"]] for d in drivers if d["type"] == "problem" and d["id"] in probs]
    cited = sum(1 for p in linked if any(c["evidence_class"] == "verified_fact" for c in p["citations"]))
    score, factors = 0.3, []
    if cited:
        score += min(0.3, 0.1 * cited)
        factors.append(f"{cited} driving problem(s) backed by dated public Cognition sources")
    else:
        factors.append("No driving problem is backed by a public Cognition source")
    if hiring_arch:
        score += 0.2
        factors.append("Cognition is already hiring roles that need this capability in these markets")
    if len(linked) >= 3:
        score += 0.1
        factors.append(f"Required by {len(linked)} customer problems")
    if need_idx is not None and need_idx >= 2:
        score -= 0.1
        factors.append("Need falls 12+ months out — more uncertainty")
    label = "high" if score >= 0.7 else "medium" if score >= 0.5 else "low"
    return label, factors
