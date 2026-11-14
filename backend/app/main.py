"""Cognition Talent Foresight API."""
import csv
import io
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db
from .connectors import ashby, cognition_blog
from .engine import analysis, kb as kb_mod, report
from .engine import builders
from .engine import candidates as cand_engine
from .seed import load as seed_load
from .seed.monitors import MONITORS

log = logging.getLogger("foresight")
MONITOR_INTERVAL_HOURS = float(os.environ.get("FORESIGHT_MONITOR_INTERVAL_HOURS", "24"))


def run_due_monitors() -> list[dict]:
    """Scheduled discovery: re-run monitors older than the interval and purge expired leads."""
    out = []
    with db.session() as conn:
        builders.purge_expired(conn)
        due = builders.due_monitors(conn, MONITOR_INTERVAL_HOURS)
    for mid in due:
        with db.session() as conn:
            out.append(builders.run_monitor(conn, kb_mod.load(conn), mid))
    return out


async def _monitor_loop():
    while True:
        try:
            await asyncio.to_thread(run_due_monitors)
        except Exception:  # noqa: BLE001
            log.exception("scheduled monitor run failed")
        await asyncio.sleep(3600)



@asynccontextmanager
async def lifespan(_app):
    if not db.DB_PATH.exists():
        seed_load.seed()
    else:
        with db.session() as conn:
            db.init_schema(conn)
            if not conn.execute("SELECT 1 FROM monitors").fetchone():
                for m in MONITORS:
                    db.upsert(conn, "monitors", m | {"active": 1, "created_at": builders._now().isoformat(timespec="seconds")})
    task = asyncio.create_task(_monitor_loop()) if MONITOR_INTERVAL_HOURS > 0 else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Cognition Talent Foresight", lifespan=lifespan)


def _kb(conn):
    return kb_mod.load(conn)


class ScenarioOverrides(BaseModel):
    scenario_id: str | None = None
    name: str | None = None
    hypothesis: str | None = None
    segment_weights: dict[str, float] | None = None
    market_weights: dict[str, float] | None = None
    capability_boosts: dict[str, float] | None = None
    extra_demand: dict[str, float] | None = None


def _analyse(conn, body: ScenarioOverrides):
    kb = _kb(conn)
    if body.scenario_id and body.scenario_id not in kb.scenarios:
        raise HTTPException(404, "Unknown scenario")
    overrides = {k: v for k, v in body.model_dump().items() if v is not None and k != "scenario_id"}
    return analysis.run(kb, conn, body.scenario_id, overrides)


@app.get("/api/meta")
def meta():
    with db.session() as conn:
        kb = _kb(conn)
        return {
            "scenarios": [{"id": s["id"], "name": s["name"], "hypothesis": s["data"]["hypothesis"]} for s in kb.scenarios.values()],
            "segments": [{"id": s["id"], "name": s["name"]} for s in kb.segments.values()],
            "capabilities": [{k: c[k] for k in ("id", "name", "category", "scarcity")} for c in kb.capabilities.values()],
            "markets": ["SG", "AU", "JP", "IN", "KR"],
            "counts": {"signals": len(kb.signals), "sources": len(kb.sources), "jobs": len(kb.jobs),
                       "organisations": len(kb.organisations), "problems": len(kb.problems)},
            "last_refresh": [dict(r) for r in conn.execute("SELECT * FROM refresh_runs ORDER BY id DESC LIMIT 4")],
        }


@app.post("/api/analysis")
def run_analysis(body: ScenarioOverrides = Body(...)):
    with db.session() as conn:
        return _analyse(conn, body)


@app.post("/api/report")
def get_report(body: ScenarioOverrides = Body(...)):
    with db.session() as conn:
        return report.build(_analyse(conn, body))


@app.post("/api/report.md", response_class=PlainTextResponse)
def get_report_md(body: ScenarioOverrides = Body(...)):
    with db.session() as conn:
        return report.to_markdown(report.build(_analyse(conn, body)))


@app.get("/api/signals")
def signals():
    with db.session() as conn:
        kb = _kb(conn)
        return [kb_mod.cite(kb, s) | {"summary": kb.signals[s]["summary"], "kind": kb.signals[s]["kind"],
                                      "regions": kb.signals[s]["regions"]} for s in kb.signals]


class Review(BaseModel):
    decision: str
    reviewer: str = "recruiter"
    note: str | None = None


@app.post("/api/evidence/{evidence_id}/review")
def review(evidence_id: str, body: Review):
    with db.session() as conn:
        try:
            return cand_engine.review_evidence(conn, evidence_id, body.decision, body.reviewer, body.note)
        except KeyError:
            raise HTTPException(404, "Unknown evidence")
        except ValueError as e:
            raise HTTPException(400, str(e))


class StatusChange(BaseModel):
    status: str
    actor: str = "recruiter"
    note: str | None = None


class ProfileLink(BaseModel):
    profile_url: str | None = None
    actor: str = "recruiter"


@app.post("/api/candidates/{candidate_id}/profile")
def profile(candidate_id: str, body: ProfileLink):
    with db.session() as conn:
        try:
            return cand_engine.set_profile(conn, candidate_id, body.profile_url, body.actor)
        except KeyError:
            raise HTTPException(404, "Unknown candidate")
        except ValueError as e:
            raise HTTPException(400, str(e))


@app.post("/api/candidates/{candidate_id}/status")
def status(candidate_id: str, body: StatusChange):
    with db.session() as conn:
        try:
            return cand_engine.set_status(conn, candidate_id, body.status, body.actor, body.note)
        except KeyError:
            raise HTTPException(404, "Unknown candidate")
        except ValueError as e:
            raise HTTPException(400, str(e))


@app.get("/api/ats-export")
def ats_export(format: str = "json"):
    with db.session() as conn:
        rows = cand_engine.ats_export(conn)
    if format == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["name", "synthetic", "headline", "current_company", "profile_url", "market", "verified_evidence"])
        for r in rows:
            w.writerow([r["name"], r["synthetic"], r["headline"], r["current_company"], r["profile_url"] or "", r["market"],
                        " | ".join(f"{e['claim']} ({e['source_url'] or 'no url'})" for e in r["verified_evidence"])])
        return Response(buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=ready_for_ats.csv"})
    return rows


@app.get("/api/audit")
def audit_log():
    with db.session() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200")]


@app.post("/api/refresh")
def refresh():
    """Pull the public Cognition blog index and job board. Only public, unauthenticated endpoints are used."""
    out = {}
    with db.session() as conn:
        for name, fn, loader in (("cognition_blog", cognition_blog.fetch_index, seed_load.load_blog_sources),
                                 ("ashby", ashby.fetch_jobs, seed_load.load_jobs)):
            try:
                n = loader(conn, fn())
                conn.execute("INSERT INTO refresh_runs (at, connector, ok, new_items, message) VALUES (datetime('now'),?,1,?,?)", (name, n, "ok"))
                out[name] = {"ok": True, "items": n}
            except Exception as e:  # network failures must not break the app
                conn.execute("INSERT INTO refresh_runs (at, connector, ok, new_items, message) VALUES (datetime('now'),?,0,0,?)", (name, str(e)[:300]))
                out[name] = {"ok": False, "error": str(e)[:300]}
    return out


class Handles(BaseModel):
    candidate_id: str | None = None
    display_name: str | None = None
    market: str = "SG"
    pool_type: str = "founder"
    github: str | None = None
    hn: str | None = None
    devto: str | None = None
    arxiv: str | None = None
    huggingface: str | None = None
    npm: str | None = None
    rss: str | None = None
    links: list[str] = []


class MonitorIn(BaseModel):
    name: str
    capability_id: str
    market: str | None = None
    queries: dict[str, str]


class LeadDecision(BaseModel):
    decision: str
    market: str | None = None
    pool_type: str = "founder"


def _guard(fn):
    try:
        return fn()
    except KeyError:
        raise HTTPException(404, "Not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/builders")
def builders_overview():
    with db.session() as conn:
        return {"monitors": builders.list_monitors(conn), "leads": builders.list_leads(conn),
                "runs": builders.runs(conn), "sources": builders.source_status(),
                "interval_hours": MONITOR_INTERVAL_HOURS, "lead_ttl_days": builders.LEAD_TTL_DAYS}


@app.post("/api/builders/investigate")
def builders_investigate(body: Handles):
    h = body.model_dump()
    with db.session() as conn:
        return _guard(lambda: builders.investigate(conn, kb_mod.load(conn), h, body.candidate_id, body.display_name,
                                                   body.market, body.pool_type))


@app.post("/api/builders/monitors")
def builders_monitor_create(body: MonitorIn):
    with db.session() as conn:
        return _guard(lambda: builders.save_monitor(conn, body.model_dump()))


@app.post("/api/builders/monitors/{monitor_id}/run")
def builders_monitor_run(monitor_id: str):
    with db.session() as conn:
        return _guard(lambda: builders.run_monitor(conn, kb_mod.load(conn), monitor_id, "recruiter"))


@app.post("/api/builders/leads/{lead_id:path}")
def builders_lead(lead_id: str, body: LeadDecision):
    with db.session() as conn:
        return _guard(lambda: builders.decide_lead(conn, lead_id, body.decision, body.market, body.pool_type))


@app.post("/api/reset")
def reset():
    seed_load.seed()
    return {"ok": True}


DIST = Path(os.environ.get("FORESIGHT_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        return FileResponse(DIST / "index.html")
