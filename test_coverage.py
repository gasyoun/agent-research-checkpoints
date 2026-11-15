"""Tests for coverage.py — stdlib unittest, positive and negative controls."""
import unittest

from coverage import (ADVISORY, BLOCKING, INERT_FOR_MODE, MISSED_BLOCK,
                      MISSED_DISPATCH, NOT_CONFIGURED, UNEXPECTED_DISPATCH,
                      UNREACHABLE_HOST, UNVERIFIED, HookFact, classify,
                      is_enforced)


def fact(**overrides):
    base = dict(hook="prior-art-gate", event="execute:post", mode="phase",
                configured=True, host_capability=True, mode_opted_in=True,
                dispatch="reached", on_violation="block",
                violation_blocked=True)
    base.update(overrides)
    return HookFact(**base)


class HookCoverageTests(unittest.TestCase):
    def test_observed_denial_positive_control_blocks(self):
        # positive control: the FULL chain including an observed,
        # attributed denial -> BLOCKING / enforced
        self.assertEqual(classify(fact()), BLOCKING)
        self.assertTrue(is_enforced(fact()))

    def test_block_policy_without_denial_proof_is_unverified(self):
        # the review counterexample: configured + reached + "block" policy
        # proves configuration and invocation ONLY — an adapter could
        # ignore exit 2 or fail open, so without an observed denial this
        # must never be reported as enforced
        f = fact(violation_blocked=None)
        self.assertEqual(classify(f), UNVERIFIED)
        self.assertFalse(is_enforced(f))

    def test_observed_violation_allowed_is_missed_block(self):
        # negative control: a violation attributed to the hook AND allowed
        # through -> ineffective block, must NOT pass
        f = fact(violation_blocked=False)
        self.assertEqual(classify(f), MISSED_BLOCK)
        self.assertNotEqual(classify(f), BLOCKING)
        self.assertFalse(is_enforced(f))

    def test_missing_host_api_is_never_enforced(self):
        # negative control: configured everywhere, host lacks the API
        f = fact(host_capability=False, dispatch=None,
                 violation_blocked=None)
        self.assertEqual(classify(f), UNREACHABLE_HOST)
        self.assertFalse(is_enforced(f))
        # a "reached" claim without the API is a contradiction, not proof
        with self.assertRaises(ValueError):
            classify(fact(host_capability=False, dispatch="reached"))

    def test_not_opted_into_quick_mode_is_inert_not_a_gap(self):
        # a phase-scoped hook observed absent during a quick task: expected
        f = fact(mode="quick", mode_opted_in=False, dispatch="not_reached",
                 violation_blocked=None)
        self.assertEqual(classify(f), INERT_FOR_MODE)
        self.assertFalse(is_enforced(f))
        # ...and it running anyway in that mode is a contract signal
        self.assertEqual(classify(fact(mode="quick", mode_opted_in=False,
                                       dispatch="reached")),
                         UNEXPECTED_DISPATCH)

    def test_no_dispatch_observation_is_unverified(self):
        f = fact(dispatch=None, violation_blocked=None)
        self.assertEqual(classify(f), UNVERIFIED)
        self.assertFalse(is_enforced(f))

    def test_expected_but_not_reached_is_missed_dispatch(self):
        # opted in, host capable, observed NOT running -> coverage gap
        f = fact(dispatch="not_reached", violation_blocked=None)
        self.assertEqual(classify(f), MISSED_DISPATCH)
        self.assertFalse(is_enforced(f))

    def test_warn_policy_runs_but_cannot_block(self):
        # warn policy with an observed-allowed violation: advisory by
        # construction, never enforced
        f = fact(on_violation="warn", violation_blocked=False)
        self.assertEqual(classify(f), ADVISORY)
        self.assertFalse(is_enforced(f))
        self.assertEqual(classify(fact(configured=False, dispatch=None,
                                       violation_blocked=None)),
                         NOT_CONFIGURED)  # negative control: unregistered

    def test_denial_attributed_to_warn_policy_is_contradiction(self):
        # a warn-policy hook cannot be the source of a denial
        with self.assertRaises(ValueError):
            classify(fact(on_violation="warn", violation_blocked=True))

    def test_denial_observation_requires_a_reached_dispatch(self):
        # an allow/deny observation without a run is unattributable
        with self.assertRaises(ValueError):
            classify(fact(dispatch=None, violation_blocked=True))
        with self.assertRaises(ValueError):
            classify(fact(dispatch="not_reached", violation_blocked=False))

    def test_malformed_and_unknown_facts_raise(self):
        with self.assertRaises(ValueError):
            classify(fact(mode="fast"))                # unknown mode token
        with self.assertRaises(ValueError):
            classify(fact(dispatch="maybe"))           # unknown observation
        with self.assertRaises(ValueError):
            classify(fact(on_violation="ignore"))      # unknown policy
        with self.assertRaises(ValueError):
            classify(fact(host_capability="yes"))      # not a bool
        with self.assertRaises(ValueError):
            classify(fact(violation_blocked="no"))     # not True/False/None
        with self.assertRaises(ValueError):
            classify(fact(event=""))                   # empty event
        for verdict in (classify(fact()), ):           # classifier is pure
            self.assertIn(verdict, {BLOCKING, ADVISORY, MISSED_BLOCK,
                                    INERT_FOR_MODE, UNEXPECTED_DISPATCH,
                                    UNVERIFIED, MISSED_DISPATCH,
                                    UNREACHABLE_HOST, NOT_CONFIGURED})


if __name__ == "__main__":
    unittest.main()
