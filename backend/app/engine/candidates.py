"""Evidence-based candidate fit and recruiter verification workflow.

A title or employer name alone contributes nothing. Unverified evidence counts half; rejected evidence counts zero."""
import re
from datetime import datetime, timezone

from .. import db
from .kb import KB

EVIDENCE_WEIGHT = {"public_artifact": 1.0, "open_source": 1.0, "publication": 0.9, "talk": 0.8, "news": 0.7,
                   "profile_self_reported": 0.3, "title_only": 0.0}
VERIFICATION_WEIGHT = {"verified": 1.0, "unverified": 0.5, "rejected": 0.0}
TRANSITIONS = {
    "discovered": {"evidence_review", "parked"},
    "evidence_review": {"verified", "parked", "discovered"},
    "verified": {"ready_for_ats", "evidence_review", "parked"},
    "ready_for_ats": {"verified", "parked"},
    "parked": {"discovered", "evidence_review"},
}
MIN_VERIFIED_FOR_VERIFIED = 2


def load_candidates(conn) -> list[dict]:
    cands = db.rows(conn.execute("SELECT * FROM candidates ORDER BY id"))
    ev = db.rows(conn.execute("SELECT * FROM candidate_evidence ORDER BY id"))
    for c in cands:
        c["evidence"] = [e for e in ev if e["candidate_id"] == c["id"]]
    return cands


def capability_scores(cand: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for e in cand["evidence"]:
        s = EVIDENCE_WEIGHT[e["evidence_type"]] * VERIFICATION_WEIGHT[e["verification"]]
        for c in e["capability_ids"]:
            if s > out.get(c, {}).get("score", -1):
                out[c] = {"score": s, "evidence_id": e["id"]}
    return out


def fit(kb: KB, cand: dict, archetype: dict, sc: dict, cap_demand: dict[str, float]) -> dict:
    scores = capability_scores(cand)
    w = archetype["capability_weights"]
    num = sum(wt * (cap_demand.get(c, 50) / 100) * scores.get(c, {}).get("score", 0) for c, wt in w.items())
    den = sum(wt * (cap_demand.get(c, 50) / 100) for c, wt in w.items()) or 1
    evidence_fit = num / den
    market = sc["market_weights"].get(cand["market"], 0)
    total = round(100 * (0.85 * evidence_fit + 0.15 * market), 1)
    demonstrated = [{"id": c, "name": kb.capabilities[c]["name"], "strength": round(scores[c]["score"], 2), "evidence_id": scores[c]["evidence_id"]}
                    for c in sorted(w, key=lambda c: -w[c]) if scores.get(c, {}).get("score", 0) > 0]
    gaps = [{"id": c, "name": kb.capabilities[c]["name"], "weight": w[c]} for c in sorted(w, key=lambda c: -w[c])
            if scores.get(c, {}).get("score", 0) == 0 and w[c] >= 0.5]
    return {"archetype_id": archetype["id"], "archetype": archetype["name"], "score": total,
            "evidence_fit": round(evidence_fit, 3), "market_fit": market, "demonstrated": demonstrated, "gaps": gaps}


def validation_questions(kb: KB, cand: dict, f: dict) -> list[str]:
    qs = []
    for e in cand["evidence"]:
        if e["verification"] == "unverified" and e["evidence_type"] not in ("title_only",):
            qs.append(f"Confirm their personal role in: \"{e['claim']}\" — what did they own, and what was the measurable result?")
        if e["evidence_type"] in ("title_only", "profile_self_reported"):
            qs.append(f"\"{e['claim']}\" is self-described only. Ask for a concrete example with outcome before crediting it.")
    for g in f["gaps"][:3]:
        cap = kb.capabilities[g["id"]]
        qs.append(f"No public evidence of {cap['name'].lower()}. Ask: {cap['description']} Have they done this? Where?")
    return qs


def transferability(kb: KB, cand: dict, f: dict, problems: list[dict]) -> str:
    demo = {d["id"] for d in f["demonstrated"]}
    best = max(problems, key=lambda p: len(demo & {c["id"] for c in p["capabilities"]}) * p["relevance"], default=None)
    if not best or not demo & {c["id"] for c in best["capabilities"]}:
        return "Transfer path unclear from current evidence."
    shared = [kb.capabilities[c["id"]]["name"].lower() for c in best["capabilities"] if c["id"] in demo]
    return (f"Has publicly demonstrated {', '.join(shared)} — the capabilities Cognition customers need to solve "
            f"\"{best['name']}\" ({best['segment']}).")


def shortlist(kb: KB, conn, sc: dict, capabilities: list[dict], archetypes: list[dict], problems: list[dict]) -> list[dict]:
    demand = {c["id"]: c["peak"] for c in capabilities}
    out = []
    for cand in load_candidates(conn):
        fits = sorted((fit(kb, cand, kb.archetypes[a["id"]], sc, demand) for a in archetypes[:8]), key=lambda x: -x["score"])
        best = fits[0]
        out.append(candidate_view(cand) | {
            "best_fit": best, "alternative_fits": [{"archetype": x["archetype"], "score": x["score"]} for x in fits[1:3]],
            "transferability": transferability(kb, cand, best, problems),
            "validation_questions": validation_questions(kb, cand, best),
            "missing_information": [g["name"] for g in best["gaps"]],
            "evidence_class": "recommendation",
        })
    return sorted(out, key=lambda x: -x["best_fit"]["score"])


SHORTLIST_SIZE = 8

# Postings no curated role profile covers; capability ids come from the capability model.
INFERRED_PROFILES = [
    ("QA Engineer", "QA & test-automation engineer",
     {"qa_test_automation": 1.0, "software_engineering": 0.7, "systems_integration": 0.5}),
    ("Partner Marketing", "Partner marketing",
     {"partner_development": 1.0, "commercialising_tech": 0.8, "japanese_enterprise": 0.6}),
]
UNSCORED_KEYWORDS = {"Recruit": "Recruiting role: outside the capability model, so candidates are not scored."}
MARKET_IN_KEYWORD = re.compile(r"Japan|Singapore|Korea|India|Australia|ANZ|APAC", re.I)
REGIONAL_TITLE = re.compile(r"\b(APAC|APJ|ANZ)\b")


def job_profile(kb: KB, job: dict) -> dict | None:
    title = job["title"].lower()
    # A keyword naming the market ("Engineer - Japan") is more specific than a generic job family.
    hits = [(bool(MARKET_IN_KEYWORD.search(k)), len(k), -i, a) for i, a in enumerate(kb.archetypes.values())
            for k in a["posting_keywords"] if k.lower() in title]
    if hits:
        a = max(hits, key=lambda h: h[:3])[3]
        return {"id": a["id"], "name": a["name"], "capability_weights": a["capability_weights"], "basis": "role_profile"}
    for kw, name, weights in INFERRED_PROFILES:
        if kw.lower() in title:
            return {"id": f"inferred:{kw}", "name": name, "capability_weights": weights, "basis": "inferred"}
    return None


def open_jobs(kb: KB, conn, sc: dict, capabilities: list[dict], size: int = SHORTLIST_SIZE) -> list[dict]:
    """Every live APAC Cognition posting with the candidates whose evidence best fits it. Suggestions only."""
    demand = {c["id"]: c["peak"] for c in capabilities}
    cands = [c for c in load_candidates(conn) if c["status"] != "parked"]
    out = []
    for j in kb.jobs:
        if not j["market"]:
            continue
        prof = job_profile(kb, j)
        regional = bool(REGIONAL_TITLE.search(j["title"]))
        job_sc = sc | {"market_weights": {m: 1.0 if m == j["market"] else (0.7 if regional else 0.3)
                                          for m in ("SG", "JP", "AU", "IN", "KR")}}
        matches = []
        for cand in cands if prof else []:
            f = fit(kb, cand, prof, job_sc, demand)
            if f["evidence_fit"] <= 0:
                continue
            matches.append({"candidate_id": cand["id"], "score": f["score"],
                            "strengths": [d["name"] for d in f["demonstrated"][:3]]})
        note = next((v for k, v in UNSCORED_KEYWORDS.items() if k.lower() in j["title"].lower()), None)
        out.append({
            "id": j["id"], "title": j["title"], "department": j["department"], "location": j["location"],
            "market": j["market"], "url": j["url"], "published_on": j["published_on"], "retrieved_on": j["retrieved_on"],
            "regional": regional, "scenario_market_weight": sc["market_weights"].get(j["market"], 0),
            "profile": {k: prof[k] for k in ("id", "name", "basis")} if prof else None,
            "note": note if not prof else None,
            "matches": sorted(matches, key=lambda m: -m["score"])[:size],
        })
    return sorted(out, key=lambda x: (-x["scenario_market_weight"], -(x["matches"][0]["score"] if x["matches"] else -1), x["title"]))


def best_jobs(jobs: list[dict]) -> dict[str, dict]:
    best: dict[str, dict] = {}
    for j in jobs:
        for m in j["matches"]:
            if m["score"] > best.get(m["candidate_id"], {}).get("score", -1):
                best[m["candidate_id"]] = {"job_id": j["id"], "title": j["title"], "url": j["url"],
                                           "market": j["market"], "score": m["score"]}
    return best


def set_profile(conn, candidate_id: str, profile_url: str | None, actor: str) -> dict:
    url = (profile_url or "").strip() or None
    if url and not re.fullmatch(r"https?://[^\s/]+\.[^\s]+", url):
        raise ValueError("Profile link must be a full http(s) URL")
    if not conn.execute("SELECT 1 FROM candidates WHERE id=?", (candidate_id,)).fetchone():
        raise KeyError(candidate_id)
    conn.execute("UPDATE candidates SET profile_url=? WHERE id=?", (url, candidate_id))
    audit(conn, actor, "profile_link", f"{candidate_id}: {url or 'removed'}")
    return {"candidate_id": candidate_id, "profile_url": url}


def role_shortlists(kb: KB, conn, sc: dict, capabilities: list[dict], archetype_ids: list[str],
                    size: int = SHORTLIST_SIZE) -> dict[str, list[dict]]:
    """Per role profile: the strongest evidence-backed candidates. Suggestions only; recruiters decide."""
    demand = {c["id"]: c["peak"] for c in capabilities}
    cands = [c for c in load_candidates(conn) if c["status"] != "parked"]
    out = {}
    for aid in archetype_ids:
        rows = []
        for cand in cands:
            f = fit(kb, cand, kb.archetypes[aid], sc, demand)
            if f["evidence_fit"] <= 0:
                continue
            rows.append({
                "candidate_id": cand["id"], "display_name": cand["display_name"], "headline": cand["headline"],
                "employer_descriptor": cand["employer_descriptor"], "profile_url": cand["profile_url"],
                "market": cand["market"], "pool_type": cand["pool_type"], "status": cand["status"],
                "score": f["score"], "strengths": [d["name"] for d in f["demonstrated"][:3]],
                "gaps": [g["name"] for g in f["gaps"][:2]],
                "verified_evidence": sum(1 for e in cand["evidence"] if e["verification"] == "verified"),
            })
        out[aid] = sorted(rows, key=lambda r: -r["score"])[:size]
    return out


def candidate_view(c: dict) -> dict:
    return {k: c[k] for k in ("id", "display_name", "synthetic", "headline", "employer_descriptor", "profile_url", "pool_type", "market",
                              "background", "learning_needs", "status", "notes", "evidence")}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def audit(conn, actor: str, action: str, detail: str) -> None:
    conn.execute("INSERT INTO audit_log (at, actor, action, detail) VALUES (?,?,?,?)", (_now(), actor, action, detail))


def gate_error(conn, candidate_id: str, status: str) -> str | None:
    if status not in ("verified", "ready_for_ats"):
        return None
    rows = conn.execute("SELECT verification FROM candidate_evidence WHERE candidate_id=?", (candidate_id,)).fetchall()
    n = sum(1 for r in rows if r["verification"] == "verified")
    if n < MIN_VERIFIED_FOR_VERIFIED:
        return f"At least {MIN_VERIFIED_FOR_VERIFIED} pieces of evidence must be recruiter-verified (has {n})"
    if status == "ready_for_ats" and any(r["verification"] == "unverified" for r in rows):
        return "Review every evidence item (verify or reject) before handing to the ATS"
    return None


def review_evidence(conn, evidence_id: str, decision: str, reviewer: str, note: str | None = None) -> dict:
    if decision not in ("verified", "rejected", "unverified"):
        raise ValueError("decision must be verified, rejected or unverified")
    ev = db.row(conn.execute("SELECT * FROM candidate_evidence WHERE id=?", (evidence_id,)).fetchone())
    if not ev:
        raise KeyError(evidence_id)
    conn.execute("UPDATE candidate_evidence SET verification=? WHERE id=?", (decision, evidence_id))
    conn.execute("INSERT INTO evidence_reviews (evidence_id, decision, note, reviewer, reviewed_at) VALUES (?,?,?,?,?)",
                 (evidence_id, decision, note, reviewer, _now()))
    audit(conn, reviewer, "evidence_review", f"{evidence_id} -> {decision}")
    cid = ev["candidate_id"]
    status = conn.execute("SELECT status FROM candidates WHERE id=?", (cid,)).fetchone()["status"]
    new = status
    if status == "discovered":
        new = "evidence_review"
    elif status == "ready_for_ats" and gate_error(conn, cid, "ready_for_ats"):
        new = "verified" if not gate_error(conn, cid, "verified") else "evidence_review"
    elif status == "verified" and gate_error(conn, cid, "verified"):
        new = "evidence_review"
    if new != status:
        conn.execute("UPDATE candidates SET status=? WHERE id=?", (new, cid))
        if status != "discovered":
            audit(conn, "system", "status_revoked", f"{cid}: {status} -> {new} (evidence {evidence_id} -> {decision})")
    return {"evidence_id": evidence_id, "verification": decision, "candidate_status": new}


def set_status(conn, candidate_id: str, status: str, actor: str, note: str | None = None) -> dict:
    c = conn.execute("SELECT status FROM candidates WHERE id=?", (candidate_id,)).fetchone()
    if not c:
        raise KeyError(candidate_id)
    if status not in TRANSITIONS.get(c["status"], set()):
        raise ValueError(f"Cannot move from {c['status']} to {status}")
    err = gate_error(conn, candidate_id, status)
    if err:
        raise ValueError(err)
    conn.execute("UPDATE candidates SET status=?, notes=COALESCE(?, notes) WHERE id=?", (status, note, candidate_id))
    audit(conn, actor, "status_change", f"{candidate_id}: {c['status']} -> {status}")
    return {"candidate_id": candidate_id, "status": status}


def ats_export(conn) -> list[dict]:
    """Only recruiter-approved candidates and only their verified evidence leave the system."""
    out = []
    for c in load_candidates(conn):
        if c["status"] != "ready_for_ats" or gate_error(conn, c["id"], "ready_for_ats"):
            continue
        out.append({"name": c["display_name"], "synthetic": bool(c["synthetic"]), "headline": c["headline"],
                    "current_company": c["employer_descriptor"], "profile_url": c["profile_url"],
                    "market": c["market"], "background": c["background"], "notes": c["notes"],
                    "verified_evidence": [{"claim": e["claim"], "problem_solved": e["problem_solved"], "source_url": e["source_url"],
                                           "source_date": e["source_date"]} for e in c["evidence"] if e["verification"] == "verified"]})
    return out
