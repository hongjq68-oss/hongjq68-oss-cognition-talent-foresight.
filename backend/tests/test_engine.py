from datetime import date

import pytest

from app.engine import analysis, kb as kb_mod, report
from app.engine import candidates as ce
from app.engine.forecast import CLASS_LABELS

TODAY = date(2026, 11, 13)


def run(conn, sid="apac_banking", **ov):
    return analysis.run(kb_mod.load(conn), conn, sid, ov or None, TODAY)


def test_banking_scenario_puts_banking_problems_first(conn):
    a = run(conn)
    assert all(p["segment_id"] == "banking" for p in a["problems"][:5])
    assert a["problems"][0]["citations"], "top problem should cite public evidence"


def test_forecast_has_horizons_and_valid_classes(conn):
    a = run(conn)
    for c in a["capabilities"]:
        assert set(c["demand"]) == {"now", "6m", "12m", "24m"}
        assert c["classification"] in CLASS_LABELS
        assert c["confidence"] in {"low", "medium", "high"}
        assert c["evidence_class"] == "prediction"
    assert {c["classification"] for c in a["capabilities"]} >= {"immediate", "emerging", "develop", "partner"}


def test_scenarios_change_the_forecast(conn):
    bank = {c["id"]: c["peak"] for c in run(conn)["capabilities"]}
    japan = {c["id"]: c["peak"] for c in run(conn, "japan_aggressive")["capabilities"]}
    sec = {c["id"]: c["peak"] for c in run(conn, "new_product_security")["capabilities"]}
    assert japan["japanese_enterprise"] > bank.get("japanese_enterprise", 0) + 20
    assert sec["appsec_remediation"] > bank["appsec_remediation"] + 20


def test_overrides_reweight_segments(conn):
    base = run(conn)
    ins = run(conn, segment_weights={"banking": 0, "insurance": 1.0})
    assert ins["problems"][0]["segment_id"] == "insurance"
    assert base["problems"][0]["segment_id"] == "banking"


def test_capability_pools_cover_five_types(conn):
    a = run(conn)
    for cid, pools in a["capability_pools"].items():
        non_empty = [pt for pt, g in pools.items() if g["organisations"]]
        assert len(non_empty) == 5, (cid, non_empty)


def test_hiring_signals_from_public_job_board(conn):
    h = run(conn)["radar"]["hiring"]
    assert h["in_scenario_markets"] > 0 and h["by_archetype"]


def test_title_only_evidence_scores_zero(conn):
    k = kb_mod.load(conn)
    cand = {"evidence": [{"id": "x", "evidence_type": "title_only", "verification": "verified", "capability_ids": ["enterprise_sales_fsi"]}],
            "market": "SG"}
    assert ce.capability_scores(cand)["enterprise_sales_fsi"]["score"] == 0
    f = ce.fit(k, cand, k.archetypes["account_director_fsi"], {"market_weights": {}}, {})
    assert f["score"] == 0 and not f["demonstrated"]


def test_verification_raises_fit(conn):
    k = kb_mod.load(conn)
    arch = k.archetypes["solution_architect_reg"]
    sc = {"market_weights": {"SG": 1.0}}

    def score():
        cand = next(c for c in ce.load_candidates(conn) if c["id"] == "c-sg-02")
        return ce.fit(k, cand, arch, sc, {})["score"]

    before = score()
    ce.review_evidence(conn, "c-sg-02-e2", "verified", "tester")
    assert score() > before
    ce.review_evidence(conn, "c-sg-02-e2", "rejected", "tester")
    assert score() < before


def test_status_workflow_gates(conn):
    with pytest.raises(ValueError):
        ce.set_status(conn, "c-sg-01", "ready_for_ats", "t")
    ce.set_status(conn, "c-sg-01", "evidence_review", "t")
    with pytest.raises(ValueError):  # only 1 verified evidence item
        ce.set_status(conn, "c-sg-01", "verified", "t")
    ce.review_evidence(conn, "c-sg-01-e2", "verified", "t")
    ce.set_status(conn, "c-sg-01", "verified", "t")
    with pytest.raises(ValueError):  # e3 still unreviewed
        ce.set_status(conn, "c-sg-01", "ready_for_ats", "t")
    ce.review_evidence(conn, "c-sg-01-e3", "rejected", "t")
    ce.set_status(conn, "c-sg-01", "ready_for_ats", "t")
    out = ce.ats_export(conn)
    assert len(out) == 1 and len(out[0]["verified_evidence"]) == 2
    assert conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] >= 5


def _status(conn, cid):
    return conn.execute("SELECT status FROM candidates WHERE id=?", (cid,)).fetchone()["status"]


def test_unreviewing_evidence_revokes_approval(conn):
    ce.set_status(conn, "c-sg-01", "evidence_review", "t")
    ce.review_evidence(conn, "c-sg-01-e2", "verified", "t")
    ce.review_evidence(conn, "c-sg-01-e3", "rejected", "t")
    ce.set_status(conn, "c-sg-01", "verified", "t")
    ce.set_status(conn, "c-sg-01", "ready_for_ats", "t")
    r = ce.review_evidence(conn, "c-sg-01-e3", "unverified", "t")  # still 2 verified, one unreviewed
    assert r["candidate_status"] == "verified" == _status(conn, "c-sg-01")
    assert ce.ats_export(conn) == []
    ce.review_evidence(conn, "c-sg-01-e2", "unverified", "t")  # drops below 2 verified
    assert _status(conn, "c-sg-01") == "evidence_review"
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE action='status_revoked'").fetchone()[0] == 2


def test_candidates_have_explanations(conn):
    for c in run(conn)["candidates"]:
        assert c["transferability"] and c["validation_questions"]


def test_report_has_eleven_tagged_sections(conn):
    r = report.build(run(conn))
    assert [s["number"] for s in r["sections"]] == list(range(1, 12))
    for s in r["sections"]:
        assert s["items"], s["title"]
        for it in s["items"]:
            assert it["evidence_class"] in r["evidence_labels"]
    md = report.to_markdown(r)
    assert "## 11. Recommended next actions for the recruiter" in md and "https://cognition.ai/blog/" in md


def test_role_shortlists_are_evidence_backed(conn):
    ce.set_status(conn, "c-sg-01", "parked", "t")
    r = run(conn)
    for s in r["strategies"]:
        sl = s["shortlist"]
        assert len(sl) <= ce.SHORTLIST_SIZE
        assert [x["score"] for x in sl] == sorted((x["score"] for x in sl), reverse=True)
        assert all(x["strengths"] for x in sl)
        assert "c-sg-01" not in {x["candidate_id"] for x in sl}
    assert any(s["shortlist"] for s in r["strategies"])
