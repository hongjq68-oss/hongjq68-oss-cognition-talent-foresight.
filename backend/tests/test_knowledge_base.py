from app.engine.pools import POOL_TYPES
from app.seed.archetypes import ARCHETYPES
from app.seed.candidates import CANDIDATES
from app.seed.capabilities import CAPABILITIES
from app.seed.organisations import ORGANISATIONS
from app.seed.scenarios import SCENARIOS
from app.seed.segments import PROBLEMS, SEGMENTS, SEGMENT_GTM
from app.seed.signals import CURATED_SIGNALS, MARKET_INTEL_SIGNALS

CAP_IDS = {c["id"] for c in CAPABILITIES}
SIG_IDS = {s["id"] for s in CURATED_SIGNALS + MARKET_INTEL_SIGNALS}


def test_five_capability_categories():
    assert {c["category"] for c in CAPABILITIES} == {"technical", "commercial", "delivery", "transformation", "entrepreneurial"}


def test_every_capability_has_all_five_pool_types():
    for c in CAPABILITIES:
        types = {o["pool_type"] for o in ORGANISATIONS if c["id"] in o["capability_ids"]}
        assert types == set(POOL_TYPES), (c["id"], set(POOL_TYPES) - types)


def test_references_resolve():
    for o in ORGANISATIONS:
        assert set(o["capability_ids"]) <= CAP_IDS, o["id"]
        assert set(o["signal_ids"]) <= SIG_IDS, o["id"]
    for p in PROBLEMS:
        assert set(p["capabilities"]) <= CAP_IDS, p["id"]
        assert set(p["signal_ids"]) <= SIG_IDS, p["id"]
    for a in ARCHETYPES:
        assert set(a["capability_weights"]) <= CAP_IDS, a["id"]
    for s in SCENARIOS:
        d = s["data"]
        assert set(d["signal_ids"]) <= SIG_IDS, s["id"]
        assert set(d["capability_boosts"]) | set(d["extra_demand"]) <= CAP_IDS, s["id"]
        assert set(d["segment_weights"]) <= {x["id"] for x in SEGMENTS}
    for seg, caps in SEGMENT_GTM.items():
        assert set(caps) <= CAP_IDS, seg
    for k in CANDIDATES:
        for e in k["evidence"]:
            assert set(e["capability_ids"]) <= CAP_IDS, k["id"]


def test_curated_signals_have_dated_public_source():
    for s in CURATED_SIGNALS:
        assert s["url"].startswith("https://cognition.ai/") and s["happened_on"], s["id"]


def test_all_segments_and_six_scenarios_present():
    assert len(SEGMENTS) == 7 and len(SCENARIOS) == 6
    assert all(any(p["segment_id"] == s["id"] for p in PROBLEMS) for s in SEGMENTS)


def test_candidates_are_marked_synthetic():
    assert all(k["synthetic"] == 1 for k in CANDIDATES)
