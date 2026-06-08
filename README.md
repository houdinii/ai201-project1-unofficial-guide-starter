# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

A guide for online students feeling out of place returning to school at the University of Texas at Austin's Computer Science program.

Many universities and program's guidance is created for traditional students who show up at 18 right after high school. If you’re coming back at a later age, 35 for instance, the questions you might have won’t be found directly answered on any .edu page, and are scattered across social media, forums and other unofficial resources. 

This seeks to answer questions like ‘Will I be the only person in my 30’s in the class?’  and subjects such as fitting classes around jobs and shedding the rust of being out of school so long.

---

## Document Sources



| #  | Source               | Description                                                                                                                                      | URL or location                                                                                |
|----|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| 1  | Reddit               | Older transfer student in their late 30s asking how to deal with feeling out of place and where older students hang out (New Wave Longhorns org) | https://www.reddit.com/r/UTAustin/comments/1njalkz/for_older_nontraditional_students_advice/   |
| 2  | Reddit               | Students describing what's on the UT Math Assessment (UTMA) and how to review for it after time off                                              | https://www.reddit.com/r/UTAustin/comments/1kdmogf/ut_math_assessment_questions/               |
| 3  | Reddit               | Working-class student's account of balancing multiple jobs with school, food insecurity, and UT support resources                                | https://www.reddit.com/r/UTAustin/comments/1bo3s8w/to_be_a_worker_poor_and_a_student/          |
| 4  | Reddit               | Prospective STEM PhD student asking whether the stipend is livable and if second jobs are allowed                                                | https://www.reddit.com/r/UTAustin/comments/196l3qy/do_phd_students_typically_have_second_jobs/ |
| 5  | Instagram            | Senate of College Councils post defining the Non-Traditional Student Scholarship and its eligibility                                             | https://www.instagram.com/p/DAQ4_hiKohH/                                                       |
| 6  | The Daily Texan      | First-person column from a nontraditional student (married, working mom of three) on her path to UT                                              | https://thedailytexan.com/2023/08/07/i-am-proud-of-the-journey-i-took-to-get-to-ut/            |
| 7  | College Confidential | Forum thread on which credits to transfer in, the 60-hour transfer cap, and in-residence requirements                                            | https://talk.collegeconfidential.com/t/transferring-college-credits/1706757                    |
| 8  | College Confidential | Forum thread on establishing Texas residency to qualify for in-state tuition                                                                     | https://talk.collegeconfidential.com/t/establishing-in-state-residency/1775711                 |
| 9  | modalshift.co        | Review of UT's online MSDS/MSCS program with cost, admissions, format, and course ratings                                                        | https://modalshift.co/msdso-review/                                                            |
| 10 | 921kiyo.com          | A person's experience of UT's online MSCS program                                                                                                | https://921kiyo.com/ut-austin-cs-online/                                                       |


---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

The titles of the documents were often irrelevant to the context, so I only included them in the metadata. I also removed dates, usernames and other short metadata related snippets. All HTML was removed, leaving only the core text and headers.

**Chunk size:**
<=256

**Overlap:**
30 tokens

**Why these choices fit your documents:**
My documents are primarily short social media comments, but longer than a single sentence. This allows for a lower chunk size and overlap.

**Final chunk count:**
183
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
I used all-MiniLM-L6-v2 from sentence-transformers, as it will run locally without issues on my device. 

**Production tradeoff reflection:**
If this were a production application, I would want to use a higher top-k across a larger set of documents.

I would also want to use a larger embedding model, too. I'm limited by the context length of the model, and the technical resources available to me.

There are other considerations, too. Everything in my corpus is in English, so I would want to use a multilingual model.

I would also want to use a model that's been fine-tuned on a domain-specific task, instead of a general-purpose model as I am. We'd want the domain accuracy to be as high as possible. I'd prefer to chunk on boundaries but I'm limited.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

| # | Question                                                                             | Expected answer                                                                                                          |
|---|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| 1 | Is Reinforcement Learning a good course to take online?                              | No — students found it disappointing: brief lectures, textbook-driven; they recommend the David Silver lectures instead. |
| 2 | How much will I actually interact with professors and classmates online?             | Very little — mostly Slack/Piazza/Discord and TA-run office hours; you have to start study groups yourself.              |
| 3 | What topics are on the UT Math Assessment, and how should I prepare after years off? | Mostly Algebra I/II and precalc (some trig, a little calc); a practice exam and review modules are provided.             |
| 4 | Can a PhD student live on the UT stipend, and are second jobs allowed?               | ~$2,400/mo is tight but livable; second jobs are usually barred by contract — extra TA/RA hours (up to 30) are the way.  |
| 5 | How do I establish Texas residency to qualify for in-state tuition?                  | Live in Texas 12 consecutive months and maintain domicile via gainful employment (student jobs don't count).             |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
