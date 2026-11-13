from app.connectors import ashby, cognition_blog


def test_meta_and_analysis(client):
    m = client.get("/api/meta").json()
    assert len(m["scenarios"]) == 6
    a = client.post("/api/analysis", json={"scenario_id": "apac_banking"}).json()
    assert a["capabilities"] and a["candidates"]
    assert client.post("/api/analysis", json={"scenario_id": "nope"}).status_code == 404


def test_custom_scenario(client):
    a = client.post("/api/analysis", json={"name": "Telco push", "segment_weights": {"telco": 1}, "market_weights": {"AU": 1}}).json()
    assert a["scenario"]["name"] == "Telco push" and a["problems"][0]["segment_id"] == "telco"


def test_review_and_status_endpoints(client):
    assert client.post("/api/evidence/c-au-01-e1/review", json={"decision": "verified"}).status_code == 200
    assert client.post("/api/evidence/c-au-01-e1/review", json={"decision": "maybe"}).status_code == 400
    r = client.post("/api/candidates/c-au-01/status", json={"status": "ready_for_ats"})
    assert r.status_code == 400
    assert client.get("/api/ats-export?format=csv").status_code == 200


def test_report_markdown(client):
    r = client.post("/api/report.md", json={"scenario_id": "apac_banking"})
    assert r.status_code == 200 and r.text.startswith("# Executive Talent Strategy")


def test_blog_parser():
    page = '<a href="/blog/singapore"><span>Opening Singapore</span><span>2026.04.30</span><p>APAC HQ</p></a>'
    posts = cognition_blog.parse_index(page)
    assert posts == [{"url": "https://cognition.ai/blog/singapore", "title": "Opening Singapore", "published_on": "2026-04-30", "summary": "APAC HQ"}]


def test_ashby_market_detection():
    assert ashby.market_of({"title": "Forward Deployed Engineer - Japan", "location": "", "secondary_locations": []}) == "Japan"
    assert ashby.market_of({"title": "AE", "location": "Singapore", "secondary_locations": []}) == "Singapore"
    assert ashby.market_of({"title": "AE", "location": "New York", "secondary_locations": []}) is None
