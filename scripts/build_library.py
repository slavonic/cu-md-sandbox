#!/usr/bin/env python3
"""
Build the Ponomar Library of Liturgical Texts (static website) from this repository.

Replaces bookbuild.pl: one command builds every book (or the ones you name),
the front page, the scan viewer and the legacy-URL redirects.

    python scripts/build_library.py                       # all books → _site/
    python scripts/build_library.py Chasoslov1991 Tipikon # only these books
    python scripts/build_library.py --fetch-pdfjs         # also install the pdf.js viewer
    python scripts/build_library.py --help

The Markdown → HTML rules are those of the ``cumd`` package (see cumd_web.py for
the additions: page links to the scans, [[notes]], images).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cumd_web  # noqa: E402
import i18n  # noqa: E402

log = logging.getLogger("maktabah")

PDFJS_VERSION = "5.4.624"
PDFJS_URL = "https://github.com/mozilla/pdf.js/releases/download/v{v}/pdfjs-{v}-dist.zip"
DEFAULT_FONTS_CSS = "https://sci.ponomar.net/css/fonts.css"

# Typefaces offered in the reader (CSS family names as published on sci.ponomar.net).
# Only faces suited to Synodal-style Slavonic; the first one is the default.
TYPEFACES = [
    ("Triodion", "Triodion"),
    ("Ponomar", "Ponomar"),
    ("Pochaevsk", "Pochaevsk"),
    ("Monomakh", "Monomakh"),
]


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

@dataclass
class Volume:
    index: int
    file: str
    offset: int = 0
    from_chapter: Optional[str] = None
    label_en: str = ""
    label_ru: str = ""
    source: str = ""


@dataclass
class Chapter:
    index: int
    file: str
    name: str
    html: str = ""
    headings: list = field(default_factory=list)
    first_page: Optional[int] = None
    last_page: Optional[int] = None
    first_label: str = ""
    last_label: str = ""
    volume: Optional[int] = None

    @property
    def href(self):
        return self.file + ".html"


@dataclass
class Book:
    id: str
    path: Path
    title_ru: str
    title_en: str
    edition_ru: str
    edition_en: str
    year: str
    note: str
    latin: str
    category: str
    order: int
    chapters: List[Chapter] = field(default_factory=list)
    volumes: List[Volume] = field(default_factory=list)
    cover: Optional[str] = None       # path relative to the book folder in the site
    cover_small: Optional[str] = None

    def volume_for(self, chapter_index: int) -> Optional[Volume]:
        vol = None
        positions = {c.file: c.index for c in self.chapters}
        for v in self.volumes:
            start = positions.get(v.from_chapter, 0) if v.from_chapter else 0
            if chapter_index >= start:
                vol = v
        return vol

    @property
    def legacy_slug(self):
        slug = f"{self.latin}{self.year}"
        return slug if slug and slug != self.id and self.latin else None


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load_config(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def read_manifest(path: Path):
    root = ET.parse(path).getroot()
    meta = {m.get("name"): (m.get("content") or "").strip() for m in root.iter("meta")}
    chapters = []
    for c in root.iter("chapter"):
        f = re.sub(r"\.(xml|md)$", "", (c.get("file") or "").strip())
        if f:
            chapters.append((f, (c.get("name") or f).strip()))
    return meta, chapters


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def discover_books(repo: Path, config: dict, only: List[str]) -> List[Book]:
    book_cfg = config.get("books", {})
    order = {k: i for i, k in enumerate(book_cfg)}
    books = []
    for manifest in sorted(repo.glob("*/manifest.xml")):
        bid = manifest.parent.name
        if only and bid not in only:
            continue
        meta, chapters = read_manifest(manifest)
        cfg = book_cfg.get(bid, {})
        publisher, year = clean(meta.get("publisher", "")), clean(meta.get("year", ""))
        edition = ", ".join(x for x in (publisher if publisher.lower() != "unknown" else "", year) if x)
        b = Book(
            id=bid,
            path=manifest.parent,
            title_ru=cfg.get("title_ru") or clean(meta.get("title", bid)),
            title_en=cfg.get("title_en") or clean(meta.get("title", bid)),
            edition_ru=cfg.get("edition_ru") or edition,
            edition_en=cfg.get("edition_en") or cfg.get("edition_ru") or edition,
            year=year,
            note=clean(meta.get("note", "")),
            latin=clean(meta.get("latin", "")),
            category=cfg.get("category", "other"),
            order=order.get(bid, 10_000),
        )
        for i, (f, name) in enumerate(chapters):
            b.chapters.append(Chapter(index=i, file=f, name=clean(name)))
        for i, v in enumerate(cfg.get("pdf", [])):
            b.volumes.append(Volume(index=i, file=v["file"], offset=int(v.get("offset", 0)),
                                    from_chapter=v.get("from_chapter"),
                                    label_en=v.get("label_en", ""), label_ru=v.get("label_ru", ""),
                                    source=v.get("source", "")))
        books.append(b)
    books.sort(key=lambda b: (b.order, b.id))
    return books


# --------------------------------------------------------------------------- #
# Building
# --------------------------------------------------------------------------- #

class Report:
    def __init__(self):
        self.items: Dict[str, List[str]] = {}

    def add(self, kind, msg):
        self.items.setdefault(kind, []).append(msg)

    def print(self):
        if not self.items:
            print("No problems found in the source files.")
            return
        print("\nThings to check:")
        for kind, msgs in self.items.items():
            print(f"  {kind} ({len(msgs)})")
            for m in msgs[:12]:
                print(f"    - {m}")
            if len(msgs) > 12:
                print(f"    … and {len(msgs) - 12} more")


def t(key, **kw):
    """Jinja helper: the interface string in every language, CSS shows one."""
    parts = []
    for i, lang in enumerate(i18n.LANGS):
        s = i18n.STRINGS[key][i]
        if kw:
            s = s.format(**kw)
        parts.append(f'<span class="l10n" lang="{lang}">{escape(s)}</span>')
    return Markup("".join(parts))


def both(en, ru):
    """Jinja helper for data with an English and a Russian value."""
    if en == ru:
        return escape(en)
    return Markup(f'<span class="l10n" lang="en">{escape(en)}</span><span class="l10n" lang="ru">{escape(ru)}</span>')


class SiteBuilder:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.repo: Path = args.repo
        self.out: Path = args.out
        self.report = Report()
        self.env = Environment(
            loader=FileSystemLoader(str(HERE / "templates")),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True, lstrip_blocks=True,
        )
        self.env.globals.update(t=t, both=both, en=lambda k: i18n.STRINGS[k][0], site=config.get("site", {}),
                                typefaces=TYPEFACES, langs=i18n.LANGS)
        self.asset_version = ""
        self.build_id = time.strftime("%Y%m%d%H%M")

    # ---- helpers -------------------------------------------------------- #

    def write(self, rel: str, text: str):
        p = self.out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def render(self, template, rel, **ctx):
        depth = rel.count("/")
        ctx.setdefault("root", "../" * depth)
        ctx["v"] = self.asset_version
        ctx["build_id"] = self.build_id
        ctx["fonts_css"] = self.fonts_css(ctx["root"])
        self.write(rel, self.env.get_template(template).render(**ctx))

    def fonts_css(self, root):
        if self.args.fonts_dir:
            return root + "assets/fonts/fonts.css"
        return self.args.fonts_css

    # ---- static assets -------------------------------------------------- #

    def copy_assets(self):
        dst = self.out / "assets"
        dst.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1()
        for f in sorted((HERE / "static").rglob("*")):
            if f.is_file():
                rel = f.relative_to(HERE / "static")
                (dst / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst / rel)
                digest.update(f.read_bytes())
        self.asset_version = digest.hexdigest()[:8]
        if self.args.fonts_dir:
            self.copy_fonts(Path(self.args.fonts_dir), dst / "fonts")

    def copy_fonts(self, src: Path, dst: Path):
        dst.mkdir(parents=True, exist_ok=True)
        rules = []
        for f in sorted(src.rglob("*.woff2")):
            m = re.match(r"(.+?)-(Regular|Bold|Italic|BoldItalic)$", f.stem)
            family, style = (m.group(1), m.group(2)) if m else (f.stem, "Regular")
            if family.endswith("Unicode"):
                family = family[: -len("Unicode")] + " Unicode"
            shutil.copy2(f, dst / f.name)
            rules.append(
                "@font-face{font-family:'%s';src:url('%s') format('woff2');font-weight:%s;font-style:%s;font-display:swap}"
                % (family, f.name, 700 if "Bold" in style else 400, "italic" if "Italic" in style else "normal"))
        (dst / "fonts.css").write_text("\n".join(rules) + "\n", encoding="utf-8")
        print(f"Self-hosted {len(rules)} font files from {src}")

    def install_pdfjs(self):
        target = self.out / "pdfjs"
        if self.args.pdfjs_dir:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(self.args.pdfjs_dir, target,
                            ignore=shutil.ignore_patterns("*.map", "compressed.tracemonkey-pldi-09.pdf"))
            return
        if not self.args.fetch_pdfjs:
            if not (target / "web" / "viewer.html").exists():
                log.warning("pdf.js is not installed in %s; run with --fetch-pdfjs once", target)
            return
        if (target / "web" / "viewer.html").exists() and (target / ".version").exists() \
                and (target / ".version").read_text().strip() == PDFJS_VERSION:
            return
        cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "maktabah"
        cache.mkdir(parents=True, exist_ok=True)
        zpath = cache / f"pdfjs-{PDFJS_VERSION}-dist.zip"
        if not zpath.exists():
            url = PDFJS_URL.format(v=PDFJS_VERSION)
            print(f"Downloading {url}")
            with urllib.request.urlopen(url) as r:
                zpath.write_bytes(r.read())
        if target.exists():
            shutil.rmtree(target)
        with zipfile.ZipFile(zpath) as z:
            for n in z.namelist():
                if n.endswith(".map") or n.endswith("compressed.tracemonkey-pldi-09.pdf"):
                    continue
                z.extract(n, target)
        (target / ".version").write_text(PDFJS_VERSION)
        print(f"Installed pdf.js {PDFJS_VERSION} in {target}")

    # ---- books ---------------------------------------------------------- #

    def pdf_url(self, book: Book, vol: Volume) -> str:
        return self.args.pdf_url.rstrip("/") + "/" + vol.file

    def check_volumes(self, book: Book):
        if not self.args.pdf_dir:
            return
        keep = []
        for v in book.volumes:
            if (Path(self.args.pdf_dir) / v.file).exists():
                keep.append(v)
            else:
                self.report.add("PDF files not found (links disabled)", f"{book.id}: {v.file}")
        for i, v in enumerate(keep):
            v.index = i
        book.volumes = keep

    def copy_cover(self, book: Book):
        src = book.path / "cover.png"
        if not src.exists():
            return
        dst_dir = self.out / book.id
        dst_dir.mkdir(parents=True, exist_ok=True)
        try:
            from PIL import Image  # optional
            with Image.open(src) as im:
                im = im.convert("RGB")
                w, h = im.size
                for name, width in (("cover.jpg", 640), ("cover-sm.jpg", 300)):
                    out = im if w <= width else im.resize((width, round(h * width / w)), Image.LANCZOS)
                    out.save(dst_dir / name, "JPEG", quality=82, optimize=True, progressive=True)
            book.cover, book.cover_small = "cover.jpg", "cover-sm.jpg"
        except ImportError:
            shutil.copy2(src, dst_dir / "cover.png")
            book.cover = book.cover_small = "cover.png"

    def build_book(self, book: Book):
        self.check_volumes(book)
        self.copy_cover(book)
        chapters_dir = book.path / "chapters"
        listed = {c.file for c in book.chapters}
        for f in sorted(chapters_dir.glob("*.md")):
            if f.stem not in listed:
                self.report.add("chapter files not in manifest.xml (skipped)", f"{book.id}/chapters/{f.name}")

        current: dict = {}

        def page_href(page, label):
            vol = current.get("vol")
            if vol is None:
                return None
            q = {"b": book.id, "p": page}
            if vol.index:
                q["v"] = vol.index
            if label != str(page):
                q["l"] = label
            return "../scan.html?" + urllib.parse.urlencode(q)

        def image_resolver(src):
            if re.match(r"^[a-z]+:", src):
                return src
            path = (chapters_dir / urllib.parse.unquote(src)).resolve()
            try:
                rel = path.relative_to(book.path.resolve())
            except ValueError:
                rel = Path("media") / path.name
            if not path.exists():
                self.report.add("missing images (dropped)", f"{book.id}/{current['ch'].file}: {src}")
                return None
            if rel.parts[0] != "media":
                rel = Path("media") / rel
            dst = self.out / book.id / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
            return rel.as_posix()

        conv = cumd_web.Converter(page_href=page_href, image_resolver=image_resolver)
        for ch in book.chapters:
            src = chapters_dir / (ch.file + ".md")
            current["ch"] = ch
            vol = book.volume_for(ch.index)
            current["vol"] = vol
            ch.volume = vol.index if vol else None
            if not src.exists():
                self.report.add("chapters listed in manifest.xml but missing", f"{book.id}: {ch.file}.md")
                ch.html = ""
                continue
            text = src.read_text(encoding="utf-8")
            ch.html, info = conv.convert(text)
            ch.headings = info.headings
            if info.pages:
                ch.first_page, ch.last_page = info.pages[0], info.pages[-1]
                labels = re.findall(r'data-l="([^"]*)"', ch.html)
                pl = [l for l in labels]
                ch.first_label = pl[0] if pl else str(ch.first_page)
                ch.last_label = pl[-1] if pl else str(ch.last_page)
            self.lint(book, ch)
        book.chapters = [c for c in book.chapters if c.html]

        for i, ch in enumerate(book.chapters):
            prev = book.chapters[i - 1] if i > 0 else None
            nxt = book.chapters[i + 1] if i + 1 < len(book.chapters) else None
            self.render("chapter.html", f"{book.id}/{ch.href}", book=book, chapter=ch,
                        prev=prev, next=nxt, page_type="chapter")
        self.render("book.html", f"{book.id}/index.html", book=book, page_type="book",
                    has_ranges=any(c.first_page for c in book.chapters))
        if book.legacy_slug:
            self.write_redirects(book)

    def lint(self, book, ch):
        where = f"{book.id}/{ch.file}.md"
        if "&lt;&lt;" in ch.html:
            self.report.add("page tags that were not recognized", where)
        if "<pre><code>" in ch.html:
            self.report.add("indented lines shown as code (remove the leading spaces)", where)
        if re.search(r">\s*==|==\s*<", ch.html):
            self.report.add("doubled '==' kinovar markers", where)

    def write_redirects(self, book: Book):
        """Keep links to the old site (…/maktabah/<latin><year>/…) working."""
        slug = book.legacy_slug
        tpl = ('<!DOCTYPE html><html><head><meta charset="utf-8"><title>{t}</title>'
               '<link rel="canonical" href="{u}"><meta http-equiv="refresh" content="0; url={u}">'
               '<script>location.replace("{u}"+location.hash)</script></head>'
               '<body><a href="{u}">{t}</a></body></html>')
        self.write(f"{slug}/index.html", tpl.format(t=escape(book.title_ru), u=f"../{book.id}/index.html"))
        for ch in book.chapters:
            self.write(f"{slug}/{ch.href}", tpl.format(t=escape(ch.name), u=f"../{book.id}/{ch.href}"))

    # ---- library data for JavaScript ----------------------------------- #

    def library_data(self, books: List[Book]) -> dict:
        cats = self.categories(books)
        data = {
            "site": self.config.get("site", {}),
            "pdfjs": "pdfjs/web/viewer.html",
            "categories": [{"id": c["id"], "en": c["en"], "ru": c["ru"]} for c in cats],
            "books": [],
            "i18n": i18n.table(),
            "typefaces": [f for f, _ in TYPEFACES],
        }
        for b in books:
            data["books"].append({
                "id": b.id,
                "title": {"en": b.title_en, "ru": b.title_ru},
                "edition": {"en": b.edition_en, "ru": b.edition_ru},
                "cat": b.category,
                "first": b.chapters[0].href if b.chapters else None,
                "pdf": [{"url": self.pdf_url(b, v), "offset": v.offset,
                         "label": {"en": v.label_en or f"Volume {v.index + 1}", "ru": v.label_ru or f"Том {v.index + 1}"}}
                        for v in b.volumes],
                "ranges": [[c.href, c.first_page, c.last_page, c.volume] for c in b.chapters if c.first_page],
            })
        return data

    def categories(self, books: List[Book]):
        cats = list(self.config.get("categories", []))
        known = {c["id"] for c in cats}
        for b in books:
            if b.category not in known:
                cats.append({"id": b.category, "en": b.category, "ru": b.category})
                known.add(b.category)
        result = []
        for c in cats:
            members = [b for b in books if b.category == c["id"]]
            if members:
                result.append(dict(c, books=members))
        return result

    # ---- main ----------------------------------------------------------- #

    def run(self, only: List[str]):
        t0 = time.time()
        all_books = discover_books(self.repo, self.config, [])
        books = [b for b in all_books if not only or b.id in only]
        if only and len(books) != len(set(only)):
            missing = set(only) - {b.id for b in books}
            sys.exit(f"Unknown book folder(s): {', '.join(sorted(missing))}")
        self.out.mkdir(parents=True, exist_ok=True)
        self.copy_assets()
        self.install_pdfjs()
        for b in books:
            n0 = time.time()
            self.build_book(b)
            print(f"  {b.id:28} {len(b.chapters):3} sections  {time.time() - n0:5.1f}s")
        if only:
            # keep the library page complete: read chapter lists of the other books quickly
            for b in all_books:
                if b not in books:
                    self.check_volumes(b)
                    b.cover = "cover.jpg" if (self.out / b.id / "cover.jpg").exists() else (
                        "cover.png" if (self.out / b.id / "cover.png").exists() else None)
                    b.cover_small = "cover-sm.jpg" if (self.out / b.id / "cover-sm.jpg").exists() else b.cover
            books_for_index = [next((x for x in books if x.id == b.id), b) for b in all_books]
        else:
            books_for_index = books
        data = self.library_data(books_for_index)
        self.write("assets/library.js", "window.MAKTABAH = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
        self.render("index.html", "index.html", categories=self.categories(books_for_index),
                    books=books_for_index, page_type="library")
        self.render("scan.html", "scan.html", page_type="scan")
        if self.args.base_url:
            self.write_sitemap(books_for_index)
        print(f"Built {len(books)} book(s) into {self.out} in {time.time() - t0:.1f}s")
        self.report.print()

    def write_sitemap(self, books):
        base = self.args.base_url.rstrip("/") + "/"
        urls = [base] + [f"{base}{b.id}/" for b in books] + [f"{base}{b.id}/{c.href}" for b in books for c in b.chapters]
        body = "".join(f"<url><loc>{escape(u)}</loc></url>" for u in urls)
        self.write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("books", nargs="*", help="book folders to build (default: all)")
    p.add_argument("--repo", type=Path, default=HERE.parent, help="repository root (default: %(default)s)")
    p.add_argument("--out", type=Path, default=HERE.parent / "_site", help="output folder (default: %(default)s)")
    p.add_argument("--config", type=Path, default=HERE / "library.toml", help="catalogue file")
    p.add_argument("--pdf-url", default="pdf", help="URL of the folder with the PDF scans, relative to the site root "
                                                    "or absolute on the same server (default: %(default)s)")
    p.add_argument("--pdf-dir", help="local folder with the PDF scans; volumes whose file is missing there get no links")
    p.add_argument("--fetch-pdfjs", action="store_true", help=f"download pdf.js {PDFJS_VERSION} into OUT/pdfjs")
    p.add_argument("--pdfjs-dir", help="copy an already unpacked pdf.js viewer instead of downloading it")
    p.add_argument("--fonts-css", default=DEFAULT_FONTS_CSS, help="stylesheet with the Church Slavonic fonts")
    p.add_argument("--fonts-dir", help="self-host the fonts: folder with *.woff2 files (overrides --fonts-css)")
    p.add_argument("--base-url", help="public URL of the site, e.g. https://www.ponomar.net/maktabah/ (writes sitemap.xml)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s: %(message)s")
    SiteBuilder(args, load_config(args.config)).run(args.books)


if __name__ == "__main__":
    main()
