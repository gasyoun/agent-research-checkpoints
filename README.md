# agent-research-checkpoints

_Created: 15-11-2026 · Last updated: 15-11-2026_

Three small, independent, dependency-free Python reference fixtures for
agent-workflow discussions. Each module answers one narrow question about
*when a workflow guarantee is actually effective* rather than merely
configured. This repository is a **reference only**: it is not a
framework, has no harness integration, is not a runtime dependency of
anything, and you can read each module in one sitting (stdlib only,
~240 lines combined for the two newest).

## The three fixtures

| Module | Question it answers | Status | Discussion target |
|---|---|---|---|
| [`checkpoints.py`](checkpoints.py) | When is recorded research still fresh enough to act on? | Reviewed; 11 tests (independent logic review 15-11-2026 fixed two semantic blockers) | Comment draft for [obra/superpowers#2129](https://github.com/obra/superpowers/issues/2129) (OPEN; research prior art before design) |
| [`coverage.py`](coverage.py) | Is a lifecycle hook *configured*, *invoked*, and *actually enforcing* at this runtime event — or inert? | Reviewed 15-11-2026: independent review forced one fix — enforcement now requires an observed denial; 11 tests | Comment draft for [open-gsd/gsd-core#6178](https://github.com/open-gsd/gsd-core/issues/6178) (OPEN; opt-in lifecycle-hook contract for quick tasks) |
| [`provenance.py`](provenance.py) | Did the executor that actually ran match the configured model route, on trusted evidence? | Independently reviewed; 7 tests | Distinct opt-in feature draft (observed-executor provenance at delegation acceptance); historical context: [#5260](https://github.com/open-gsd/gsd-core/issues/5260) (CLOSED — fixed argv `--model`) |

All three accompany proposal drafts under [`proposals/`](proposals/);
nothing has been posted upstream. Upstream issue states above were
re-verified with `gh issue view` on 15-11-2026.

## What each fixture pins down

**`checkpoints.py` — research freshness.** A receipt goes stale once ANY
question in its scope is answered afterwards (a merely pending question
invalidates nothing); batch start and completion both fence the whole
scope; a failed research run is never evidence; everything is isolated
per `(repo, session)` scope. Freshness is purely timestamp bookkeeping —
it does not measure semantic-search quality.

**`coverage.py` — effective hook coverage.** A BLOCKING verdict requires
the full chain: configured AND the host exposes the dispatch API AND the
hook opted into this execution mode AND a runtime observation says it
ran AND its violation policy is "block" AND a negative-control
observation attributes an actually-DENIED violation to it.
Configuration plus invocation proves nothing by itself — an adapter can
ignore the block signal or fail open — so a block policy without
observed denial proof stays UNVERIFIED, and a violation that was
observed ALLOWED is MISSED_BLOCK (an ineffective block that fails any
coverage audit). A configured hook on a host without the API is
UNREACHABLE (never enforced); a phase-scoped hook absent during a quick
task is INERT for that mode — its absence is expected and proves neither
a gap nor safety; a "warn" policy is ADVISORY and can never enforce.
Malformed or contradictory facts raise, never guess.

**`provenance.py` — executor provenance.** PASS requires an exact match
between the configured (provider, model) route and a *trusted*
observation of what ran. Same provider but a different model is never
PASS; a permitted fallback inside the allowlist is FALLBACK (still not
PASS); a model's own prose and process output are not trusted
attestation — with no trusted observation the verdict is UNKNOWN, even
when the run reported success. No host adapter or cryptographic
attestation is implemented or claimed.

## Tests

```
python -m unittest -v test_checkpoints test_coverage test_provenance
```

29 tests total, stdlib `unittest` only, deterministic (injectable /
strictly increasing clocks and plain data facts — no I/O, no network).

## Claims this repo does not make

No performance, scale, or production-deployment claims — nothing here
has been deployed, and none of the fixtures are production plugins or
real host adapters. They illustrate acceptance semantics for upstream
discussion; they do not claim to reproduce any upstream bug or implement
any upstream feature (native implementation is the maintainers'
decision, and this repo does not simulate host integration or claim
native enforcement anywhere). Proposal drafts in `proposals/` are
reviewable texts; the implementation examples are independent of upstream.

## Attribution and license

**Dr. Marcis Gasuns**; drafted with **GLM 5.3** (`zai-coding-plan/glm-5.3`),
November 2026. MIT — see [LICENSE](LICENSE).

_Dr. Mārcis Gasūns_
