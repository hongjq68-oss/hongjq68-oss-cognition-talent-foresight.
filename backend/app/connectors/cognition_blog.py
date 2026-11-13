"""Public connector: cognition.ai/blog index (titles, dates, summaries, links)."""
from __future__ import annotations

import html
import re
from datetime import date

import httpx

BLOG_URL = "https://cognition.ai/blog"
_ANCHOR = re.compile(r'<a[^>]+href="(/blog/[^"#?]+)"[^>]*>(.*?)</a>', re.S)
_DATE = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})")


def parse_index(page: str) -> list[dict]:
    posts: dict[str, dict] = {}
    for href, inner in _ANCHOR.findall(page):
        parts = [p.strip() for p in html.unescape(re.sub(r"<[^>]+>", "\n", inner)).split("\n")]
        parts = [re.sub(r"\s+", " ", p) for p in parts if p.strip()]
        when = next((p for p in parts if _DATE.fullmatch(p)), None)
        if not parts or not when:
            continue
        title = parts[0]
        rest = [p for p in parts[1:] if p != when]
        y, m, d = _DATE.fullmatch(when).groups()
        url = "https://cognition.ai" + href
        posts.setdefault(url, {
            "url": url,
            "title": title,
            "published_on": f"{y}-{m}-{d}",
            "summary": " ".join(rest)[:600],
        })
    return sorted(posts.values(), key=lambda p: p["published_on"], reverse=True)


def fetch_index(timeout: float = 20.0) -> list[dict]:
    r = httpx.get(BLOG_URL, timeout=timeout, follow_redirects=True,
                  headers={"User-Agent": "Mozilla/5.0 (CognitionTalentForesight)"})
    r.raise_for_status()
    posts = parse_index(r.text)
    for p in posts:
        p["retrieved_on"] = date.today().isoformat()
    return posts
