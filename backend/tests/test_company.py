"""Company packs: any company can be inserted from public sources without touching Cognition's data."""
import pytest

from app.connectors import company as src

JOBS = [
    {"id": "1", "title": "Enterprise Account Executive", "location": "Singapore", "secondary_locations": [], "department": "Sales"},
    {"id": "2", "title": "Solutions Engineer", "location": "Singapore", "secondary_locations": [], "department": "Sales"},
    {"id": "3", "title": "Account Executive, Japan", "location": "Tokyo, Japan", "secondary_locations": [], "department": "Sales"},
    {"id": "4", "title": "Software Engineer, Backend", "location": "Sydney, Australia", "secondary_locations": [], "department": "Eng"},
    {"id": "5", "title": "Partner Manager", "location": "Tokyo", "secondary_locations": [], "department": "BD"},
    {"id": "6", "title": "Account Executive", "location": "Tokyo", "secondary_locations": [], "department": "Sales"},
    {"id": "7", "title": "Software Engineer", "location": "San Francisco, CA", "secondary_locations": [], "department": "Eng"},
]
NEWS = [{"title": "Acme opens Tokyo office to serve Japanese banks", "url": "https://acme.example/blog/tokyo",
         "published_on": "2026-10-01", "summary": "Expanding in Japan with financial services customers."},
        {"title": "Acme partners with Accenture", "url": "https://acme.example/blog/accenture", "published_on": "2026-09-01", "summary": ""}]


@pytest.fixture
def stub(monkeypatch):
    def board(name, careers_url=None):
        if name.lower().startswith("nojobs"):
            return None
        return ("greenhouse", "acme", [j | {"published_on": "2026-11-01", "url": f"https://x/{j['id']}", "team": None,
                                             "market": src.market_of(j["title"] + " " + j["location"]), "retrieved_on": "2026-11-20"} for j in JOBS])
    monkeypatch.setattr(src, "find_board", board)
    monkeypatch.setattr(src, "find_feed", lambda site, feed=None: ("https://acme.example/rss", NEWS))
    monkeypatch.setattr(src, "hn_stories", lambda name: [])
    monkeypatch.setattr(src, "wikipedia", lambda name: {"title": name, "summary": f"{name} is a software company.", "url": "https://en.wikipedia.org/wiki/X"})


def test_board_url_parsing_and_markets():
    assert src.parse_board_url("https://jobs.ashbyhq.com/openai/123") == ("ashby", "openai")
    assert src.parse_board_url("https://job-boards.greenhouse.io/anthropic") == ("greenhouse", "anthropic")
    assert src.parse_board_url("https://boards.greenhouse.io/stripe/jobs/1") == ("greenhouse", "stripe")
    assert src.parse_board_url("https://jobs.lever.co/palantir") == ("lever", "palantir")
    assert src.parse_board_url("https://careers.smartrecruiters.com/Canva") == ("smartrecruiters", "Canva")
    assert src.parse_board_url("https://example.com/careers") is None
    assert src.market_of("Bengaluru, India") == "IN" and src.market_of("Seoul") == "KR" and src.market_of("Paris") is None
    assert src.slug_guesses("Scale AI") == ["scaleai", "scale-ai", "scale"]


def test_feed_parsing():
    rss = """<rss><channel><item><title>Launch</title><link>https://a/1</link><pubDate>Tue, 03 Nov 2026 10:00:00 GMT</pubDate>
             <description>&lt;p&gt;New &amp; improved&lt;/p&gt;</description></item></channel></rss>"""
    assert src.parse_feed(rss) == [{"title": "Launch", "url": "https://a/1", "published_on": "2026-11-03", "summary": "New & improved"}]
    atom = """<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Post</title><link href="https://a/2"/>
              <published>2026-10-01T00:00:00Z</published><summary>Hi</summary></entry></feed>"""
    assert src.parse_feed(atom)[0]["url"] == "https://a/2"


def test_add_company_builds_plan_and_keeps_cognition_isolated(client, stub):
    before = client.post("/api/analysis", json={"scenario_id": "apac_banking"}).json()
    r = client.post("/api/companies", json={"name": "Acme", "website": "acme.example"})
    assert r.status_code == 200
    c = r.json()
    assert c["id"] == "acme" and c["jobs"] == 7 and c["apac_jobs"] == 6 and c["signals"] == 3
    m = client.get("/api/meta?company=acme").json()
    ids = [s["id"] for s in m["scenarios"]]
    assert ids[0] == "acme:balanced" and "acme:market_jp" in ids
    assert m["company"]["name"] == "Acme" and m["counts"]["jobs"] == 7
    a = client.post("/api/analysis", json={"company": "acme", "scenario_id": "acme:market_jp"}).json()
    j = a["journey"]
    assert j["goal"]["inferred"] and j["goal"]["title"] == "Build Acme Japan into a bigger business"
    assert j["goal"]["top_markets"] == ["Japan"]
    assert "Country lead / general manager" in [h["name"] for h in j["hires"]]
    assert all(o["sensitivity"] == "none" for p in a["ecosystem"] for o in p["organisations"])
    assert {x["id"].split(":")[0] for x in a["open_jobs"]} == {"acme"}
    assert all(s["url"].startswith("https://acme.example") or "wikipedia" in s["url"] for s in a["radar"]["drivers"])
    # Cognition is unchanged and never sees Acme's jobs or news.
    after = client.post("/api/analysis", json={"scenario_id": "apac_banking"}).json()
    assert after["journey"] == before["journey"] and len(after["open_jobs"]) == len(before["open_jobs"])
    assert not any("acme" in (s["url"] or "") for s in client.get("/api/signals").json())


def test_company_refresh_delete_and_errors(client, stub):
    assert client.post("/api/companies", json={"name": "Acme"}).status_code == 200
    assert client.post("/api/companies", json={"name": "Acme"}).json()["jobs"] == 7  # rebuild replaces, not duplicates
    assert client.post("/api/companies/acme/refresh").status_code == 200
    assert [c["id"] for c in client.get("/api/companies").json()] == ["cognition", "acme"]
    assert client.post("/api/companies", json={"name": "Cognition"}).status_code == 422
    assert client.post("/api/companies", json={"name": " "}).status_code == 422
    assert client.post("/api/companies", json={"name": "X", "careers_url": "not a link"}).status_code == 422
    assert client.post("/api/analysis", json={"company": "nope"}).status_code == 404
    assert client.delete("/api/companies/cognition").status_code == 404
    assert client.delete("/api/companies/acme").status_code == 200
    assert client.get("/api/meta?company=acme").status_code == 404


def test_company_without_board_still_gets_a_plan(client, stub):
    c = client.post("/api/companies", json={"name": "NoJobs Ltd"}).json()
    assert c["jobs"] == 0 and any("No public careers board" in g for g in c["gaps"])
    a = client.post("/api/analysis", json={"company": c["id"], "scenario_id": f"{c['id']}:balanced"}).json()
    assert a["journey"]["hires"] and a["open_jobs"] == []
