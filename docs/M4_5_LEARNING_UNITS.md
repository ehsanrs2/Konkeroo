# M4.5 — Active-recall learning units

Tracking: #65; predecessor #63 / merged #64. Baseline main: 9c35dd6ac42638f3c24678b9e253d18334ace860.

## Private pilot

119 provisional learning units cover all 119 concepts and, through their existing relationships, all 30 pilot questions. There are 64 meaning recall, 27 contextual completion, 12 grammar application, 10 strategy practice and 6 semantic contrast units. Each has one separate feedback record. Practice prompts are authored, not presented as source quotations; lexical meanings derive from M4.4. Context completion and strategy scenarios are authored exercises. There is only one unit per concept in this pilot, not independent evidence of mastery or comprehensive coverage. Some completions admit alternative valid responses.

The private JSON pins the M4.4 knowledge artifact SHA-256. The SQLite learning_unit table binds the exact knowledge revision and concept ID through a composite foreign key. Its primary key is (artifact_sha256, unit_id); the learning_unit_feedback table references that exact unit revision. The learning_unit_prompt view projects explicit prompt-only fields. Feedback includes expected answer, Persian guidance, and inherited caveats. Six units linked to the two earlier wording uncertainties are marked REVIEW_REQUIRED and excluded from the private practice cycle. The remaining 113 are PRIVATE_PILOT_ONLY, not released or final verified.

## Practice cycle

The standard-library Python module english_exam.m4_practice provides an in-memory PracticeSession: prompt -> explicit retrieval attempt (including abstention) -> reveal -> self-assessment (again, hard, good, easy). It refuses unknown revisions, review-required units, out-of-order transitions, missing feedback and invalid ratings. The event identifies the exact unit revision and rating, not a mastery estimate. Use a read-only connection against a fixed private database snapshot. The view and session API separate display fields from feedback; they are not a security boundary against a caller with raw database access. No automatic scoring, learner identity, durable event storage, due-date scheduling or Android UI is implemented.

## Validation

- All nine files listed by the M4.4 input manifest matched their SHA-256 pins.
- All 119 concept IDs covered exactly once; distinct prompts and unit IDs; both caveats retained.
- SQLite integrity ok, zero foreign-key violations. Definitions, counts and bidirectional row-set comparisons for all 17 prior tables/views passed. Input database hash unchanged.
- Three synthetic pytest tests passed in the local isolated module harness. A read-only scripted integration exercised all 113 eligible private units and rejected all six review-required units; database bytes unchanged. This is a software check, not a human learning trial.
- Full repository CI, Ruff and semantic review remain separate and unconfirmed.

No private content, answers, databases or artifacts are committed; D-010 publication remains blocked. D-014 continues to apply. No production migration or final verification is claimed.

## Next

Review pilot educational quality and build a reproducible batch content workflow for the remaining 400 questions. In parallel where appropriate, define versioned learner event storage, deterministic review scheduling and concept-level evidence aggregation using synthetic fixtures. Evaluate retention with actual learners before claiming learning efficacy. Android remains downstream of the content and release gates.
