# 250,000-question background factory

This directory tracks a bounded, resumable discovery run for **250,000 new
Malay review candidates** across the same 300 topics.

The worker uses Wikimedia's public MediaWiki/Wikidata endpoints and Python's
standard library. It does not call Gemini, OpenAI, Anthropic, or another LLM,
so it consumes no model/API-generation tokens. It still uses network bandwidth,
CPU time, disk space, and Wikimedia request capacity.

## Safety contract

- Every result remains `pending_owner_review`; production approval is always
  false.
- Exact questions, repeated source facts, same-topic repeated answers, and
  near-duplicates sharing an answer are rejected.
- Local answer-derived seed pages cannot bypass source search relevance.
- Candidates are published as JSONL shards of at most 5,000 records, avoiding
  GitHub's 100 MB single-file limit.
- Checkpoints are saved after each ten-topic source job.
- The worker exits automatically when the target is reached.
- If the safe source sweep cannot reach the target, it exits as
  `SOURCE_EXHAUSTED`; it never pads the count with weak material.

`status.json` is the machine-readable live status. A completed batch is still
only a review batch and must not be loaded into the production bot without
manual review.

Run `python3 factory/validate_factory.py` from the repository root to validate
all currently published factory batches against the original public review
pack.
