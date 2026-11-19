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
        self.title = ""
        self.json_ld = []
        self._current_tag = None
        self._buffer = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        self.elements.append((tag, attr_map))
        if tag == "title" or (tag == "script" and attr_map.get("type") == "application/ld+json"):
            self._current_tag = tag
            self._buffer = []

    def handle_data(self, data):
        if self._current_tag:
            self._buffer.append(data)

    def handle_endtag(self, tag):
        if tag == self._current_tag:
            text_value = "".join(self._buffer)
            if tag == "title":
                self.title = text_value
            else:
                self.json_ld.append(json.loads(text_value))
            self._current_tag = None
            self._buffer = []


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
        self.assertEqual(len(list(self.output.rglob("*.html"))), 48)
        titles = []
        descriptions = []
        for code, content in self.locales.items():
            for index, page in enumerate(build.PAGES):
                with self.subTest(language=code, page=page):
                    html = (self.output / build.page_path(code, page)).read_text(encoding="utf-8")
                    parser = PageParser(html)
                    elements = parser.elements
                    self.assertIn(("html", {"lang": code}), elements)
                    self.assertEqual(sum(tag == "h1" for tag, _ in elements), 1)
                    headings = [int(tag[1]) for tag, _ in elements if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}]
                    self.assertEqual(headings[0], 1)
                    for prev_level, next_level in zip(headings, headings[1:]):
                        self.assertLessEqual(next_level, prev_level + 1, f"Skipped heading level: {headings}")
                    self.assertNotIn('class=""', html)
                    self.assertEqual(parser.title, build.page_title(content, page))
                    self.assertTrue(25 <= len(parser.title) <= 70, parser.title)
                    titles.append(parser.title)
                    description = content["guide"]["description"] if page == "how-to-use.html" else content["descriptions"][index]
                    descriptions.append(description)
                    self.assertIn(description, [
                        attrs.get("content") for tag, attrs in elements
                        if tag == "meta" and attrs.get("name") == "description"
                    ])
                    self.assertIn(build.absolute_page_url(code, page, self.url), [
                        attrs.get("href") for tag, attrs in elements
                        if tag == "link" and attrs.get("rel") == "canonical"
                    ])
                    self.assertIn(self.url + "/sitemap.xml", [
                        attrs.get("href") for tag, attrs in elements
                        if tag == "link" and attrs.get("rel") == "sitemap"
                    ])
                    alternates = {
                        attrs["hreflang"]: attrs["href"] for tag, attrs in elements
                        if tag == "link" and attrs.get("rel") == "alternate"
                    }
                    self.assertEqual(set(alternates), set(self.locales) | {"x-default"})
                    self.assertEqual(alternates["x-default"], build.absolute_page_url("tr", page, self.url))
                    meta = {
                        attrs.get("name") or attrs.get("property"): attrs.get("content")
                        for tag, attrs in elements if tag == "meta"
                    }
                    self.assertEqual(meta["robots"], build.ROBOTS_DIRECTIVE)
                    self.assertEqual(meta["og:title"], parser.title)
                    self.assertEqual(meta["twitter:title"], parser.title)
                    self.assertEqual(meta["og:url"], build.absolute_page_url(code, page, self.url))
                    self.assertEqual(meta["og:image"], self.url + "/" + build.SOCIAL_IMAGE)
                    self.assertEqual(meta["og:image:secure_url"], meta["og:image"])
                    self.assertEqual(meta["twitter:card"], "summary_large_image")
                    self.assertEqual(meta["twitter:image"], meta["og:image"])
                    self.assertEqual(meta["og:image:alt"], content["socialImageAlt"])
                    self.assertEqual(meta["twitter:image:alt"], content["socialImageAlt"])
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
        self.assertEqual(len(set(titles)), 48)
        self.assertEqual(len(set(descriptions)), 48)

    def test_structured_data_across_all_page_types(self):
        for code, content in self.locales.items():
            for page in build.PAGES:
                with self.subTest(language=code, page=page):
                    html = (self.output / build.page_path(code, page)).read_text(encoding="utf-8")
                    blocks = PageParser(html).json_ld
                    self.assertEqual(len(blocks), 2)
                    canonical = build.absolute_page_url(code, page, self.url)
                    if page == "index.html":
                        app_ld, site_ld = blocks
                        self.assertEqual(app_ld["@context"], "https://schema.org")
                        self.assertEqual(app_ld["@type"], "SoftwareApplication")
                        self.assertEqual(app_ld["name"], build.BRAND_LABEL)
                        self.assertEqual(app_ld["description"], content["descriptions"][0])
                        self.assertEqual(app_ld["url"], canonical)
                        self.assertEqual(app_ld["downloadUrl"], build.STORE_URL)
                        self.assertEqual(len(app_ld["screenshot"]), 10)
                        self.assertEqual(len(app_ld["featureList"]), 6)
                        self.assertNotIn("index.html", app_ld["url"])
                        self.assertEqual(site_ld["@type"], "WebSite")
                        self.assertEqual(site_ld["url"], canonical)
                        self.assertEqual(site_ld["inLanguage"], code)
                    else:
                        breadcrumb_ld, page_ld = blocks
                        self.assertNotEqual(page_ld["@type"], "SoftwareApplication")
                        self.assertEqual(breadcrumb_ld["@type"], "BreadcrumbList")
                        self.assertEqual(len(breadcrumb_ld["itemListElement"]), 2)
                        self.assertEqual(
                            breadcrumb_ld["itemListElement"][0]["item"],
                            build.absolute_page_url(code, "index.html", self.url),
                        )
                        self.assertEqual(breadcrumb_ld["itemListElement"][1]["item"], canonical)
                        if page == "how-to-use.html":
                            self.assertEqual(page_ld["@type"], "HowTo")
                            self.assertEqual(len(page_ld["step"]), 10)
                            self.assertEqual(page_ld["step"][0]["url"], canonical + "#tour-step-1")
                        elif page == "support.html":
                            self.assertEqual(page_ld["@type"], "FAQPage")
                            self.assertEqual(len(page_ld["mainEntity"]), len(content["faqs"]))
                        else:
                            self.assertEqual(page_ld["@type"], "WebPage")
                            self.assertEqual(page_ld["url"], canonical)

    def test_privacy_navigation_precedes_support_on_every_page(self):
        labels = {
            "tr": "Gizlilik", "en": "Privacy", "de": "Datenschutz",
            "fr": "Confidentialité", "es": "Privacidad", "pt": "Privacidade",
            "nl": "Privacy", "it": "Privacy",
        }
        for code, label in labels.items():
            for page in build.PAGES:
                with self.subTest(language=code, page=page):
                    html = (self.output / build.page_path(code, page)).read_text(encoding="utf-8")
                    nav = html.split('<nav class="nav"', 1)[1].split("</nav>", 1)[0]
                    links = [attrs for tag, attrs in PageParser(nav).elements if tag == "a"]
                    targets = [attrs["href"] for attrs in links]
                    self.assertEqual(targets.count("privacy.html"), 1)
                    self.assertEqual(targets[targets.index("privacy.html") + 1], "support.html")
                    self.assertIn(f'>{build.text(label)}</a>', nav)
                    self.assertEqual([
                        attrs["href"] for attrs in links if attrs.get("aria-current") == "page"
                    ], [page])

    def test_privacy_pages_reuse_localized_content_and_authoritative_policies(self):
        for code, content in self.locales.items():
            with self.subTest(language=code):
                html = (self.output / build.page_path(code, "privacy.html")).read_text(encoding="utf-8")
                self.assertIn(f'<h1>{build.text(content["privacyTitle"])}</h1>', html)
                self.assertIn(build.text(content["privacyText"]), html)
                links = [attrs["href"] for tag, attrs in PageParser(html).elements if tag == "a"]
                self.assertIn(
                    "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement",
                    links,
                )
                self.assertIn(build.APP_URL + "/blob/main/PRIVACY.MD", links)
                self.assertNotIn(build.APP_URL + "/issues/new", links)

    def test_internal_links_assets_and_fragments_resolve(self):
        for file in self.output.rglob("*.html"):
            parser = PageParser(file.read_text(encoding="utf-8"))
            for tag, attrs in parser.elements:
                for key in ("href", "src", "aria-controls", "aria-labelledby"):
                    value = attrs.get(key)
                    if not value:
                        continue
                    url = urlsplit(value)
                    if url.scheme or url.netloc:
                        continue
                    with self.subTest(file=file.relative_to(self.output), link=value):
                        self.assertFalse(value.startswith("/"), "Project-site links must be relative")
                        if key in {"aria-controls", "aria-labelledby"}:
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
                self.assertEqual(captures[0].get("loading"), "eager")
                self.assertEqual(captures[0].get("fetchpriority"), "high")
                self.assertTrue(all(c.get("loading") == "lazy" and c.get("decoding") == "async" for c in captures[1:]))
                states = [attrs for _, attrs in elements if "data-tour-state" in attrs]
                self.assertEqual({attrs["data-tour-state"] for attrs in states}, {"before", "after"})
                self.assertTrue(all("hidden" not in attrs for attrs in states))
                self.assertIn(build.STORE_URL, [attrs.get("href") for tag, attrs in elements if tag == "a"])
                self.assertIn(build.text(content["guide"]["recordingNote"]), html)
                self.assertIn(
                    f'<a href="support.html" class="text-link">{build.text(content["nav"][4])}</a>',
                    html,
                )
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
        namespace = {
            "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "xhtml": "http://www.w3.org/1999/xhtml",
            "image": "http://www.google.com/schemas/sitemap-image/1.1",
        }
        sitemap = ElementTree.parse(self.output / "sitemap.xml")
        url_nodes = sitemap.findall("s:url", namespace)
        urls = [node.findtext("s:loc", namespaces=namespace) for node in url_nodes]
        self.assertEqual(len(urls), 48)
        self.assertEqual(len(set(urls)), 48)
        self.assertTrue(all(url.startswith(self.url + "/") for url in urls))
        self.assertIn(self.url + "/", urls)
        self.assertIn(self.url + "/en/", urls)
        self.assertNotIn(self.url + "/index.html", urls)
        self.assertNotIn(self.url + "/en/index.html", urls)
        for node in url_nodes:
            lastmod = node.findtext("s:lastmod", namespaces=namespace)
            self.assertRegex(lastmod, r"^\d{4}-\d{2}-\d{2}$")
            xhtml_links = {
                link.attrib["hreflang"]: link.attrib["href"]
                for link in node.findall("xhtml:link", namespace)
            }
            self.assertEqual(set(xhtml_links), set(self.locales) | {"x-default"})
        image_locs = [
            node.text for node in sitemap.findall("s:url/image:image/image:loc", namespace)
        ]
        self.assertEqual(len(image_locs), 8 * 1 + 8 * 11)
        self.assertTrue(all(loc.startswith(self.url + "/assets/tour/") for loc in image_locs))
        self.assertIn(self.url + "/sitemap.xml", (self.output / "robots.txt").read_text())
        self.assertTrue((self.output / ".nojekyll").is_file())
        html = build.render("de", "support.html", self.locales, "https://example.com/custom")
        self.assertIn('href="https://example.com/custom/de/support.html"', html)
        for invalid in ("http://example.com", "https://example.com?query=1", "/local"):
            with self.subTest(url=invalid), self.assertRaises(ValueError):
                build.build(self.output, invalid)


if __name__ == "__main__":
    unittest.main()
