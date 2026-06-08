#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["trafilatura"]
# ///
"""
url_to_md.py — fetch a web page, save clean markdown to a file, stamp the source.

Self-contained: trafilatura is declared inline, so uv runs this in its own
isolated env and your repo's pinned dependencies are never touched.

Run:
    uv run --script scripts/url_to_md.py "<url>" docs/output.md
"""
import sys
from pathlib import Path

import trafilatura


def main():
    if len(sys.argv) < 3:
        print('usage: uv run --script scripts/url_to_md.py "<url>" <out.md>')
        return

    url, out = sys.argv[1], sys.argv[2]

    html = trafilatura.fetch_url(url)
    if not html:
        print(f"couldn't fetch {url}")
        return

    md = trafilatura.extract(
        html,
        output_format="markdown",
        include_tables=True,
        include_comments=False,
    )
    if not md:
        print("trafilatura extracted nothing — likely a stats/JS-heavy page. "
              "Try markdownify on the raw HTML, or grab the table by hand.")
        return

    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"<!-- source: {url} -->\n\n{md}", encoding="utf-8")
    print(f"wrote {p}  ({len(md)} chars) — open it and check the table survived")


if __name__ == "__main__":
    main()