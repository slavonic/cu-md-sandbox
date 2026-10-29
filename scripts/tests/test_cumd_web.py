"""Tests for the web layer on top of cumd:  python -m pytest scripts/tests"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cumd_web as c  # noqa: E402


def href(p, label):
    return "scan?p=%d" % p


def conv(text, **kw):
    return c.convert(text, page_href=kw.get("page_href", href), image_resolver=kw.get("image_resolver"))


def test_arabic_page_anchor_links_to_pdf_page():
    html, info = conv("Помѧне́тъ <<39>> всѧ́кꙋ")
    assert '<a class="pg" data-l="39" data-p="39" href="scan?p=39" id="p39"></a>' in html
    assert "&lt;" not in html and "39" not in html.replace('"39"', "").replace("p=39", "").replace("p39", "")
    assert info.pages == [39]


def test_slavonic_label_with_page_number():
    html, _ = conv("текст <<а҃ ѡ҆б.: 2>> текст")
    assert 'data-l="а҃ ѡ҆б."' in html and 'data-p="2"' in html and 'href="scan?p=2"' in html


def test_legacy_cumd_order_number_first():
    html, _ = conv("x <<5: л. 3 об.>> y")
    assert 'data-l="л. 3 об."' in html and 'data-p="5"' in html


def test_anchor_without_number_is_shown_but_not_linked():
    html, _ = conv("x <<а҃>> y")
    assert '<span class="pg" data-l="а҃"></span>' in html


def test_no_pdf_means_no_link():
    html, _ = c.convert("x <<5>> y", page_href=None)
    assert '<span class="pg" data-l="5" data-p="5" id="p5"></span>' in html


def test_lone_anchor_paragraph_is_merged_into_next_block():
    html, _ = conv("<<38>>\n\n=Нача́ло ᲂу҆́трени.=")
    assert html.startswith('<p><a class="pg"') and html.count("<p>") == 1


def test_parse_page_anchor():
    assert c.parse_page_anchor("25") == (25, "25")
    assert c.parse_page_anchor("рп҃в: 363") == (363, "рп҃в")
    assert c.parse_page_anchor("а҃") == (None, "а҃")


def test_cumd_rules_are_kept():
    html, _ = conv("=^Н=аречѐ ~Слава +широко+ ((и))")
    assert '<span class="red"><span class="bukvitsa">Н</span></span>' in html
    assert '<span class="red">С</span>лава' in html
    assert '<span class="wide">широко</span>' in html
    assert '<span class="verse">и</span>' in html


def test_block_attributes():
    html, _ = conv("{{text_align=center}}\nтекст\n\n{{liturgical=u/can/1/9/ex tone=8}}\nтекст\n\n{{u/50ps}}\nтекст")
    assert '<p class="align-center" style="text-align:center">' in html
    assert 'data-liturgical="u/can/1/9/ex"' in html and 'data-tone="8"' in html
    assert 'data-liturgical="u/50ps"' in html
    assert "{{" not in html


def test_double_bracket_notes_become_footnotes_in_reading_order():
    html, _ = conv("~Оу҆слы́шитъ[[Ѱ. ѳ҃і]] тѧ̀ и҆ дале́е[^1]\n\n[^1]: второе")
    assert html.index('href="#fn-cu1">1<') < html.index('href="#fn-1">2<')
    assert "Ѱ. ѳ҃і" in html.split('class="footnote"')[1]
    assert "[[" not in html


def test_cuxml_image_link_and_missing_images():
    html, _ = conv("[!image](../media/1.png)\n\n![x](Pictures/none.png)",
                   image_resolver=lambda s: "media/1.png" if "media" in s else None)
    assert '<img alt="" loading="lazy" src="media/1.png">' in html
    assert "none.png" not in html


def test_headings_get_ids():
    html, info = conv("### Пѣ́снь а҃\n\nтекст")
    assert '<h3 id="s1">' in html and info.headings[0].text == "Пѣ́снь а҃"
