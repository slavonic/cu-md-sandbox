# cu-md-sandbox

Church Slavonic texts in Markdown format

## List of structural IDs

See [markup-tags.md](markup-tags.md).

## Building the website

The [scripts/](scripts/) folder contains a static site builder that turns these Markdown
books into the [Ponomar Library of Liturgical Texts](https://www.ponomar.net/maktabah/),
a bilingual (English / Russian), mobile-friendly website. It also has a tool for
preparing the PDF page scans.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/build_library.py --fetch-pdfjs      # → _site/
```

For all options, the converter's rules, PDF scans, adding books and automatic builds,
see [scripts/README.md](scripts/README.md).

