# The Unofficial Guide — Project 1

## Domain

A guide for older students feeling out of place returning to school at the University of Texas at Austin's Computer Science program. Most university and program guidance is written for traditional students who arrive at 18 straight out of high school. If you're coming back later at, say, 35 for instance,the questions you have won't be answered directly on any .edu page; they're scattered across social media, forums, and other unofficial resources. This guide sets out to answer questions like "Will I be the only person in my 30s in the class?" along with subjects like fitting classes around a job and shedding the rust of being out of school for so long.

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

## Chunking Strategy

Before chunking, I cleaned each document. The titles were often irrelevant to the surrounding context, so I kept them only in the metadata, and I stripped out dates, usernames, and other short metadata-related snippets. All HTML was removed, leaving only the core text and its headers.

I chunk to a maximum of 256 tokens with a 30-token overlap. My documents are primarily short social-media comments — though generally longer than a single sentence — which is why a smaller chunk size and a modest overlap suit them; the 256-token ceiling also matches all-MiniLM-L6-v2, which truncates anything longer. Across all ten documents, this produced 183 chunks.

## Embedding Model

I used all-MiniLM-L6-v2 from sentence-transformers because it runs locally without issues on my device.

If this were a production application, I would make several changes. I would use a higher top-k across a larger set of documents, and I would move to a larger embedding model. I'm currently limited by the model's context length and the technical resources available to me. Everything in my corpus is in English, so I would also want a multilingual model to widen who it can serve. Finally, I would prefer a model fine-tuned on a domain-specific task rather than the general-purpose one I'm using, so that domain accuracy could be as high as possible, and I would chunk on natural boundaries if I weren't constrained.

## Grounded Generation

The system enforces grounding in several layers. First, low-relevance chunks (8 tokens or fewer) are filtered out before anything reaches the model.

The system prompt then applies a hard "only" rule: *Answer using ONLY the information in the SOURCES. Never add facts from your own general knowledge, even if you are confident.* That is followed by a refusal contract (a hard refusal) *If the SOURCES do not contain enough to answer, reply with exactly: "I don't have enough information on that."* Every claim must carry an inline citation (*Cite the source document name(s) you used, inline, like (source: )*), and I included a voice constraint to keep the answer in the right voice. 

Structurally, the source filenames are sent alongside the chunks so the model can cite them easily, and I set the temperature to 0.2 to lower drift.

Source attribution is surfaced two ways. The LLM cites the source document inline in its answer text, like (source: modalshift_ut_austin_msds_online_review.md), and `ask()` independently returns the deduped list of retrieved source documents with their URLs, which the Gradio UI renders as clickable links under "📍 Retrieved from" — along with the exact chunks and distances in the "🧾 receipts" accordion.

## Evaluation Report

| # | Question                                                                             | Expected answer                                                                                                            |
|---|--------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| 1 | Is Reinforcement Learning a good course to take online?                              | No, students found it disappointing: brief lectures, textbook-driven; they recommend the David Silver lectures instead.    |
| 2 | How much will I actually interact with professors and classmates online?             | Very little. Mostly Slack/Piazza/Discord and TA-run office hours; you have to start study groups yourself.                 |
| 3 | What topics are on the UT Math Assessment, and how should I prepare after years off? | Mostly Algebra I/II and precalc (some trig, a little calc); a practice exam and review modules are provided.               |
| 4 | Can a PhD student live on the UT stipend, and are second jobs allowed?               | ~$2,400/mo is tight but livable; second jobs are usually barred by contract with extra TA/RA hours (up to 30) are the way. |
| 5 | How do I establish Texas residency to qualify for in-state tuition?                  | Live in Texas 12 consecutive months and maintain domicile via gainful employment (student jobs don't count).               |

Retrieval quality was strong overall, with the only wrinkle being a citation issue on the Texas residency question. Questions 1 through 4 returned relevant chunks, and question 5 was partially relevant. Response accuracy followed the same pattern: questions 1 through 4 were accurate, and question 5 was partially accurate. The system answered every question in the test set. The one issue was the Texas residency question, where the model did not cite all of its claims and it's unclear whether it drew on its own information, but otherwise everything worked.

### More from the question bank

These are additional questions I synthetically created to further test the system's ability to answer. A couple of them intentionally have no supporting answer in the corpus, in order to test the model's refusal behavior.

| #  | Question                                                                            | Expected answer                                                                                                             |
|----|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| 6  | Is the online CS master's the same degree as the on-campus one?                     | Yes — the same degree; the transcript may just note it was taken online.                                                    |
| 7  | How much does the online CS/Data Science master's cost per course and in total?     | $1,000 per course, $10,000 total (international students pay a small per-semester fee).                                     |
| 8  | Do I need a GRE score or a CS undergrad degree to get into the online program?      | No — the GRE is waived and you don't need a CS undergrad degree.                                                            |
| 9  | How long do I have to finish, and is every course offered every semester?           | Up to 6 years; not every course runs each term, and only a few are offered in summer.                                       |
| 10 | What's it like taking two courses at once while working full time?                  | Doable but leaves almost no free time for family or hobbies.                                                                |
| 11 | Is there a thesis or research option in the online programs?                        | MSCSO and MSAIO offer a thesis option; MSDSO does not.                                                                      |
| 12 | What is New Wave Longhorns and how do I join?                                       | A student org for nontraditional/25+ students — @newwavelonghorns on Instagram, an active GroupMe, and monthly events.      |
| 13 | Who counts as a "nontraditional student" at UT, and is there a scholarship?         | 25+/veteran/transfer/parent/first-gen/international; the Senate Non-Traditional Student Scholarship (2 semesters, 3.0 GPA). |
| 14 | What UT resources help students struggling with money or food?                      | UT Outpost and the Student Emergency Fund; favor grants/Pell over loans.                                                    |
| 15 | How many credit hours can I transfer in, and how many must I complete in residence? | Max 60 transfer hours; 60 in-residence plus 36 upper-division hours to graduate.                                            |

## Failure Case Analysis

The question that failed was "How do I establish Texas residency for in-state tuition?" The system returned:

```
To establish Texas residency for in-state tuition, you must meet certain criteria. According to the rules mentioned (source: college_confidential_establish_residency.md), if you are independent for tax purposes, you may gain resident status if you establish domicile in the state. To establish domicile, you must live in Texas for 12 consecutive months and establish and maintain domicile for 12 consecutive months, as evidenced by gainful employment in Texas, sole or joint marital ownership of residential real property in Texas, ownership and operation of a business in Texas, or marriage for one year to a person who has established domicile in Texas.
```

The root cause sits at the retrieval/generation stages. The model returned a partially cited answer but elaborated in a way that drew on its own knowledge. The information does exist in the source documents, so this may be due to the lower k value, or to a prompt that didn't spell out the requirements firmly enough. To fix it, I would raise k somewhat and do some prompt engineering to keep the model within bounds. Overall, though, I was impressed with the citations across the board — more than I expected.

## Spec Reflection

The spec acted as a source of truth between me and the model I was working with (Claude Code). I have trouble remembering the exact steps I need to take by nature, so the spec was as helpful to me as it was to the model.

My implementation diverged from the spec on top-k. I had planned to use k=10, but the Reddit comments were very short and the results came back a bit odd, so I backed off and settled on 5. Its a value that returned enough to answer questions without pulling in so much that the results filled with extraneous information.

## AI Usage

In the first instance, I gave the AI my planning document and a text-only version of my flowchart. It produced a chunking strategy tailored to my documents, and I overrode the chunk size from 500 to 256 because my documents are short social posts.

In the second instance, I gave it my planning document, a text-only version of my flowchart, and a list of documents. It produced a restatement of my pipeline in new terms (to help me understand it), along with my questions permutated in various ways. I overrode almost all of it. This wasn't a great strategy for brainstorming,  but working through the corrections gave me a ton of understanding.
