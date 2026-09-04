import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.sync_brunch as sync_module
from scripts.sync_brunch import FeedItem


def rss(items):
    body = "".join(
        f"""<item><title>{title}</title><link>{url}</link><description>{description}</description>
        <pubDate>{date}</pubDate><guid>{guid}</guid></item>"""
        for title, url, description, date, guid in items
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>{body}</channel></rss>'


def article_html(title, url, keyword="UX"):
    structured = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting", "headline": title,
        "description": f"{title} 설명", "articleBody": f"{title} 본문", "keywords": keyword,
        "url": url, "image": ["https://example.com/thumbnail.jpg"],
    }, ensure_ascii=False)
    return f'<script type="application/ld+json">{structured}</script><div class="wrap_body"><p class="wrap_item item_type_text">{title} 본문</p></div>'


class FutureSyncTests(unittest.TestCase):
    old_record = (
        "기존 글", "https://brunch.co.kr/@hyj402/10", "기존 설명",
        "Mon, 01 Sep 2026 00:00:00 GMT", "article-10",
    )
    new_record = (
        "새 글", "https://brunch.co.kr/@hyj402/11", "새 설명",
        "Tue, 02 Sep 2026 00:00:00 GMT", "article-11",
    )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temporary.name) / "data"
        self.article_dir = self.data_dir / "articles"
        self.article_dir.mkdir(parents=True)

    def tearDown(self):
        self.temporary.cleanup()

    def write_existing_article(self):
        title, url, description, date, guid = self.old_record
        item = FeedItem(title, url, description, sync_module.iso_date(date), guid)
        detail = {
            "id": guid, "type": "article", "title": title, "description": description,
            "date": item.published_at, "thumbnail": "https://example.com/old.jpg", "tags": ["UX"],
            "content": "기존 본문", "contentFormat": "text",
            "contentBlocks": [{"type": "text", "style": "paragraph", "text": "기존 본문"}],
            "images": [], "originalUrl": url, "slug": item.slug,
            "source": {"provider": "brunch", "guid": guid, "fingerprint": item.fingerprint, "extractionVersion": sync_module.EXTRACTION_VERSION},
        }
        (self.article_dir / f"{item.slug}.json").write_text(json.dumps(detail), encoding="utf-8")
        card_fields = ("id", "type", "title", "description", "date", "thumbnail", "tags", "originalUrl", "slug", "source")
        index = {"schemaVersion": 1, "source": sync_module.RSS_URL, "generatedAt": "unchanged", "items": [{key: detail[key] for key in card_fields}]}
        (self.data_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
        return item

    def run_with(self, responses):
        with patch.object(sync_module, "DATA_DIR", self.data_dir), patch.object(sync_module, "ARTICLE_DIR", self.article_dir), patch.object(sync_module, "fetch_text", side_effect=lambda url: responses[url]) as fetch:
            sync_module.sync()
            return [call.args[0] for call in fetch.call_args_list]

    def test_new_article_is_added_without_refetching_unchanged_article(self):
        old_item = self.write_existing_article()
        feed = rss([self.new_record, self.old_record])
        calls = self.run_with({
            sync_module.RSS_URL: feed,
            self.new_record[1]: article_html(self.new_record[0], self.new_record[1]),
        })
        index = json.loads((self.data_dir / "index.json").read_text())
        self.assertEqual([item["slug"] for item in index["items"]], ["hyj402-11", "hyj402-10"])
        self.assertEqual(calls, [sync_module.RSS_URL, self.new_record[1]])
        self.assertTrue((self.article_dir / "hyj402-11.json").exists())
        self.assertEqual(index["items"][1]["source"]["fingerprint"], old_item.fingerprint)

    def test_changed_article_is_refetched(self):
        self.write_existing_article()
        changed = ("수정된 기존 글", *self.old_record[1:])
        calls = self.run_with({
            sync_module.RSS_URL: rss([changed]),
            changed[1]: article_html(changed[0], changed[1], "UX,업데이트"),
        })
        detail = json.loads((self.article_dir / "hyj402-10.json").read_text())
        self.assertEqual(calls, [sync_module.RSS_URL, changed[1]])
        self.assertEqual(detail["title"], "수정된 기존 글")
        self.assertEqual(detail["tags"], ["UX", "업데이트"])

    def test_empty_rss_keeps_existing_data(self):
        self.write_existing_article()
        before = (self.data_dir / "index.json").read_text()
        with patch.object(sync_module, "DATA_DIR", self.data_dir), patch.object(sync_module, "ARTICLE_DIR", self.article_dir), patch.object(sync_module, "fetch_text", return_value=rss([])):
            with self.assertRaisesRegex(ValueError, "keeping the existing feed"):
                sync_module.sync()
        self.assertEqual((self.data_dir / "index.json").read_text(), before)

    def test_article_outside_rss_window_is_kept(self):
        self.write_existing_article()
        calls = self.run_with({
            sync_module.RSS_URL: rss([self.new_record]),
            self.new_record[1]: article_html(self.new_record[0], self.new_record[1]),
        })
        index = json.loads((self.data_dir / "index.json").read_text())
        self.assertEqual([item["slug"] for item in index["items"]], ["hyj402-11", "hyj402-10"])
        self.assertEqual(calls, [sync_module.RSS_URL, self.new_record[1]])


if __name__ == "__main__":
    unittest.main()
