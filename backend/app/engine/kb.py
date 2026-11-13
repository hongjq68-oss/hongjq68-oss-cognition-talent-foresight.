"""Loads the knowledge base from SQLite into plain dicts for the deterministic engine."""
from dataclasses import dataclass

from .. import db


@dataclass
class KB:
    signals: dict
    sources: dict
    jobs: list
    segments: dict
    capabilities: dict
    problems: dict
    problem_caps: dict  # problem_id -> {capability_id: (weight, rationale)}
    organisations: list
    archetypes: dict
    scenarios: dict


def load(conn) -> KB:
    pc: dict = {}
    for r in conn.execute("SELECT * FROM problem_capabilities"):
        pc.setdefault(r["problem_id"], {})[r["capability_id"]] = (r["weight"], r["rationale"])
    by_id = lambda q: {r["id"]: r for r in db.rows(conn.execute(q))}
    return KB(
        signals=by_id("SELECT * FROM signals"),
        sources=by_id("SELECT * FROM sources"),
        jobs=db.rows(conn.execute("SELECT * FROM job_postings WHERE active = 1")),
        segments=by_id("SELECT * FROM segments"),
        capabilities=by_id("SELECT * FROM capabilities"),
        problems=by_id("SELECT * FROM customer_problems"),
        problem_caps=pc,
        organisations=db.rows(conn.execute("SELECT * FROM organisations")),
        archetypes=by_id("SELECT * FROM archetypes"),
        scenarios=by_id("SELECT * FROM scenarios"),
    )


def cite(kb: KB, signal_id: str) -> dict:
    """Return a citation for a signal: title, url, date, evidence class."""
    s = kb.signals.get(signal_id)
    if not s:
        return {"id": signal_id, "title": signal_id, "url": None, "date": None, "evidence_class": "hypothesis"}
    src = kb.sources.get(s["source_id"]) if s["source_id"] else None
    return {"id": s["id"], "title": s["title"], "url": src["url"] if src else None, "date": s["happened_on"],
            "evidence_class": s["evidence_class"], "source_needed": src is None}
