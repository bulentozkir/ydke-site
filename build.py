"""Build a dependency-free, localized GitHub Pages website."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
import math
from pathlib import Path
import shutil
import struct
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
PAGES = ("index.html", "license.html", "copyright.html", "privacy.html", "support.html", "how-to-use.html")
APP_URL = "https://github.com/bulentozkir/ydke"
BRAND_LABEL = "YDKE - Yabancı Dil Kelime Ezberleme"
STORE_URL = "https://apps.microsoft.com/detail/9N8LFRMX67ZF?hl=neutral&gl=TR&ocid=pdpshare"
LICENSE_URL = "https://polyformproject.org/licenses/noncommercial/1.0.0"
AUTHORS = ("Bulent Ozkir", "Ahmet Arda Ozkir", "Halit Eren Ozkir")
INTERFACE_LANGUAGES = ("tr", "en", "de", "fr", "es", "pt", "nl")
ROBOTS_DIRECTIVE = "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
NOTICE = (
    "Required Notice: Copyright 2026 Bulent Ozkir, Ahmet Arda Ozkir, "
    "Halit Eren Ozkir (YDKE - Yabancı Dil Kelime Ezberleme)"
)
CONTACT = "bulentozkir@hotmail.com"
SOCIAL_IMAGE = "assets/tour/cards.png"
LOCALES = {
    "tr": "tr_TR",
    "en": "en_US",
    "de": "de_DE",
    "fr": "fr_FR",
    "es": "es_ES",
    "pt": "pt_PT",
    "nl": "nl_NL",
    "it": "it_IT",
}


def text(value):
    return escape(value, quote=True)


def page_path(language, page):
    return page if language == "tr" else f"{language}/{page}"


def canonical_path(language, page):
    if page == "index.html":
        return "" if language == "tr" else f"{language}/"
    return page_path(language, page)


def absolute_page_url(language, page, site_url):
    return site_url.rstrip("/") + "/" + canonical_path(language, page)


def relative_path(language, target):
    return ("" if language == "tr" else "../") + target


def link(url, label, css=""):
    cls = f' class="{text(css)}"' if css else ""
    return f'<a href="{text(url)}"{cls}>{text(label)}</a>'


def sections(items, prefix="section"):
    return "".join(
        f'<section class="document-section" id="{prefix}-{index}" aria-labelledby="{prefix}-title-{index}">'
        f'<h2 id="{prefix}-title-{index}">{text(title)}</h2>'
        f"<p>{text(body)}</p></section>"
        for index, (title, body) in enumerate(items, 1)
    )


def page_title(c, page):
    if page == "index.html":
        return f"YDKE — {c['tagline']} | Windows"
    if page == "how-to-use.html":
        return f"{c['guide']['title']} — YDKE"
    if page == "support.html":
        return f"{c['nav'][PAGES.index('support.html')]} — {c['supportTitle']} | YDKE"
    if page == "copyright.html":
        return f"{c['copyrightTitle']} — YDKE"
    kind = page.removesuffix(".html")
    return f"{c[f'{kind}Title']} — {BRAND_LABEL}"


def home(c):
    features = "".join(
        f'<article class="feature"><span class="feature-icon" aria-hidden="true">{icon}</span>'
        f"<h3>{text(title)}</h3><p>{text(body)}</p></article>"
        for icon, (title, body) in zip(("▤", "✓", "✦", "☆", "▣", "↗"), c["features"], strict=True)
    )
    stats = "".join(
        f'<div class="stat"><strong>{value}</strong><span>{text(label)}</span></div>'
        for value, label in zip(("7", "A1–C2", "25"), c["stats"], strict=True)
    )
    languages = "".join(f'<span class="language-pill">{text(name)}</span>' for name in c["studyLanguages"])
    levels = "".join(f"<span>{level}</span>" for level in ("A1", "A2", "B1", "B2", "C1", "C2"))
    steps = "".join(
        f'<li><span class="step-number" aria-hidden="true">0{number}</span>'
        f"<h3>{text(title)}</h3><p>{text(body)}</p></li>"
        for number, (title, body) in enumerate(c["steps"], 1)
    )
    trust = "".join(f"<li>{text(c[key])}</li>" for key in ("offline", "account", "local"))
    hero_parts = c["hero"].split("<br>")
    hero_title = text(hero_parts[0]) + "<br><span>" + text(" ".join(hero_parts[1:])) + "</span>"
    translated_example = "" if c["example"] == "I flourish with small steps every day." else f'<p>{text(c["example"])}</p>'
    return f"""
    <section class="hero" aria-labelledby="hero-title">
      <div>
        <p class="eyebrow">{text(c["eyebrow"])}</p>
        <h1 id="hero-title">{hero_title}</h1>
        <p class="lead">{text(c["intro"])}</p>
        <div class="actions">
          {link(STORE_URL, c["store"] + " ↗", "button")}
        </div>
        <p class="platform">{text(c["platform"])}</p>
        {link("#features", c["explore"] + " ↓", "text-link hero-link")}
        <span class="hero-link-divider" aria-hidden="true">/</span>
        {link("how-to-use.html", c["guide"]["nav"] + " →", "text-link hero-link")}
        <ul class="trust">{trust}</ul>
      </div>
      <figure class="preview">
        <div class="study-card">
          <div class="preview-chrome" aria-hidden="true"><i></i><i></i><i></i><span>YDKE / WINDOWS</span></div>
          <div class="card-top"><span>{text(c["word"])}</span><span class="level" lang="en">EN · B2</span></div>
          <div class="plant" aria-hidden="true"><i class="stem"></i><i class="leaf one"></i><i class="leaf two"></i><i class="leaf three"></i><i class="pot"></i></div>
          <p class="sample-word" lang="en">flourish</p>
          <p class="sample-pronunciation" lang="en">/ˈflʌr.ɪʃ/</p>
          <div class="meaning" id="card-meaning" aria-live="polite">
            <strong>{text(c["meaning"])}</strong>
            <p lang="en">I flourish with small steps every day.</p>
            {translated_example}
          </div>
          <button hidden type="button" class="button" data-reveal data-show="{text(c["reveal"])}" data-hide="{text(c["hide"])}" aria-controls="card-meaning" aria-expanded="false">{text(c["reveal"])}</button>
          <p class="card-hint">{text(c["cardHint"])}</p>
        </div>
        <figcaption>{text(c["preview"])}</figcaption>
      </figure>
    </section>
    <div class="stats">{stats}</div>
    <section class="section" id="features" aria-labelledby="features-title">
      <p class="eyebrow">{text(c["featuresLabel"])}</p>
      <h2 id="features-title">{text(c["featuresTitle"])}</h2>
      <p class="section-intro">{text(c["featuresIntro"])}</p>
      <div class="features">{features}</div>
    </section>
    <section class="language-section" id="languages" aria-labelledby="languages-title">
      <div><p class="eyebrow">{text(c["languagesLabel"])}</p><h2 id="languages-title">{text(c["languagesTitle"])}</h2><p class="section-intro">{text(c["languagesIntro"])}</p></div>
      <div><div class="language-list">{languages}</div><div class="levels">{levels}</div><p class="language-note">{text(c["interfaceNote"])}</p></div>
    </section>
    <section class="section" id="getting-started" aria-labelledby="steps-title">
      <h2 class="eyebrow" id="steps-title">{text(c["stepsLabel"])}</h2>
      <ol class="steps">{steps}</ol>
    </section>
    <section class="cta" id="download" aria-labelledby="cta-title">
      <div><h2 id="cta-title">{text(c["ctaTitle"])}</h2><p>{text(c["ctaText"])}</p></div>
      {link(STORE_URL, c["store"] + " ↗", "button")}
    </section>"""


def privacy_links(c):
    return f"""
      <div class="legal-links">
        {link("https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement", c["hostPrivacy"])}
        {link(APP_URL + "/blob/main/PRIVACY.MD", c["appPrivacy"])}
      </div>"""


def document(c, page):
    kind = page.removesuffix(".html")
    title = c[f"{kind}Title"]
    intro = c["privacyText"] if kind == "privacy" else c[f"{kind}Intro"]
    label = c["supportLabel"] if kind == "support" else c["legalLabel"]
    header = f'<p class="eyebrow">{text(label)}</p><h1>{text(title)}</h1><p class="lead">{text(intro)}</p>'
    if kind == "privacy":
        return header + privacy_links(c)
    if kind == "license":
        return header + sections(c["licenseSections"], "license") + f"""
        <div class="legal-links">
          {link(APP_URL + "/blob/main/LICENSE.md", c["fullLicense"])}
          {link(LICENSE_URL, c["officialLicense"])}
          {link("mailto:" + CONTACT, c["permission"])}
        </div>"""
    if kind == "copyright":
        credits = "".join(
            f"<li>{text(body)}<br>{link(source, name)} · {link(license_url, license_name)}</li>"
            for body, source, name, license_url, license_name in zip(
                c["attributions"],
                ("https://www.wiktionary.org", "https://tatoeba.org"),
                ("Wiktionary", "Tatoeba"),
                ("https://creativecommons.org/licenses/by-sa/4.0/", "https://creativecommons.org/licenses/by/2.0/fr/"),
                ("CC BY-SA 4.0", "CC BY 2.0 FR"),
                strict=True,
            )
        )
        return header + f"""
        <section class="document-section" id="required-notice" aria-labelledby="notice-title"><h2 id="notice-title">{text(c["requiredNotice"])}</h2><p class="notice" lang="en">{text(NOTICE)}</p></section>
        <section class="document-section" id="attributions" aria-labelledby="attribution-title"><h2 id="attribution-title">{text(c["attributionTitle"])}</h2><ul class="attribution">{credits}</ul>{link(APP_URL + "/blob/main/NOTICE.md", c["noticeLink"])}</section>
        """ + sections([(c["trademarkTitle"], c["trademarkText"])], "trademark")
    faqs = "".join(
        f"<details><summary>{text(question)}</summary><p>{text(answer)}</p></details>"
        for question, answer in c["faqs"]
    )
    return header + sections([(c["helpTitle"], c["helpText"])], "in-app-help") + f"""
    <section class="document-section" id="report-issue" aria-labelledby="issue-title">
      <h2 id="issue-title">{text(c["issueTitle"])}</h2><p>{text(c["issueText"])}</p>
      {link(APP_URL + "/issues/new", c["issueLink"] + " ↗", "button")}
    </section>
    <section class="document-section" id="contact" aria-labelledby="contact-title">
      <h2 id="contact-title">{text(c["contactTitle"])}</h2><p>{text(c["contactText"])}</p>{link("mailto:" + CONTACT, CONTACT)}
    </section>
    <section class="document-section faq" id="faq" aria-labelledby="faq-title"><h2 id="faq-title">{text(c["faqTitle"])}</h2>{faqs}</section>
    <section class="document-section" id="site-privacy" aria-labelledby="privacy-title">
      <h2 id="privacy-title">{text(c["privacyTitle"])}</h2><p>{text(c["privacyText"])}</p>
      {privacy_links(c)}
    </section>"""


def guide_page(c, language, frames=None):
    guide = c["guide"]
    if frames is None:
        frames = load_tour()
    steps = []
    chapters = []

    def screenshot(frame, title, control, state=""):
        boxes = "".join(
            f'<span class="tour-highlight" aria-hidden="true" style="left:{box["x"]:.3f}%;top:{box["y"]:.3f}%;width:{box["width"]:.3f}%;height:{box["height"]:.3f}%"></span>'
            for box in frame["highlights"]
        )
        url = relative_path(language, "assets/tour/" + frame["image"])
        state_attr = f' data-tour-state="{text(state)}"' if state else ""
        loading_attrs = 'loading="eager" fetchpriority="high"' if frame["id"] == "toolbar" else 'loading="lazy" decoding="async"'
        return f"""
          <div class="tour-image"{state_attr}>
            <a href="{url}" aria-label="{text(guide["openImage"] + ' — ' + title)}">
              <img src="{url}" alt="{text(title + ' — ' + control)}" width="{frame["width"]}" height="{frame["height"]}" {loading_attrs}>
            </a>
            {boxes}
          </div>"""

    for index, (frame, step) in enumerate(zip(frames, guide["steps"], strict=True)):
        title, description, control, tip = step
        number = index + 1
        chapters.append(
            f'<li><a href="#tour-step-{number}" data-tour-chapter="{index}">'
            f'<span>{number:02}</span>{text(title)}</a></li>'
        )
        image = screenshot(frame, title, control)
        comparison_button = ""
        if "before" in frame:
            image = (
                f'<div data-tour-comparison data-show="{text(c["reveal"])}" data-hide="{text(c["hide"])}">'
                + screenshot(frame["before"], title, c["reveal"], "before")
                + screenshot(frame, title, control, "after")
                + "</div>"
            )
            comparison_button = f'<button hidden type="button" class="button secondary" data-tour-reveal aria-pressed="false">{text(c["reveal"])}</button>'
        steps.append(f"""
        <article class="tour-step" id="tour-step-{number}" data-tour-step="{index}" aria-labelledby="tour-title-{number}">
          {image}
          <div class="tour-caption">
            <div class="tour-step-count">{number:02} / {len(frames):02}</div>
            <h2 id="tour-title-{number}">{text(title)}</h2>
            <p>{text(description)}</p>
            {comparison_button}
            <div class="tour-control"><strong>{text(guide["control"])}</strong><span>{text(control)}</span></div>
            <div class="tour-tip"><strong>{text(guide["tip"])}</strong><span>{text(tip)}</span></div>
          </div>
        </article>""")
    keyboard = "".join(
        f"<li><kbd>{text(key)}</kbd><span>{text(label)}</span></li>"
        for key, label in zip(("Tab", "Shift + Tab", "Enter", "F11", "Esc", "1–4"), guide["keys"], strict=True)
    )
    return f"""
    <div class="guide-header">
      <p class="eyebrow">{text(guide["label"])}</p><h1>{text(guide["title"])}</h1>
      <p class="lead">{text(guide["intro"])}</p>
      <p class="small">{text(guide["recordingNote"])}</p>
    </div>
    <div class="tour-layout" data-tour data-play="{text(guide["play"])}" data-pause="{text(guide["pause"])}">
      <aside class="tour-chapters"><h2>{text(guide["chapters"])}</h2><ol>{"".join(chapters)}</ol></aside>
      <div class="tour-player">
        <div class="tour-toolbar" hidden data-tour-toolbar>
          <button type="button" class="button" data-tour-play aria-pressed="false">{text(guide["play"])}</button>
          <button type="button" class="button secondary" data-tour-previous>{text(guide["previous"])}</button>
          <button type="button" class="button secondary" data-tour-next>{text(guide["next"])}</button>
          <button type="button" class="text-button" data-tour-restart>{text(guide["restart"])}</button>
        </div>
        <p class="sr-only" role="status" data-tour-status></p>
        <div class="tour-track">{"".join(steps)}</div>
        <p class="small tour-motion">{text(guide["motionNote"])}</p>
      </div>
    </div>
    <section class="section keyboard-section" id="keyboard-shortcuts" aria-labelledby="keys-title">
      <p class="eyebrow">YDKE / WINDOWS</p><h2 id="keys-title">{text(guide["keysTitle"])}</h2>
      <ul class="keyboard-list">{keyboard}</ul>
    </section>
    <section class="cta" id="download" aria-labelledby="guide-cta-title">
      <div><h2 id="guide-cta-title">{text(guide["startTitle"])}</h2><p>{text(guide["startText"])}</p></div>
      <div class="guide-links">
        {link(STORE_URL, c["store"] + " ↗", "button")}
        {link("support.html", c["nav"][PAGES.index("support.html")], "text-link")}
      </div>
    </section>"""


def structured_data_scripts(language, page, c, description, canonical, site_url, frames, app_version):
    site_root = site_url.rstrip("/")
    home_url = absolute_page_url(language, "index.html", site_url)
    nav_labels = [*c["nav"], c["guide"]["nav"]]
    index = PAGES.index(page)
    authors_ld = [{"@type": "Person", "name": name} for name in AUTHORS]
    if page == "index.html":
        blocks = [
            {
                "@context": "https://schema.org",
                "@type": "SoftwareApplication",
                "@id": f"{site_root}/#software",
                "name": BRAND_LABEL,
                "alternateName": "YDKE",
                "description": description,
                "url": canonical,
                "image": f"{site_root}/{SOCIAL_IMAGE}",
                "screenshot": [f"{site_root}/assets/tour/{frame['image']}" for frame in frames],
                "operatingSystem": "Windows 10 version 1809 or later, Windows 11",
                "processorRequirements": "x64, ARM64",
                "applicationCategory": "EducationalApplication",
                "applicationSubCategory": "Language Learning",
                "inLanguage": list(INTERFACE_LANGUAGES),
                "featureList": [f"{title}: {body}" for title, body in c["features"]],
                "softwareVersion": app_version,
                "license": LICENSE_URL,
                "downloadUrl": STORE_URL,
                "installUrl": STORE_URL,
                "sameAs": [STORE_URL, APP_URL],
                "author": authors_ld,
                "copyrightHolder": authors_ld,
                "copyrightYear": 2026,
            },
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "@id": f"{site_root}/#website",
                "name": "YDKE",
                "alternateName": BRAND_LABEL,
                "description": description,
                "url": canonical,
                "inLanguage": language,
            },
        ]
    else:
        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": c["nav"][0],
                    "item": home_url,
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": nav_labels[index],
                    "item": canonical,
                },
            ],
        }
        if page == "how-to-use.html":
            page_ld = {
                "@context": "https://schema.org",
                "@type": "HowTo",
                "name": c["guide"]["title"],
                "description": description,
                "url": canonical,
                "inLanguage": language,
                "image": f"{site_root}/assets/tour/toolbar.png",
                "step": [
                    {
                        "@type": "HowToStep",
                        "position": number,
                        "name": step_title,
                        "text": step_description,
                        "url": f"{canonical}#tour-step-{number}",
                        "image": f"{site_root}/assets/tour/{frame['image']}",
                    }
                    for number, (frame, (step_title, step_description, _, _)) in enumerate(
                        zip(frames, c["guide"]["steps"], strict=True), 1
                    )
                ],
            }
        elif page == "support.html":
            page_ld = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "name": c["supportTitle"],
                "description": description,
                "url": canonical,
                "inLanguage": language,
                "isPartOf": {"@id": f"{site_root}/#website"},
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": answer,
                        },
                    }
                    for question, answer in c["faqs"]
                ],
            }
        else:
            kind = page.removesuffix(".html")
            page_ld = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": c[f"{kind}Title"],
                "description": description,
                "url": canonical,
                "inLanguage": language,
                "isPartOf": {"@id": f"{site_root}/#website"},
            }
        blocks = [breadcrumb, page_ld]
    return "\n  ".join(
        '<script type="application/ld+json">'
        + json.dumps(block, ensure_ascii=False).replace("</", "<\\/")
        + "</script>"
        for block in blocks
    )


def render(language, page, locales, site_url, tour_manifest=None):
    c = locales[language]
    if tour_manifest is None:
        tour_manifest = load_tour_manifest()
    frames = tour_manifest["frames"]
    app_version = tour_manifest["appVersion"].split("+", 1)[0]
    index = PAGES.index(page)
    nav_labels = [*c["nav"], c["guide"]["nav"]]
    description = c["guide"]["description"] if page == "how-to-use.html" else c["descriptions"][index]
    title = page_title(c, page)
    site_root = site_url.rstrip("/")
    canonical = absolute_page_url(language, page, site_url)
    alternates = "\n  ".join(
        f'<link rel="alternate" hreflang="{code}" href="{text(absolute_page_url(code, page, site_url))}">'
        for code in locales
    )
    nav = "".join(
        f'<a href="{target}"{" aria-current=\"page\"" if target == page else ""}>{text(label)}</a>'
        for target, label in zip(PAGES, nav_labels, strict=True)
    )
    language_links = "".join(
        f'<li><a lang="{code}" hreflang="{code}" href="{relative_path(language, page_path(code, page))}"'
        f'{" aria-current=\"page\"" if code == language else ""}>{text(other["name"])}</a></li>'
        for code, other in locales.items()
    )
    assets = relative_path(language, "assets/")
    footer = "".join(link(target, label) for target, label in zip(PAGES[1:], nav_labels[1:], strict=True))
    main_content = home(c) if index == 0 else guide_page(c, language, frames) if page == "how-to-use.html" else document(c, page)
    social_image = site_root + "/" + SOCIAL_IMAGE
    locale_alternates = "\n  ".join(
        f'<meta property="og:locale:alternate" content="{text(locale)}">'
        for code, locale in LOCALES.items() if code != language
    )
    structured_data = structured_data_scripts(
        language, page, c, description, canonical, site_url, frames, app_version
    )
    return f"""<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{text(title)}</title>
  <meta name="description" content="{text(description)}">
  <meta name="robots" content="{ROBOTS_DIRECTIVE}">
  <meta name="author" content="{text(", ".join(AUTHORS))}">
  <meta name="application-name" content="YDKE">
  <meta name="color-scheme" content="light">
  <meta name="theme-color" content="#3652cb">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="YDKE">
  <meta property="og:locale" content="{text(LOCALES[language])}">
  {locale_alternates}
  <meta property="og:title" content="{text(title)}">
  <meta property="og:description" content="{text(description)}">
  <meta property="og:url" content="{text(canonical)}">
  <meta property="og:image" content="{text(social_image)}">
  <meta property="og:image:secure_url" content="{text(social_image)}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1938">
  <meta property="og:image:height" content="1158">
  <meta property="og:image:alt" content="{text(c["socialImageAlt"])}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{text(title)}">
  <meta name="twitter:description" content="{text(description)}">
  <meta name="twitter:image" content="{text(social_image)}">
  <meta name="twitter:image:alt" content="{text(c["socialImageAlt"])}">
  <link rel="canonical" href="{text(canonical)}">
  {alternates}
  <link rel="alternate" hreflang="x-default" href="{text(absolute_page_url("tr", page, site_url))}">
  <link rel="sitemap" type="application/xml" href="{text(site_root + "/sitemap.xml")}">
  <link rel="icon" type="image/svg+xml" sizes="any" href="{assets}favicon.svg">
  <link rel="stylesheet" href="{assets}site.css">
  {structured_data}
  <script defer src="{assets}site.js"></script>
</head>
<body>
  <a class="skip" href="#main">{text(c["skip"])}</a>
  <header class="header wrap">
    <a class="brand" href="index.html" aria-label="{text(BRAND_LABEL)} — {text(c["nav"][0])}"><img src="{assets}favicon.svg" alt="" width="42" height="42" decoding="async">{text(BRAND_LABEL)}</a>
    <nav class="nav" aria-label="{text(c["nav"][0])}">{nav}</nav>
    <details class="locale">
      <summary><span aria-hidden="true">◎</span> {text(c["name"])}<span class="sr-only"> — {text(c["language"])}</span></summary>
      <ul>{language_links}</ul>
    </details>
  </header>
  <main id="main" class="wrap{"" if index == 0 else " guide" if page == "how-to-use.html" else " document"}" tabindex="-1">{main_content}</main>
  <footer class="footer">
    <div class="wrap">
      <div class="footer-top"><div><strong>YDKE</strong><p>{text(c["footer"])}</p></div><nav class="footer-links" aria-label="{text(c["legalLabel"])}">{footer}</nav></div>
      <p>{text(c["siteNote"])}</p>
      <p lang="en">© 2026 Bulent Ozkir, Ahmet Arda Ozkir, Halit Eren Ozkir</p>
    </div>
  </footer>
</body>
</html>
"""


def load_tour_manifest():
    folder = ROOT / "assets" / "tour"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    expected = ("toolbar", "cards", "card-reveal", "quiz-picker", "quiz-answer", "words", "games", "statistics", "settings", "help")
    frames = manifest["frames"]
    if tuple(frame["id"] for frame in frames) != expected or manifest["interfaceLanguage"] != "tr":
        raise ValueError("Tour recording must contain all ten essential chapters in Turkish.")
    for frame in frames:
        for image in [frame, *([frame["before"]] if "before" in frame else [])]:
            path = folder / image["image"]
            if path.parent != folder or path.suffix != ".png":
                raise ValueError("Tour images must be PNG files in assets/tour.")
            with path.open("rb") as source:
                header = source.read(24)
            if header[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", header[16:24]) != (image["width"], image["height"]):
                raise ValueError(f"Invalid recorded PNG dimensions: {path.name}")
            if not image["highlights"]:
                raise ValueError(f"Missing control highlights: {path.name}")
            for box in image["highlights"]:
                values = [box[key] for key in ("x", "y", "width", "height")]
                if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
                    raise ValueError(f"Invalid control coordinates: {path.name}")
                if min(values) < 0 or box["width"] <= 0 or box["height"] <= 0 or box["x"] + box["width"] > 100 or box["y"] + box["height"] > 100:
                    raise ValueError(f"Control outside recording: {path.name}")
    return manifest


def load_tour():
    return load_tour_manifest()["frames"]


def load_content():
    locales = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
    expected_languages = {"tr", "en", "de", "fr", "es", "pt", "nl", "it"}
    if set(locales) != expected_languages:
        raise ValueError("Website must cover every YDKE interface and study language.")
    reference = locales["tr"]

    def validate(value, template, path):
        if type(value) is not type(template):
            raise ValueError(f"Invalid translation type: {path}")
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"Empty translation: {path}")
        if isinstance(value, list):
            if len(value) != len(template):
                raise ValueError(f"Invalid translation count: {path}")
            for number, (item, original) in enumerate(zip(value, template, strict=True)):
                validate(item, original, f"{path}[{number}]")
        if isinstance(value, dict):
            if value.keys() != template.keys():
                raise ValueError(f"Missing or extra translation keys: {path}")
            for key in template:
                validate(value[key], template[key], f"{path}.{key}")

    for code, content in locales.items():
        validate(content, reference, code)
    return locales


def build_sitemap(locales, site_url, frames):
    site_root = site_url.rstrip("/")
    source_files = [
        p for p in (
            Path(__file__).resolve(),
            ROOT / "content.json",
            ROOT / "assets" / "site.css",
            ROOT / "assets" / "site.js",
            ROOT / "assets" / "tour" / "manifest.json",
        ) if p.is_file()
    ]
    lastmod = datetime.fromtimestamp(
        max(p.stat().st_mtime for p in source_files), tz=timezone.utc
    ).strftime("%Y-%m-%d")
    guide_images = []
    for frame in frames:
        if "before" in frame:
            guide_images.append(f"{site_root}/assets/tour/{frame['before']['image']}")
        guide_images.append(f"{site_root}/assets/tour/{frame['image']}")
    entries = []
    for page in PAGES:
        alternates = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{alt}" href="{text(absolute_page_url(alt, page, site_url))}"/>'
            for alt in locales
        ) + f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{text(absolute_page_url("tr", page, site_url))}"/>'
        page_images = (
            [f"{site_root}/{SOCIAL_IMAGE}"] if page == "index.html"
            else guide_images if page == "how-to-use.html"
            else []
        )
        image_xml = "".join(
            f"\n    <image:image><image:loc>{text(img)}</image:loc></image:image>"
            for img in page_images
        )
        for code in locales:
            loc = text(absolute_page_url(code, page, site_url))
            entries.append(
                f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>{alternates}{image_xml}\n  </url>"
            )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def build(output, site_url):
    site_url = site_url.rstrip("/")
    parsed = urlsplit(site_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError("Site URL must be an absolute HTTPS URL without query or fragment.")
    output.mkdir(parents=True, exist_ok=True)
    locales = load_content()
    tour_manifest = load_tour_manifest()
    for code in locales:
        for page in PAGES:
            destination = output / page_path(code, page)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(render(code, page, locales, site_url, tour_manifest), encoding="utf-8")
    shutil.copytree(ROOT / "assets", output / "assets", dirs_exist_ok=True)
    shutil.copyfile(ROOT / ".nojekyll", output / ".nojekyll")
    (output / "sitemap.xml").write_text(
        build_sitemap(locales, site_url, tour_manifest["frames"]), encoding="utf-8"
    )
    (output / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n", encoding="utf-8"
    )
    print(f"Built {len(locales) * len(PAGES)} pages in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--site-url", default="https://bulentozkir.github.io/ydke-site")
    args = parser.parse_args()
    build(args.output.resolve(), args.site_url.rstrip("/"))
