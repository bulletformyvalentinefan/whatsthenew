"""Fetchers de empleo: Chile, global remoto y Australia."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import feedparser

from ..classify import classify
from ..models import Item
from .base import HttpClient

STACK: list[str] = []  # se rellena desde el pipeline con config roles.json["stack"]


def _classify(title: str, text: str = "", location: str = "") -> dict:
    return classify(title, text, STACK, location)


# --------------------------------------------------------------------------
# GetOnBrd (Chile / LATAM) — feed XML con <job>
# --------------------------------------------------------------------------
def fetch_getonbrd(client: HttpClient, url: str) -> list[Item]:
    text = client.get_text(url)
    root = ET.fromstring(text)
    items: list[Item] = []
    for job in root.iter("job"):
        def _t(tag: str) -> str:
            el = job.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""

        title = _t("title")
        desc = _t("description")
        location = _t("location")
        tags = _classify(title, f"{desc} {_t('category')}", location)
        items.append(
            Item(
                category="jobs",
                source="getonbrd.com",
                source_type="xml",
                url=_t("url"),
                title=title,
                company=_t("company"),
                location=location,
                posted_at=_t("date"),
                salary="",
                excerpt=desc[:2000],
                role=_t("category"),
                **tags,
            )
        )
    return items


# --------------------------------------------------------------------------
# Seek (Australia) — API interna JSON
# --------------------------------------------------------------------------
def fetch_seek_jobs(client: HttpClient, url_template: str, queries: list[str], pages: int = 1) -> list[Item]:
    items: list[Item] = []
    for query in queries:
        for page in range(1, pages + 1):
            url = url_template.format(query=query.replace(" ", "%20"), page=page)
            data = client.get_json(url)
            for job in data.get("data", []):
                title = job.get("title", "")
                company = job.get("companyName", "")
                loc = (job.get("location") or "") if isinstance(job.get("location"), str) else ""
                tags = _classify(title, f"{title} {job.get('workType', '')}", loc)
                items.append(
                    Item(
                        category="jobs",
                        source="seek.com.au",
                        source_type="api",
                        url=f"https://www.seek.com.au/job/{job.get('id', '')}",
                        title=title,
                        company=company,
                        location=loc,
                        posted_at=str(job.get("listingDate", "")),
                        query=query,
                        **tags,
                    )
                )
    return items


# --------------------------------------------------------------------------
# Jobicy — API JSON
# --------------------------------------------------------------------------
def fetch_jobicy(client: HttpClient, url_template: str, tags: list[str]) -> list[Item]:
    items: list[Item] = []
    for tag in tags:
        data = client.get_json(url_template.format(tag=tag))
        for job in data.get("jobs", []):
            title = job.get("jobTitle", "")
            geo = job.get("jobGeo", "")
            cls = _classify(title, title, geo)
            items.append(
                Item(
                    category="jobs",
                    source="jobicy.com",
                    source_type="api",
                    url=job.get("url", ""),
                    title=title,
                    company=job.get("companyName", ""),
                    location=geo,
                    posted_at=str(job.get("pubDate", "")),
                    query=tag,
                    level=job.get("jobLevel", "").lower() or cls["level"],
                    years=cls["years"],
                    skills=cls["skills"],
                    remote=cls["remote"],
                )
            )
    return items


# --------------------------------------------------------------------------
# Otros tableros JSON (remotive, remoteok, workingnomads, himalayas, landing.jobs)
# --------------------------------------------------------------------------
def fetch_json_board(client: HttpClient, source_id: str, url: str) -> list[Item]:
    data = client.get_json(url)
    items: list[Item] = []

    def add(title: str, company: str, location: str, link: str, date: str, salary: str, text: str = "") -> None:
        tags = _classify(title, text or title, location)
        items.append(
            Item(
                category="jobs",
                source=f"{source_id}.json",
                source_type="api",
                url=link,
                title=title,
                company=company,
                location=location,
                posted_at=str(date or ""),
                salary=str(salary or ""),
                excerpt=(text or "")[:2000],
                **tags,
            )
        )

    if source_id == "remotive":
        for j in data.get("jobs", []):
            add(j.get("title", ""), j.get("company_name", ""), j.get("candidate_required_location", ""),
                j.get("url", ""), j.get("publication_date", ""), j.get("salary", ""), j.get("description", ""))
    elif source_id == "remoteok":
        for j in data:
            if not isinstance(j, dict) or "position" not in j:
                continue  # el primer elemento es aviso legal
            add(j.get("position", ""), j.get("company", ""), j.get("location", ""),
                j.get("url") or j.get("apply_url", ""), j.get("date", ""), j.get("salary", ""),
                " ".join(j.get("tags", []) or []))
    elif source_id == "workingnomads":
        for j in data:
            add(j.get("title", ""), "", j.get("location", ""), j.get("url", ""), j.get("pub_date", ""), "")
    elif source_id == "himalayas":
        for j in (data.get("jobs", data) if isinstance(data, dict) else data):
            loc = j.get("locationRestrictions") or j.get("location") or ""
            if isinstance(loc, list):
                loc = ", ".join(loc)
            add(j.get("title", ""), j.get("companyName", ""), str(loc), j.get("applicationLink", ""),
                j.get("pubDate", ""), j.get("salaryRange", "") or j.get("salary", ""))
    elif source_id == "landingjobs":
        rows = data.get("jobs", data) if isinstance(data, dict) else data
        for j in rows:
            add(j.get("title", ""), (j.get("company") or {}).get("name", "") if isinstance(j.get("company"), dict) else "",
                j.get("location", "") or "", j.get("url", ""), j.get("published_at", ""), "")
    return items


# --------------------------------------------------------------------------
# WeWorkRemotely y otros RSS de empleo
# --------------------------------------------------------------------------
def fetch_rss_jobs(client: HttpClient, url: str, source: str) -> list[Item]:
    parsed = feedparser.parse(client.get_text(url))
    items: list[Item] = []
    for e in parsed.entries:
        title = e.get("title", "")
        text = e.get("summary", "")
        tags = _classify(title, text)
        items.append(
            Item(
                category="jobs",
                source=source,
                source_type="rss",
                url=e.get("link", ""),
                title=title,
                company=e.get("author", ""),
                location=e.get("region", ""),
                posted_at=e.get("published", ""),
                excerpt=text[:2000],
                **tags,
            )
        )
    return items


# --------------------------------------------------------------------------
# Hacker News "Who is hiring" (Algolia)
# --------------------------------------------------------------------------
def fetch_hackernews_whoishiring(client: HttpClient, url_template: str, query: str) -> list[Item]:
    data = client.get_json(url_template.format(query=query.replace(" ", "%20")))
    items: list[Item] = []
    for hit in data.get("hits", []):
        text: str = hit.get("comment_text", "") or ""
        title = text.strip().splitlines()[0][:120] if text.strip() else "(comentario)"
        tags = _classify(title, text)
        items.append(
            Item(
                category="jobs",
                source="news.ycombinator.com",
                source_type="api",
                url=f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                title=title,
                posted_at=str(hit.get("created_at", "")),
                query=query,
                excerpt=text[:2000],
                **tags,
            )
        )
    return items
