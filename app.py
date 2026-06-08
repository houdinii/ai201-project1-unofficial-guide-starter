"""
Milestone 5 (interface) — a Gradio web UI for The Unofficial Guide.

Wraps query.ask() in a UT-flavored front end: ask a question, get a grounded,
cited answer, the source docs it drew from, and (optionally) "the receipts" —
the exact chunks retrieval pulled, with cosine distances.

Run:  python app.py   ->   http://localhost:7860
"""

from __future__ import annotations

import gradio as gr

from query import ask

# --- look & feel -----------------------------------------------------------
THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.orange,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

CSS = """
.gradio-container { max-width: 900px !important; margin: auto !important; }
#hero {
  background: linear-gradient(135deg, #bf5700 0%, #e87500 100%);
  color: #fff; padding: 30px 34px; border-radius: 20px;
  box-shadow: 0 10px 34px rgba(191, 87, 0, .28); margin-bottom: 16px;
}
#hero h1 { margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -.5px; }
#hero p  { margin: .45rem 0 0; font-size: 1.05rem; opacity: .96; }
#answer-card {
  border-left: 5px solid #bf5700; border-radius: 12px;
  padding: 4px 20px; min-height: 64px;
}
#ask-btn { font-weight: 700 !important; }
.qbtn {
  width: 100% !important;
  white-space: normal !important;   /* wrap long questions instead of truncating */
  text-align: left !important;
  height: auto !important; min-height: 0 !important;
  line-height: 1.35 !important;
  padding: 10px 14px !important;
  font-weight: 500 !important;
}
.qbtn:hover { border-color: #bf5700 !important; color: #bf5700 !important; }
footer { display: none !important; }
"""

HERO = """
<div id="hero">
  <h1>🤘 The Unofficial Guide</h1>
  <p>Real talk for older, returning &amp; nontraditional Longhorns — answered only
     from what UT students actually shared online. No brochure copy.</p>
</div>
"""

EXAMPLES = [
    "Is Reinforcement Learning a good course to take online?",
    "What's on the UT Math Assessment, and how do I prep after years off?",
    "Can a PhD student live on the UT stipend, and are second jobs allowed?",
    "Where do older students at UT find each other?",
    "How do I establish Texas residency for in-state tuition?",
]

MORE_EXAMPLES = [
    "Is the online CS master's the same degree as the on-campus one?",
    "How much does the online CS/Data Science master's cost per course and in total?",
    "Do I need a GRE score or a CS undergrad degree to get into the online program?",
    "How long do I have to finish, and is every course offered every semester?",
    "What's it like taking two courses at once while working full time?",
    "Is there a thesis or research option in the online programs?",
    "What is New Wave Longhorns and how do I join?",
    "Who counts as a 'nontraditional student' at UT, and is there a scholarship?",
    "What UT resources help students struggling with money or food?",
    "How many credit hours can I transfer in, and how many must I complete in residence?",
]


def handle_query(question: str):
    result = ask(question)

    if result["sources"]:
        sources_md = "\n".join(f"- [{s['source']}]({s['url']})" for s in result["sources"])
    else:
        sources_md = "_No sources — the guide didn't find this in its documents._"

    receipts = []
    for h in result["hits"]:
        snippet = " ".join(h["text"].split())
        if " — " in snippet[:90]:                 # drop the "Doc — Section" prefix
            snippet = snippet.split(" — ", 1)[1]
        receipts.append(
            f"**`dist {h['distance']:.3f}`** · `{h['source']}#{h['chunk_index']}`\n\n"
            f"> {snippet[:260]}{'…' if len(snippet) > 260 else ''}"
        )
    receipts_md = "\n\n---\n\n".join(receipts) if receipts else "_Nothing retrieved._"

    return result["answer"], sources_md, receipts_md


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.HTML(HERO)

    question = gr.Textbox(
        label="Your question",
        placeholder="e.g. Will I be the only person in my 30s in class?",
        autofocus=True,
    )
    ask_btn = gr.Button("Ask the guide  🤘", variant="primary", elem_id="ask-btn")

    gr.Markdown("**Try one of these**")
    example_btns = [gr.Button(q, elem_classes="qbtn") for q in EXAMPLES]
    with gr.Accordion("…or dig into the details", open=False):
        example_btns += [gr.Button(q, elem_classes="qbtn") for q in MORE_EXAMPLES]

    gr.Markdown("### Answer")
    answer = gr.Markdown(elem_id="answer-card")
    gr.Markdown("### 📍 Retrieved from")
    sources = gr.Markdown()
    with gr.Accordion("🧾 Show the receipts (the exact chunks it read)", open=False):
        receipts = gr.Markdown()

    outputs = [answer, sources, receipts]
    ask_btn.click(handle_query, inputs=question, outputs=outputs)
    question.submit(handle_query, inputs=question, outputs=outputs)

    # each example button drops its text into the box, then answers
    for btn in example_btns:
        btn.click(lambda v=btn.value: v, outputs=question).then(
            handle_query, inputs=question, outputs=outputs
        )


if __name__ == "__main__":
    demo.launch(theme=THEME, css=CSS)