"""Builds the SQLite database from the seed knowledge base and public snapshots."""
import json
from pathlib import Path

from .. import db
from .archetypes import ARCHETYPES
from .candidates import CANDIDATES
from .capabilities import CAPABILITIES
from .organisations import ORGANISATIONS
from .scenarios import SCENARIOS
from .segments import PROBLEMS, SEGMENTS
from .signals import CURATED_SIGNALS, MARKET_INTEL_SIGNALS

SNAP = Path(__file__).parent / "snapshots"
MARKET_CODES = {"Singapore": "SG", "Japan": "JP", "Australia": "AU", "India": "IN", "South Korea": "KR"}


def _source_id(url: str) -> str:
    return "src-" + url.rstrip("/").rsplit("/", 1)[-1][:80]


def load_jobs(conn, jobs: list[dict]) -> int:
    conn.execute("UPDATE job_postings SET active = 0")
    for j in jobs:
        market = j.get("market")
        db.upsert(conn, "job_postings", dict(
            id=j["id"], title=j["title"], department=j.get("department"), team=j.get("team"),
            location=", ".join([j.get("location") or ""] + (j.get("secondary_locations") or [])).strip(", "),
            market=MARKET_CODES.get(market, market), published_on=j.get("published_on"), url=j.get("url"),
            retrieved_on=j.get("retrieved_on"), active=1))
    return len(jobs)


def load_blog_sources(conn, posts: list[dict]) -> int:
    for p in posts:
        db.upsert(conn, "sources", dict(id=_source_id(p["url"]), title=p["title"], url=p["url"], publisher="Cognition",
                                        published_on=p["published_on"], retrieved_on=p.get("retrieved_on"),
                                        source_type="company_blog"))
    return len(posts)


def seed(reset: bool = True) -> None:
    if reset and db.DB_PATH.exists():
        db.DB_PATH.unlink()
    with db.session() as conn:
        db.init_schema(conn)
        load_blog_sources(conn, json.loads((SNAP / "cognition_blog.json").read_text()))
        load_jobs(conn, json.loads((SNAP / "cognition_jobs.json").read_text()))
        db.upsert(conn, "sources", dict(id="src-ashby", title="Cognition public job board (Ashby)",
                                        url="https://jobs.ashbyhq.com/cognition", publisher="Ashby",
                                        source_type="job_board", retrieved_on=None))
        for s in CURATED_SIGNALS:
            sid = _source_id(s["url"])
            if not conn.execute("SELECT 1 FROM sources WHERE id=?", (sid,)).fetchone():
                db.upsert(conn, "sources", dict(id=sid, title=s["title"], url=s["url"], publisher="Cognition",
                                                published_on=s["happened_on"], source_type="company_blog"))
            db.upsert(conn, "signals", dict(id=s["id"], kind=s["kind"], title=s["title"], summary=s["summary"],
                                            happened_on=s["happened_on"], regions=s["regions"], segment_ids=s["segment_ids"],
                                            source_id=sid, evidence_class="verified_fact", curated=1))
        for s in MARKET_INTEL_SIGNALS:
            db.upsert(conn, "signals", dict(id=s["id"], kind=s["kind"], title=s["title"], summary=s["summary"],
                                            happened_on=None, regions=s["regions"], segment_ids=s["segment_ids"],
                                            source_id=None, evidence_class="market_intel", curated=1))
        for s in SEGMENTS:
            db.upsert(conn, "segments", s)
        for c in CAPABILITIES:
            db.upsert(conn, "capabilities", c)
        for p in PROBLEMS:
            rec = {k: v for k, v in p.items() if k != "capabilities"}
            db.upsert(conn, "customer_problems", rec)
            for cid, (w, why) in p["capabilities"].items():
                db.upsert(conn, "problem_capabilities", dict(problem_id=p["id"], capability_id=cid, weight=w, rationale=why or None))
        for o in ORGANISATIONS:
            db.upsert(conn, "organisations", o)
        for a in ARCHETYPES:
            db.upsert(conn, "archetypes", a)
        for s in SCENARIOS:
            db.upsert(conn, "scenarios", s)
        for k in CANDIDATES:
            rec = {x: v for x, v in k.items() if x != "evidence"}
            db.upsert(conn, "candidates", rec)
            for i, e in enumerate(k["evidence"], 1):
                db.upsert(conn, "candidate_evidence", dict(id=f"{k['id']}-e{i}", candidate_id=k["id"], **e))


if __name__ == "__main__":
    seed()
    print("seeded", db.DB_PATH)
