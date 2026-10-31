# IRCdPro Trivia — Strict 300 × 10 Review Pack (WIP)

This repository is the public, review-only workbench for 10 new Malay trivia
questions for each of 300 existing topics (3,000 questions total).

**Current gate: `STRICT-FAIL-NOT-PUBLISHABLE`.** The current conservative
snapshot contains 2,539 automated candidates; 461 slots remain unfilled. It is
published for transparent review and progress tracking, not as a completed
question pack.

The snapshot is **not production-approved**. Every retained record is linked to a
fixed Wikipedia revision plus Wikidata, or to explicit evidence from a
first-party official source. The questions remain in Malay even when a sparse
topic requires an English source. The owner must
review and approve the records before they are imported into the live bot.

The authoritative status is `manifest.json`; README prose never overrides it:

- `STRICT-PASS-REVIEW-ONLY` means the automated strict gate passed.
- `STRICT-FAIL-NOT-PUBLISHABLE` means the pack is incomplete or invalid.
- `production_approved` remains `false` until a separate owner-review step.

See [STRICT_REQUIREMENTS.md](STRICT_REQUIREMENTS.md) for the fail-closed rules.

## Layout

- `questions/` — one JSONL file per topic
- `topic-names.json` — compact display name and preserved full scope for all topics
- `all-questions.jsonl` — all accepted records in topic order
- `manifest.json` — authoritative gate status and counts
- `deficits.json` — topics that did not meet exactly ten questions
- `validation-failures.json` — rejected records and reasons
- `validate.py` — independent repository validator

See [AUDIT_FINDINGS.md](AUDIT_FINDINGS.md) for rejected generation passes and
known limitations. No question in this repository is automatically loaded by
the production bot.
