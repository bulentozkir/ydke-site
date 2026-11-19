# YDKE website

A Turkish-first public introduction to **YDKE – Yabancı Dil Kelime Ezberleme**,
the offline-first Windows vocabulary app for Turkish students. A static website
for GitHub Pages, with no backend, runtime dependencies, external fonts,
analytics, cookies or account system.

## Languages and pages

Home, license, copyright, privacy, support and **Show me how to use the app** pages are available in Turkish, English,
German, French, Spanish, Portuguese, Dutch and Italian. Turkish is always the
default at the site root; other languages have their own directories. The language
menu preserves the current page, works without JavaScript and never automatically
overrides the visitor's choice.

The shared toolbar places **Privacy** immediately before **Support**. The privacy
page presents the localized site privacy summary and links to the GitHub hosting
and YDKE app policies.

YDKE has seven **interface** languages (all the above except Italian). Its seven
**study** languages include Italian but not Turkish. The website covers their
union and explicitly explains the distinction.

Product facts and legal summaries were checked against the local YDKE repository
at `C:\GitHub\ydke`, specifically its README, `ExperienceStrings.cs`, license,
notice and privacy policy. The path originally supplied, `C:\gitrepo\ydke`, was
not present. The example card is an illustration, not a screenshot or an
embedded version of the app. Every localized homepage and guide page links
exclusively to the
[YDKE Microsoft Store listing](https://apps.microsoft.com/detail/9N8LFRMX67ZF?hl=neutral&gl=TR&ocid=pdpshare)
provided by the publisher to install the app, retaining the supplied URL
parameters.

## Design and interactive app guide

The site uses a professional responsive product layout with a navy/indigo palette,
clear download actions, consistent navigation and accessible focus states. Its
home-page sample card remains a clearly labelled illustration.
The header logo is labelled **YDKE - Yabancı Dil Kelime Ezberleme** in every
website language.

The [how-to guide](https://bulentozkir.github.io/ydke-site/how-to-use.html) has
**10 chapters and 11 genuine screenshots** of the native YDKE interface:
the top toolbar, Cards, revealing a card, quiz picker, saved-answer feedback,
Words, game controls, Statistics, Settings and Help. Recordings show the Turkish
interface; captions and controls are translated into all eight website languages.

Visitors can select a chapter, use Previous/Next, restart, play or pause. Playback
advances every nine seconds and stops at the end; it never starts automatically.
The card chapter includes a manually controllable recorded before/after reveal,
also demonstrated during playback. Reduced-motion preferences remove transitions
and the timed card reveal. Backgrounding the page pauses playback. Without
JavaScript, all chapters and both card images remain readable as a static guide.
Click any screenshot to open it at full size. The screenshots do not run the app,
and the walkthrough does not imply the website can change native app settings.

### Refreshing the recordings

[tools/Record-AppTour.ps1](tools/Record-AppTour.ps1) records **only the YDKE
window**, using `PrintWindow` and UI Automation. It launches the provided
executable with `--test-mode` and a **new, empty** `--data-dir`, rejects existing
profiles, never captures the desktop, and stops only the process it starts.
No existing learning profile is opened; the widget and its online features are
not enabled. Highlight coordinates are measured from the actual native controls.

Use a built native YDKE executable and Windows PowerShell 5.1. For UTF-8 script
loading (including on systems whose default code page is not UTF-8):

```powershell
powershell.exe -NoProfile -Command "& ([scriptblock]::Create([IO.File]::ReadAllText('C:\GitHub\ydke-site\tools\Record-AppTour.ps1'))) -AppPath 'C:\path\to\YDKE.exe' -ProfilePath 'C:\temp\ydke-tour-new-profile' -OutputPath 'C:\GitHub\ydke-site\assets\tour'"
```

`-InspectOnly` lists controls without recording. Each run needs a fresh profile
path. Keep all screenshots and `assets/tour/manifest.json` together, then rebuild
and run tests. The build verifies PNG dimensions, chapter order and highlight
bounds and fails rather than publishing missing or invalid recordings.

## Build and preview

Python **3.12 or newer** is the only build requirement. No packages to install.

```powershell
python build.py
python -m unittest discover -s tests -v
python -m http.server 8000 --bind 127.0.0.1 --directory _site
```

Open <http://127.0.0.1:8000>. Stop the preview with Ctrl+C. `_site` is generated
and ignored by Git. All published paths are relative, including assets and
language links, so the site works under GitHub's `/ydke-site/` project path.

For a different public URL:

```powershell
python build.py --site-url https://example.com
```

This updates canonical links, language alternates, localized social-sharing
metadata, Schema.org structured data (`SoftwareApplication`, `WebSite`, `HowTo`,
`FAQPage`, `WebPage` and `BreadcrumbList`), the multilingual/image sitemap and
robots file. Homepage canonicals use directory URLs (for example, `/` and `/en/`) to
avoid duplicate `index.html` addresses. For a custom domain, configure that
domain in GitHub Pages and update the build command in the workflow accordingly.

## Publish to GitHub Pages

1. Push this repository to `bulentozkir/ydke-site` on the `main` branch.
2. In **Settings → Pages → Build and deployment**, choose **GitHub Actions**.
3. Run **Actions → Deploy GitHub Pages → Run workflow**, or push to `main`.
4. After deployment succeeds, visit
   <https://bulentozkir.github.io/ydke-site/>.

The workflow tests and builds the site before uploading only `_site` as a Pages
artifact. Build output is not checked in. Creating these files does not itself
enable Pages or publish the website.

## Updating content

Edit [content.json](content.json) for translations,
[build.py](build.py) for templates, and [assets/site.css](assets/site.css)
for styling. Every language must have the same keys and list lengths; the build
fails explicitly for incomplete translations. Update all languages together when
product behavior or legal terms change.

The localized legal pages are informational summaries of the app's existing
**PolyForm Noncommercial License 1.0.0**, not newly invented licenses or binding
translations. Commercial use requires prior written permission under the
app's additional terms. They link to the authoritative app license and notices;
third-party Wiktionary and Tatoeba content retains its own licenses. This website
does not grant a separate license over the app or third-party content.

The license contact comes from the app's existing public license; support does
not promise a response time. GitHub issue submissions are public and the support
pages advise visitors not to upload personal information or private backups.
Review legal summaries, contact details and download availability before
publishing, especially when updating the app.
