import unittest

from scripts.sync_brunch import clean_preview, first_image, parse_rss


RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
  <title>테스트 글</title>
  <link>https://brunch.co.kr/@@8FXu/4</link>
  <description>본문 &lt;img src="http://example.com/a.png" /&gt;</description>
  <pubDate>Thu, 21 Dec 2023 17:03:44 GMT</pubDate>
  <guid>article-4</guid>
</item></channel></rss>"""


class SyncTests(unittest.TestCase):
    def test_parse_rss(self):
        item = parse_rss(RSS)[0]
        self.assertEqual(item.title, "테스트 글")
        self.assertEqual(item.slug, "hyj402-4")
        self.assertEqual(item.published_at, "2023-12-21T17:03:44Z")

    def test_preview_and_image(self):
        item = parse_rss(RSS)[0]
        self.assertEqual(clean_preview(item.description_html), "본문")
        self.assertEqual(first_image(item.description_html), "https://example.com/a.png")


if __name__ == "__main__":
    unittest.main()

