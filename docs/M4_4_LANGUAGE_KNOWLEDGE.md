# M4.4 — Language knowledge

Tracking: #63; predecessor #61 / merged #62. Baseline main: 3d654c67e2440ad4cb801d48523d328ba7763df5.

## Private pilot

The 1391/510A pilot now contains 119 distinct provisional concepts (64 vocabulary, 27 collocations, 12 grammar, 10 skills, 6 semantic relations) and 130 question-concept links covering all 30 questions. Eight concepts occur in multiple questions. All 40 vocabulary option positions were considered. This is a curated selection, not exhaustive extraction of every word or grammatical structure in the corpus.

The JSON artifact pins the key-excluded packet and explanation artifact by SHA-256. Every link has a literal anchor in its associated question stem, option or shared passage; source kind, reference and zero-based Unicode code-point offsets (end exclusive) identify the selected occurrence. Of the 130 links, 91 are source-anchored concepts and 39 authored guidance. Labels and Persian glosses are authored even when their supporting spans are literal. Added examples, contrastive vocabulary and strategy guidance are not represented as verbatim source text. When an anchor occurs more than once, the pilot uses the first matching field in stem/option/passage order and the first occurrence in that field.

## Additive staging schema

- language_concept: composite key (artifact_sha256, concept_id), category, normalized English label, Persian gloss or guidance, provisional status, final_verified constrained to zero.
- question_concept: composite key (artifact_sha256, concept_id, question_id), exact explanation revision, source kind/reference/offsets/excerpt and derivation type. Foreign keys bind the concept and the exact explanation revision for that question.
- Concept IDs are derived from a SHA-256 prefix of category and case-folded label. Identical labels within a category are reused only when their glosses agree. This is pilot-level deduplication, not a general word-sense ontology; distinguish different senses or parts of speech explicitly.
- Prior uncertainty notes remain in the referenced explanations/reconciliation and in the private knowledge JSON. No answer authority is changed.

## Validation and limits

All six input files listed in the M4.3 manifest matched their recorded digests. All anchors were found in permitted fields, all question IDs covered, no duplicate concept/question pair, both prior uncertainty caveats retained, SQLite integrity ok and zero foreign-key violations. All 15 prior tables/views were compared for definitions, counts and bidirectional set equality; prior database bytes unchanged.

This was assistant curation plus local structural validation, not independent semantic approval, production migration or comprehensive lexical coverage. No public importer or automated linguistic extraction is introduced. No private questions, answer values, excerpts, knowledge records or database are committed. D-010 / publication BLOCKED. D-014 remains applicable. Repository CI and review are separate; this PR is documentation only.

## Next: M4.5

Create provisional active-recall learning units from the pilot: meaning retrieval, production, contextual completion, grammar discrimination, and reading strategy practice as appropriate. Separate prompt from feedback/expected answer; bind each unit to concept revision and provenance; avoid using identical prompts as independent mastery evidence. Define scoring and review eligibility, keep user learning state separate from content, and preserve uncertainty restrictions. Validate a complete pilot learning cycle before expanding to the remaining 400 questions or implementing Android. 
