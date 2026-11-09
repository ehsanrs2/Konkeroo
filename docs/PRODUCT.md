# Product vision and learning contract

## Mission

**Konkeroo** is an adaptive, exam-driven English learning system, initially targeting the English section of Iran's Computer Engineering master's entrance exam. It should help a learner understand the language, retrieve knowledge reliably, transfer skills to unseen questions, and use study time effectively—not merely memorize answer positions.

The project begins with approximately 15 exam years (1391–1405), with original papers and official keys where available. The 1405 corpus currently has no official key. Coverage and English question numbering vary by year and must be established from the actual paper.

## Intended learner experience

1. Diagnose vocabulary, cloze, and reading performance through source-linked exam questions and relevant practice.
2. Study with contextual explanations, vocabulary word families, and evidence-backed feedback.
3. Practice **active recall**, **spaced repetition**, and **interleaving**, rather than only repeated passive review.
4. Adapt study selection based on mastery, retention, accuracy, response time, mistakes, and confidence, while avoiding misleading single-number mastery claims.
5. Track learning trends and transfer to **unseen** questions; distinguish performance improvement from repeated exposure.
6. Support motivation with quality-based streaks, daily quests, and achievements, avoiding incentives for rapid guessing or meaningless activity.
7. Eventually use an offline-friendly Android interface with clear accessibility and privacy boundaries.

These are **target capabilities**, not descriptions of current working product features.

## Content quality contract

- Original exam text, detected OCR/text-layer defects, normalized content, human corrections, and generated explanations must remain distinguishable.
- All questions, options, blanks, and passages should retain traceable source provenance.
- An official answer is evidence of the **source key's claim**, not an infallible semantic truth. Record key edition (e.g., initial) and special scoring annotations.
- AI answers should be generated independently of the official key when used for cross-checking, then compared rather than silently replacing the official source.
- A learner-facing answer/explanation is published only after an explicit verification policy is satisfied; ambiguity must remain visible.
- Some sources permit multiple accepted positions, deleted questions, and positive-effect annotations; do not flatten these into ordinary single-option keys.

## Success criteria (future evaluation)

- **Data reliability:** reproducible imports, complete expected question mapping, independently checkable source references, visible unresolved cases.
- **Learning value:** retention after delays, calibration of confidence, accuracy and latency trends, and generalization to held-out exam questions.
- **Usability:** manageable daily sessions, comprehensible feedback, accessible reading experience, and sensible offline operation.
- **Trust:** explanations identify their basis; the system distinguishes official, AI, and verified outcomes.

No efficacy benefit is claimed before a proper evaluation design and evidence exist.

## Scope boundaries

In scope over time: corpus ingestion, official-key parsing, review workflows, language analysis, curriculum/skill tagging, adaptive practice, analytics, motivation, and Android delivery.

Out of scope **today**: launching the Android app, AI-correcting source text without review, choosing answers by model consensus alone, publishing full exam-derived datasets by default, or inferring an official key where none exists.

Potential reuse for broader English exams is a future product question, not a reason to hard-code generic assumptions prematurely.
