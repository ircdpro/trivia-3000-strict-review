# Audit findings

## Current status

- Automated candidates retained: 2,539 of 3,000.
- Topic files present: 300 of 300.
- Topics still below ten candidates: 128.
- Automated cross-pack validation failures: 14.
- Production approval: **false**.

The strict gate deliberately fails while any count, duplication, evidence, or
review requirement is unmet.

## Rejected experiments

Two higher-yield fallback passes were discarded after semantic spot audits.
They produced valid-looking source links but matched ambiguous entity names to
the wrong topic. Examples included a country under Malaysian ten-pin bowling
and a television network under Malaysian targeted subsidies.

Those passes are not included in this repository. This is why missing slots
remain empty instead of being padded to 3,000.

## Human review

Source-backed automation verifies record shape, fixed source revisions,
duplicate thresholds, and structured claim support. It does not prove that
every topic assignment is editorially ideal. Each record therefore remains
`pending_owner_review`; human approval is mandatory before import.
