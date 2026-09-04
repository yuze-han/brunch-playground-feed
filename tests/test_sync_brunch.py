import unittest

from scripts.sync_brunch import clean_preview, content_blocks_from_html, first_image, parse_rss


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

    def test_preserves_article_block_order(self):
        source = """
        <p class="wrap_item item_type_text"><span>첫 문단</span><br><span>다음 줄</span></p>
        <h2 class="wrap_item item_type_text"><b>소제목</b></h2>
        <div class="wrap_item item_type_img" data-app="{&quot;caption&quot;:&quot;설명&quot;,&quot;images&quot;:[{&quot;url&quot;:&quot;http://example.com/a.png&quot;,&quot;width&quot;:&quot;1200&quot;,&quot;height&quot;:&quot;800&quot;}]}"><img src="ignored.jpg"></div>
        <blockquote class="wrap_item item_type_text">인용문</blockquote>
        """
        self.assertEqual(content_blocks_from_html(source), [
            {"type": "text", "style": "paragraph", "text": "첫 문단\n다음 줄"},
            {"type": "text", "style": "heading2", "text": "소제목"},
            {"type": "image", "url": "https://example.com/a.png", "width": 1200, "height": 800, "caption": "설명", "alt": "설명"},
            {"type": "text", "style": "quote", "text": "인용문"},
        ])


if __name__ == "__main__":
    unittest.main()
