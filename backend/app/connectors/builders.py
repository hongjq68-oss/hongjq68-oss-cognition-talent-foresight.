"""Public builder-evidence connectors. Unauthenticated public APIs only (GitHub uses GITHUB_TOKEN if set).

Every item is professional work evidence: what was built, where it is published and when. Contact details
(emails, phone numbers) are never read into the system."""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import quote, urlparse

import httpx

UA = {"User-Agent": "cognition-talent-foresight/0.1 (builder-evidence research)"}
TIMEOUT = 20.0


class SourceError(RuntimeError):
    pass


def _get(url: str, headers: dict | None = None, as_text: bool = False):
    r = httpx.get(url, headers=UA | (headers or {}), timeout=TIMEOUT, follow_redirects=True)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SourceError("rate limited: add a GITHUB_TOKEN" if "github" in url else "rate limited")
    if r.status_code >= 400:
        raise SourceError(f"HTTP {r.status_code}")
    return r.text if as_text else r.json()


def _person(source: str, handle: str, name: str | None = None, profile_url: str | None = None,
            location: str | None = None, company: str | None = None, bio: str | None = None) -> dict:
    return {"key": f"{source}:{handle.lower()}", "source": source, "handle": handle, "name": name or handle,
            "profile_url": profile_url, "location": location, "company": company, "bio": bio}


def _item(source, kind, title, url, date, text, person, **metrics):
    return {"source": source, "kind": kind, "title": title, "url": url, "date": (date or "")[:10] or None,
            "text": (text or "").strip(), "person": person, "metrics": metrics}


# ---- GitHub -------------------------------------------------------------------------------------------------
def _gh(path: str):
    tok = os.environ.get("GITHUB_TOKEN")
    return _get(f"https://api.github.com{path}", {"Accept": "application/vnd.github+json"} |
                ({"Authorization": f"Bearer {tok}"} if tok else {}))


def _gh_person(u: dict) -> dict:
    return _person("github", u["login"], u.get("name"), u.get("html_url"), u.get("location"),
                   (u.get("company") or "").lstrip("@") or None, u.get("bio"))


def _gh_repo_item(r: dict, person: dict) -> dict:
    text = " ".join([r.get("description") or "", " ".join(r.get("topics") or []), r.get("language") or ""])
    return _item("github", "repo", r["full_name"], r["html_url"], r.get("pushed_at"), text, person,
                 stars=r.get("stargazers_count", 0), homepage=r.get("homepage") or None)


def github_user(login: str, limit: int = 8) -> list[dict]:
    person = _gh_person(_gh(f"/users/{quote(login)}"))
    repos = _gh(f"/users/{quote(login)}/repos?sort=pushed&per_page=50&type=owner")
    repos = sorted((r for r in repos if not r.get("fork") and not r.get("archived")),
                   key=lambda r: -r.get("stargazers_count", 0))[:limit]
    return [_gh_repo_item(r, person) for r in repos]


def github_search(query: str, location: str | None = None, limit: int = 10) -> list[dict]:
    res = _gh(f"/search/repositories?q={quote(query)}&sort=stars&order=desc&per_page={limit}")
    out, people = [], {}
    for r in res.get("items", []):
        if r["owner"].get("type") != "User":
            continue
        login = r["owner"]["login"]
        if login not in people:
            people[login] = _gh_person(_gh(f"/users/{quote(login)}"))
        p = people[login]
        if location and location.lower() not in (p["location"] or "").lower():
            continue
        out.append(_gh_repo_item(r, p))
    return out


# ---- Hacker News (Show HN launches and demos) ---------------------------------------------------------------
def _hn_items(hits: list[dict]) -> list[dict]:
    out = []
    for h in hits:
        a = h.get("author")
        if not a:
            continue
        p = _person("hn", a, None, f"https://news.ycombinator.com/user?id={a}")
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
        out.append(_item("hn", "launch", h.get("title") or "", url, h.get("created_at"),
                         re.sub(r"<[^>]+>", " ", unescape(h.get("story_text") or "")), p,
                         points=h.get("points") or 0, discussion=f"https://news.ycombinator.com/item?id={h['objectID']}"))
    return out


def hn_user(username: str, limit: int = 10) -> list[dict]:
    return _hn_items(_get(f"https://hn.algolia.com/api/v1/search_by_date?tags=show_hn,author_{quote(username)}"
                          f"&hitsPerPage={limit}")["hits"])


def hn_search(query: str, limit: int = 15) -> list[dict]:
    return _hn_items(_get(f"https://hn.algolia.com/api/v1/search?query={quote(query)}&tags=show_hn"
                          f"&numericFilters=points>5&hitsPerPage={limit}")["hits"])


# ---- dev.to (technical writing) -----------------------------------------------------------------------------
def _devto_items(arts: list[dict]) -> list[dict]:
    out = []
    for a in arts:
        u = a.get("user") or {}
        p = _person("devto", u.get("username") or "unknown", u.get("name"), f"https://dev.to/{u.get('username')}")
        out.append(_item("devto", "article", a["title"], a["url"], a.get("published_at"),
                         (a.get("description") or "") + " " + " ".join(a.get("tag_list") or []), p,
                         reactions=a.get("public_reactions_count", 0)))
    return out


def devto_user(username: str, limit: int = 10) -> list[dict]:
    return _devto_items(_get(f"https://dev.to/api/articles?username={quote(username)}&per_page={limit}"))


def devto_tag(tag: str, limit: int = 15) -> list[dict]:
    return _devto_items(_get(f"https://dev.to/api/articles?tag={quote(tag)}&top=365&per_page={limit}"))


# ---- arXiv (papers) -----------------------------------------------------------------------------------------
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def _arxiv(q: str, limit: int, author: str | None = None) -> list[dict]:
    feed = ET.fromstring(_get(f"https://export.arxiv.org/api/query?search_query={quote(q)}&max_results={limit}"
                              f"&sortBy=submittedDate&sortOrder=descending", as_text=True))
    out = []
    for e in feed.findall("a:entry", ATOM):
        names = [n.text or "" for n in e.findall("a:author/a:name", ATOM)]
        who = next((n for n in names if author and author.lower() in n.lower()), names[0] if names else "unknown")
        p = _person("arxiv", who, who, f"https://arxiv.org/a/{quote(who)}")
        out.append(_item("arxiv", "paper", " ".join((e.findtext("a:title", "", ATOM)).split()),
                         e.findtext("a:id", "", ATOM), e.findtext("a:published", "", ATOM),
                         " ".join(e.findtext("a:summary", "", ATOM).split())[:600], p, coauthors=len(names) - 1))
    return out


def arxiv_author(name: str, limit: int = 10) -> list[dict]:
    return _arxiv(f'au:"{name}"', limit, author=name)


def arxiv_search(query: str, limit: int = 10) -> list[dict]:
    return _arxiv(f'all:"{query}"', limit)


# ---- Hugging Face (models and demo Spaces) ------------------------------------------------------------------
def huggingface_user(author: str, limit: int = 8) -> list[dict]:
    p = _person("huggingface", author, author, f"https://huggingface.co/{author}")
    out = []
    for kind, path in (("model", "models"), ("demo", "spaces")):
        for m in _get(f"https://huggingface.co/api/{path}?author={quote(author)}&sort=likes&limit={limit}"):
            base = "https://huggingface.co/" + ("spaces/" if kind == "demo" else "")
            out.append(_item("huggingface", kind, m["id"], base + m["id"], m.get("lastModified") or m.get("createdAt"),
                             " ".join(t for t in (m.get("tags") or []) if ":" not in t), p, likes=m.get("likes", 0)))
    return out


# ---- npm (packages maintained) ------------------------------------------------------------------------------
def npm_maintainer(username: str, limit: int = 10) -> list[dict]:
    p = _person("npm", username, username, f"https://www.npmjs.com/~{username}")
    res = _get(f"https://registry.npmjs.org/-/v1/search?text=maintainer:{quote(username)}&size={limit}")
    return [_item("npm", "package", o["package"]["name"], o["package"]["links"].get("npm"), o["package"].get("date"),
                  (o["package"].get("description") or "") + " " + " ".join(o["package"].get("keywords") or []), p)
            for o in res.get("objects", [])]


# ---- RSS / Atom blog feeds ----------------------------------------------------------------------------------
def rss(url: str, owner: str, limit: int = 10) -> list[dict]:
    root = ET.fromstring(_get(url, as_text=True))
    p = _person("blog", owner, owner, f"{urlparse(url).scheme}://{urlparse(url).netloc}")
    out = []
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        get = lambda n: next((c for c in it if c.tag.split("}")[-1] == n), None)  # noqa: E731
        link = get("link")
        href = (link.get("href") if link is not None and link.get("href") else (link.text if link is not None else None))
        text = get("description") if get("description") is not None else get("summary")
        date = get("pubDate") if get("pubDate") is not None else get("published")
        out.append(_item("blog", "article", (get("title").text or "").strip() if get("title") is not None else href, href,
                         _iso(date.text) if date is not None else None,
                         re.sub(r"<[^>]+>", " ", unescape(text.text or ""))[:600] if text is not None else "", p))
        if len(out) >= limit:
            break
    return out


def _iso(s: str | None) -> str | None:
    from email.utils import parsedate_to_datetime
    if not s:
        return None
    try:
        return parsedate_to_datetime(s).date().isoformat()
    except (TypeError, ValueError):
        return s[:10]


# ---- Single public pages: patents, product launches, demos --------------------------------------------------
PATENT_HOSTS = ("patents.google.com", "patents.justia.com", "ppubs.uspto.gov", "worldwide.espacenet.com", "patentscope.wipo.int")


def _meta(html: str, *names: str) -> str | None:
    for n in names:
        m = re.search(rf'<meta[^>]+(?:name|property)=["\']{re.escape(n)}["\'][^>]+content=["\']([^"\']+)', html, re.I)
        if m:
            return unescape(m.group(1)).strip()
    return None


def page(url: str, owner: str) -> list[dict]:
    if urlparse(url).scheme not in ("http", "https"):
        raise SourceError("only http(s) links")
    html = _get(url, as_text=True)
    host = urlparse(url).netloc.lower()
    is_patent = any(h in host for h in PATENT_HOSTS)
    title = _meta(html, "DC.title", "og:title", "twitter:title") or \
        (re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S) or [None, url])[1]
    desc = _meta(html, "DC.description", "description", "og:description") or ""
    date = _meta(html, "DC.date", "citation_publication_date", "article:published_time")
    kind = "patent" if is_patent else ("demo" if any(k in host for k in ("youtube.", "youtu.be", "vimeo.", "loom.")) else "launch")
    p = _person("web", owner, owner)
    return [_item("web", kind, " ".join(unescape(title).split())[:200], url, date, desc[:600], p)]
