"""
Milestone 5 (generation) — grounded, cited answers for The Unofficial Guide.

Pipeline tail: retrieve top-k chunks (Milestone 4) -> build a context-only prompt
-> Groq llama-3.3-70b-versatile -> an answer that uses ONLY the retrieved sources
(or says it doesn't have enough information), plus the source docs it drew from.

Run:  python query.py                       # runs the built-in grounding tests
      python query.py "your question here"  # one-off
"""

from __future__ import annotations

import os
import textwrap

from dotenv import load_dotenv
from groq import Groq

from embed import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
NO_INFO = "I don't have enough information on that."
MAX_DISTANCE = 0.80   # if even the nearest chunk is past this, don't try to answer
DEFAULT_K = 5

SYSTEM = (
    "You are The Unofficial Guide, a survival guide for older, returning, and "
    "nontraditional students at UT Austin. The SOURCES you are given are real things "
    "UT students shared online.\n\n"
    "Rules:\n"
    "- Answer using ONLY the information in the SOURCES. Never add facts from your own "
    "general knowledge, even if you are confident.\n"
    f'- If the SOURCES do not contain enough to answer, reply with exactly: "{NO_INFO}"\n'
    "- Cite the source document name(s) you used, inline, like (source: <name>).\n"
    "- Keep it plain, honest, and specific to UT Austin — a real student's voice, not "
    "brochure copy."
)

_client: Groq | None = None


def client() -> Groq:
    global _client
    if _client is None:
        key = os.environ.get("GROQ_API_KEY")
        if not key or key == "your_key_here":
            raise SystemExit("GROQ_API_KEY missing/placeholder — set it in .env")
        _client = Groq(api_key=key)
    return _client


def _format_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{i}] (source: {h['source']})\n{h['text']}"
                       for i, h in enumerate(hits, 1))


def ask(question: str, k: int = DEFAULT_K, **filters) -> dict:
    """Return {answer, sources, hits} for a question, grounded in retrieved chunks.

    Extra keyword filters (sources, since_ts, include_undated, min_score) are passed
    straight through to retrieve()."""
    question = (question or "").strip()
    if not question:
        return {"answer": "Ask me something about life at UT Austin.", "sources": [], "hits": []}

    hits = retrieve(question, k=k, **filters)

    # deduped source docs (with URLs) for attribution
    sources, seen = [], set()
    for h in hits:
        if h["source"] not in seen:
            seen.add(h["source"])
            sources.append({"source": h["source"], "url": h["url"]})

    # off-topic guard: nothing close enough to ground an answer
    if not hits or hits[0]["distance"] > MAX_DISTANCE:
        return {"answer": NO_INFO, "sources": [], "hits": hits}

    prompt = (
        f"SOURCES:\n{_format_context(hits)}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the SOURCES above, and cite the source name(s) you used."
    )
    resp = client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600,
    )
    answer = resp.choices[0].message.content.strip()

    # if the model declined, don't attach sources it didn't actually use
    declined = answer.lower().startswith("i don't have enough information")
    return {"answer": answer, "sources": [] if declined else sources, "hits": hits}


if __name__ == "__main__":
    import sys

    queries = sys.argv[1:] or [
        "Is Reinforcement Learning a good course to take online?",          # in-corpus
        "How do I establish Texas residency to qualify for in-state tuition?",  # in-corpus
        "What's the best dining hall on campus?",                            # NOT in corpus
    ]
    for q in queries:
        r = ask(q)
        print("\n" + "=" * 88)
        print(f"Q: {q}\n")
        print(textwrap.fill(r["answer"], 86))
        print("\nRetrieved from:", ", ".join(s["source"] for s in r["sources"]) or "(none)")