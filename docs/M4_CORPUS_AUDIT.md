# M4 corpus audit and provisional concept grouping

Tracking: #83; predecessor #81 / merged #82. Baseline main: 357ca4cc678ae68b45f589357a2f6618bfafd9de.

## Structural audit

The private complete-coverage archive and all 30 manifest-listed file digests were verified. The private database was opened read-only. All 430 explanations were checked for identity, exact evidence location, nonempty educational fields and option-analysis position coverage, including the separately corrected answer and abstentions. All 914 source anchors were checked by exact Unicode offsets against the associated question, option or passage. All 902 practice units and feedback rows were checked for coverage, nonempty content and valid revision links. No existing risk-gate bypass was found for registered source defects, uncertainty, abstentions or answer conflicts.

All 105 review-required prompts and expected answers were screened at prompt level. Two proposed rewrites address underdetermined context and remain unapplied; none of the 105 gates was cleared. The other 797 units retain their existing private self-assessment eligibility, not semantic approval. This is not a full independent semantic review of every explanation and practice unit. No original PDF reinspection, new printed-defect confirmation or final answer promotion is claimed.

## Conservative cross-revision grouping

41 repeated kind/normalized-label groups were identified. Nineteen groups whose registered Persian glosses also match were grouped provisionally; the remaining 22 same-label groups with differing glosses stay separate pending sense/usage review. The mapping contains 878 clusters for all 902 original records (24 redundant memberships), preserving every original record, unit, feedback item, source link and revision. Matching is a conservative heuristic, not proof of semantic equivalence, lemmatization or comprehensive word-sense deduplication.

The private cluster index stores member counts, distinct linked question counts, distinct year counts and distinct source-anchored question counts separately. These are counts of curated relationships, not exhaustive corpus token frequencies or evidence of exam importance. 21 repeated unit-type/prompt groups contain 48 practice records. Flag them as non-independent mastery evidence; no scheduling or mastery algorithm is implemented and no exercise was deleted or disabled by grouping.

## Additive private artifact

The audit JSON is bound to the exact input database SHA-256. Four additive SQLite tables record explanation audit rows, provisional clusters, concept memberships and unit audit rows, with revision foreign keys. Pending sense groups and two prompt rewrite proposals are included in the private JSON. All 25 pre-existing tables/views and rows were preserved; definitions, counts and bidirectional row equality checked. Input database digest unchanged. SQLite integrity check passed, foreign-key violations zero, and the output archive was reopened and verified against its manifest.

All 430 frozen first-pass records, reconciliation records, two conflict reviews, 170 blocked alignments, and existing D-015 source quality records remain unchanged. No final verified answer, independent learning outcome, release or mastery claim. Earlier private packages remain necessary for complete provenance. D-010 remains BLOCKED.

Next: review the 22 pending label groups by sense, context and part of speech; continue semantic review of the corpus, including the 105 gated units and proposed rewrites; implement versioned learner event persistence and deterministic scheduling against synthetic fixtures. Use cluster mappings without treating duplicate prompts as separate mastery evidence. This PR is documentation only, with no private content or public runtime change. Full repository CI remains unconfirmed.
