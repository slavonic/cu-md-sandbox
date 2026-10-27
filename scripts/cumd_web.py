"""
cumd_web — web-publishing layer on top of the ``cumd`` Church Slavonic Markdown dialect.

The rendering rules of ``cumd`` (red letters ``~``, kinovar ``=…=``, wide ``+…+``,
bukvitsa ``^``, verse labels ``((…))`` and block attributes ``{{key=value}}``) are
reused unchanged from the ``cumd`` package, in its "simplified" mode, which emits
standard ``<span class="…">`` elements that copy-paste cleanly into word processors.

This module adds what a public reading site needs:

* **Page anchors become links to the scan.**  ``<<25>>`` links to page 25 of the
  book's PDF; ``<<а҃ ѡ҆б.: 2>>`` links to page 2 but is displayed as "а҃ ѡ҆б.".
  The older ``cumd`` order ``<<2: label>>`` is also understood.  The marker itself
  is an empty ``<a class="pg">`` whose visible label is drawn by CSS
  (``content: attr(data-l)``), so the tags never appear in the text and are not
  picked up when the reader copies text.
* ``[[note text]]`` (the cumd footnote markup) becomes a real footnote, rendered
  exactly like Markdown ``[^1]`` footnotes.
* ``{{text_align=center}}`` becomes ``style="text-align:center"`` (survives
  pasting into Word); other attributes such as ``liturgical``/``tone`` become
  ``data-*`` attributes.
* ``[!image](path)`` (as written by ``cuxml``) is treated as an image; images are
  resolved through a callback so the site builder can copy them or drop missing ones.
* Headings get stable ids, and the list of headings and page numbers is exposed
  for building navigation.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as et
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import markdown
from markdown.extensions import Extension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.inlinepatterns import InlineProcessor
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor

from cumd.cumd import RedBukvaExtension

log = logging.getLogger("cumd_web")

#: callable(page_number, label) -> href or None (None = page has no scan to link to)
PageHref = Callable[[int, str], Optional[str]]
#: callable(src) -> new src or None (None = drop the image)
ImageResolver = Callable[[str], Optional[str]]


# --------------------------------------------------------------------------- #
# Page anchors
# --------------------------------------------------------------------------- #

RE_PAGE_ANCHOR = r"<<\s*([^<>]+?)\s*>>"


def parse_page_anchor(inner: str) -> Tuple[Optional[int], str]:
    """Parse the inside of ``<<…>>``.

    Returns ``(page_number, display_label)``.  ``page_number`` is ``None`` when the
    anchor carries no Arabic page number (then it is shown but not linked).

    >>> parse_page_anchor('25')
    (25, '25')
    >>> parse_page_anchor('а҃ ѡ҆б.: 2')
    (2, 'а҃ ѡ҆б.')
    >>> parse_page_anchor('2: л. 1 об.')   # legacy cumd order
    (2, 'л. 1 об.')
    """
    inner = inner.strip()
    if ":" in inner:
        left, right = (s.strip() for s in inner.rsplit(":", 1))
        if right.isdigit() and right.isascii():
            return int(right), left or right
        left2, right2 = (s.strip() for s in inner.split(":", 1))
        if left2.isdigit() and left2.isascii():
            return int(left2), right2 or left2
        return None, inner
    if inner.isdigit() and inner.isascii():
        return int(inner), inner
    return None, inner


class PageAnchorPattern(InlineProcessor):
    """``<<25>>`` / ``<<label: 25>>`` → ``<a class="pg" href=… data-p=25 data-l=label>``."""

    def __init__(self, ext: "CuWebExtension"):
        super().__init__(RE_PAGE_ANCHOR)
        self.ext = ext

    def handleMatch(self, m, data):
        page, label = parse_page_anchor(m.group(1))
        href = self.ext.page_href(page, label) if (page is not None and self.ext.page_href) else None
        el = et.Element("a" if href else "span", {"class": "pg"})
        if href:
            el.set("href", href)
        if page is not None:
            el.set("data-p", str(page))
        el.set("data-l", label)
        return el, m.start(0), m.end(0)


# --------------------------------------------------------------------------- #
# Preprocessing: [[notes]] and [!image](…)
# --------------------------------------------------------------------------- #

RE_CU_NOTE = re.compile(r"\[\[(.+?)\]\]", re.S)
RE_CUXML_IMAGE = re.compile(r"(?<!!)\[!image\]\(")


class CuNotesPreprocessor(Preprocessor):
    """Rewrite ``[[text]]`` into Markdown footnotes and fix ``[!image](…)``."""

    def run(self, lines):
        text = "\n".join(lines)
        text = RE_CUXML_IMAGE.sub("![](", text)
        notes: List[str] = []

        def sub(m):
            notes.append(re.sub(r"\s+", " ", m.group(1)).strip())
            return "[^cu%d]" % len(notes)

        text = RE_CU_NOTE.sub(sub, text)
        if notes:
            text += "\n\n" + "\n\n".join("[^cu%d]: %s" % (i + 1, n) for i, n in enumerate(notes)) + "\n"
        return text.split("\n")


# --------------------------------------------------------------------------- #
# Block attributes {{key=value, key=value}}
# --------------------------------------------------------------------------- #

RE_BLOCK_ATTR = re.compile(r"\n?{{(.*?)}}\n?")
SAFE_ATTR = re.compile(r"[^a-z0-9_-]+")


class BlockAttributeProcessor(Treeprocessor):
    """Same syntax as ``cumd`` but emits valid, paste-friendly HTML.

    ``text_align`` → inline ``style`` (Word keeps inline styles on paste) plus the
    ``align-*`` class; every other key → ``data-<key>``.  Expressions may be
    separated by commas (cumd) or spaces (as used in the sandbox markup).
    A bare value without ``=`` (e.g. ``{{u/50ps}}``) is kept as ``data-liturgical``.
    """

    def run(self, root):
        for block in root.iter():
            if block.text and "{{" in block.text:
                block.text = RE_BLOCK_ATTR.sub(lambda m: self._apply(block, m.group(1)), block.text)

    def _apply(self, block, expr):
        for e in re.split(r"[,\s]+", expr.strip()):
            if not e:
                continue
            if "=" not in e:
                block.set("data-liturgical", e)
                continue
            key, value = e.split("=", 1)
            key = SAFE_ATTR.sub("-", key.strip().lower()).strip("-")
            value = value.strip()
            if not key:
                log.warning("Could not parse block attribute %r", e)
            elif key in ("text_align", "text-align"):
                if value in ("center", "right", "left", "justify"):
                    block.set("style", "text-align:%s" % value)
                    _add_class(block, "align-" + value)
            else:
                block.set("data-" + key.replace("_", "-"), value)
        return ""


def _add_class(el, cls):
    classes = el.get("class", "").split()
    if cls not in classes:
        classes.append(cls)
    el.set("class", " ".join(classes))


# --------------------------------------------------------------------------- #
# Post-processing: lone page markers, heading ids, images, collected metadata
# --------------------------------------------------------------------------- #

@dataclass
class Heading:
    id: str
    level: int
    text: str


@dataclass
class ChapterInfo:
    headings: List[Heading] = field(default_factory=list)
    pages: List[int] = field(default_factory=list)


class FinishProcessor(Treeprocessor):
    def __init__(self, md, ext):
        super().__init__(md)
        self.ext = ext

    def run(self, root):
        info = self.ext.info
        # cumd emits <verse label="…"/>; show the label as a small rubric instead
        for v in root.iter("verse"):
            v.tag = "span"
            v.text = v.attrib.pop("label", "")
            v.set("class", "verse")
        parent = {c: p for p in root.iter() for c in p}

        # 1. a paragraph holding nothing but a page marker: move the marker into
        #    the start of the following block so it does not leave an empty line.
        blocks = list(root)
        for i, b in enumerate(blocks):
            if (b.tag == "p" and not (b.text or "").strip() and len(b) == 1
                    and _is_pg(b[0]) and not (b[0].tail or "").strip()
                    and i + 1 < len(blocks) and blocks[i + 1].tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6")):
                marker, nxt = b[0], blocks[i + 1]
                b.remove(marker)
                marker.tail = nxt.text
                nxt.text = None
                nxt.insert(0, marker)
                root.remove(b)
                parent[marker] = nxt

        # 2. ids for page markers (first occurrence) and headings
        seen = set()
        n_head = 0
        for el in root.iter():
            if _is_pg(el) and el.get("data-p"):
                p = int(el.get("data-p"))
                info.pages.append(p)
                if p not in seen:
                    seen.add(p)
                    el.set("id", "p%d" % p)
            elif el.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                n_head += 1
                hid = "s%d" % n_head
                el.set("id", hid)
                text = re.sub(r"\s+", " ", "".join(el.itertext())).strip()
                info.headings.append(Heading(hid, int(el.tag[1]), text))

        # 3. images
        for img in [e for e in root.iter("img")]:
            src = img.get("src", "")
            new = self.ext.image_resolver(src) if self.ext.image_resolver else src
            if new:
                img.set("src", new)
                img.set("loading", "lazy")
                if not img.get("alt"):
                    img.set("alt", "")
            else:
                _remove_keep_tail(img, parent)


def _is_pg(el):
    return "pg" in el.get("class", "").split()


def _remove_keep_tail(el, parent):
    p = parent.get(el)
    if p is None:
        return
    tail = el.tail or ""
    idx = list(p).index(el)
    if idx == 0:
        p.text = (p.text or "") + tail
    else:
        prev = p[idx - 1]
        prev.tail = (prev.tail or "") + tail
    p.remove(el)


# --------------------------------------------------------------------------- #
# Extension and convenience API
# --------------------------------------------------------------------------- #

class CuWebExtension(Extension):
    def __init__(self, page_href: Optional[PageHref] = None, image_resolver: Optional[ImageResolver] = None):
        super().__init__()
        self.page_href = page_href
        self.image_resolver = image_resolver
        self.info = ChapterInfo()

    def reset(self):
        self.info = ChapterInfo()

    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.preprocessors.register(CuNotesPreprocessor(md), "cu_notes", 27)
        # same names as in cumd → these replace cumd's processors
        md.inlinePatterns.register(PageAnchorPattern(self), "pageBreak", 106)
        md.treeprocessors.register(BlockAttributeProcessor(md), "blockAttr", 100)
        md.treeprocessors.register(FinishProcessor(md, self), "cu_finish", 4)


def make_markdown(page_href: Optional[PageHref] = None,
                  image_resolver: Optional[ImageResolver] = None) -> Tuple[markdown.Markdown, CuWebExtension]:
    ext = CuWebExtension(page_href=page_href, image_resolver=image_resolver)
    fn_config = {"SEPARATOR": "-", "BACKLINK_TEXT": "↩", "BACKLINK_TITLE": "↩ {}"}
    if "USE_DEFINITION_ORDER" in FootnoteExtension().config:  # Python-Markdown >= 3.8
        fn_config["USE_DEFINITION_ORDER"] = False  # number notes in reading order
    md = markdown.Markdown(
        extensions=[
            RedBukvaExtension(simplified=True),
            FootnoteExtension(**fn_config),
            ext,
        ],
        output_format="html5",
    )
    return md, ext


def convert(text: str, page_href: Optional[PageHref] = None,
            image_resolver: Optional[ImageResolver] = None) -> Tuple[str, ChapterInfo]:
    """Convert one chapter of cu-Markdown to an HTML fragment."""
    md, ext = make_markdown(page_href, image_resolver)
    html = md.convert(text)
    return html, ext.info


class Converter:
    """Reusable converter (one Markdown instance per book is much faster)."""

    def __init__(self, page_href: Optional[PageHref] = None, image_resolver: Optional[ImageResolver] = None):
        self.md, self.ext = make_markdown(page_href, image_resolver)

    def convert(self, text: str) -> Tuple[str, ChapterInfo]:
        self.md.reset()
        html = self.md.convert(text)
        return html, self.ext.info


if __name__ == "__main__":  # tiny CLI for spot checks: python cumd_web.py file.md
    import sys
    src = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    out, _ = convert(src, page_href=lambda p, l: "#scan-%d" % p)
    sys.stdout.write(out)
