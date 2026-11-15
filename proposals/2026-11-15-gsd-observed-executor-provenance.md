# Proposal draft — opt-in observed-executor provenance checks (new gsd-core feature)

_Created: 15-11-2026 · Last updated: 15-11-2026_

**Status: reviewed proposal text.** Native upstream implementation requires maintainer approval; these independent examples are discussion material.

## Relationship to existing threads (verified 15-11-2026 via `gh issue view`)

- [open-gsd/gsd-core#6178](https://github.com/open-gsd/gsd-core/issues/6178)
  is OPEN, with maintainer engagement (go, with conditions) — that
  thread is about the lifecycle-hook contract and is separate.
- [open-gsd/gsd-core#5260](https://github.com/open-gsd/gsd-core/issues/5260)
  is CLOSED — fixed by adding `--model` to the OpenCode worktree argv.
  It is cited here ONLY as historical context: it established that
  executor-model intent used to be lost at the launch boundary, and the
  fix pinned the *configured* route. This proposal is NOT a duplicate of
  that bug report.
- The distinct, narrow gap this feature addresses, verified against
  `next` on 15-11-2026: the execute-phase cross_ai_delegation acceptance
  seam in
  [gsd-core/workflows/execute-phase/detail/elaboration.md](https://github.com/open-gsd/gsd-core/blob/7977b4762a2fdabd617d9ccc81b770cdf8a4a5b2/gsd-core/workflows/execute-phase/detail/elaboration.md)
  accepts a delegated run on exit code 0 plus a meaningful
  heading/description/SUMMARY — there is no model-identity proof in that
  acceptance seam. This is a claim about that seam only; gsd-core may
  well have provenance machinery elsewhere, and nothing here asserts
  otherwise.

## Problem (scoped)

With `cross_ai_execution`, a phase's execution is delegated to an
external AI CLI. Acceptance at the elaboration seam checks that the
delegate produced structured output and exited 0. It does not check
*which model actually executed the phase*. A user who pinned an executor
model (the thing #5260 fixed how to express) has no acceptance-level
answer to "did the run I am about to build on actually come from the
route I asked for, or from whatever the delegate's session default was
that day?" Exit 0 and a tidy SUMMARY do not distinguish a configured
executor from a silent substitution.

## Benefit

- Turns "which model ran" into an acceptance-level, auditable fact
  instead of a launch-argv hope, for users who care about reproducibility
  and cost attribution.
- Gives delegated phases the same identity discipline the #5260 fix
  gave launch configuration — closing the loop from *configured* intent
  to *observed* execution.
- Small, opt-in surface: one check at one acceptance seam, no new
  workflow phases.

## Native extension point (where this would live)

The elaboration/delegation acceptance step: when `cross_ai_execution`
is enabled and the user opts in, acceptance additionally records a
provenance fact (configured route, observed route, evidence source,
verdict) beside the existing SUMMARY acceptance. The check is a seam
addition, not a new component: same file, same lifecycle point, default
off.

## User stories

1. As a user delegating execution to a cheaper model, I want acceptance
   to FAIL (not silently pass) when the observed executor differs from
   my configured route, so a session-default substitution never
   masquerades as my pinned executor.
2. As a user who occasionally permits fallback within a known allowlist,
   I want fallback recorded explicitly as FALLBACK — never silently
   reported as the configured route — so my audit trail distinguishes
   "asked and got" from "asked, got substitute, allowed it".
3. As a user whose delegate reports success but whose host telemetry
   carries no identity evidence, I want the verdict to be UNKNOWN rather
   than PASS, so "successful-looking" never attests identity.
4. As a maintainer, I want the feature default-off and stdlib-testable,
   so existing workflows are byte-for-byte unaffected until opted in.

## Acceptance cases (the contract, not the code)

1. Exact match between the configured (provider, model) route and a
   TRUSTED observation of what ran, route inside the allowlist ⇒ PASS.
2. Trusted channel reports nothing, or only untrusted evidence (the
   model's own prose, process output) ⇒ UNKNOWN — even if the run
   reported success.
3. Observed route differs, fallback not permitted ⇒ MISMATCH
   (acceptance fails); fallback explicitly permitted and inside the
   allowlist ⇒ FALLBACK (recorded, still not PASS).
4. Configured route outside the allowlist ⇒ MISMATCH — never a quiet
   PASS.
5. No implicit fallback: every substitution is either explicitly
   permitted-and-recorded or a failure. There is no third state.
6. Malformed provenance facts (half-filled identities, unknown evidence
   sources) fail loudly — the checker never guesses.

A ~100-line stdlib reference fixture pinning exactly these cases
(accompanying this series, MIT):

- [provenance.py](https://github.com/gasyoun/agent-research-checkpoints/blob/main/provenance.py)
- [test_provenance.py](https://github.com/gasyoun/agent-research-checkpoints/blob/main/test_provenance.py)
  — 7 unit tests; run `python -m unittest -v test_provenance`

## Alternatives considered

- **Status quo** (trust exit 0 + SUMMARY): cheapest, but cannot answer
  the substitution question at all — that is the gap.
- **Full cryptographic attestation** (signed manifests from executors):
  strongest evidence class, but heavy: new trust infrastructure, executor
  cooperation, key management. Overkill for the acceptance-seam question;
  this proposal deliberately requires only that the evidence SOURCE be
  explicit and trusted-by-the-host, whatever the host decides that is.
- **Log scraping post-hoc**: no acceptance semantics — discovers
  substitutions after acceptance already passed, which is the failure
  mode being fixed.

## Runtime compatibility & maintenance

- Default OFF; zero behavior change for every existing workflow until a
  user opts in per-configuration.
- One seam, one fact type, one verdict function: small to review, small
  to maintain; stdlib-unit-testable with plain data facts (no I/O, no
  network) — the reference fixture demonstrates the test surface.
- What counts as a trusted evidence channel stays a host decision; the
  contract only requires the decision to be explicit.

## Limits, stated plainly

The reference fixture is not a gsd-core plugin, has no host adapter, and
does not simulate host integration or claim native enforcement; it has
not been deployed, and no performance claims are made or implied. No
live-run observations of gsd-core are claimed — the seam description is
from the public `next` branch as of 15-11-2026. Native implementation is
the maintainers' call; no upstream PR is planned from us.

_Dr. Mārcis Gasūns_ · drafted with GLM 5.3 (`zai-coding-plan/glm-5.3`)
