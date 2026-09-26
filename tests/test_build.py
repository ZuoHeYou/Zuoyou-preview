"""验证层级关联与公开构建边界，不运行 Flutter 或 Appium。"""

import copy
import json
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
import render


class References(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.links, self.images, self.ids = [], [], set()
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs["src"])


class PreviewBuildTests(unittest.TestCase):
    def setUp(self):
        self.progress, self.requirements, self.media = build.load_data()
        self.pages = render.render_pages(self.progress, self.requirements, self.media)

    def test_progressive_disclosure(self):
        for path, content in self.pages.items():
            if not path.startswith("ac-"):
                self.assertEqual(References(content).images, [], path)
        self.assertIn("暂无对应预览图", self.pages["ac-05-02-01.html"])
        self.assertEqual(len(References(self.pages["ac-03-02-01.html"]).images), 1)
        self.assertIn("不单独证明请求", self.pages["ac-03-04-01.html"])

    def test_navigation_and_evidence_references(self):
        assets = {"media/" + i["asset"] for i in self.media["images"]}
        parsed = {path: References(content) for path, content in self.pages.items()}
        for path, content in self.pages.items():
            refs = parsed[path]
            for target in refs.links + refs.images:
                file, _, fragment = target.partition("#")
                if file in {"site.css", "reader.css", "site.js"} | assets:
                    continue
                target_page = file or path
                self.assertIn(target_page, self.pages, (path, target))
                if fragment:
                    self.assertIn(fragment, parsed[target_page].ids)
            self.assertNotIn("{{", content)
            self.assertNotIn(".brain/", content)
            self.assertNotIn("/Users/", content)

    def test_state_aggregation_does_not_overclaim(self):
        self.assertEqual(render.aggregate([{"status": "demo"}, {"status": "todo"}]), "partial")
        self.assertEqual(render.aggregate([{"status": "skeleton"}, {"status": "todo"}]), "skeleton")
        self.assertEqual(render.aggregate([{"status": "implemented"}] * 2), "implemented")

    def test_book_boundaries_and_current_location(self):
        self.assertNotIn('data-turn="previous"', self.pages["index.html"])
        self.assertNotIn('data-turn="next"', self.pages["ac-14-02-02.html"])
        page = self.pages["ac-03-02-01.html"]
        self.assertIn('href="ac-03-02-01.html" aria-current="page"', page)
        self.assertIn('data-turn="previous" href="req-03-02.html"', page)
        self.assertIn('data-turn="next" href="ac-03-02-02.html"', page)

    def test_untrusted_text_is_escaped(self):
        progress = copy.deepcopy(self.progress)
        progress["intro"] = '<script>alert("x")</script>'
        page = render.render_overview(progress, self.requirements["groups"])
        self.assertNotIn(progress["intro"], page)
        self.assertIn("&lt;script&gt;", page)

    def test_invalid_hierarchy_and_media_fail_closed(self):
        for corruption in ("parent", "unknown_image", "empty_module", "todo_preview"):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "data").mkdir()
                requirements = copy.deepcopy(self.requirements)
                first = requirements["groups"][0]["items"][0]
                if corruption == "parent":
                    first["id"] = "AC-99-01-01"
                elif corruption == "unknown_image":
                    first["previews"][0]["id"] = "missing"
                elif corruption == "empty_module":
                    requirements["groups"] = requirements["groups"][2:]
                else:
                    first["status"] = "todo"
                for name, data in (("progress", self.progress), ("media", self.media), ("requirements", requirements)):
                    (root / f"data/{name}.json").write_text(json.dumps(data))
                with patch.object(build, "SOURCE", root), self.assertRaises(ValueError):
                    build.load_data()

    def test_altered_image_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / self.media["images"][0]["asset"]).write_bytes(b"altered image")
            with self.assertRaisesRegex(ValueError, "图片校验失败"):
                build.materialize_images(self.media, root, root, None)


if __name__ == "__main__":
    unittest.main()
