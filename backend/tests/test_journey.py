from datetime import date

from app.engine import analysis, journey
from app.engine import kb as kb_mod


def test_goal_to_shortlist_journey(conn):
    kb = kb_mod.load(conn)
    j = analysis.run(kb, conn, "apac_banking", today=date(2026, 11, 17))["journey"]
    assert j["goal"]["title"].startswith("Win 3 more major banks")
    assert 1 <= len(j["hires"]) <= 6
    for h in j["hires"]:
        assert h["when"]["tone"] in ("now", "soon", "later")
        assert all(c["goal_weight"] > 0 for c in h["where"])
        assert [c["priority"] for c in h["where"]] == sorted((c["priority"] for c in h["where"]), reverse=True)
        assert all(o["pool_type"] != "direct" for o in h["companies"])
        assert len(h["shortlist"]) <= 8
        assert [p["match"] for p in h["shortlist"]] == sorted((p["match"] for p in h["shortlist"]), reverse=True)
        assert all(p["status"] != "parked" for p in h["shortlist"])
        hot = {c["market"] for c in h["where"][:2]}
        for p in h["shortlist"]:
            assert (p["market"] in hot) == any("a top country" in r for r in p["reasons"])
    rows = j["map"]["rows"]
    assert len(rows) == len(j["hires"]) and all(len(r["cells"]) == 5 for r in rows)
    assert max(c["supply"] for r in rows for c in r["cells"]) == 100
    assert all(0 <= c["supply"] <= 100 for r in rows for c in r["cells"])


def test_market_of_location():
    assert journey.market_of("Tokyo, Japan") == "JP"
    assert journey.market_of("Bengaluru") == "IN"
    assert journey.market_of("Berlin") is None and journey.market_of(None) is None


def test_meta_lists_plain_goals(client):
    goals = {s["id"]: s["goal"] for s in client.get("/api/meta").json()["scenarios"]}
    assert goals["japan_aggressive"] == "Build Cognition Japan into a full country business"
