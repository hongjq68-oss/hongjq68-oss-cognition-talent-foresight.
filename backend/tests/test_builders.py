import pytest

from app.connectors import builders as src
from app.engine import builders as be
from app.engine import kb as kb_mod


def _p(source, handle, location=None):
    return src._person(source, handle, handle.title(), f"https://example.org/{handle}", location)


ITEMS = {
    "repo": src._item("github", "repo", "mei/cobol-lens", "https://github.com/mei/cobol-lens", "2026-10-01",
                      "Trace data through COBOL copybooks mainframe", _p("github", "mei", "Singapore"), stars=420),
    "launch": src._item("hn", "launch", "Show HN: Copybook parser", "https://news.ycombinator.com/item?id=1", "2026-09-01",
                        "COBOL copybook parser in Rust", _p("hn", "kenji"), points=88),
    "off_topic": src._item("devto", "article", "My sourdough journey", "https://dev.to/x/bread", "2026-08-01",
                           "baking", _p("devto", "baker")),
}


@pytest.fixture
def kb(conn):
    return kb_mod.load(conn)


def test_title_free_mapping_and_unverified(kb):
    ev = be.to_evidence(kb, ITEMS["repo"])
    assert {"legacy_modernisation", "software_engineering"} <= set(ev["capability_ids"])
    assert ev["verification"] == "unverified" and ev["source_url"].startswith("https://github.com/")
    assert ev["evidence_type"] == "open_source" and "420 stars" in ev["claim"]
    assert be.to_evidence(kb, ITEMS["off_topic"]) is None


def test_investigate_adds_sourced_evidence_once(conn, kb, monkeypatch):
    monkeypatch.setitem(be.HANDLE_SOURCES, "github", lambda h: [ITEMS["repo"]])
    monkeypatch.setitem(be.HANDLE_SOURCES, "hn", lambda h: (_ for _ in ()).throw(src.SourceError("down")))
    r = be.investigate(conn, kb, {"github": "mei", "hn": "mei"}, display_name="Mei Real", market="SG", pool_type="founder")
    assert r["added"] == 1 and r["sources"]["hn"]["ok"] is False
    cand = conn.execute("SELECT synthetic, status, profile_url FROM candidates WHERE id=?", (r["candidate_id"],)).fetchone()
    assert tuple(cand) == (0, "discovered", "https://example.org/mei")
    again = be.investigate(conn, kb, {"github": "mei"}, candidate_id=r["candidate_id"])
    assert again["added"] == 0
    with pytest.raises(ValueError):
        be.investigate(conn, kb, {"github": "mei"}, display_name="X", pool_type="nope")


def test_monitor_finds_new_builders_then_dedupes(conn, kb, monkeypatch):
    monkeypatch.setitem(be.MONITOR_SOURCES, "github", lambda q, loc: [ITEMS["repo"]])
    monkeypatch.setitem(be.MONITOR_SOURCES, "hn", lambda q, loc: [ITEMS["launch"]])
    monkeypatch.setitem(be.MONITOR_SOURCES, "devto", lambda q, loc: [ITEMS["off_topic"]])
    monkeypatch.setitem(be.MONITOR_SOURCES, "arxiv", lambda q, loc: [])
    first = be.run_monitor(conn, kb, "m-cobol-apac")
    assert first["new"] == 2 and first["builders"] == 2
    assert be.run_monitor(conn, kb, "m-cobol-apac")["new"] == 0
    leads = be.list_leads(conn, "m-cobol-apac")
    assert {lead["display_name"] for lead in leads} == {"Mei", "Kenji"}
    mei = next(lead for lead in leads if lead["display_name"] == "Mei")
    out = be.decide_lead(conn, mei["id"], "promote", "SG", "founder")
    ev = conn.execute("SELECT verification FROM candidate_evidence WHERE candidate_id=?", (out["candidate_id"],)).fetchall()
    assert ev and all(v[0] == "unverified" for v in ev)
    with pytest.raises(ValueError):
        be.decide_lead(conn, mei["id"], "dismiss")
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE action IN ('monitor_run','lead_promoted')").fetchone()[0] == 3


def test_expired_leads_are_purged(conn, kb, monkeypatch):
    for s in be.MONITOR_SOURCES:
        monkeypatch.setitem(be.MONITOR_SOURCES, s, lambda q, loc: [ITEMS["launch"]])
    be.run_monitor(conn, kb, "m-cobol-apac")
    conn.execute("UPDATE leads SET expires_at='2000-01-01T00:00:00+00:00'")
    assert be.purge_expired(conn) == 1 and not be.list_leads(conn)


def test_api_overview(client):
    r = client.get("/api/builders").json()
    assert len(r["monitors"]) >= 5 and "github" in r["sources"]
    assert client.post("/api/builders/monitors", json={"name": "x", "capability_id": "nope", "queries": {"hn": "a"}}).status_code == 400
