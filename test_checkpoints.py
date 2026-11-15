"""Tests for agent-research-checkpoints — stdlib unittest, deterministic clock."""
import unittest

from checkpoints import FAILED, Ledger, Scope

PARENT = Scope("repo-a", "session-1")
WORKER = Scope("repo-a", "session-2")
OTHER_REPO = Scope("repo-b", "session-1")


class ManualClock:
    """Strictly increasing test clock."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        self.now += 1.0
        return self.now


class ResearchFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.clock = ManualClock()
        self.ledger = Ledger(clock=self.clock)

    def test_pending_question_does_not_invalidate(self):
        q = self.ledger.ask_question(PARENT, "which framework?")
        self.ledger.record_research(PARENT, q, "compared 3 frameworks")
        # question still pending — research stays fresh
        self.assertTrue(self.ledger.research_is_fresh(PARENT, q))

    def test_answer_invalidates_prior_research(self):
        q = self.ledger.ask_question(PARENT, "which framework?")
        self.ledger.record_research(PARENT, q, "compared 3 frameworks")
        self.ledger.answer_question(PARENT, q, "pilot gsd-core")
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q))
        # research re-run AFTER the answer is fresh again
        self.ledger.record_research(PARENT, q, "re-checked after answer")
        self.assertTrue(self.ledger.research_is_fresh(PARENT, q))

    def test_answer_to_any_question_invalidates_earlier_research(self):
        # regression (independent logic review 15-11-2026): answering a NEW
        # requirement question must invalidate research recorded before it,
        # not only receipts tied to the very same question
        q1 = self.ledger.ask_question(PARENT, "which framework?")
        self.ledger.record_research(PARENT, q1, "compared 3 frameworks")
        q2 = self.ledger.ask_question(PARENT, "new requirement: budget?")
        self.ledger.answer_question(PARENT, q2, "capped")
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q1))
        # refreshed after the answer -> fresh again
        self.ledger.record_research(PARENT, q1, "re-checked after q2 answer")
        self.assertTrue(self.ledger.research_is_fresh(PARENT, q1))

    def test_failed_research_is_never_fresh(self):
        q = self.ledger.ask_question(PARENT, "which framework?")
        self.ledger.record_research(PARENT, q, "search errored out",
                                    status=FAILED)
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q))

    def test_batch_start_is_a_boundary(self):
        q = self.ledger.ask_question(PARENT, "which framework?")
        self.ledger.record_research(PARENT, q, "old research")
        self.ledger.start_batch(PARENT, "prepare batch")
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q))
        # fresh research inside the preparation window (before dispatch)
        self.ledger.record_research(PARENT, q, "research after batch start")
        self.assertTrue(self.ledger.research_is_fresh(PARENT, q))

    def test_completion_invalidates_then_refresh_then_next_batch(self):
        # regression (independent logic review 15-11-2026): completion is a
        # boundary too — pre-implementation research must not survive to the
        # final review; a refresh after completion is fresh until the NEXT
        # batch starts
        q = self.ledger.ask_question(PARENT, "which framework?")
        b1 = self.ledger.start_batch(PARENT, "batch 1")
        self.ledger.record_research(PARENT, q, "research in batch 1")
        self.assertTrue(self.ledger.research_is_fresh(PARENT, q))
        self.ledger.complete_batch(PARENT, b1)
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q))
        self.ledger.record_research(PARENT, q, "refresh before final review")
        self.assertTrue(self.ledger.research_is_fresh(PARENT, q))
        self.ledger.start_batch(PARENT, "batch 2")
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q))

    def test_scope_isolation_by_session(self):
        q_parent = self.ledger.ask_question(PARENT, "shared question?")
        q_worker = self.ledger.ask_question(WORKER, "shared question?")
        self.ledger.record_research(WORKER, q_worker, "worker research")
        # parent answers ITS copy — the answer fence never leaks across scopes
        self.ledger.answer_question(PARENT, q_parent, "ruled")
        self.assertTrue(self.ledger.research_is_fresh(WORKER, q_worker))
        with self.assertRaises(KeyError):
            self.ledger.answer_question(WORKER, q_parent, "cross-scope")

    def test_scope_isolation_by_repo(self):
        q = self.ledger.ask_question(PARENT, "question?")
        self.ledger.record_research(PARENT, q, "repo-a research")
        self.ledger.start_batch(PARENT, "repo-a batch")
        # a batch boundary in repo-a must not leak into repo-b
        q_b = self.ledger.ask_question(OTHER_REPO, "question?")
        self.ledger.record_research(OTHER_REPO, q_b, "repo-b research")
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q))
        self.assertTrue(self.ledger.research_is_fresh(OTHER_REPO, q_b))

    def test_newest_ok_receipt_wins_over_older_failed(self):
        q = self.ledger.ask_question(PARENT, "which framework?")
        self.ledger.record_research(PARENT, q, "failed attempt", status=FAILED)
        self.assertFalse(self.ledger.research_is_fresh(PARENT, q))
        self.ledger.record_research(PARENT, q, "good attempt")
        st = self.ledger.status(PARENT, q)
        self.assertTrue(st["fresh_now"])
        self.assertEqual(st["fresh"], 1)
        self.assertEqual(st["stale_or_failed"], 1)

    def test_status_reports_pending_vs_answered(self):
        q = self.ledger.ask_question(PARENT, "which framework?")
        self.assertEqual(self.ledger.status(PARENT, q)["state"], "pending")
        self.ledger.answer_question(PARENT, q, "ruled")
        self.assertEqual(self.ledger.status(PARENT, q)["state"], "answered")

    def test_rejects_unknown_status_and_unknown_question(self):
        q = self.ledger.ask_question(PARENT, "which framework?")
        with self.assertRaises(ValueError):
            self.ledger.record_research(PARENT, q, "x", status="maybe")
        with self.assertRaises(KeyError):
            self.ledger.record_research(WORKER, q, "cross-scope")


if __name__ == "__main__":
    unittest.main()
