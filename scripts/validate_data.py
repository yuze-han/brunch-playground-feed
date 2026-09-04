#!/usr/bin/env python3
"""Validate the generated feed before it is consumed by Figma Sites."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def is_https_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme == "https"


def validate_detail(detail: dict[str, Any], expected_slug: str) -> None:
    prefix = f"article {expected_slug}"
    require(detail.get("slug") == expected_slug, f"{prefix}: slug mismatch")
    require(detail.get("type") == "article", f"{prefix}: invalid type")
    for field in ("id", "title", "description", "date", "originalUrl"):
        require(bool(detail.get(field)), f"{prefix}: missing {field}")
    require(is_https_url(detail["originalUrl"]), f"{prefix}: originalUrl must use HTTPS")
    require(detail.get("source", {}).get("provider") == "brunch", f"{prefix}: invalid source provider")
    require(isinstance(detail.get("source", {}).get("fingerprint"), str), f"{prefix}: missing fingerprint")
    require(isinstance(detail.get("source", {}).get("extractionVersion"), int), f"{prefix}: missing extractionVersion")
    if detail.get("thumbnail"):
        require(is_https_url(detail["thumbnail"]), f"{prefix}: thumbnail must use HTTPS")

    tags = detail.get("tags")
    require(isinstance(tags, list), f"{prefix}: tags must be a list")
    require(all(isinstance(tag, str) and tag.strip() for tag in tags), f"{prefix}: invalid tag")

    blocks = detail.get("contentBlocks")
    require(isinstance(blocks, list) and blocks, f"{prefix}: contentBlocks must not be empty")
    for index, block in enumerate(blocks):
        block_prefix = f"{prefix} block {index}"
        require(isinstance(block, dict), f"{block_prefix}: must be an object")
        if block.get("type") == "text":
            require(block.get("style") in {"paragraph", "heading2", "heading3", "quote"}, f"{block_prefix}: invalid text style")
            require(bool(block.get("text")), f"{block_prefix}: empty text")
        elif block.get("type") == "image":
            require(is_https_url(block.get("url")), f"{block_prefix}: image URL must use HTTPS")
            if block.get("caption") is not None:
                require(bool(str(block["caption"]).strip()), f"{block_prefix}: empty caption")
        else:
            raise ValueError(f"{block_prefix}: invalid block type")


def validate_repository_data(data_dir: Path = DATA_DIR) -> dict[str, int]:
    index_path = data_dir / "index.json"
    require(index_path.exists(), "index.json is missing")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    require(index.get("schemaVersion") == 1, "unsupported schemaVersion")
    items = index.get("items")
    require(isinstance(items, list), "index items must be a list")

    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    image_count = 0
    block_count = 0
    for card in items:
        require(isinstance(card, dict), "index card must be an object")
        article_id = card.get("id")
        slug = card.get("slug")
        require(isinstance(article_id, str) and article_id not in seen_ids, "duplicate or missing article id")
        require(isinstance(slug, str) and slug not in seen_slugs, "duplicate or missing article slug")
        seen_ids.add(article_id)
        seen_slugs.add(slug)
        detail_path = data_dir / "articles" / f"{slug}.json"
        require(detail_path.exists(), f"detail file is missing for {slug}")
        detail = json.loads(detail_path.read_text(encoding="utf-8"))
        validate_detail(detail, slug)
        for field in ("id", "type", "title", "description", "date", "thumbnail", "tags", "originalUrl", "slug"):
            require(card.get(field) == detail.get(field), f"{slug}: index/detail mismatch for {field}")
        blocks = detail["contentBlocks"]
        block_count += len(blocks)
        image_count += sum(block.get("type") == "image" for block in blocks)

    return {"articles": len(items), "blocks": block_count, "images": image_count}


if __name__ == "__main__":
    try:
        result = validate_repository_data()
        print(f"Validated {result['articles']} article(s), {result['blocks']} block(s), {result['images']} image(s)")
    except Exception as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
