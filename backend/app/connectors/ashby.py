"""Public connector: Ashby posting API for Cognition's job board (hiring-trend signals)."""
from __future__ import annotations

from datetime import date

import httpx

BOARD = "cognition"
API = "https://api.ashbyhq.com/posting-api/job-board/{board}"

APAC_MARKERS = {
    "Singapore": "Singapore", "Tokyo": "Japan", "Japan": "Japan", "Sydney": "Australia",
    "Melbourne": "Australia", "ANZ": "Australia", "India": "India", "Bangalore": "India",
    "Bengaluru": "India", "South Korea": "South Korea", "Seoul": "South Korea", "Korea": "South Korea",
}


def market_of(job: dict) -> str | None:
    hay = " ".join([job.get("title", ""), job.get("location", "")] + job.get("secondary_locations", []))
    for marker, market in APAC_MARKERS.items():
        if marker in hay:
            return market
    return None


def slim(job: dict) -> dict:
    return {
        "id": job.get("id"),
        "title": job.get("title"),
        "department": job.get("department"),
        "team": job.get("team"),
        "location": job.get("location") or "",
        "secondary_locations": [s.get("location", "") for s in job.get("secondaryLocations", []) or []],
        "published_on": (job.get("publishedAt") or "")[:10],
        "url": job.get("jobUrl"),
    }


def fetch_jobs(board: str = BOARD, timeout: float = 20.0) -> list[dict]:
    r = httpx.get(API.format(board=board), timeout=timeout)
    r.raise_for_status()
    jobs = [slim(j) for j in r.json().get("jobs", [])]
    for j in jobs:
        j["market"] = market_of(j)
        j["retrieved_on"] = date.today().isoformat()
    return jobs
