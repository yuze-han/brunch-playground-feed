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
from html.parser import HTMLParser
from pathlib import Path
from time import sleep
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


def fetch_text(url: str, attempts: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/rss+xml"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception as error:
            last_error = error
            if attempt + 1 < attempts:
                sleep(2**attempt)
    assert last_error is not None
    raise last_error


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


def keyword_list(value: Any) -> list[str]:
    if isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = re.split(r"[,|]", value)
    else:
        values = []
    return [str(item).strip() for item in values if str(item).strip()]


class BrunchBodyParser(HTMLParser):
    """Extract Brunch's rendered article items without executing page scripts."""

    TEXT_STYLES = {"h2": "heading2", "h3": "heading3", "blockquote": "quote"}
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, Any]] = []
        self._depth = 0
        self._tag = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if self._depth:
            if tag == "br" and self._tag != "div":
                self._text.append("\n")
            if tag not in self.VOID_TAGS:
                self._depth += 1
            return
        if "wrap_item" not in classes:
            return
        if "item_type_text" in classes:
            self._depth = 1
            self._tag = tag
            self._text = []
        elif "item_type_img" in classes:
            self._append_images(values.get("data-app"))
            self._depth = 1
            self._tag = "div"

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._depth and tag == "br" and self._tag != "div":
            self._text.append("\n")

    def handle_data(self, data: str) -> None:
        if self._depth and self._tag != "div":
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._depth:
            return
        self._depth -= 1
        if self._depth:
            return
        if self._tag != "div":
            text = re.sub(r"[ \t\r\f\v]+", " ", "".join(self._text))
            text = re.sub(r" *\n *", "\n", text).strip()
            if text:
                self.blocks.append({
                    "type": "text",
                    "style": self.TEXT_STYLES.get(self._tag, "paragraph"),
                    "text": text,
                })
        self._tag = ""
        self._text = []

    def _append_images(self, raw: str | None) -> None:
        if not raw:
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        caption = clean_preview(str(data.get("caption") or ""), limit=500)
        for image in data.get("images") or []:
            if not isinstance(image, dict) or not image.get("url"):
                continue
            block: dict[str, Any] = {"type": "image", "url": normalize_url(image["url"])}
            for field in ("width", "height"):
                if image.get(field):
                    try:
                        block[field] = int(image[field])
                    except (TypeError, ValueError):
                        pass
            if caption:
                block["caption"] = caption
                block["alt"] = caption
            self.blocks.append(block)


def content_blocks_from_html(source: str) -> list[dict[str, Any]]:
    parser = BrunchBodyParser()
    parser.feed(source)
    return parser.blocks


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
    if not items and existing.get("items"):
        raise ValueError("RSS returned no articles; keeping the existing feed")
    previous = {item["source"]["guid"]: item for item in existing.get("items", [])}
    cards: list[dict[str, Any]] = []
    any_article_changed = False

    for item in items:
        old = previous.get(item.guid)
        detail_path = ARTICLE_DIR / f"{item.slug}.json"
        changed = old is None or old.get("source", {}).get("fingerprint") != item.fingerprint

        needs_upgrade = False
        if detail_path.exists():
            saved_detail = json.loads(detail_path.read_text(encoding="utf-8"))
            needs_upgrade = "contentBlocks" not in saved_detail or "tags" not in saved_detail

        if changed or not detail_path.exists() or needs_upgrade:
            any_article_changed = True
            article_html = fetch_text(item.original_url)
            article = json_ld_from_html(article_html)
            images = image_records(article.get("image"))
            content_blocks = content_blocks_from_html(article_html)
            tags = keyword_list(article.get("keywords"))
            description = clean_preview(article.get("description") or item.description_html)
            detail = {
                "id": item.guid,
                "type": "article",
                "title": article.get("headline") or item.title,
                "description": description,
                "date": item.published_at,
                "thumbnail": images[0]["url"] if images else first_image(item.description_html),
                "tags": tags,
                "content": article.get("articleBody") or "",
                "contentFormat": "text",
                "contentBlocks": content_blocks,
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
            "id", "type", "title", "description", "date", "thumbnail", "tags", "originalUrl", "slug", "source"
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
