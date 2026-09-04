import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_data import validate_repository_data


class ValidateDataTests(unittest.TestCase):
    def test_current_repository_data_is_valid(self):
        self.assertEqual(validate_repository_data(), {"articles": 2, "blocks": 69, "images": 7})

    def test_rejects_insecure_image_url(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            article_dir = data_dir / "articles"
            article_dir.mkdir()
            detail = {
                "id": "1", "type": "article", "title": "Title", "description": "Description",
                "date": "2026-01-01T00:00:00Z", "thumbnail": None, "tags": [],
                "originalUrl": "https://example.com/article", "slug": "article-1",
                "contentBlocks": [{"type": "image", "url": "http://example.com/image.jpg"}],
            }
            (article_dir / "article-1.json").write_text(json.dumps(detail), encoding="utf-8")
            card = {key: detail.get(key) for key in ("id", "type", "title", "description", "date", "thumbnail", "tags", "originalUrl", "slug")}
            (data_dir / "index.json").write_text(json.dumps({"schemaVersion": 1, "items": [card]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "image URL must use HTTPS"):
                validate_repository_data(data_dir)


if __name__ == "__main__":
    unittest.main()
