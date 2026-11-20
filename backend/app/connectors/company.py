"""Public connectors for any company: careers boards (Ashby, Greenhouse, Lever, SmartRecruiters),
the company's own blog/news feed, Hacker News stories and the Wikipedia summary.
Only public, unauthenticated endpoints are used."""
from __future__ import annotations

import re
import time
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote, urljoin, urlparse
from xml.etree import ElementTree as ET

import httpx

UA = {"User-Agent": "TalentForesight/1.0 (+https://github.com/hongjq68-oss/hongjq68-oss-cognition-talent-foresight.) python-httpx"}
TIMEOUT = 20.0

MARKERS = [
    ("Singapore", "SG"), ("Tokyo", "JP"), ("Osaka", "JP"), ("Japan", "JP"), ("Sydney", "AU"), ("Melbourne", "AU"),
    ("Brisbane", "AU"), ("Perth", "AU"), ("Australia", "AU"), ("ANZ", "AU"), ("Bengaluru", "IN"), ("Bangalore", "IN"),
    ("Hyderabad", "IN"), ("Mumbai", "IN"), ("Pune", "IN"), ("Gurgaon", "IN"), ("Gurugram", "IN"), ("Delhi", "IN"),
    ("Chennai", "IN"), ("India", "IN"), ("Seoul", "KR"), ("Korea", "KR"),
]


def market_of(text: str) -> str | None:
    for marker, code in MARKERS:
        if re.search(rf"\b{marker}\b", text or ""):
            return code
    return None


def _get(url: str, **kw) -> httpx.Response:
    r = httpx.get(url, headers=UA, timeout=TIMEOUT, follow_redirects=True, **kw)
    r.raise_for_status()
    return r


def _strip(html: str | None, n: int = 400) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html or ""))).strip()[:n]


# ---------------- Careers boards ----------------

def _ashby(slug):
    data = _get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}").json()
    for j in data.get("jobs", []):
        yield dict(id=j.get("id"), title=j.get("title"), department=j.get("department"), team=j.get("team"),
                   location=j.get("location") or "", secondary_locations=[s.get("location", "") for s in j.get("secondaryLocations") or []],
                   published_on=(j.get("publishedAt") or "")[:10], url=j.get("jobUrl"))


def _greenhouse(slug):
    data = _get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs").json()
    for j in data.get("jobs", []):
        yield dict(id=j.get("id"), title=j.get("title"), department=None, team=None,
                   location=(j.get("location") or {}).get("name", ""), secondary_locations=[],
                   published_on=(j.get("updated_at") or "")[:10], url=j.get("absolute_url"))


def _lever(slug):
    for j in _get(f"https://api.lever.co/v0/postings/{slug}?mode=json").json():
        cat = j.get("categories") or {}
        yield dict(id=j.get("id"), title=j.get("text"), department=cat.get("department"), team=cat.get("team"),
                   location=cat.get("location") or "", secondary_locations=cat.get("allLocations") or [],
                   published_on=datetime.fromtimestamp((j.get("createdAt") or 0) / 1000, timezone.utc).date().isoformat(),
                   url=j.get("hostedUrl"))


def _smartrecruiters(slug):
    offset = 0
    while offset < 1000:
        data = _get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={offset}").json()
        for j in data.get("content", []):
            loc = j.get("location") or {}
            yield dict(id=j.get("id"), title=j.get("name"), department=(j.get("department") or {}).get("label"), team=None,
                       location=", ".join(x for x in (loc.get("city"), loc.get("country", "").upper()) if x),
                       secondary_locations=[], published_on=(j.get("releasedDate") or "")[:10],
                       url=f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}")
        offset += 100
        if offset >= data.get("totalFound", 0):
            break


PROVIDERS = {"ashby": _ashby, "greenhouse": _greenhouse, "lever": _lever, "smartrecruiters": _smartrecruiters}
BOARD_URLS = {"ashby": "https://jobs.ashbyhq.com/{}", "greenhouse": "https://job-boards.greenhouse.io/{}",
              "lever": "https://jobs.lever.co/{}", "smartrecruiters": "https://careers.smartrecruiters.com/{}"}
URL_PATTERNS = [
    (r"jobs\.ashbyhq\.com/([^/?#]+)", "ashby"), (r"api\.ashbyhq\.com/posting-api/job-board/([^/?#]+)", "ashby"),
    (r"(?:job-)?boards(?:-api)?\.greenhouse\.io/(?:v1/boards/)?([^/?#]+)", "greenhouse"),
    (r"jobs\.(?:eu\.)?lever\.co/([^/?#]+)", "lever"), (r"api\.lever\.co/v0/postings/([^/?#]+)", "lever"),
    (r"(?:careers|jobs)\.smartrecruiters\.com/([^/?#]+)", "smartrecruiters"),
]


def parse_board_url(url: str) -> tuple[str, str] | None:
    for pat, provider in URL_PATTERNS:
        m = re.search(pat, url or "")
        if m:
            return provider, m.group(1)
    return None


def slug_guesses(name: str) -> list[str]:
    base = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    out = [base.replace(" ", ""), base.replace(" ", "-"), base.split(" ")[0] if base else ""]
    return list(dict.fromkeys(s for s in out if s))


def fetch_jobs(provider: str, slug: str) -> list[dict]:
    today = date.today().isoformat()
    jobs = []
    for j in PROVIDERS[provider](slug):
        hay = " ".join([j["title"] or "", j["location"] or ""] + list(j["secondary_locations"] or []))
        jobs.append(j | {"market": market_of(hay), "retrieved_on": today})
    return jobs


def find_board(name: str, careers_url: str | None = None) -> tuple[str, str, list[dict]] | None:
    """Return (provider, slug, jobs) for the first public board that has postings."""
    tries = []
    if careers_url and (p := parse_board_url(careers_url)):
        tries.append(p)
    tries += [(prov, s) for s in slug_guesses(name) for prov in PROVIDERS]
    for prov, slug in tries:
        try:
            jobs = fetch_jobs(prov, slug)
        except (httpx.HTTPError, ValueError):
            continue
        if jobs:
            return prov, slug, jobs
    return None


# ---------------- Blog / news feed ----------------

FEED_PATHS = ["/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/blog/rss.xml", "/blog/feed", "/blog/rss",
              "/news/rss.xml", "/newsroom/rss.xml", "/blog/feed.xml", "/index.xml"]


def _date(s: str | None) -> str | None:
    if not s:
        return None
    try:
        return parsedate_to_datetime(s).date().isoformat()
    except (TypeError, ValueError):
        return s[:10] if re.match(r"\d{4}-\d{2}-\d{2}", s) else None


def parse_feed(xml: str) -> list[dict]:
    root = ET.fromstring(xml)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for it in root.iter("item"):
        out.append(dict(title=_strip(it.findtext("title"), 200), url=(it.findtext("link") or "").strip(),
                        published_on=_date(it.findtext("pubDate")), summary=_strip(it.findtext("description"))))
    for e in root.findall("a:entry", ns):
        link = e.find("a:link", ns)
        out.append(dict(title=_strip(e.findtext("a:title", namespaces=ns), 200), url=link.get("href") if link is not None else "",
                        published_on=_date(e.findtext("a:published", namespaces=ns) or e.findtext("a:updated", namespaces=ns)),
                        summary=_strip(e.findtext("a:summary", namespaces=ns) or e.findtext("a:content", namespaces=ns))))
    return [p for p in out if p["title"] and p["url"]]


def find_feed(website: str | None, feed_url: str | None = None) -> tuple[str, list[dict]] | None:
    tries = [feed_url] if feed_url else []
    if website:
        site = website if website.startswith("http") else f"https://{website}"
        try:
            html = _get(site).text
            for m in re.finditer(r'<link[^>]+type="application/(?:rss|atom)\+xml"[^>]*>', html):
                h = re.search(r'href="([^"]+)"', m.group(0))
                if h:
                    tries.append(urljoin(site, unescape(h.group(1))))
        except httpx.HTTPError:
            pass
        root = f"{urlparse(site).scheme}://{urlparse(site).netloc}"
        tries += [root + p for p in FEED_PATHS]
    for u in dict.fromkeys(tries):
        try:
            r = _get(u)
            if "<rss" not in r.text[:2000] and "<feed" not in r.text[:2000]:
                continue
            posts = parse_feed(r.text)
        except (httpx.HTTPError, ET.ParseError):
            continue
        if posts:
            return u, posts[:60]
    return None


# ---------------- Hacker News & Wikipedia ----------------

def hn_stories(name: str, months: int = 24, min_points: int = 15) -> list[dict]:
    since = int(time.time()) - months * 30 * 86400
    url = (f"https://hn.algolia.com/api/v1/search?query={quote(name)}&tags=story&hitsPerPage=50"
           f"&numericFilters=created_at_i>{since},points>{min_points}")
    word = re.compile(rf"\b{re.escape(name)}\b", re.I)
    out = []
    for h in _get(url).json().get("hits", []):
        if not word.search(h.get("title") or ""):
            continue
        out.append(dict(title=h["title"], url=h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                        published_on=(h.get("created_at") or "")[:10], summary=f"{h.get('points', 0)} points on Hacker News",
                        hn_url=f"https://news.ycombinator.com/item?id={h['objectID']}"))
    return out[:25]


def wikipedia(name: str) -> dict | None:
    for title in (name, f"{name} (company)"):
        try:
            d = _get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}").json()
        except httpx.HTTPError:
            continue
        if d.get("type") == "standard" and d.get("extract"):
            return dict(title=d.get("title"), summary=d["extract"][:600], url=d.get("content_urls", {}).get("desktop", {}).get("page"))
    return None
