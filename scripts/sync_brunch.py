#!/usr/bin/env python3
"""Create a static Playground feed from a public Brunch RSS feed."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARTICLE_DIR = DATA_DIR / "articles"
RSS_URL = "https://brunch.co.kr/rss/@@8FXu"
USER_AGENT = "yuzehan-playground-feed/1.0 (+https://yuzehan.com)"


@dataclass(frozen=True)
class FeedItem:
    title: str
    original_url: str
    description_html: str
    published_at: str
    guid: str

    @property
    def slug(self) -> str:
        article_no = self.original_url.rstrip("/").rsplit("/", 1)[-1]
        return f"hyj402-{article_no}"

    @property
    def fingerprint(self) -> str:
        raw = "\n".join(
            (self.title, self.original_url, self.description_html, self.published_at, self.guid)
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/rss+xml"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def iso_date(value: str) -> str:
    return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_rss(source: str) -> list[FeedItem]:
    root = ET.fromstring(source)
    items: list[FeedItem] = []
    for node in root.findall("./channel/item"):
        read = lambda name: (node.findtext(name) or "").strip()
        url = read("link")
        if not url:
            continue
        items.append(
            FeedItem(
                title=read("title"),
                original_url=url,
                description_html=read("description"),
                published_at=iso_date(read("pubDate")),
                guid=read("guid") or url,
            )
        )
    return items


def clean_preview(value: str, limit: int = 180) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", html.unescape(value))
    compact = re.sub(r"\s+", " ", without_tags).strip()
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


def first_image(value: str) -> str | None:
    match = re.search(r"<img\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)", html.unescape(value), re.I)
    return normalize_url(match.group(1)) if match else None


def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("http://"):
        return "https://" + value.removeprefix("http://")
    return value


def json_ld_from_html(source: str) -> dict[str, Any]:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        source,
        flags=re.I | re.S,
    )
    for block in blocks:
        try:
            value = json.loads(html.unescape(block))
        except json.JSONDecodeError:
            continue
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            if isinstance(candidate, dict) and candidate.get("@type") == "BlogPosting":
                return candidate
    raise ValueError("BlogPosting JSON-LD was not found")


def image_records(value: Any) -> list[dict[str, Any]]:
    values = value if isinstance(value, list) else ([value] if value else [])
    result: list[dict[str, Any]] = []
    for item in values:
        if isinstance(item, str):
            result.append({"url": normalize_url(item)})
        elif isinstance(item, dict) and item.get("url"):
            record = {"url": normalize_url(item["url"])}
            for field in ("width", "height"):
                if item.get(field) is not None:
                    record[field] = item[field]
            result.append(record)
    return result


def load_existing_index() -> dict[str, Any]:
    path = DATA_DIR / "index.json"
    if not path.exists():
        return {"items": []}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def sync() -> int:
    items = parse_rss(fetch_text(RSS_URL))
    existing = load_existing_index()
    previous = {item["source"]["guid"]: item for item in existing.get("items", [])}
    cards: list[dict[str, Any]] = []
    any_article_changed = False

    for item in items:
        old = previous.get(item.guid)
        detail_path = ARTICLE_DIR / f"{item.slug}.json"
        changed = old is None or old.get("source", {}).get("fingerprint") != item.fingerprint

        if changed or not detail_path.exists():
            any_article_changed = True
            article = json_ld_from_html(fetch_text(item.original_url))
            images = image_records(article.get("image"))
            description = clean_preview(article.get("description") or item.description_html)
            detail = {
                "id": item.guid,
                "type": "article",
                "title": article.get("headline") or item.title,
                "description": description,
                "date": item.published_at,
                "thumbnail": images[0]["url"] if images else first_image(item.description_html),
                "content": article.get("articleBody") or "",
                "contentFormat": "text",
                "images": images,
                "originalUrl": normalize_url(article.get("url")) or item.original_url,
                "slug": item.slug,
                "source": {
                    "provider": "brunch",
                    "guid": item.guid,
                    "fingerprint": item.fingerprint,
                    "dateModified": article.get("dateModified"),
                },
            }
            write_json(detail_path, detail)
        else:
            detail = json.loads(detail_path.read_text(encoding="utf-8"))

        cards.append({key: detail.get(key) for key in (
            "id", "type", "title", "description", "date", "thumbnail", "originalUrl", "slug", "source"
        )})

    comparable_previous = existing.get("items", [])
    index_changed = cards != comparable_previous
    generated_at = existing.get("generatedAt")
    if any_article_changed or index_changed or not generated_at:
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    index = {
        "schemaVersion": 1,
        "source": RSS_URL,
        "generatedAt": generated_at,
        "items": cards,
    }
    write_json(DATA_DIR / "index.json", index)
    print(f"Synced {len(cards)} article(s)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(sync())
    except Exception as error:
        print(f"Sync failed: {error}", file=sys.stderr)
        raise
