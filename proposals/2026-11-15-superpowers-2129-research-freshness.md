# Proposal draft — research-freshness acceptance cases (obra/superpowers#2129)

_Created: 15-11-2026 · Last updated: 15-11-2026_

**Status: reviewed proposal text.** Native upstream implementation requires maintainer approval; these independent examples are discussion material.

## Target thread (existing — do not open a duplicate)

[obra/superpowers#2129](https://github.com/obra/superpowers/issues/2129)
«brainstorming: research prior art / existing solutions before design» —
OPEN as of 15-11-2026. History: the topic was moved there by the
maintainer from CLOSED
[#983](https://github.com/obra/superpowers/issues/983);
[PR #2116](https://github.com/obra/superpowers/pull/2116) is open/unmerged
and implements conditional prior-art research after the questions.

## What our prototype illustrates

A ~170-line stdlib-only reference state machine pinning WHEN recorded
research is still fresh enough to act on — the subtle half of
"research before design" that #2129/#2116 will need acceptance cases
for, beyond "run the research":

- [checkpoints.py](https://github.com/gasyoun/agent-research-checkpoints/blob/main/checkpoints.py)
  (reference fixture, MIT)
- [test_checkpoints.py](https://github.com/gasyoun/agent-research-checkpoints/blob/main/test_checkpoints.py)
  — 11 unit tests; run `python -m unittest -v test_checkpoints`
- Reviewed 15-11-2026: an independent logic review found and fixed two
  semantic blockers (answer-staleness must cross questions; batch
  completion must also be a boundary).

## Minimal upstream desired acceptance

Not adoption of our code — four acceptance cases any implementation of
#2129 should pass:

1. Research recorded while questions are pending stays valid; the moment
   ANY question in the scope is answered, receipts recorded before that
   answer are stale — even if the answered question is not the one that
   was researched.
2. Batch start and batch completion are both fences for the whole scope
   (a spawned worker's pre-batch receipts never count as the batch's
   research; a final review needs research refreshed after completion).
3. A failed research run is never evidence ("we tried" is not fresh).
4. Scope isolation: one session's answers never invalidate another
   session's receipts; cross-scope lookups fail loudly.

## Limits, stated plainly

The fixture is not a superpowers plugin; freshness is timestamp
bookkeeping only and does not measure semantic-search quality; it has
not been deployed at scale, so no performance claims are made or
implied. If #2116 already handles any case differently, treat this as a
cross-check, not an objection. Native implementation is the
maintainer's call; no upstream PR is planned from us.

_Dr. Mārcis Gasūns_ · drafted with GLM 5.3 (`zai-coding-plan/glm-5.3`)
