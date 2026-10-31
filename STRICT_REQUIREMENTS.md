# Strict question requirements

These rules are mandatory and fail closed. A shortfall is reported; it is
never filled with an unverified or weak question.

## Required pack shape

1. Exactly 300 topic files.
2. Exactly 10 accepted questions per topic.
3. Exactly 3,000 accepted questions overall.
4. Stable unique IDs in the form `strict-NNN-XX`.
5. Each topic has a unique compact display name of at most 28 characters.
6. The original full topic scope is preserved separately; shortening a display
   name may not broaden or change what belongs in that topic.

## Required question quality

1. Malay language.
2. A direct, compact question no longer than 160 characters.
3. An answer no longer than 80 characters or 10 words.
4. The answer must not appear in the question.
5. No compound “same answer for two clues” construction.
6. No exact duplicate or near-duplicate against the live bank.
7. No exact duplicate, near-duplicate, repeated source fact, or repeated answer
   inside the same topic pack.
8. The question must match its assigned topic, not merely share a generic word.

## Required evidence

1. Wikimedia records link to a fixed Malay or English Wikipedia revision
   (`oldid`) and their Wikidata entity.
2. A Wikimedia structured claim must be visible in the cited lead or carry a
   source reference, or the question must be a faithful identity definition.
3. Where Wikimedia coverage is insufficient, an official-source record must
   include its publisher, retrieval date, exact evidence excerpt, excerpt
   SHA-256, and a unique source-fact ID.
4. Source metadata and evidence fields may not be removed.

## Approval policy

Passing automation means **reviewable**, not error-free and not approved for
production. Human owner review is mandatory. A record remains
`pending_owner_review` until that review is completed separately.

Any failed rule blocks publication as a completed pack and blocks production
activation.
