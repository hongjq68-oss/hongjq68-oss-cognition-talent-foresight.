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
    company: dict | None = None


COGNITION = "cognition"


def load(conn, company_id: str = COGNITION) -> KB:
    """Cognition uses its curated knowledge; any other company uses its own public data plus the general library."""
    pc: dict = {}
    for r in conn.execute("SELECT * FROM problem_capabilities"):
        pc.setdefault(r["problem_id"], {})[r["capability_id"]] = (r["weight"], r["rationale"])
    lib = COGNITION if company_id == COGNITION else "*"
    own = lambda t, extra="": db.rows(conn.execute(f"SELECT * FROM {t} WHERE company_id = ?{extra}", (company_id,)))
    shared = lambda t: db.rows(conn.execute(f"SELECT * FROM {t} WHERE company_id = ?", (lib,)))
    by_id = lambda rs: {r["id"]: r for r in rs}
    company = db.row(conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone())
    problems = by_id(shared("customer_problems"))
    orgs = db.rows(conn.execute("SELECT * FROM organisations"))
    if company_id != COGNITION:
        # Sensitivity flags describe relationships with Cognition; they don't carry over to another company.
        me = (company or {}).get("name", "").lower()
        orgs = [o | {"sensitivity": "none", "sensitivity_note": None} for o in orgs
                if not (me and (o["name"].lower() == me or o["name"].lower().startswith(me + " ")))]
    return KB(
        signals=by_id(own("signals")),
        sources=by_id(own("sources")),
        jobs=own("job_postings", " AND active = 1"),
        segments=by_id(shared("segments")),
        capabilities=by_id(db.rows(conn.execute("SELECT * FROM capabilities"))),
        problems=problems,
        problem_caps={k: v for k, v in pc.items() if k in problems},
        organisations=orgs,
        archetypes=by_id(shared("archetypes")),
        scenarios=by_id(own("scenarios")),
        company=company,
    )


def cite(kb: KB, signal_id: str) -> dict:
    """Return a citation for a signal: title, url, date, evidence class."""
    s = kb.signals.get(signal_id)
    if not s:
        return {"id": signal_id, "title": signal_id, "url": None, "date": None, "evidence_class": "hypothesis"}
    src = kb.sources.get(s["source_id"]) if s["source_id"] else None
    return {"id": s["id"], "title": s["title"], "url": src["url"] if src else None, "date": s["happened_on"],
            "evidence_class": s["evidence_class"], "source_needed": src is None}
