"""Tests for provenance.py — stdlib unittest, no host adapter claimed."""
import unittest

from provenance import (FALLBACK, MISMATCH, PASS, UNKNOWN, ProvenanceFact,
                        passed, verify)

ALLOWLIST = {("zai", "glm-5.3"), ("zai", "glm-5.3-flash"),
             ("anthropic", "claude-sonnet-5")}


def fact(**overrides):
    base = dict(configured_provider="zai", configured_model="glm-5.3",
                observed_provider="zai", observed_model="glm-5.3",
                observed_source="host_telemetry",
                fallback_permitted=False, run_reported_success=True)
    base.update(overrides)
    return ProvenanceFact(**base)


class ExecutorProvenanceTests(unittest.TestCase):
    def test_exact_allowed_route_passes(self):
        # positive control: exact GLM route, trusted observation
        self.assertEqual(verify(fact(), ALLOWLIST), PASS)
        self.assertTrue(passed(fact(), ALLOWLIST))

    def test_unknown_identity_is_unknown_not_pass(self):
        self.assertEqual(verify(fact(observed_provider=None,
                                     observed_model=None), ALLOWLIST),
                         UNKNOWN)
        self.assertFalse(passed(fact(observed_provider=None,
                                     observed_model=None), ALLOWLIST))
        # trusted channel that reported nothing is still unknown
        self.assertEqual(verify(fact(observed_provider=None,
                                     observed_model=None), ALLOWLIST),
                         UNKNOWN)

    def test_model_self_report_never_attests(self):
        # the model's own prose matches the configured route exactly —
        # and still cannot attest trusted identity
        self.assertEqual(verify(fact(observed_source="model_self_report"),
                                ALLOWLIST), UNKNOWN)
        self.assertEqual(verify(fact(observed_source="process_output"),
                                ALLOWLIST), UNKNOWN)

    def test_false_success_output_still_unknown(self):
        # a successful-looking run with untrusted identity evidence
        f = fact(observed_source="process_output",
                 run_reported_success=True)
        self.assertEqual(verify(f, ALLOWLIST), UNKNOWN)
        self.assertFalse(passed(f, ALLOWLIST))

    def test_same_provider_different_model_is_not_pass(self):
        # fallback NOT permitted -> mismatch
        f = fact(observed_model="glm-5.3-flash")
        self.assertEqual(verify(f, ALLOWLIST), MISMATCH)
        self.assertFalse(passed(f, ALLOWLIST))
        # fallback explicitly permitted and inside allowlist -> still not PASS
        g = fact(observed_model="glm-5.3-flash", fallback_permitted=True)
        self.assertEqual(verify(g, ALLOWLIST), FALLBACK)
        self.assertFalse(passed(g, ALLOWLIST))

    def test_configured_route_outside_allowlist_is_mismatch(self):
        f = fact(configured_provider="openai", configured_model="gpt-9",
                 observed_provider="openai", observed_model="gpt-9")
        self.assertEqual(verify(f, ALLOWLIST), MISMATCH)

    def test_malformed_facts_raise(self):
        with self.assertRaises(ValueError):   # unknown source token
            verify(fact(observed_source="gut_feeling"), ALLOWLIST)
        with self.assertRaises(ValueError):   # half-filled identity
            verify(fact(observed_model=None), ALLOWLIST)
        with self.assertRaises(ValueError):   # empty provider string
            verify(fact(configured_provider=""), ALLOWLIST)
        with self.assertRaises(ValueError):   # non-bool flag
            verify(fact(fallback_permitted="no"), ALLOWLIST)
        with self.assertRaises(ValueError):   # non-bool success flag
            verify(fact(run_reported_success=1), ALLOWLIST)


if __name__ == "__main__":
    unittest.main()
