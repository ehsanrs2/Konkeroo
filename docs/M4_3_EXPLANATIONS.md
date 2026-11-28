# M4.3 — Persian educational explanations

Tracking: #61. Predecessor: #59 / merged #60. Baseline main: 5aecff6ecc9ef603685ef7dfe341f0de19e7c92e.

## Local pilot

The private 1391/510A pilot contains 30 explanations, 90 distractor analyses, 30 exact source evidence excerpts and 30 learning tips. Both prior wording caveats are retained. All five input artifact digests matched their M4.2 manifest. The output is a separate database copy and JSON revision, not a production schema migration.

Input packet, AI run and reconciliation revisions are pinned by SHA-256. All question IDs, proposed option positions and comparison states were checked against the frozen records. Each evidence excerpt is a literal substring of the associated question stem or passage. This check establishes provenance, not the semantic correctness of the explanation. All 30 records have exactly three distinct distractor positions excluding the proposed answer.

## Private data contract

The JSON artifact contains schema version, status, publication status, packet SHA-256, AI run SHA-256, reconciliation SHA-256, and explanation records. Each record includes question identity, section, proposed option position, Persian explanation, evidence excerpt and source location, three position-specific Persian distractor reasons, Persian learning tip, original confidence and uncertainty, reconciliation note, provisional status and final_verified=false.

The local SQLite educational_explanation table uses a composite primary key of artifact_sha256 and question_id. Composite foreign keys bind the exact reconciliation and AI run revisions to that same question. The status is PROVISIONAL_EDUCATIONAL_EXPLANATION and final_verified is constrained to zero. Option position, confidence and caveats are available through the referenced prior records; the JSON retains them explicitly. No authority is replaced. This additive staging table is not a claim of application readiness.

## Validation and limits

- Input artifact digests, question identity, evidence substring and distractor coverage passed.
- Output SQLite integrity check returned ok; foreign key check returned no rows.
- All 14 previous tables/views were compared for identical definitions, counts and bidirectional set equality; prior database bytes unchanged.
- No human semantic review, independent answer validation, production importer or release is claimed. Confidence is not calibrated.
- Only aggregate counts and technical metadata enter GitHub. All private educational content, answer values, source passages and database files remain local. D-010 and D-014 remain in force.

The remaining 400 questions are outside this pilot. M4.4 should derive source-linked vocabulary, collocations, grammar and reading skills, distinguish observed source spans from authored learning guidance, and deduplicate concepts without changing the underlying question or answer records. M4.5 should then design active recall learning units before scaling the full pipeline.

Repository CI and review are separate from private validation; this PR adds documentation only.
