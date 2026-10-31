# Ponomar Library website builder

These scripts turn the Markdown books in this repository into the
[Ponomar Library of Liturgical Texts](https://www.ponomar.net/maktabah/): a static,
bilingual (English / Russian), mobile-friendly website. They replace `bookbuild.pl`.

```
scripts/
  build_library.py   build the whole site (or some books)
  cumd_web.py        Markdown → HTML: the cumd rules + page links, notes, images
  library.toml       catalogue: English titles, front-page sections, PDF scans
  i18n.py            interface strings in English and Russian
  prepare_pdf.py     download DJVU/PDF scans, convert, linearize for the web
  templates/         Jinja2 page templates
  static/            CSS, JavaScript, interface font (copied to assets/)
  tests/             pytest tests for the converter
  ci/build-site.yml  GitHub Actions workflow (move to .github/workflows/ to use)
```

## Build

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/build_library.py --fetch-pdfjs      # → _site/
python -m http.server -d _site 8000                 # → http://localhost:8000
```

* `python scripts/build_library.py Chasoslov1991 Tipikon` rebuilds only those books
  (the front page is always rebuilt).
* `--out DIR` chooses the output folder (default `_site/`).
* `--fetch-pdfjs` downloads the pdf.js viewer once into `OUT/pdfjs/`; later builds keep it.
* `--pdf-url URL` is where the scans are served (default `pdf`, i.e. `OUT/pdf/`).
  pdf.js only opens PDFs from the same server as the page, so keep them on ponomar.net.
* `--pdf-dir DIR` points at the local copy of the scans; volumes whose file is missing
  there get no page links, so readers never meet a broken scan.
* `--fonts-css URL` (default `https://sci.ponomar.net/css/fonts.css`), or
  `--fonts-dir DIR` to self-host a folder of `*.woff2` files instead.
* `--base-url https://www.ponomar.net/maktabah/` also writes `sitemap.xml`.

At the end the build lists things to fix in the sources (unrecognized page tags,
indented lines that Markdown shows as code, doubled `==`, images that are not in the
repository, chapter files missing from `manifest.xml`).

## What the converter does

All rules of [`cumd`](https://github.com/slavonic/cumd) are used as they are (`~`, `=…=`,
`+…+`, `^`, `((…))`, `{{…}}`), in its “simplified” mode, which writes ordinary
`<span class="red">` etc., so text copied from the site keeps its kinovar in Word.
`cumd_web.py` adds:

| Markdown | HTML |
|---|---|
| `<<25>>` | link to page 25 of the scan, shown as a small “25” in the margin |
| `<<а҃ ѡ҆б.: 2>>` | link to page 2, shown as “а҃ ѡ҆б.” |
| `<<а҃>>` (no Arabic number) | shown, not linked |
| `[[Ѱ. ѳ҃і]]` | a numbered footnote (tap for a popup) |
| `{{text_align=center}}` | `style="text-align:center"` (kept when pasting into Word) |
| `{{liturgical=u/can/1/9/ex tone=8}}` | `data-liturgical="…" data-tone="8"` |
| `[!image](../media/1.png)` | an image, copied into the book’s `media/` folder |

The page-number label is drawn by CSS from a `data-l` attribute, so the `<<…>>` tags
never show in the text and page numbers are not picked up when the reader copies text.
`<<…>>` tags were also not converted at all by the old pipeline for Cyrillic-paginated
books (cumd expects the number first); they now are.

## Page scans (PDF)

1. List each volume in `library.toml` (most books already are, with their minei.ru source).
2. Produce web-ready PDFs on the server, once:
   ```bash
   sudo apt install djvulibre-bin qpdf
   python scripts/prepare_pdf.py --out /var/www/ponomar/maktabah/pdf
   python scripts/prepare_pdf.py --out /var/www/ponomar/maktabah/pdf --check
   ```
   The PDFs are *linearized*: with the web server’s normal range-request support, pdf.js
   fetches only the pages being looked at, so a 900-page Triodion opens at page 600 at once.
3. Set each volume’s `offset` (PDF page index − printed page number). Open any section,
   click a page number, and compare. Multi-volume books use `from_chapter` to say which
   sections belong to the second PDF.

**If the viewer stays blank:** pdf.js is made of `.mjs` modules, and browsers refuse them
unless the server sends `Content-Type: text/javascript`. Many servers don't know `.mjs`.
The build writes `pdfjs/.htaccess` for Apache (needs `AllowOverride FileInfo`). For nginx add to
`mime.types` (or the server block): `types { text/javascript mjs; }`. Check with
`curl -I https://your.site/maktabah/pdfjs/build/pdf.mjs`. The page now says so after 8 seconds
and offers the PDF itself instead of staying empty. Also make sure the server does not send
`X-Frame-Options: DENY` (use `SAMEORIGIN`), because the viewer runs in an iframe.

On wide screens a page number opens the scan beside the text; on phones (or with
Ctrl/⌘-click) it opens the full-screen viewer, which has a “Show this page in the text”
button that leads back to the matching section.

## Adding a book

Add the folder with `manifest.xml`, `chapters/*.md` and `cover.png` as before. It appears
under “Other books” until you give it an entry in `library.toml` (English title, section).

## Old links

The old site used `<latin><year>` folders (`MineyaFebvral1996`, `MineyaIyul1996`,
`AugmentedPsalter21993`…). The build writes small redirect pages under those names, so
existing links and bookmarks keep working.

## Automatic builds

`ci/build-site.yml` builds and tests the site on every push to `master` and, when the
`DEPLOY_*` secrets are set, rsyncs it to the server (leaving `pdf/` alone). Move it to
`.github/workflows/` to switch it on.
