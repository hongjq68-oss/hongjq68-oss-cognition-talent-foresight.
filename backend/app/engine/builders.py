"""Builder Evidence Agent: turns public work (repos, launches, writing, papers, demos, patents) into
unverified, sourced candidate evidence, and runs discovery monitors that surface new builders.

Rules: only items that map to a capability become evidence; everything enters as 'unverified'; nobody is contacted."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from .. import db
from ..connectors import builders as src
from .candidates import audit
from .kb import KB

LEAD_TTL_DAYS = 30
POOLS = {"direct", "adjacent", "customer_side", "consulting", "founder"}

# Technical vocabulary in repos/posts, on top of each capability's evidence_phrases.
BUILDER_TERMS = {
    "agentic_systems": ["agent", "agents", "agentic", "llm", "rag", "evals", "eval", "mcp", "langchain", "tool calling", "copilot"],
    "legacy_modernisation": ["cobol", "mainframe", "jcl", "copybook", "z/os", "rpg", "fortran", "legacy migration", "modernization", "modernisation"],
    "cloud_infra": ["terraform", "kubernetes", "k8s", "helm", "aws", "gcp", "azure", "serverless", "pulumi"],
    "security_architecture": ["security", "threat model", "iam", "zero trust", "oauth", "encryption"],
    "appsec_remediation": ["sast", "dast", "vulnerability", "vulnerabilities", "cve", "fuzzing", "fuzzer", "semgrep", "appsec"],
    "dev_productivity": ["developer tool", "devtools", "developer experience", "ci/cd", "github actions", "build system", "monorepo", "cli", "code review"],
    "qa_test_automation": ["test automation", "testing", "pytest", "playwright", "selenium", "e2e", "regression"],
    "data_engineering": ["etl", "data pipeline", "spark", "dbt", "airflow", "data lineage", "lakehouse"],
    "systems_integration": ["iso 20022", "integration", "kafka", "api gateway", "swift", "payments"],
    "technical_troubleshooting": ["observability", "tracing", "opentelemetry", "debugging", "incident"],
    "productivity_measurement": ["dora", "engineering metrics", "benchmark", "productivity"],
    "japanese_enterprise": ["japanese", "japan"],
}
JP_CHARS = re.compile(r"[\u3040-\u30ff\u4e00-\u9faf]")
KIND = {  # kind -> (evidence_type, verb)
    "repo": ("open_source", "Built and maintains"), "package": ("open_source", "Publishes"),
    "model": ("open_source", "Published model"), "launch": ("public_artifact", "Launched"),
    "demo": ("public_artifact", "Public demo"), "article": ("publication", "Wrote"),
    "paper": ("publication", "Authored"), "patent": ("patent", "Named inventor on"),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _has(term: str, text: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])", text))


def map_capabilities(kb: KB, item: dict) -> list[str]:
    hay = f"{item['title']} {item['text']}".lower()
    caps = {cid for cid, c in kb.capabilities.items() for ph in c["evidence_phrases"] if _has(ph, hay)}
    caps |= {cid for cid, terms in BUILDER_TERMS.items() if cid in kb.capabilities and any(_has(t, hay) for t in terms)}
    if JP_CHARS.search(item["title"] + item["text"]):
        caps.add("japanese_enterprise")
    if item["kind"] in ("repo", "package", "model") and caps:
        caps.add("software_engineering")
    if item["kind"] == "launch" and caps:
        caps.add("zero_to_one")
    return sorted(caps)


def to_evidence(kb: KB, item: dict) -> dict | None:
    caps = map_capabilities(kb, item)
    if not caps:
        return None
    etype, verb = KIND[item["kind"]]
    m = item["metrics"]
    reach = next((f" ({m[k]} {lbl})" for k, lbl in (("stars", "stars"), ("points", "HN points"), ("likes", "likes"),
                                                    ("reactions", "reactions")) if m.get(k)), "")
    claim = f"{verb} {item['title']}{reach}"
    problem = (item["text"].split(". ")[0] or item["title"])[:240]
    return {"claim": claim[:300], "problem_solved": problem, "capability_ids": caps, "evidence_type": etype,
            "source_url": item["url"], "source_date": item["date"], "verification": "unverified",
            "source": item["source"], "kind": item["kind"]}


# ---- Investigate one person ---------------------------------------------------------------------------------
HANDLE_SOURCES = {
    "github": src.github_user, "hn": src.hn_user, "devto": src.devto_user, "arxiv": src.arxiv_author,
    "huggingface": src.huggingface_user, "npm": src.npm_maintainer,
}


def collect(handles: dict, owner: str) -> tuple[list[dict], dict]:
    items, report = [], {}
    for name, fn in HANDLE_SOURCES.items():
        h = (handles.get(name) or "").strip()
        if not h:
            continue
        try:
            got = fn(h)
            items += got
            report[name] = {"ok": True, "items": len(got)}
        except (src.SourceError, Exception) as e:  # noqa: BLE001 - one source failing must not stop the others
            report[name] = {"ok": False, "error": str(e)[:200]}
    for i, url in enumerate([handles.get("rss")] + list(handles.get("links") or [])):
        if not url:
            continue
        key = "rss" if i == 0 else f"link {i}"
        try:
            got = src.rss(url, owner) if i == 0 else src.page(url, owner)
            items += got
            report[key] = {"ok": True, "items": len(got)}
        except Exception as e:  # noqa: BLE001
            report[key] = {"ok": False, "error": str(e)[:200]}
    return items, report


def add_evidence(conn, candidate_id: str, evidence: list[dict]) -> int:
    have = {r[0] for r in conn.execute("SELECT source_url FROM candidate_evidence WHERE candidate_id=?", (candidate_id,))}
    n = conn.execute("SELECT COUNT(*) FROM candidate_evidence WHERE candidate_id=?", (candidate_id,)).fetchone()[0]
    added = 0
    for e in evidence:
        if e["source_url"] in have:
            continue
        n += 1
        added += 1
        have.add(e["source_url"])
        db.upsert(conn, "candidate_evidence", {k: v for k, v in e.items() if k not in ("source", "kind")} |
                  {"id": f"{candidate_id}-b{n}", "candidate_id": candidate_id})
    return added


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "builder"


def create_candidate(conn, name: str, market: str, pool_type: str, headline: str = "", company: str | None = None,
                     profile_url: str | None = None, background: str = "") -> str:
    if pool_type not in POOLS:
        raise ValueError(f"pool_type must be one of {sorted(POOLS)}")
    if market not in MARKET_LOCATION:
        raise ValueError(f"market must be one of {sorted(MARKET_LOCATION)}")
    cid, i = f"r-{_slug(name)}", 1
    while conn.execute("SELECT 1 FROM candidates WHERE id=?", (cid,)).fetchone():
        i += 1
        cid = f"r-{_slug(name)}-{i}"
    db.upsert(conn, "candidates", dict(
        id=cid, display_name=name, synthetic=0, headline=headline or "Builder (public evidence)",
        employer_descriptor=company or "Unknown: verify", profile_url=profile_url, pool_type=pool_type, market=market,
        background=background or "Found by the Builder Evidence Agent from public work. Recruiter to verify identity and history.",
        learning_needs=[], status="discovered", notes=""))
    return cid


def investigate(conn, kb: KB, handles: dict, candidate_id: str | None = None, display_name: str | None = None,
                market: str = "SG", pool_type: str = "founder", actor: str = "recruiter") -> dict:
    owner = display_name or candidate_id or "unknown"
    items, report = collect(handles, owner)
    evidence = [e for e in (to_evidence(kb, it) for it in items) if e]
    if not candidate_id:
        if not display_name:
            raise ValueError("Give a candidate or a display name")
        gh = next((it["person"] for it in items if it["source"] == "github"), None)
        candidate_id = create_candidate(conn, display_name, market, pool_type, (gh or {}).get("bio") or "",
                                        (gh or {}).get("company"), (gh or {}).get("profile_url"))
    elif not conn.execute("SELECT 1 FROM candidates WHERE id=?", (candidate_id,)).fetchone():
        raise KeyError(candidate_id)
    added = add_evidence(conn, candidate_id, evidence)
    gh_url = next((it["person"]["profile_url"] for it in items if it["source"] == "github"), None)
    if gh_url:
        conn.execute("UPDATE candidates SET profile_url=COALESCE(profile_url, ?) WHERE id=?", (gh_url, candidate_id))
    _log_run(conn, "investigate", candidate_id, report, len(items), added)
    audit(conn, actor, "builder_investigate", f"{candidate_id}: {len(items)} public items, {added} evidence added (unverified)")
    return {"candidate_id": candidate_id, "sources": report, "items_found": len(items),
            "mapped": len(evidence), "added": added, "unmapped": len(items) - len(evidence)}


# ---- Discovery monitors -------------------------------------------------------------------------------------
MONITOR_SOURCES = {
    "github": lambda q, loc: src.github_search(q, loc), "hn": lambda q, loc: src.hn_search(q),
    "devto": lambda q, loc: src.devto_tag(q), "arxiv": lambda q, loc: src.arxiv_search(q),
}
MARKET_LOCATION = {"SG": "Singapore", "JP": "Japan", "AU": "Australia", "IN": "India", "KR": "Korea"}
APAC_LOCATIONS = ["Singapore", "Japan", "Tokyo", "Osaka", "Australia", "Sydney", "Melbourne", "India", "Bangalore",
                  "Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Korea", "Seoul"]


def list_monitors(conn) -> list[dict]:
    mons = db.rows(conn.execute("SELECT * FROM monitors ORDER BY created_at"))
    for m in mons:
        m["queries"] = json.loads(m["queries"]) if isinstance(m["queries"], str) else m["queries"]
        c = conn.execute("SELECT SUM(status='new'), SUM(status='new' AND first_seen=?), SUM(status='promoted') FROM leads "
                         "WHERE monitor_id=?", (m["last_run_at"], m["id"])).fetchone()
        m["leads_open"], m["leads_new_last_run"], m["leads_promoted"] = c[0] or 0, c[1] or 0, c[2] or 0
    return mons


def save_monitor(conn, rec: dict) -> dict:
    if rec["capability_id"] not in {r[0] for r in conn.execute("SELECT id FROM capabilities")}:
        raise ValueError("Unknown capability")
    bad = set(rec["queries"]) - set(MONITOR_SOURCES)
    if bad or not any(v.strip() for v in rec["queries"].values()):
        raise ValueError(f"Queries need at least one of {sorted(MONITOR_SOURCES)}")
    mid = rec.get("id") or f"m-{_slug(rec['name'])}"
    db.upsert(conn, "monitors", dict(id=mid, name=rec["name"], capability_id=rec["capability_id"], market=rec.get("market"),
                                     queries=rec["queries"], active=1, created_at=_now().isoformat(timespec="seconds"),
                                     last_run_at=None))
    return {"id": mid}


def run_monitor(conn, kb: KB, monitor_id: str, actor: str = "scheduler") -> dict:
    m = db.row(conn.execute("SELECT * FROM monitors WHERE id=?", (monitor_id,)).fetchone())
    if not m:
        raise KeyError(monitor_id)
    queries = json.loads(m["queries"]) if isinstance(m["queries"], str) else m["queries"]
    loc = [MARKET_LOCATION[m["market"]]] if m["market"] else APAC_LOCATIONS
    now = _now().isoformat(timespec="seconds")
    items, report = [], {}
    for s, q in queries.items():
        if not q.strip():
            continue
        try:
            got = MONITOR_SOURCES[s](q, loc)
            items += got
            report[s] = {"ok": True, "items": len(got)}
        except Exception as e:  # noqa: BLE001
            report[s] = {"ok": False, "error": str(e)[:200]}
    by_person: dict[str, dict] = {}
    for it in items:
        ev = to_evidence(kb, it)
        if not ev or m["capability_id"] not in ev["capability_ids"]:
            continue
        p = it["person"]
        g = by_person.setdefault(p["key"], {"person": p, "evidence": []})
        if ev["source_url"] not in {e["source_url"] for e in g["evidence"]}:
            g["evidence"].append(ev)
    new = 0
    for key, g in by_person.items():
        lid = f"{monitor_id}:{key}"
        old = db.row(conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone())
        if old and old["status"] != "new":
            continue
        p = g["person"]
        market_known = bool(p["location"])
        merged = (old["evidence"] if old else []) + g["evidence"]
        merged = list({e["source_url"]: e for e in merged}.values())
        db.upsert(conn, "leads", dict(
            id=lid, monitor_id=monitor_id, person_key=key, display_name=p["name"], source=p["source"],
            profile_url=p["profile_url"], location=p["location"], company=p["company"], bio=p["bio"],
            market_verified=1 if market_known and any(x.lower() in p["location"].lower() for x in loc) else 0, evidence=merged,
            capability_ids=sorted({c for e in merged for c in e["capability_ids"]}),
            first_seen=old["first_seen"] if old else now, last_seen=now, status="new", candidate_id=None,
            expires_at=(_now() + timedelta(days=LEAD_TTL_DAYS)).isoformat(timespec="seconds")))
        new += 0 if old else 1
    conn.execute("UPDATE monitors SET last_run_at=? WHERE id=?", (now, monitor_id))
    _log_run(conn, "monitor", monitor_id, report, len(items), new)
    audit(conn, actor, "monitor_run", f"{monitor_id}: {len(items)} public items, {len(by_person)} builders, {new} new")
    return {"monitor_id": monitor_id, "sources": report, "items_found": len(items), "builders": len(by_person), "new": new}


def list_leads(conn, monitor_id: str | None = None, status: str = "new") -> list[dict]:
    q, args = "SELECT * FROM leads WHERE status=?", [status]
    if monitor_id:
        q += " AND monitor_id=?"
        args.append(monitor_id)
    out = db.rows(conn.execute(q + " ORDER BY market_verified DESC, first_seen DESC, display_name", args))
    for r in out:
        r["evidence"] = json.loads(r["evidence"]) if isinstance(r["evidence"], str) else r["evidence"]
    return out


def decide_lead(conn, lead_id: str, decision: str, market: str | None = None, pool_type: str = "founder",
                actor: str = "recruiter") -> dict:
    lead = db.row(conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone())
    if not lead:
        raise KeyError(lead_id)
    if lead["status"] != "new":
        raise ValueError(f"Lead already {lead['status']}")
    if decision == "dismiss":
        conn.execute("UPDATE leads SET status='dismissed' WHERE id=?", (lead_id,))
        audit(conn, actor, "lead_dismissed", lead_id)
        return {"lead_id": lead_id, "status": "dismissed"}
    if decision != "promote":
        raise ValueError("decision must be promote or dismiss")
    mon = conn.execute("SELECT market FROM monitors WHERE id=?", (lead["monitor_id"],)).fetchone()
    ev = json.loads(lead["evidence"]) if isinstance(lead["evidence"], str) else lead["evidence"]
    cid = create_candidate(conn, lead["display_name"], market or (mon[0] if mon else None) or "SG", pool_type,
                           lead["bio"] or "", lead["company"], lead["profile_url"])
    added = add_evidence(conn, cid, ev)
    conn.execute("UPDATE leads SET status='promoted', candidate_id=?, expires_at=NULL WHERE id=?", (cid, lead_id))
    audit(conn, actor, "lead_promoted", f"{lead_id} -> {cid} ({added} unverified evidence)")
    return {"lead_id": lead_id, "status": "promoted", "candidate_id": cid, "added": added}


def purge_expired(conn) -> int:
    n = conn.execute("DELETE FROM leads WHERE status!='promoted' AND expires_at < ?", (_now().isoformat(timespec="seconds"),)).rowcount
    if n:
        audit(conn, "scheduler", "leads_purged", f"{n} leads past {LEAD_TTL_DAYS}-day retention")
    return n


def due_monitors(conn, interval_hours: float) -> list[str]:
    cutoff = (_now() - timedelta(hours=interval_hours)).isoformat(timespec="seconds")
    return [r[0] for r in conn.execute("SELECT id FROM monitors WHERE active=1 AND (last_run_at IS NULL OR last_run_at < ?)", (cutoff,))]


def runs(conn, limit: int = 20) -> list[dict]:
    out = db.rows(conn.execute("SELECT * FROM builder_runs ORDER BY id DESC LIMIT ?", (limit,)))
    for r in out:
        r["sources"] = json.loads(r["sources"]) if isinstance(r["sources"], str) else r["sources"]
    return out


def _log_run(conn, kind: str, target: str, report: dict, items: int, added: int) -> None:
    conn.execute("INSERT INTO builder_runs (at, kind, target, sources, items, added) VALUES (?,?,?,?,?,?)",
                 (_now().isoformat(timespec="seconds"), kind, target, json.dumps(report), items, added))


def source_status() -> dict:
    import os
    return {"github": {"ready": True, "authenticated": bool(os.environ.get("GITHUB_TOKEN")),
                       "note": None if os.environ.get("GITHUB_TOKEN") else "Anonymous: 60 requests/hour shared; set GITHUB_TOKEN"},
            "hn": {"ready": True}, "devto": {"ready": True}, "arxiv": {"ready": True}, "huggingface": {"ready": True},
            "npm": {"ready": True}, "rss": {"ready": True},
            "patents": {"ready": True, "note": "Paste public patent URLs (Google Patents, Justia, Espacenet). No patent search API key configured."},
            "product_hunt": {"ready": False, "note": "Needs an API token; launches covered by Show HN and pasted links"},
            "youtube": {"ready": False, "note": "Needs an API key; paste demo links instead"}}
