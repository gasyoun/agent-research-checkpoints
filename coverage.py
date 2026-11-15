"""hook coverage — configured vs invoked vs enforcing (illustrative).

Portable sketch of the difference between a lifecycle hook that is
*configured*, one that was *invoked*, and one that is *actually
enforcing* at a runtime event. Companion fixture for the upstream
discussion in open-gsd/gsd-core#6178 (opt-in lifecycle-hook contract
for quick tasks).

Semantics (each pinned by a test):

1. A verdict of BLOCKING requires the full chain: configured AND the host
   exposes the dispatch API for it AND the hook opted into this execution
   mode AND a runtime observation says it actually ran AND its violation
   policy is "block" AND a negative-control observation attributes an
   actually-DENIED violation to it. Configuration plus invocation proves
   neither: an adapter can ignore the block signal or fail open, so
   without an observed denial the chain is UNVERIFIED — never enforced.
2. A hook that ran with a "block" policy while an attributed violation
   was observed ALLOWED did not enforce: MISSED_BLOCK. It must fail any
   "is this hook effective here?" audit; it is not a pass.
3. A configured hook on a host that lacks the dispatch API is
   UNREACHABLE_HOST — INERT, never ENFORCED. Facts claiming the hook ran
   on a host without the API are contradictory and raise ValueError:
   the classifier never guesses, and it never reports ENFORCED on the
   basis of a claim it cannot reconcile. A denial observation without a
   "reached" dispatch observation is the same class of contradiction.
4. A hook not opted into the current mode (e.g. a phase-scoped hook
   observed during a quick task) is INERT_FOR_MODE — its not running is
   EXPECTED and is NOT proof of a coverage gap, and not proof of safety
   either. It running anyway is UNEXPECTED_DISPATCH (a contract signal).
5. No dispatch observation recorded yet → UNVERIFIED; observed NOT
   running where it was expected → MISSED_DISPATCH. Silence is never
   treated as enforcement.
6. A "warn" policy is ADVISORY by construction and can never be
   enforced; a denial attributed to a warn-policy hook is a
   contradiction, not evidence of enforcement.

This module is a reference contract only: it has NO host adapter, does
not read manifests or transcripts, does not simulate any host
integration, and does not implement any part of the upstream feature
(that is the maintainer's call). Positive control: the BLOCKING verdict
(observed, attributed denial). Negative controls: NOT_CONFIGURED,
UNREACHABLE_HOST, INERT_FOR_MODE, UNVERIFIED (block policy without
denial proof), MISSED_BLOCK (violation observed allowed).

MIT License. (c) 2026 Dr. Marcis Gasuns. Drafted with GLM 5.3, November 2026.
"""
from collections import namedtuple

MODES = ("phase", "quick")
DISPATCH_TOKENS = ("reached", "not_reached")
VIOLATION_POLICIES = ("block", "warn")

NOT_CONFIGURED = "NOT_CONFIGURED"
UNREACHABLE_HOST = "UNREACHABLE_HOST"
INERT_FOR_MODE = "INERT_FOR_MODE"
UNEXPECTED_DISPATCH = "UNEXPECTED_DISPATCH"
UNVERIFIED = "UNVERIFIED"
MISSED_DISPATCH = "MISSED_DISPATCH"
MISSED_BLOCK = "MISSED_BLOCK"
ADVISORY = "ADVISORY"
BLOCKING = "BLOCKING"

HookFact = namedtuple("HookFact", ["hook", "event", "mode", "configured",
                                   "host_capability", "mode_opted_in",
                                   "dispatch", "on_violation",
                                   "violation_blocked"])


def _validate(fact):
    """Reject malformed/unknown facts loudly — never classify a guess."""
    for field in ("hook", "event"):
        if not isinstance(getattr(fact, field), str) or not getattr(fact, field):
            raise ValueError("%s must be a non-empty string" % field)
    if fact.mode not in MODES:
        raise ValueError("unknown mode %r (expected one of %s)"
                         % (fact.mode, MODES))
    for field in ("configured", "host_capability", "mode_opted_in"):
        if not isinstance(getattr(fact, field), bool):
            raise ValueError("%s must be a bool" % field)
    if fact.dispatch is not None and fact.dispatch not in DISPATCH_TOKENS:
        raise ValueError("unknown dispatch observation %r (expected None or %s)"
                         % (fact.dispatch, DISPATCH_TOKENS))
    if fact.on_violation not in VIOLATION_POLICIES:
        raise ValueError("unknown violation policy %r (expected one of %s)"
                         % (fact.on_violation, VIOLATION_POLICIES))
    if fact.violation_blocked is not None \
            and not isinstance(fact.violation_blocked, bool):
        raise ValueError("violation_blocked must be True, False or None")
    # a denial/allowance is an observation about an actual run: without a
    # "reached" dispatch observation it cannot be attributed to anything
    if fact.violation_blocked is not None and fact.dispatch != "reached":
        raise ValueError(
            "contradiction: violation_blocked observation for %r without a "
            "reached dispatch observation" % fact.hook)


def classify(fact):
    """Classify one hook at one runtime event into exactly one verdict."""
    _validate(fact)
    if not fact.configured:
        return NOT_CONFIGURED
    if not fact.host_capability:
        if fact.dispatch == "reached":
            raise ValueError(
                "contradiction: %r reported reached on a host without the "
                "dispatch API — never classified as enforced" % fact.hook)
        return UNREACHABLE_HOST
    if not fact.mode_opted_in:
        return (UNEXPECTED_DISPATCH if fact.dispatch == "reached"
                else INERT_FOR_MODE)
    if fact.dispatch is None:
        return UNVERIFIED
    if fact.dispatch == "not_reached":
        return MISSED_DISPATCH
    if fact.on_violation == "warn":
        if fact.violation_blocked:
            raise ValueError(
                "contradiction: denial attributed to warn-policy hook %r — "
                "warn can never enforce" % fact.hook)
        return ADVISORY
    # block policy and the hook ran: enforcement needs a proven denial
    if fact.violation_blocked is None:
        return UNVERIFIED      # configured + invoked is NOT proof of blocking
    return BLOCKING if fact.violation_blocked else MISSED_BLOCK


def is_enforced(fact):
    """True only for the full BLOCKING chain — an observed, attributed
    denial. Configuration and invocation alone never qualify."""
    return classify(fact) == BLOCKING
