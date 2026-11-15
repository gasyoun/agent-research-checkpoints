# Proposal draft — effective hook-coverage acceptance fixture (open-gsd/gsd-core#6178)

_Created: 15-11-2026 · Last updated: 15-11-2026_

**Status: reviewed proposal text.** Native upstream implementation requires maintainer approval; these independent examples are discussion material.

## Target thread (existing — do not open a duplicate)

[open-gsd/gsd-core#6178](https://github.com/open-gsd/gsd-core/issues/6178)
«Opt-in lifecycle-hook contract for quick tasks (`/gsd-quick`,
`/gsd-quick-batch`)» — OPEN as of 15-11-2026. The issue documents the
real gap that hook *registered* ≠ hook *reachable/effective* per host
and mode, with a per-host dispatch matrix and a checkpoint ledger.

## What our prototype illustrates

A ~130-line stdlib-only classifier distinguishing the states #6178's
matrix implies, as a **small acceptance fixture** — we are NOT
implementing the upstream feature (that is the maintainers' decision)
and we claim no native gsd-core bug:

- [coverage.py](https://github.com/gasyoun/agent-research-checkpoints/blob/main/coverage.py)
  (reference contract, MIT)
- [test_coverage.py](https://github.com/gasyoun/agent-research-checkpoints/blob/main/test_coverage.py)
  — 11 unit tests with positive and negative controls

Verdicts it separates: `BLOCKING` (configured + host has the dispatch
API + opted into this execution mode + observed running + policy
"block" + a negative-control observation attributes an actually-DENIED
violation) vs `ADVISORY` (ran with a warn policy — can only advise,
never enforce) vs `MISSED_BLOCK` (ran with a block policy but an
attributed violation was observed ALLOWED — the block was ineffective
and must fail the audit) vs `UNVERIFIED` (block policy without observed
denial proof — configuration plus invocation prove nothing) vs
`INERT_FOR_MODE` (phase-scoped hook absent during a quick task —
expected, proving neither a gap nor safety) vs `UNREACHABLE_HOST` (host
lacks the API — never enforced) vs `MISSED_DISPATCH` (observed absent
where expected) vs `NOT_CONFIGURED`.

The enforcement gate came from review, not intuition: an earlier draft
of this fixture treated "configured + invoked + block policy" as
enforced, and an independent logic review rejected exactly that — an
adapter can ignore the block signal or fail open, so only an observed,
attributed denial counts.

## Minimal upstream desired acceptance

Not adoption of our code — a handful of acceptance cases the #6178
contract should be testable against:

1. A hook whose host lacks the dispatch API must never be reported as
   enforcing, however it is configured; a "ran anyway" claim on such a
   host is a contradiction that fails the audit, not a pass.
2. A hook not opted into the current mode (`executionContexts`) being
   absent there is EXPECTED — that absence is not proof of a coverage
   gap, and its presence is a contract signal worth surfacing.
3. "Enforced" is gated on the full chain: configuration + host capability
   + a runtime dispatch observation + an OBSERVED, ATTRIBUTED DENIAL. A
   block policy with no denial proof ⇒ UNVERIFIED, never enforced; a
   violation observed allowed ⇒ MISSED_BLOCK, and the coverage audit
   fails.
4. Malformed or unknown facts (modes, tokens, non-bool flags) fail the
   audit loudly — the classifier never guesses.

## Limits, stated plainly

Reference contract only: no host adapter, no manifest/transcript
parsing, no gsd-core internals read or reproduced; no deployment, no
performance claims. Native implementation of #6178 requires maintainer
approval; no upstream PR is planned from us.

_Dr. Mārcis Gasūns_ · drafted with GLM 5.3 (`zai-coding-plan/glm-5.3`)
