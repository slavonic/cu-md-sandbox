# MineyaDopolnitelnaya

Минея Дополнительная (Supplementary Menaion), in two parts.
Издательство Московской патриархии, Москва 2018.
Тексты приводятся по изданию: МИНЕ́Ѧ дополни́тельнаѧ. ча́сть а҃ септе́мврїй _ феврꙋа́рїй; ча́сть в҃ ма́ртъ _ а҆́ѵгꙋстъ. Москва, 2018.

Part 1 covers September–February and part 2 covers March–August. The scans are
`MineyaDopolnitelnaya2018-1.pdf` and `MineyaDopolnitelnaya2018-2.pdf` (see `scripts/library.toml`).

## Status of the text

- **All chapters are OCR output that has not been proofread.** The model was fine-tuned
  on lines from this repository. On 10 September, compared with the proofread text and checked
  against the page images, it made about 0.1 % character errors (about 35 in 37,000). Most of
  them are in diacritics and in letters next to large decorated initials.
- `ocr/09_10.md.bak` (10 September, All Saints of Lipetsk) is an earlier file that was typeset by Ponomar Technologies, Inc.
  and is partially proofread. It will be deleted after `chapters/09_10.md` is proofread.
- `chapters/00_1.md` and `chapters/00_2.md` (title page and table of contents of each part) are
  given exactly as read, without any correction, and are of poor quality.

## Chapters

One file per service, named `MM_DD.md` after its date in the Julian calendar (`09_01` is
1 September). When a day has more than one service, the files get a letter in book order:
`10_11a`, `10_11b`. The other files are:

| File | Contents |
|---|---|
| `00_1`, `00_2` | Title page and table of contents of part 1 and part 2 |
| `pascha9_fri` | Friday of the 9th week after Pascha: Tabynsk icon of the Mother of God |
| `pent3_sun` | 3rd Sunday after Pentecost: All Saints of St Petersburg |
| `pent4_sun` | 4th Sunday after Pentecost: Venerable Fathers of the Pskov Caves |
| `theotokia_1`, `theotokia_2` | Appendix at the end of each part: resurrectional Theotokia in the eight tones, dismissal Theotokia, etc. |

`manifest.xml` lists part 1 first, then part 2, in calendar order within each part. This is
not always the order of the printed book: 10 and 18 September and 5 November are printed at the
end of part 1, and 14 June, 25 June (Dalmatus of Iset) and 26 August at the end of part 2. Order matters for the
website: `from_chapter = "00_2"` in `scripts/library.toml` says that every chapter from `00_2`
onward links to the part 2 scan.

The OCR delivered each part as numbered files (`tom1/NN.md`, `tom2/NN.md`) split at each
«Мѣ́сѧца …» heading. Those were renamed as above, and the files that held more than one service
were split at page boundaries:
- `tom2/15.md` became `06_25a`, `pascha9_fri`, `pent3_sun` and `pent4_sun`.
- `tom1/42.md` became `11_05` and `theotokia_1`.
- `tom2/30.md` became `08_26` and `theotokia_2`.

`ocr/index.tsv` maps every chapter to its original file.

## Markup

The markup follows the rest of the repository (see `../markup-tags.md`):
- Paragraphs are separated by a blank line.
- Red text is `=…=` and a red initial is `~`. (The OCR wrote `*…*`; this was replaced with `=`
  everywhere.)
- «꙳» stands where it is printed.
- Running heads, page numbers and catchwords are removed, and hyphenated words are joined.

Paragraph breaks and red text were found from the line layout and the color of the page. As a
result paragraphs are sometimes smaller than in hand-made files: consecutive centered rubric lines
are not merged into one paragraph.

### Page tags

Each page begins with `<<label: N>>`. Here `N` is the page of the PDF and `label` is the printed
page number in Church Slavonic numerals. For example, `<<з҃: 10>>` is printed page 7, which is
page 10 of the PDF. If a page begins with a new paragraph, the tag is on a line of its own;
otherwise it stands inside the paragraph, before the first word of the page.

Because the tag already gives the PDF page, both volumes have `offset = 0` in
`scripts/library.toml`. The difference between printed and PDF page numbers is not constant:

- **Part 1.** The difference is 3 up to printed page 517 and 2 after it. The blank verso,
  p. 518, is missing from the PDF.
- **Part 2.** The difference is 3 up to p. 229, 5 from p. 230 to p. 503, and 4 after that.
- **Part 2 duplicates two pages.** PDF pages 233–234 repeat PDF 231–232 (printed pp. 228–229).
  The text contains them only once. The blank verso, p. 504, is missing from the PDF.
- **Pages without a printed number.** On pages such as headpieces and section titles, the label
  is the number the page would have.
- **Pages with no text.** Covers, endpapers, the frontispiece icon and the music appendix of
  part 2 (PDF 581–582) are left out.

## OCR data (`ocr/`)

These files come from the OCR and are kept so that the text can be checked against the scans.
The site builder ignores them. Pages are written `p0521S` (page 521 of the PDF) and image
coordinates are in pixels of the page image.

| File | Contents |
|---|---|
| `index.tsv` | One row per chapter: `chapter`, `part`, `source` (original OCR file), `first_pdf_page`, `last_pdf_page`, `proofread` |
| `<chapter>.words.tsv` | Every word of `chapters/<chapter>.md` with its location: `word`, `page`, `x0 y0 x1 y1` (the box of the line it is on) |
| `09_10.ocr.md`, `09_10.ocr.words.tsv` | The OCR of 10 September, kept for reference. The text used is the proofread `chapters/09_10.md` |
| `tom1.pages.tsv`, `tom2.pages.tsv` | `pdf` page → `printed` page number, and `how` the number was found (e.g. `обложка`, cover: no number) |
| `tom1.index.tsv`, `tom2.index.tsv` | The OCR's original list of files: `file`, `date`, `first_page`, `last_page`, `paragraphs`, `first_paragraph`. The dates were read by OCR and two are wrong: `tom1/13.md` is 11 October, not 1 October, and `tom2/19.md` is 15 July, not 5 July |
| `tom1.headers.tsv`, `tom2.headers.tsv` | Running `header` and `catchword` removed from each page |
| `tom1.dropcaps.tsv`, `tom2.dropcaps.tsv` | Drop caps (see below): `page`, `read` (as read), `fixed` (as restored) |
| `tom1.linestart.tsv`, `tom2.linestart.tsv` | Lost first letters (see below): `page`, `read`, `fixed` |
| `tom1.stars.tsv`, `tom2.stars.tsv` | Added «꙳» (see below): `page`, `spot` (x y of the mark), `word` (the word it follows) |

### What was restored rather than read

Three kinds of correction were made automatically. All of them are listed so they can be
checked:

- **Drop caps (`dropcaps.tsv`).** The model does not read the large initials, so the first
  letter was taken from a dictionary of the other books in this repository (excluding this
  Menaion).
  - An empty `fixed` cell means no match was found and the word was left as read.
  - `red` means the line has a red rubric, not a drop cap.
- **First letters of lines (`linestart.tsv`).** At the very left edge the model sometimes loses a
  letter, for example «рⷭ҇та̀» for «хрⷭ҇та̀». Unknown words there were restored from the same
  dictionary.
- **Asterisks (`stars.tsv`).** The model often misses «꙳» at the end of a line, and pale red ones.
  They were found from the color of the page and inserted after the word they follow. There are
  about 1,100 per part, roughly one asterisk in ten.
