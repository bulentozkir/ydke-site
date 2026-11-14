from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

import build


class PageParser(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class WebsiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.url = "https://bulentozkir.github.io/ydke-site"
        cls.locales = build.load_content()
        build.build(cls.output, cls.url)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_localized_pages_and_metadata(self):
        self.assertEqual(len(list(self.output.rglob("*.html"))), 40)
        for code, content in self.locales.items():
            for index, page in enumerate(build.PAGES):
                with self.subTest(language=code, page=page):
                    html = (self.output / build.page_path(code, page)).read_text(encoding="utf-8")
                    elements = PageParser(html).elements
                    self.assertIn(("html", {"lang": code}), elements)
                    self.assertEqual(sum(tag == "h1" for tag, _ in elements), 1)
                    description = content["guide"]["description"] if page == "how-to-use.html" else content["descriptions"][index]
                    self.assertIn(description, [
                        attrs.get("content") for tag, attrs in elements
                        if tag == "meta" and attrs.get("name") == "description"
                    ])
                    self.assertIn(self.url + "/" + build.page_path(code, page), [
                        attrs.get("href") for tag, attrs in elements
                        if tag == "link" and attrs.get("rel") == "canonical"
                    ])
                    alternates = {
                        attrs["hreflang"]: attrs["href"] for tag, attrs in elements
                        if tag == "link" and attrs.get("rel") == "alternate"
                    }
                    self.assertEqual(set(alternates), set(self.locales) | {"x-default"})
                    self.assertEqual(alternates["x-default"], self.url + "/" + page)
                    language_links = {
                        attrs["hreflang"]: attrs["href"] for tag, attrs in elements
                        if tag == "a" and "hreflang" in attrs
                    }
                    for other_code in self.locales:
                        target = self.output / build.page_path(other_code, page)
                        self.assertEqual(
                            ((self.output / build.page_path(code, page)).parent / language_links[other_code]).resolve(),
                            target.resolve(),
                        )

    def test_internal_links_assets_and_fragments_resolve(self):
        for file in self.output.rglob("*.html"):
            parser = PageParser(file.read_text(encoding="utf-8"))
            for tag, attrs in parser.elements:
                for key in ("href", "src", "aria-controls"):
                    value = attrs.get(key)
                    if not value:
                        continue
                    url = urlsplit(value)
                    if url.scheme or url.netloc:
                        continue
                    with self.subTest(file=file.relative_to(self.output), link=value):
                        self.assertFalse(value.startswith("/"), "Project-site links must be relative")
                        if key == "aria-controls":
                            target = file
                            fragment = value
                        else:
                            target = (file.parent / unquote(url.path)).resolve() if url.path else file
                            fragment = url.fragment
                        self.assertTrue(target.is_file(), str(target))
                        if fragment:
                            ids = {
                                attributes["id"] for _, attributes in PageParser(
                                    target.read_text(encoding="utf-8")
                                ).elements if "id" in attributes
                            }
                            self.assertIn(fragment, ids)

    def test_default_is_turkish_and_content_is_not_javascript_dependent(self):
        html = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="tr">', html)
        parser = PageParser(html)
        meaning = next(attrs for _, attrs in parser.elements if attrs.get("id") == "card-meaning")
        self.assertNotIn("hidden", meaning)
        button = next(attrs for tag, attrs in parser.elements if tag == "button")
        self.assertIn("hidden", button)
        self.assertEqual(button["aria-controls"], "card-meaning")
        for file in self.output.rglob("*.html"):
            self.assertNotIn('href="#"', file.read_text(encoding="utf-8"))
            self.assertFalse(any(
                tag in {"iframe", "form"} or (tag == "script" and attrs.get("src", "").startswith("https://"))
                for tag, attrs in PageParser(file.read_text(encoding="utf-8")).elements
            ))

    def test_store_link_is_only_install_option_on_every_homepage(self):
        expected_url = "https://apps.microsoft.com/detail/9N8LFRMX67ZF?hl=neutral&gl=TR&ocid=pdpshare"
        for code, content in self.locales.items():
            with self.subTest(language=code):
                html = (self.output / build.page_path(code, "index.html")).read_text(encoding="utf-8")
                links = [attrs for tag, attrs in PageParser(html).elements if tag == "a"]
                store_links = [attrs for attrs in links if attrs.get("href") == expected_url]
                self.assertEqual(len(store_links), 2)
                self.assertTrue(all(link["class"] == "button" for link in store_links))
                self.assertIn(build.text(content["store"]), html)
                self.assertIn("&amp;gl=TR&amp;ocid=pdpshare", html)
                self.assertFalse(any(
                    attrs.get("href") in {build.APP_URL, build.APP_URL + "/releases"}
                    for attrs in links
                ))
                self.assertNotIn("İndirme seçenekleri", html)

    def test_legal_and_support_pages_use_authoritative_sources(self):
        for code in self.locales:
            license_html = (self.output / build.page_path(code, "license.html")).read_text(encoding="utf-8")
            copyright_html = (self.output / build.page_path(code, "copyright.html")).read_text(encoding="utf-8")
            support_html = (self.output / build.page_path(code, "support.html")).read_text(encoding="utf-8")
            self.assertIn("PolyForm Noncommercial License 1.0.0", license_html)
            self.assertIn(build.APP_URL + "/blob/main/LICENSE.md", license_html)
            self.assertIn(build.NOTICE, copyright_html)
            self.assertIn("https://creativecommons.org/licenses/by-sa/4.0/", copyright_html)
            self.assertIn("https://creativecommons.org/licenses/by/2.0/fr/", copyright_html)
            self.assertIn(build.APP_URL + "/issues/new", support_html)
            self.assertIn("mailto:" + build.CONTACT, support_html)
            self.assertIn(build.APP_URL + "/blob/main/PRIVACY.MD", support_html)

    def test_guide_has_recorded_chapters_controls_and_accessible_static_content(self):
        for code, content in self.locales.items():
            with self.subTest(language=code):
                html = (self.output / build.page_path(code, "how-to-use.html")).read_text(encoding="utf-8")
                elements = PageParser(html).elements
                steps = [attrs for _, attrs in elements if "data-tour-step" in attrs]
                chapters = [attrs for tag, attrs in elements if tag == "a" and "data-tour-chapter" in attrs]
                self.assertEqual(len(steps), 10)
                self.assertTrue(all("hidden" not in attrs for attrs in steps))
                self.assertEqual([attrs["href"] for attrs in chapters], [f"#tour-step-{number}" for number in range(1, 11)])
                captures = [attrs for tag, attrs in elements if tag == "img" and "/tour/" in attrs.get("src", "")]
                self.assertEqual(len(captures), 11)
                self.assertTrue(all(attrs["alt"] and int(attrs["width"]) >= 800 and int(attrs["height"]) >= 600 for attrs in captures))
                states = [attrs for _, attrs in elements if "data-tour-state" in attrs]
                self.assertEqual({attrs["data-tour-state"] for attrs in states}, {"before", "after"})
                self.assertTrue(all("hidden" not in attrs for attrs in states))
                self.assertIn(build.STORE_URL, [attrs.get("href") for tag, attrs in elements if tag == "a"])
                self.assertIn(build.text(content["guide"]["recordingNote"]), html)
                for control in ("data-tour-play", "data-tour-previous", "data-tour-next", "data-tour-restart", "data-tour-reveal"):
                    self.assertTrue(any(tag == "button" and control in attrs and attrs.get("type") == "button" for tag, attrs in elements))
                home = (self.output / build.page_path(code, "index.html")).read_text(encoding="utf-8")
                self.assertIn('href="how-to-use.html"', home)

    def test_recordings_reject_invalid_dimensions_and_out_of_bounds_highlights(self):
        manifest_path = build.ROOT / "assets" / "tour" / "manifest.json"
        for mutation in ("dimensions", "coordinates"):
            with self.subTest(mutation=mutation):
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if mutation == "dimensions":
                    manifest["frames"][0]["width"] += 1
                else:
                    manifest["frames"][0]["highlights"][0]["x"] = 101
                with patch.object(build.json, "loads", return_value=manifest), self.assertRaises(ValueError):
                    build.load_tour()

    def test_translation_validation_rejects_missing_or_empty_content(self):
        original = json.loads((build.ROOT / "content.json").read_text(encoding="utf-8"))
        for mutation in ("missing", "empty", "short_list"):
            with self.subTest(mutation=mutation):
                content = json.loads(json.dumps(original))
                if mutation == "missing":
                    del content["de"]["supportIntro"]
                elif mutation == "empty":
                    content["de"]["supportIntro"] = " "
                else:
                    content["de"]["faqs"].pop()
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / "content.json").write_text(json.dumps(content), encoding="utf-8")
                    with patch.object(build, "ROOT", root), self.assertRaises(ValueError):
                        build.load_content()

    def test_sitemap_and_custom_project_path(self):
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap = ElementTree.parse(self.output / "sitemap.xml")
        urls = [node.text for node in sitemap.findall("s:url/s:loc", namespace)]
        self.assertEqual(len(urls), 40)
        self.assertEqual(len(set(urls)), 40)
        self.assertTrue(all(url.startswith(self.url + "/") for url in urls))
        self.assertIn(self.url + "/sitemap.xml", (self.output / "robots.txt").read_text())
        self.assertTrue((self.output / ".nojekyll").is_file())
        html = build.render("de", "support.html", self.locales, "https://example.com/custom")
        self.assertIn('href="https://example.com/custom/de/support.html"', html)
        for invalid in ("http://example.com", "https://example.com?query=1", "/local"):
            with self.subTest(url=invalid), self.assertRaises(ValueError):
                build.build(self.output, invalid)


if __name__ == "__main__":
    unittest.main()
