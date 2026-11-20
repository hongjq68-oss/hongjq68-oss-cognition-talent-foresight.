"""Business goal -> key hires -> where to hire -> talent heat map -> auto-shortlist, in plain language."""
import json
from datetime import date, timedelta

from . import candidates as cand_engine
from .kb import KB

MARKETS = ["SG", "JP", "AU", "IN", "KR"]
MARKET_NAMES = {"SG": "Singapore", "JP": "Japan", "AU": "Australia", "IN": "India", "KR": "South Korea"}
LOCATION_WORDS = {
    "SG": ["singapore"],
    "JP": ["japan", "tokyo", "osaka", "kyoto", "fukuoka"],
    "AU": ["australia", "sydney", "melbourne", "brisbane", "perth", "canberra"],
    "IN": ["india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", "pune", "chennai", "gurgaon", "noida"],
    "KR": ["korea", "seoul"],
}
AREAS = {
    "direct": "AI coding & dev-tool companies",
    "adjacent": "Tech & cloud companies",
    "customer_side": "Banks & enterprise tech teams",
    "consulting": "Consultancies & SIs",
    "founder": "Founders & startups",
}
GOALS = {
    "apac_banking": ("Win 3 more major banks in APAC in the next 12 months",
                     ["3 new tier-1 bank customers (e.g. Singapore, Australia, Japan)",
                      "Every bank live past pilot within 6 months",
                      "OCBC-style results become the reference story"]),
    "consulting_partnership": ("Grow APAC revenue through a big consulting partner",
                               ["Most new enterprise deals come through a partner",
                                "Partner teams can deliver Devin work without us",
                                "India becomes the partner delivery hub"]),
    "japan_aggressive": ("Build Cognition Japan into a full country business",
                         ["Named bank, manufacturing and SIer customers in Japan",
                          "A local team that sells and delivers in Japanese",
                          "Japan partners resell and deliver Devin"]),
    "enterprise_ai_scale": ("Take enterprise customers from pilots to large-scale use",
                            ["Thousands of agent sessions a week per customer",
                             "Clear productivity numbers customers trust",
                             "Governance that passes security and risk review"]),
    "new_product_security": ("Make Devin Security a lead product for APAC banks and insurers",
                             ["Security-led deals with banks, insurers and telcos",
                              "Measurable cuts in customers' vulnerability backlog",
                              "Security teams become Devin champions"]),
    "account_expansion": ("Grow usage inside the customers we already have",
                          ["More teams and use cases in each existing account",
                           "Higher renewal and expansion revenue",
                           "Proven results that make expansion easy to approve"]),
}


def market_of(location: str | None) -> str | None:
    loc = (location or "").lower()
    for m, words in LOCATION_WORDS.items():
        if any(w in loc for w in words):
            return m
    return None


def _when(need_by: str | None, start_by: str | None, today: date) -> dict:
    if not need_by:
        return {"label": "Later (12+ months)", "tone": "later", "start_by": start_by, "need_by": None}
    nb = date.fromisoformat(need_by)
    if (start_by and date.fromisoformat(start_by) <= today + timedelta(weeks=4)) or nb <= today + timedelta(weeks=13):
        return {"label": "Start now", "tone": "now", "start_by": start_by, "need_by": need_by}
    if nb <= today + timedelta(weeks=26):
        return {"label": "Next 6 months", "tone": "soon", "start_by": start_by, "need_by": need_by}
    return {"label": "Within 12 months", "tone": "later", "start_by": start_by, "need_by": need_by}


def _overlap(weights: dict, caps) -> float:
    total = sum(weights.values()) or 1
    return sum(w for c, w in weights.items() if c in caps) / total


def heat_map(kb: KB, archetype_ids: list[str]) -> dict:
    """Talent supply per role type x country, from the organisations that build these skills there."""
    raw = {}
    for aid in archetype_ids:
        w = kb.archetypes[aid]["capability_weights"]
        for m in MARKETS:
            orgs = []
            for o in kb.organisations:
                if m in o["markets"]:
                    presence = 1.0
                elif "APAC" in o["markets"] or "GLOBAL" in o["markets"]:
                    presence = 0.5
                else:
                    continue
                ov = _overlap(w, o["capability_ids"])
                if ov < 0.3:
                    continue
                orgs.append((ov * presence, o))
            orgs.sort(key=lambda x: -x[0])
            raw[(aid, m)] = (sum(s for s, _ in orgs), orgs)
    top = max((v[0] for v in raw.values()), default=1) or 1
    cells = {}
    for (aid, m), (s, orgs) in raw.items():
        areas = {}
        for _, o in orgs:
            areas[o["pool_type"]] = areas.get(o["pool_type"], 0) + 1
        cells[(aid, m)] = {
            "supply": round(100 * s / top),
            "companies": [{"name": o["name"], "area": AREAS[o["pool_type"]], "pool_type": o["pool_type"],
                           "local": m in o["markets"], "sensitivity": o["sensitivity"], "teams": o["teams"][:2]}
                          for _, o in orgs[:6]],
            "areas": sorted(({"pool_type": k, "label": AREAS[k], "count": v} for k, v in areas.items()), key=lambda x: -x["count"]),
        }
    return cells


def _leads(conn) -> list[dict]:
    try:
        rows = conn.execute("SELECT * FROM leads WHERE status='new'").fetchall()
    except Exception:
        return []
    out = []
    for r in rows:
        d = dict(r)
        for k in ("capability_ids", "evidence"):
            if isinstance(d.get(k), str):
                d[k] = json.loads(d[k])
        out.append(d)
    return out


def build(kb: KB, conn, sc: dict, capabilities: list[dict], archetypes: list[dict], problems: list[dict],
          n_hires: int = 6, today: date | None = None) -> dict:
    today = today or date.today()
    cap = {c["id"]: c for c in capabilities}
    hires_a = archetypes[:n_hires]
    ids = [a["id"] for a in hires_a]
    cells = heat_map(kb, ids)
    goal_w = {m: sc["market_weights"].get(m, 0) for m in MARKETS}
    role_lists = cand_engine.role_shortlists(kb, conn, sc, capabilities, ids, size=100)
    leads = _leads(conn)

    hires, map_rows = [], []
    for a in hires_a:
        w = kb.archetypes[a["id"]]["capability_weights"]
        must = [c for c in a["capabilities"] if c["weight"] >= 0.7][:3]
        starts = [cap[c["id"]]["start_search_by"] for c in must if c["id"] in cap and cap[c["id"]]["start_search_by"]]
        when = _when(a["need_by"], min(starts) if starts else None, today)
        top_cap = cap.get(must[0]["id"]) if must else None
        why = next((d["label"] for d in (top_cap or {}).get("drivers", []) if d["type"] in ("problem", "gtm")), None)
        if why:
            why = (f"helps {why[0].lower()}{why[1:]}" if sc.get("inferred") and not why.startswith("Go-to-market")
                   else f"needed for {why[0].lower()}{why[1:]}")
        open_in_goal = [r for r in a["open_roles"] if goal_w.get(r["market"], 0) > 0]
        if sc.get("inferred") and len(open_in_goal) >= 2 and when["tone"] != "now":
            # For an inferred plan, live postings are the strongest signal that the hire is needed today.
            when = when | {"label": "Start now", "tone": "now", "note": "Already hiring"}

        countries = []
        for m in MARKETS:
            c = cells[(a["id"], m)]
            priority = round(0.5 * 100 * goal_w[m] + 0.5 * c["supply"])
            countries.append({"market": m, "name": MARKET_NAMES[m], "goal_weight": goal_w[m], "supply": c["supply"],
                              "priority": priority, "open_roles": sum(1 for r in a["open_roles"] if r["market"] == m)})
        countries.sort(key=lambda x: -x["priority"])
        where = [c for c in countries if c["goal_weight"] > 0][:3]
        hot = {c["market"] for c in where[:2]}
        area_count = {}
        for c in where:
            for ar in cells[(a["id"], c["market"])]["areas"]:
                area_count[ar["pool_type"]] = area_count.get(ar["pool_type"], 0) + ar["count"]
        top_areas = [k for k, _ in sorted(area_count.items(), key=lambda kv: -kv[1]) if k != "direct"][:3]
        companies, seen = [], set()
        for c in where:
            for o in cells[(a["id"], c["market"])]["companies"]:
                if o["name"] not in seen and o["pool_type"] != "direct":
                    seen.add(o["name"])
                    companies.append(o | {"market": c["market"]})
        companies = companies[:8]
        company_words = [o["name"].split(" (")[0].lower() for o in companies]

        people = []
        for r in role_lists[a["id"]]:
            reasons = [f"Proven skills: {', '.join(r['strengths'][:2])}"] if r["strengths"] else []
            bonus = 0
            if r["market"] in hot:
                bonus += 10
                reasons.append(f"Based in {MARKET_NAMES.get(r['market'], r['market'])}, a top country for this hire")
            if r["pool_type"] in top_areas:
                bonus += 6
                reasons.append(f"Comes from a top area: {AREAS[r['pool_type']]}")
            emp = (r["employer_descriptor"] or "").lower()
            if any(cw and cw in emp for cw in company_words):
                bonus += 4
                reasons.append("Works at a target company")
            people.append(r | {"match": min(100, round(0.8 * r["score"] + bonus + 4)), "reasons": reasons})
        people.sort(key=lambda x: -x["match"])

        builders = []
        for ld in leads:
            ov = _overlap(w, ld["capability_ids"])
            if ov <= 0:
                continue
            lm = market_of(ld.get("location"))
            if lm and goal_w.get(lm, 0) <= 0:
                continue
            match = round(55 * ov + (20 if lm in hot else 8 if lm else 0) + min(10, 3 * len(ld["evidence"])))
            builders.append({"lead_id": ld["id"], "display_name": ld["display_name"], "source": ld["source"],
                             "profile_url": ld["profile_url"], "market": lm, "location": ld.get("location"),
                             "match": match, "work": [e["claim"] for e in ld["evidence"][:2]],
                             "skills": [kb.capabilities[c]["name"] for c in ld["capability_ids"] if c in w and c in kb.capabilities][:3]})
        builders.sort(key=lambda x: -x["match"])

        hires.append({
            "archetype_id": a["id"], "name": a["name"], "summary": a["summary"], "score": a["score"],
            "why": why, "when": when, "must_have": [c["name"] for c in must],
            "open_roles": len(open_in_goal), "open_role_links": open_in_goal[:4],
            "headcount": max(1, len(open_in_goal)),
            "where": where, "areas": [{"pool_type": k, "label": AREAS[k]} for k in top_areas],
            "companies": companies, "also_consider": a["unconventional_backgrounds"][:3],
            "shortlist": people[:8], "builders": builders[:5],
        })
        map_rows.append({"archetype_id": a["id"], "name": a["name"],
                         "cells": [{"market": m, **cells[(a["id"], m)],
                                    "goal_weight": goal_w[m],
                                    "in_pipeline": sum(1 for r in role_lists[a["id"]] if r["market"] == m)} for m in MARKETS]})

    title, outcomes = GOALS.get(sc.get("id"), (sc.get("goal") or sc["name"], sc.get("outcomes") or sc.get("business_changes", [])[:3]))
    return {
        "goal": {"title": title, "outcomes": outcomes, "story": sc["hypothesis"],
                 "inferred": bool(sc.get("inferred")), "basis": sc.get("basis", []),
                 "what_changes": sc.get("business_changes", [])[:4], "risks": sc.get("derailers", [])[:3],
                 "customer_problems": [p["name"] for p in problems[:3]],
                 "top_markets": [MARKET_NAMES[m] for m, wt in sorted(goal_w.items(), key=lambda kv: -kv[1]) if wt >= 0.6]},
        "hires": hires,
        "map": {"markets": [{"id": m, "name": MARKET_NAMES[m], "goal_weight": goal_w[m]} for m in MARKETS], "rows": map_rows},
    }
