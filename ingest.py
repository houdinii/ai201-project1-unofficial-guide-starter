"""
Milestone 3 — Ingestion + chunking for The Unofficial Guide.

Loads the UT-Austin student-voice corpus from documents/, cleans each file, and
produces retrieval chunks per the spec in planning.md:

  * chunk size <= 256 tokens  (all-MiniLM-L6-v2 truncates beyond 256, incl. specials)
  * 30-40 token overlap        (applied to prose splits only)
  * structure-aware splitting:
      - Reddit: the post is one chunk; each top-level comment is its own chunk,
        with the post title/question prepended so a lone comment carries context.
      - Prose (blogs / forum threads / columns): split on Markdown headings, then
        into sentence windows when a section exceeds the token cap. Each prose
        chunk leads with "<doc title> — <section>" so the subject (e.g. a course
        name) stays in the embedded text; Reddit chunks keep the post title in
        metadata only.
  * dedup repeated comments so copy-pasted replies don't dominate the top-k.
  * drop near-contentless fragments (body < MIN_BODY_TOKENS tokens).

Output: chunks.jsonl (one JSON object per line) + a summary to stdout.

Setup:  python -m venv .venv && source .venv/bin/activate
        pip install -r requirements.txt        # provides transformers via sentence-transformers
Run:    python ingest.py
        python ingest.py --source documents --out chunks.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

import transformers
from transformers import AutoTokenizer

transformers.logging.set_verbosity_error()  # mute the >512 length notice (we split anyway)

# --- spec constants (mirror planning.md) ------------------------------------
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_MAX_TOKENS = 256       # hard model limit; embedder truncates beyond this
MAX_CHUNK_TOKENS = 250       # content budget, leaves headroom for [CLS]/[SEP]
OVERLAP_TOKENS = 35          # prose overlap (30-40 band)
MIN_BODY_TOKENS = 8          # drop chatter fragments below this many body tokens
DEFAULT_SOURCE = "documents"
DEFAULT_OUTPUT = "chunks.jsonl"

# Sentence / paragraph boundaries used when windowing long prose.
_SENT_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n{2,}")
# A Reddit comment list item:  "- (109) text..."  (score may be negative)
_COMMENT = re.compile(r"^\s*-\s*\((-?\d+)\)\s?", re.M)
_HEADING = re.compile(r"^#{1,6}\s")

_tok = None


def tok():
    global _tok
    if _tok is None:
        _tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
    return _tok


def n_tokens(text: str) -> int:
    """Content-token count as the embedder sees it (no special tokens)."""
    return len(tok().encode(text, add_special_tokens=False))


@dataclass
class Chunk:
    id: str
    text: str
    source: str          # filename
    url: str             # citation URL from the "~ source:" header
    date: str            # publication date YYYY-MM-DD, if known (else "")
    title: str           # document title (first # heading, else from filename)
    section: str         # prose heading, or "post"/"comment" for Reddit
    kind: str            # reddit_post | reddit_comment | prose
    chunk_index: int
    n_tokens: int
    score: int | None = None   # Reddit comment upvotes, when applicable


# --- loading / cleaning -----------------------------------------------------
def read_doc(path: Path) -> tuple[str, str, str, str]:
    """Return (body, url, title, date): drop the leading '~' header lines, capture
    the source URL and (if present) a '~ date: YYYY-MM-DD' line, and pull the first
    Markdown heading as the title."""
    raw = path.read_text(encoding="utf-8")
    url = date = ""
    body_lines: list[str] = []
    for line in raw.splitlines():
        s = line.lstrip()
        if s.startswith("~"):                       # metadata header line — drop it
            if not url:
                m = re.search(r"https?://\S+", line)
                if m:
                    url = m.group(0).rstrip("/")
            if not date and "date" in s.lower():
                dm = re.search(r"\d{4}-\d{2}-\d{2}", s)
                if dm:
                    date = dm.group(0)
            continue
        body_lines.append(line)

    title = ""
    for line in body_lines:
        if _HEADING.match(line):
            title = line.strip().lstrip("#").strip()
            break

    return "\n".join(body_lines).strip(), url, title, date


# --- token windowing (prose) ------------------------------------------------
def _hard_split(text: str, budget: int) -> list[str]:
    """Last resort: a single sentence longer than the budget — split by tokens."""
    ids = tok().encode(text, add_special_tokens=False)
    return [tok().decode(ids[i:i + budget]).strip() for i in range(0, len(ids), budget)]


def pack(text: str, prefix_tokens: int = 0) -> list[str]:
    """Greedily pack sentences into <=budget-token windows with token overlap.
    Window sizes are measured on the *joined* string (what the embedder sees),
    not a sum of per-unit counts, so subword merges at boundaries can't drift
    a chunk over the cap."""
    budget = max(16, MAX_CHUNK_TOKENS - prefix_tokens)

    units: list[str] = []
    for sent in _SENT_BOUNDARY.split(text):
        sent = sent.strip()
        if not sent:
            continue
        units.extend(_hard_split(sent, budget) if n_tokens(sent) > budget else [sent])

    windows: list[str] = []
    cur: list[str] = []
    for u in units:
        if cur and n_tokens(" ".join(cur + [u])) > budget:
            windows.append(" ".join(cur))
            # carry a token-overlap tail (measured on the joined tail) forward
            tail: list[str] = []
            for prev in reversed(cur):
                if tail and n_tokens(" ".join([prev] + tail)) > OVERLAP_TOKENS:
                    break
                tail.insert(0, prev)
            cur = tail
        cur.append(u)
    if cur:
        windows.append(" ".join(cur))
    return windows


def chunkify(text: str, prefix: str = "") -> list[str]:
    """Window `text`, prepending `prefix` (e.g. the post question) to each window
    so every chunk carries context. Prefix tokens are counted against the budget,
    and each assembled chunk is verified against the cap as a final guard."""
    text = text.strip()
    if not text:
        return []
    prefix = prefix.strip()
    ptoks = n_tokens(prefix) + 1 if prefix else 0
    out: list[str] = []
    for w in pack(text, prefix_tokens=ptoks):
        full = f"{prefix}\n{w}" if prefix else w
        # safety net: if boundary effects still push over, trim by tokens
        if n_tokens(full) > MAX_CHUNK_TOKENS:
            ids = tok().encode(full, add_special_tokens=False)[:MAX_CHUNK_TOKENS]
            full = tok().decode(ids).strip()
        out.append(full)
    return out


# --- structure-aware splitting ----------------------------------------------
def split_reddit(body: str) -> tuple[str, list[tuple[int, str]]]:
    """Return (post_body, [(score, comment_text), ...])."""
    parts = re.split(r"^##\s+Comments\s*$", body, maxsplit=1, flags=re.M)
    head, comment_block = parts[0], (parts[1] if len(parts) > 1 else "")

    # post body = head minus all heading lines (# title, ## Post)
    post = "\n".join(l for l in head.splitlines() if not _HEADING.match(l)).strip()

    comments: list[tuple[int, str]] = []
    marks = list(_COMMENT.finditer(comment_block))
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(comment_block)
        text = comment_block[start:end].strip()
        if text:
            comments.append((int(m.group(1)), text))
    return post, comments


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split prose on Markdown headings → [(heading, section_body), ...]."""
    sections: list[tuple[str, str]] = []
    head = ""
    cur: list[str] = []
    for line in body.splitlines():
        if _HEADING.match(line):
            if cur:
                sections.append((head, "\n".join(cur).strip()))
            head = line.strip().lstrip("#").strip()
            cur = []
        else:
            cur.append(line)
    if cur:
        sections.append((head, "\n".join(cur).strip()))
    return [(h, t) for h, t in sections if t.strip()]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _title_from_filename(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip()


def process_document(path: Path) -> tuple[list[Chunk], list[tuple[str, str]]]:
    body, url, title, date = read_doc(path)
    src = path.name
    doc_title = title or _title_from_filename(path)
    chunks: list[Chunk] = []
    dropped: list[tuple[str, str]] = []

    def add(text: str, kind: str, section: str, score: int | None = None) -> None:
        idx = len(chunks)
        chunks.append(Chunk(
            id=f"{src}#{idx}",
            text=text.strip(),
            source=src,
            url=url,
            date=date,
            title=doc_title,
            section=section,
            kind=kind,
            chunk_index=idx,
            n_tokens=n_tokens(text),
            score=score,
        ))

    def too_short(t: str) -> bool:
        return n_tokens(t) < MIN_BODY_TOKENS

    if "## Comments" in body:  # Reddit thread — post title lives in metadata only
        post, comments = split_reddit(body)
        if post and not too_short(post):
            for w in chunkify(post):
                add(w, "reddit_post", section="post")
        seen: set[str] = set()
        for score, ctext in comments:
            h = hashlib.md5(_norm(ctext).encode()).hexdigest()
            if h in seen:                       # dedup repeated / copy-pasted replies
                continue
            seen.add(h)
            if too_short(ctext):                # drop chatter fragments
                dropped.append((src, ctext))
                continue
            for w in chunkify(ctext):
                add(w, "reddit_comment", section="comment", score=score)
    else:                                       # prose — lead with subject context
        for head, sect in split_sections(body):
            if too_short(sect):
                dropped.append((src, sect))
                continue
            prefix = " — ".join(p for p in (doc_title, head) if p)
            for w in chunkify(sect, prefix=prefix):
                add(w, "prose", section=head)

    return chunks, dropped


# --- entrypoint -------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest + chunk the corpus (Milestone 3).")
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="folder of .md source docs")
    ap.add_argument("--out", default=DEFAULT_OUTPUT, help="output JSONL path")
    args = ap.parse_args()

    src_dir = Path(args.source)
    files = sorted(src_dir.glob("*.md"))
    if not files:
        sys.exit(f"No .md files found in {src_dir}/")

    print(f"Tokenizer: {EMBED_MODEL}  (cap {MAX_CHUNK_TOKENS} content tokens)\n")
    all_chunks: list[Chunk] = []
    all_dropped: list[tuple[str, str]] = []
    for f in files:
        cs, dropped = process_document(f)
        all_chunks.extend(cs)
        all_dropped.extend(dropped)
        tail = f"  ({len(dropped)} dropped)" if dropped else ""
        print(f"  {f.name:52s} -> {len(cs):3d} chunks{tail}")

    with open(args.out, "w", encoding="utf-8") as fh:
        for c in all_chunks:
            fh.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

    toks = [c.n_tokens for c in all_chunks]
    by_kind: dict[str, int] = {}
    for c in all_chunks:
        by_kind[c.kind] = by_kind.get(c.kind, 0) + 1
    over = sum(1 for t in toks if t > MODEL_MAX_TOKENS - 2)  # -2 for [CLS]/[SEP]

    print(f"\n{len(all_chunks)} chunks from {len(files)} docs -> {args.out}")
    print(f"  by kind: {by_kind}")
    print(f"  tokens : min {min(toks)}, mean {mean(toks):.0f}, max {max(toks)}")
    print(f"  over 254-token embed limit: {over}  (want 0)")
    print(f"  dropped {len(all_dropped)} fragments (< {MIN_BODY_TOKENS} body tokens):")
    for _src, frag in all_dropped:
        print(f"      - {frag[:64]!r}")


if __name__ == "__main__":
    main()