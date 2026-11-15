"""executor provenance — configured vs trusted observed identity (illustrative).

Portable sketch of one question: did the executor that ACTUALLY ran match
the model the configuration/launch argv asked for? Companion fixture for
a DISTINCT opt-in feature draft (see proposals/): an observed-executor
provenance check at delegation acceptance. Historical context:
open-gsd/gsd-core#5260 is CLOSED — fixed by adding --model to the
OpenCode worktree argv — and is cited only as motivation. The narrow gap
verified 15-11-2026 against main: the execute-phase cross_ai_delegation
acceptance seam (gsd-core/workflows/execute-phase/detail/elaboration.md)
accepts exit 0 plus a meaningful heading/description/SUMMARY and asks
for no model-identity proof in that seam — a claim about that seam only,
not about gsd-core at large. This module is an acceptance contract, not
a repro of their internals.

Semantics (each pinned by a test):

1. PASS requires an EXACT match between the configured (provider, model)
   route and a TRUSTED observation of what ran, and the configured route
   must be inside the allowlist. Same provider but a different model is
   never PASS.
2. Identity evidence is only trusted from the host/telemetry channel.
   A model's own prose ("I am model X") and process output are NOT
   trusted attestation: with no trusted observation the verdict is
   UNKNOWN — even if the run reported success.
3. Observed identity differing from the configured route is a fallback:
   MISMATCH when fallback is not permitted; FALLBACK (still not PASS)
   when it is explicitly permitted and the observed route is inside the
   allowlist. A configured route outside the allowlist is MISMATCH.
4. Malformed facts (empty identities, half-filled identities, unknown
   source tokens) raise ValueError — the checker never guesses.

Reference contract only: no host adapter is implemented and no
cryptographic attestation is claimed or possible here. What a real host
counts as its trusted channel is that host's decision; this module only
requires that the decision be explicit.

MIT License. (c) 2026 Dr. Marcis Gasuns. Drafted with GLM 5.3, November 2026.
"""
from collections import namedtuple

TRUSTED_SOURCES = ("host_telemetry",)
UNTRUSTED_SOURCES = ("model_self_report", "process_output")
KNOWN_SOURCES = TRUSTED_SOURCES + UNTRUSTED_SOURCES

PASS = "PASS"
MISMATCH = "MISMATCH"
UNKNOWN = "UNKNOWN"
FALLBACK = "FALLBACK"

ProvenanceFact = namedtuple(
    "ProvenanceFact",
    ["configured_provider", "configured_model", "observed_provider",
     "observed_model", "observed_source", "fallback_permitted",
     "run_reported_success"])


def _identity(provider, model):
    """Validate one (provider, model) identity; both or neither present."""
    present = (provider is not None, model is not None)
    if present[0] != present[1]:
        raise ValueError("identity must be fully present or fully absent: "
                         "provider=%r model=%r" % (provider, model))
    if provider is not None:
        for part in (provider, model):
            if not isinstance(part, str) or not part:
                raise ValueError("identity parts must be non-empty strings")
    return None if provider is None else (provider, model)


def _validate(fact):
    if not isinstance(fact.fallback_permitted, bool):
        raise ValueError("fallback_permitted must be a bool")
    if not isinstance(fact.run_reported_success, bool):
        raise ValueError("run_reported_success must be a bool")
    if fact.observed_source not in KNOWN_SOURCES:
        raise ValueError("unknown observation source %r (expected one of %s)"
                         % (fact.observed_source, KNOWN_SOURCES))


def verify(fact, allowlist):
    """Verdict for one executor run against an allowlist of routes.

    ``allowlist`` is a set of (provider, model) tuples that may be used.
    Note: ``run_reported_success`` deliberately cannot influence the
    verdict — a successful-looking run never attests its own identity.
    """
    _validate(fact)
    configured = _identity(fact.configured_provider, fact.configured_model)
    if configured is None or configured not in allowlist:
        return MISMATCH  # nothing valid was asked for
    if fact.observed_source not in TRUSTED_SOURCES:
        return UNKNOWN   # no trusted channel: identity simply unknown
    observed = _identity(fact.observed_provider, fact.observed_model)
    if observed is None:
        return UNKNOWN   # trusted channel, but it did not report identity
    if observed == configured:
        return PASS
    if fact.fallback_permitted and observed in allowlist:
        return FALLBACK
    return MISMATCH


def passed(fact, allowlist):
    return verify(fact, allowlist) == PASS
