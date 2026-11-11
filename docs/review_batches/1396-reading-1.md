# 1396 Reading Passage 1 — source-context packet (Q16–19)

**Workflow change (owner decision, 2026-11-11):** this source-context packet is no longer a mandatory human-review handoff. It is a locator for an **assistant-only, mechanically guarded provisional preview** (see [policy](../ASSISTANT_ONLY_PROVISIONAL.md)). The 14 Reading tasks remain **unreviewed by a human**, not automatically accepted or resolved. The historical docket has **19 recorded human decisions / 75 pending**, publication **BLOCKED**.

- **Original printed exam:** `source/96.pdf`, booklet **C**, SHA-256 `69bc3434ae61c05c85bc9fabffd0b2ce13e5b39bc71b1dfd71c16709c9638ba2`.
- **Page locator:** original PDF **page 3** (the header on the scanned page says Persian page 3). Passage 1 begins below the **PART C: Reading Comprehension** box; Q16–19 are near the bottom.
- **Revision-pinned review artifact:** `dataset/review/1396-reading-text-review.json`, Git blob SHA-1 `2f8f9b3c323b2b7173fcf7d8cf237e44804621f1`.
- **Tracking:** [Issue #28](https://github.com/ehsanrs2/Konkeroo/issues/28). Compare against the **rendered original PDF**, not only the PDF text layer or linguistically plausible wording.
- **Evidence convention:** bold in the printed-context column marks the suggested reading at that location. These short excerpts were visually compared to the original PDF page **as navigation guides**; they **do not count as human-approved decisions**.

## Twelve independently decidable editorial proposals

For each task select **`ACCEPTED`**, **`REJECTED`**, or **`NEEDS_FOLLOWUP`** and report what the original page actually displays. The “proposed” column is *candidate printed wording*, not a verified data field.

| Task suffix | Raw text-layer fragment → proposed reading | Printed context to find (target bold) | Where to look on PDF page 3 | Human decision |
| --- | --- | --- | --- | --- |
| `r1396-01` | `lo 1983` → `In 1983` | **In 1983** a new type of phonograph disc reached the marketplace | Passage 1, paragraph 1, **first words** | pending |
| `r1396-02` | `IWO technical systems` → `two technical systems` | made use of **two technical systems:** digital recording and laser beams | Passage 1, paragraph 1, after “compact disc” | pending |
| `r1396-03` | `rhere was` → `there was` | With analog recording, **there was** always a bit of slippage | Passage 1, paragraph 1, middle | pending |
| `r1396-04` | `bit of slippage. which` → `bit of slippage, which` | a **bit of slippage, which** added distortion. Digital recording | Passage 1, paragraph 1, middle | pending |
| `r1396-05` | `Tims the fidelity` → `Thus the fidelity` | eliminated. **Thus the fidelity** of the compact disc is extremely high | Passage 1, paragraph 1, **last sentence** | pending |
| `r1396-06` | `die disc` → `the disc` | device is in contact with **the disc**, and therefore there is no friction | Passage 1, paragraph 2, first lines | pending |
| `r1396-07` | `indefinitely.T his` → `indefinitely. This` | the compact disc should last **indefinitely. This** is in contrast | Passage 1, paragraph 2, middle | pending |
| `r1396-08` | `WhAt is` → `What is` | Q16: **What is** the author's purpose in writing this passage? | Q16 stem, lower portion of page | pending |
| `r1396-09` | `11assage?` → `passage?` | Q16: What is the author's purpose in writing this **passage?** | Q16 stem, same line | pending |
| `r1396-10` | `nostalgia i11 rhe l990s` → `nostalgia in the 1990s` | Q17 choice 1: **nostalgia in the 1990s** | Q17, **choice 1**, bottom portion | pending |
| `r1396-11` | `IS.-` → `18-` | **18-** Which of the following is NOT mentioned as an advantage | Q18 **number marker**, bottom portion | pending |
| `r1396-12` | `~OT mentioned` → `NOT mentioned` | Q18: Which of the following is **NOT mentioned** as an advantage | Q18 stem, immediately beside number | pending |

Only these twelve edits belong to Reading Passage 1. The seven earlier Cloze corrections are not part of this batch. **Do not infer answers to Q16–19 from the text or promote any official-key positions.**

## One nonlocal word-order anomaly — Q19

- Task: `anomaly:reading:r1396-order-q19`; printed PDF **page 3**, **bottom**, Q19 immediately below Q18 options.
- Damaged PDF extraction order: a fragment `as------.` appears on a **separate earlier line**, before `19- The tone...`.
- Printed source reads, in one stem: **“19- The tone of the passage could best be described as”**, followed by a dashed blank; choices below are positive / negative / humorous / argumentative.
- Human task: inspect the complete Q19 stem, its printed leader and whether the extracted trailing **`as`** is already present somewhere else. Choose **`RESOLVED`** *only if* you can explain the complete source-aligned order and treatment of that fragment. Otherwise **`NEEDS_FOLLOWUP`**. A sentence that looks plausible is not sufficient to certify a nonlocal repair.

## One source-printed oddity — preserve, don't autocorrect

- Task ID: `printed:reading:1269c830ea440b51` (digest generated from source page **3** + exact printed fragment `format of the fixture`).
- Location: Passage 1 **paragraph 3, last sentence**, just above Q16.
- Visible printed context: **“as the CD becomes the recording format of the fixture.”**
- The original actually says **fixture**. It may look as though **future** would be more natural English, but there is **no authority to replace what was printed**.
- Choose **`ACKNOWLEDGED`** if your independent check confirms the original printed words; **`DISPUTED`** if your evidence says otherwise. Recording an acknowledgment never authorizes editorial substitution.

## Optional independent review (not required for provisional work)

If an independent human audit is explicitly requested later, compare the 14 items against **page 3 of the original PDF** and use the following format. **Do not request these 14 decisions for current assistant-only provisional development:**

```text
edit:reading:r1396-01: ACCEPTED / REJECTED / NEEDS_FOLLOWUP — page 3, observed: ...
...
edit:reading:r1396-12: ACCEPTED / REJECTED / NEEDS_FOLLOWUP — page 3, observed: ...
anomaly:reading:r1396-order-q19: RESOLVED / NEEDS_FOLLOWUP — complete Q19 order and stray token handling: ...
printed:reading:1269c830ea440b51: ACKNOWLEDGED / DISPUTED — page 3, observed: ...
```

A single owner's batch-level confirmation can be recorded **only as a clearly labeled group-level owner report**, not fabricated per-row quotes. Later decisions must preserve `INDEPENDENT_HUMAN`, `ehsanrs2`, source PDF SHA-256, `evidence_pdf_page: 3`, and this exact Reading review Git blob SHA-1. Proposals and anomaly records stay **pinned and unchanged**; decisions go into a separate ledger PR only after real observations.

After the source-aligned **provisional** Passage 1 implementation: Passage 2 (PDF page 4 and Q25 page-5 bridge), then Passage 3 (page 5). The initial official key remains explicitly unverified. None of these stages implies independently verified or public educational content.
