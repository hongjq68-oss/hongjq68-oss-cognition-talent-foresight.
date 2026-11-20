"""Runs the full pipeline for one scenario."""
from datetime import date

from . import candidates as cand_engine
from . import forecast, journey, pools
from .kb import KB


def run(kb: KB, conn, scenario_id: str | None, overrides: dict | None = None, today: date | None = None) -> dict:
    sc = forecast.resolve_scenario(kb, scenario_id, overrides)
    radar = forecast.business_radar(kb, sc)
    problems = forecast.rank_problems(kb, sc)
    caps = forecast.capability_forecast(kb, sc, problems, today)
    archetypes = pools.rank_archetypes(kb, caps, radar["hiring"])
    ecosystem = pools.ecosystem(kb, sc, caps)
    cap_pools = {c["id"]: pools.pools_for_capability(kb, c["id"], sc) for c in caps[:15]}
    strategies = [pools.search_strategy(kb, a, sc, caps) for a in archetypes[:6]]
    shortlist = cand_engine.shortlist(kb, conn, sc, caps, archetypes, problems)
    role_lists = cand_engine.role_shortlists(kb, conn, sc, caps, [s["archetype_id"] for s in strategies])
    for s in strategies:
        s["shortlist"] = role_lists[s["archetype_id"]]
    jobs = cand_engine.open_jobs(kb, conn, sc, caps)
    best = cand_engine.best_jobs(jobs)
    for c in shortlist:
        c["best_job"] = best.get(c["id"])
    plan = journey.build(kb, conn, sc, caps, archetypes, problems, today=today)
    return {"company_name": (kb.company or {}).get("name", "Cognition"), "journey": plan, "scenario": sc, "radar": radar, "problems": problems, "capabilities": caps, "archetypes": archetypes,
            "ecosystem": ecosystem, "capability_pools": cap_pools, "strategies": strategies, "candidates": shortlist,
            "open_jobs": jobs,
            "segments": {k: v for k, v in kb.segments.items() if sc["segment_weights"].get(k, 0) > 0}}
