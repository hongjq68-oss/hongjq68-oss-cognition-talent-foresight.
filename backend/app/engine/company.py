"""Builds a company pack from public sources so the engine can run for any company.

Goals are inferred by rules from what the company is hiring for and what it publishes;
they are hypotheses for a recruiter to confirm, not statements of the company's plans."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from .. import db
from ..connectors import company as src
from ..seed import generic
from ..seed.load import load_jobs

MARKETS = ["SG", "JP", "AU", "IN", "KR"]
NAMES = {"SG": "Singapore", "JP": "Japan", "AU": "Australia", "IN": "India", "KR": "South Korea"}
DEFAULT_MARKETS = {"SG": 0.8, "AU": 0.6, "JP": 0.6, "IN": 0.6, "KR": 0.4}

ROLE_THEME = {
    "g_country_lead": "t_market", "g_enterprise_ae": "t_enterprise", "g_solutions": "t_enterprise", "g_fde": "t_enterprise",
    "g_software_eng": "t_product", "g_infra": "t_product", "g_product": "t_product", "g_design": "t_product",
    "g_ml": "t_ai", "g_data": "t_ai", "g_security": "t_trust", "g_marketing": "t_growth", "g_partner": "t_partners",
    "g_customer_success": "t_customers", "g_recruiting": "t_scale", "g_ops": "t_scale",
}
KIND_RULES = [
    ("funding", r"\b(raises?|raised|funding|series [a-f]|valuation|ipo)\b"),
    ("acquisition", r"\b(acquires?|acquired|acquisition)\b"),
    ("partnership", r"\b(partner(s|ship)?|alliance|collaborat\w+|integrat\w+ with)\b"),
    ("expansion", r"\b(expand\w*|launch\w* in|opens?|office|headquarters|hq|enters?)\b"),
    ("customer", r"\b(customer|case study|deploy\w*|selects?|chooses?|adopts?)\b"),
    ("leadership", r"\b(appoint\w*|hires?|joins as|chief|ceo|cto|president)\b"),
    ("regulatory", r"\b(regulat\w+|complian\w+|privacy|gdpr|certif\w+|soc 2|iso 27001)\b"),
    ("product", r"\b(launch\w*|introduc\w+|announc\w+|release\w*|new|model|feature)\b"),
]
THEME_RULES = {
    "t_market": r"\b(expand\w*|office|headquarters|launch\w* in|local|country|region\w*|apac|asia)\b",
    "t_enterprise": r"\b(enterprise|bank\w*|financial|insur\w+|government|public sector|regulated|telco|fortune)\b",
    "t_product": r"\b(platform|feature|launch\w*|release\w*|product|app|api)\b",
    "t_ai": r"\b(ai|a\.i\.|llm|model|machine learning|agent\w*|genai|generative)\b",
    "t_partners": r"\b(partner\w*|alliance|reseller|marketplace|aws|azure|google cloud|accenture|deloitte|infosys)\b",
    "t_growth": r"\b(users|brand|campaign|community|creators?|consumers?|growth)\b",
    "t_customers": r"\b(customers?|renew\w*|expan\w+ with|retention)\b",
    "t_trust": r"\b(security|privacy|compliance|trust|safety|certif\w+|residency)\b",
    "t_scale": r"\b(hiring|team|employees|headcount|talent)\b",
}
SEGMENT_HINTS = {"banking": r"\bbank\w*|financial", "insurance": r"insur", "telco": r"telco|telecom",
                 "healthcare": r"health|hospital|pharma", "manufacturing": r"manufactur|automotive", "it_services": r"consult|integrator"}
GOAL_TITLES = {
    "t_enterprise": "Win more large enterprise customers in APAC", "t_product": "Ship product faster from APAC engineering hubs",
    "t_ai": "Build AI into {name}'s product", "t_partners": "Grow {name} through partners in APAC",
    "t_growth": "Grow {name}'s users and brand in APAC", "t_customers": "Grow revenue from existing customers in APAC",
    "t_trust": "Make security and compliance a strength in APAC", "t_scale": "Scale {name}'s APAC team quickly",
}
DERAILERS = {
    "t_market": "Country leader hired too late, so the first customers slip", "t_enterprise": "Security and procurement reviews take longer than planned",
    "t_product": "Senior engineering hires take 4+ months to land", "t_ai": "ML talent is scarce and competitors pay more",
    "t_partners": "Partners take the customer relationship", "t_growth": "Local marketing doesn't translate from global campaigns",
    "t_customers": "Customers churn before value is proven", "t_trust": "A local privacy or residency rule blocks deals",
    "t_scale": "Hiring speed drops the quality bar",
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "company"


def _match(rules: dict, text: str) -> list[str]:
    return [k for k, pat in rules.items() if re.search(pat, text, re.I)]


def classify(text: str) -> str:
    return next((k for k, pat in KIND_RULES if re.search(pat, text, re.I)), "news")


def _role_of(title: str) -> str | None:
    t = title.lower()
    hits = [(len(k), r["id"]) for r in generic.ROLE_TYPES for k in r["posting_keywords"] if k.lower() in t]
    return max(hits)[1] if hits else None


def infer_goals(name: str, jobs: list[dict], signals: list[dict]) -> list[dict]:
    apac = [j for j in jobs if j.get("market") in MARKETS]
    by_market = {m: sum(1 for j in apac if j["market"] == m) for m in MARKETS}
    sig_market = {m: sum(1 for s in signals if m in s["regions"]) for m in MARKETS}
    theme = {t["id"]: 0.0 for t in generic.THEMES}
    market_theme = {m: dict.fromkeys(theme, 0.0) for m in MARKETS}
    for j in apac:
        r = _role_of(j["title"])
        if r:
            theme[ROLE_THEME[r]] += 1
            market_theme[j["market"]][ROLE_THEME[r]] += 1
    for s in signals:
        for t in s["segment_ids"]:
            if t in theme:
                theme[t] += 0.5
    for m in MARKETS:
        if by_market[m] >= 3:
            theme["t_market"] += 0.5
    top_m = max(by_market.values()) or 0
    if top_m:
        mw = {m: round(0.2 + 0.8 * by_market[m] / top_m, 2) if by_market[m] else (0.3 if sig_market[m] else 0.0) for m in MARKETS}
    elif any(sig_market.values()):
        top_s = max(sig_market.values())
        mw = {m: round(0.3 + 0.7 * sig_market[m] / top_s, 2) for m in MARKETS}
    else:
        mw = dict(DEFAULT_MARKETS)
    peak = max(theme.values()) or 1
    weights = {t: round(v / peak, 2) for t, v in sorted(theme.items(), key=lambda kv: -kv[1]) if v / peak >= 0.2}
    if not weights:
        weights = {"t_market": 1.0, "t_enterprise": 0.6, "t_product": 0.5}
    tdata = {t["id"]: t for t in generic.THEMES}
    basis = [f"{len(apac)} open APAC jobs (" + ", ".join(f"{NAMES[m]} {n}" for m, n in by_market.items() if n) + ")" if apac
             else "No open APAC jobs found on a public careers board", f"{len(signals)} public news items and posts read"]

    def sig_ids(themes, markets):
        recent = sorted(signals, key=lambda s: s["happened_on"] or "", reverse=True)
        hits = [s for s in recent if set(s["segment_ids"]) & set(themes) or set(s["regions"]) & set(markets)]
        return [s["id"] for s in (hits + [s for s in recent if s not in hits])[:6]]

    def goal(id_, title, hypothesis, seg_w, mkt_w, themes):
        lead = [t for t in themes if t in tdata][:3]
        return dict(id=id_, name=title, data=dict(
            hypothesis=hypothesis, signal_ids=sig_ids(lead, [m for m, w in mkt_w.items() if w >= 0.6]),
            segment_weights=seg_w, market_weights=mkt_w, capability_boosts={}, extra_demand={},
            business_changes=[c for t in lead for c in tdata[t]["data"]["challenges"]][:4],
            derailers=[DERAILERS[t] for t in lead], alternatives=[],
            assumptions=["Inferred from public jobs and news. Confirm the goal with the business before acting."] + basis,
            goal=title, outcomes=[g for t in lead for g in tdata[t]["data"]["goals"]][:3], inferred=True, basis=basis))

    focus = [m for m, w in sorted(mw.items(), key=lambda kv: -kv[1]) if w >= 0.6]
    themes_txt = ", ".join(tdata[t]["name"].lower() for t in list(weights)[:3])
    hypothesis = (f"{name} keeps growing in APAC, led by " + (", ".join(NAMES[m] for m in focus[:3]) or "its main markets")
                  + f", with hiring focused on {themes_txt}." if apac or signals else
                  f"We found no public jobs or news for {name}, so this is a starting template, not a forecast: "
                  f"a typical APAC expansion focused on {themes_txt}. Add the careers page or blog link to make it specific.")
    out = [goal("balanced", f"Grow {name} in APAC over the next 12 months", hypothesis, weights, mw, list(weights))]
    for m in sorted(MARKETS, key=lambda m: -(by_market[m] + sig_market[m]))[:2]:
        if by_market[m] < 3 and sig_market[m] < 2:
            continue
        mt = market_theme[m]
        pk = max(mt.values()) or 1
        seg = {"t_market": 1.0} | {t: round(v / pk, 2) for t, v in mt.items() if v / pk >= 0.3 and t != "t_market"}
        out.append(goal(f"market_{m.lower()}", f"Build {name} {NAMES[m]} into a bigger business",
                        f"{name} grows {NAMES[m]} from {by_market[m]} open roles into a full local business with its own customers and team.",
                        seg, {x: 1.0 if x == m else 0.2 for x in MARKETS}, list(seg)))
    for t in [t for t in weights if t in GOAL_TITLES][:3]:
        seg = {t: 1.0} | {x: round(0.4 * w, 2) for x, w in weights.items() if x != t}
        out.append(goal(f"theme_{t[2:]}", GOAL_TITLES[t].format(name=name),
                        f"{name} focuses its APAC plan on {tdata[t]['name'].lower()}.", seg, mw, [t] + list(weights)))
    return out


def _signal(cid, i, item, source_type, publisher, evidence_class):
    text = f"{item['title']} {item.get('summary', '')}"
    return dict(id=f"{cid}:sig{i}", company_id=cid, kind=classify(text), title=item["title"][:200],
                summary=item.get("summary") or item["title"], happened_on=item.get("published_on"),
                regions=sorted({m for m in MARKETS if re.search(rf"\b({NAMES[m]}|{m})\b", text)} | ({"APAC"} if re.search(r"\b(APAC|Asia)\b", text) else set())),
                segment_ids=_match(THEME_RULES, text) + _match(SEGMENT_HINTS, text),
                source_id=f"{cid}:src{i}", evidence_class=evidence_class, curated=0), \
        dict(id=f"{cid}:src{i}", company_id=cid, title=item["title"][:200], url=item["url"], publisher=publisher,
             published_on=item.get("published_on"), retrieved_on=datetime.now(timezone.utc).date().isoformat(), source_type=source_type)


def build(conn, name: str, website: str | None = None, careers_url: str | None = None, blog_url: str | None = None) -> dict:
    name = name.strip()
    cid = slugify(name)
    if cid == "cognition":
        raise ValueError("Cognition is already set up with curated data")
    gaps, items = [], []
    board = None
    try:
        board = src.find_board(name, careers_url)
    except Exception as e:  # noqa: BLE001 — a dead source must not stop the build
        gaps.append(f"Careers board failed: {str(e)[:120]}")
    if not board:
        gaps.append("No public careers board found (tried Ashby, Greenhouse, Lever, SmartRecruiters). Paste the careers page link to fix.")
    wiki = None
    try:
        wiki = src.wikipedia(name)
    except Exception:  # noqa: BLE001
        pass
    if wiki:
        items.append((dict(title=f"{wiki['title']}: company profile", url=wiki["url"], published_on=None, summary=wiki["summary"]),
                      "analyst", "Wikipedia", "market_intel"))
    try:
        feed = src.find_feed(website, blog_url)
    except Exception:  # noqa: BLE001
        feed = None
    if feed:
        items += [(p, "company_blog", name, "verified_fact") for p in feed[1]]
    else:
        gaps.append("No blog or news feed found. Paste the blog's RSS link to add the company's own announcements.")
    try:
        items += [(h, "press", "Hacker News", "market_intel") for h in src.hn_stories(name)]
    except Exception:  # noqa: BLE001
        gaps.append("Hacker News search failed")

    for t in ("signals", "sources", "job_postings", "scenarios"):
        conn.execute(f"DELETE FROM {t} WHERE company_id = ?", (cid,))
    signals = []
    for i, (it, stype, pub, ev) in enumerate(items, 1):
        sig, source = _signal(cid, i, it, stype, pub, ev)
        db.upsert(conn, "sources", source)
        db.upsert(conn, "signals", sig)
        signals.append(sig)
    jobs = board[2] if board else []
    if board:
        load_jobs(conn, jobs, cid)
        db.upsert(conn, "sources", dict(id=f"{cid}:board", company_id=cid, title=f"{name} public job board ({board[0].title()})",
                                        url=src.BOARD_URLS[board[0]].format(board[1]), publisher=board[0].title(), source_type="job_board",
                                        retrieved_on=datetime.now(timezone.utc).date().isoformat()))
    goals = infer_goals(name, jobs, signals)
    for g in goals:
        db.upsert(conn, "scenarios", g | {"id": f"{cid}:{g['id']}", "company_id": cid})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prev = db.row(conn.execute("SELECT created_at FROM companies WHERE id = ?", (cid,)).fetchone())
    rec = dict(id=cid, name=name, website=website, careers_url=src.BOARD_URLS[board[0]].format(board[1]) if board else careers_url,
               board={"provider": board[0], "slug": board[1]} if board else None, blog_feed=feed[0] if feed else blog_url,
               description=wiki["summary"] if wiki else None, curated=0, created_at=prev["created_at"] if prev else now,
               refreshed_at=now, gaps=gaps)
    db.upsert(conn, "companies", rec)
    conn.execute("INSERT INTO audit_log (at, actor, action, detail) VALUES (?,?,?,?)",
                 (now, "recruiter", "company_built", f"{cid}: {len(jobs)} jobs, {len(signals)} signals, {len(goals)} goals"))
    return rec | {"jobs": len(jobs), "apac_jobs": sum(1 for j in jobs if j.get("market")), "signals": len(signals), "goals": len(goals)}
