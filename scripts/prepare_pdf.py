#!/usr/bin/env python3
"""
Prepare the PDF scans that the library links to.

For every PDF volume in library.toml that has a ``source`` (a DJVU or PDF scan,
e.g. on minei.ru), this script downloads the scan, converts DJVU to PDF and
*linearizes* the result ("fast web view").  A linearized PDF served by a web
server that supports HTTP range requests (Apache and nginx do by default) lets
pdf.js open page 600 of a 900-page book without downloading the whole file.

    python scripts/prepare_pdf.py --out /var/www/maktabah/pdf            # all volumes
    python scripts/prepare_pdf.py --out pdf Chasoslov1991 Tipikon         # some books
    python scripts/prepare_pdf.py --out pdf --check                       # what is there

Needs: ``ddjvu`` (package djvulibre-bin) for DJVU sources and ``qpdf``.
    sudo apt install djvulibre-bin qpdf

After converting, set ``offset`` in library.toml for each volume: open the PDF,
find the page that carries printed page number 1 (or the first number used in
the <<…>> tags) and enter (its PDF page index − that number).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

HERE = Path(__file__).resolve().parent


def need(tool, package):
    if not shutil.which(tool):
        sys.exit(f"'{tool}' was not found. Install it first, e.g.: sudo apt install {package}")


def page_count(pdf: Path) -> str:
    try:
        return subprocess.run(["qpdf", "--show-npages", str(pdf)], check=True, capture_output=True, text=True).stdout.strip()
    except Exception:
        return "?"


def download(url: str, dest: Path):
    print(f"    downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "ponomar-maktabah/1.0"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)


def convert(src: Path, out: Path, quality: int):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_pdf = Path(tmp) / "raw.pdf"
        if src.suffix.lower() == ".djvu":
            need("ddjvu", "djvulibre-bin")
            print("    converting DJVU → PDF (this can take a few minutes)")
            subprocess.run(["ddjvu", "-format=pdf", f"-quality={quality}", "-verbose", str(src), str(tmp_pdf)], check=True)
        else:
            shutil.copy2(src, tmp_pdf)
        print("    linearizing for fast web view")
        subprocess.run(["qpdf", "--linearize", "--object-streams=generate", str(tmp_pdf), str(out)], check=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("books", nargs="*", help="book folders (default: every book with a PDF source)")
    p.add_argument("--out", type=Path, required=True, help="folder the site serves as pdf/")
    p.add_argument("--config", type=Path, default=HERE / "library.toml")
    p.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "maktabah" / "sources",
                   help="where downloaded originals are kept (default: %(default)s)")
    p.add_argument("--quality", type=int, default=85, help="ddjvu JPEG quality for DJVU conversion (default: %(default)s)")
    p.add_argument("--force", action="store_true", help="rebuild PDFs that already exist")
    p.add_argument("--check", action="store_true", help="only report which PDFs exist and their page counts")
    args = p.parse_args(argv)

    with open(args.config, "rb") as f:
        config = tomllib.load(f)
    if not args.check:
        need("qpdf", "qpdf")
    args.out.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)

    for bid, cfg in config.get("books", {}).items():
        if args.books and bid not in args.books:
            continue
        for vol in cfg.get("pdf", []):
            out = args.out / vol["file"]
            print(f"{bid}: {vol['file']}")
            if args.check:
                print(f"    {'present, ' + page_count(out) + ' pages' if out.exists() else 'MISSING'}; offset = {vol.get('offset', 0)}")
                continue
            if out.exists() and not args.force:
                print(f"    already there ({page_count(out)} pages); use --force to rebuild")
                continue
            src_url = vol.get("source")
            if not src_url:
                print("    no 'source' in library.toml — put the PDF there by hand")
                continue
            src = args.cache / Path(src_url).name
            if not src.exists():
                download(src_url, src)
            convert(src, out, args.quality)
            print(f"    done: {page_count(out)} pages")


if __name__ == "__main__":
    main()
