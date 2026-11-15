"""agent-research-checkpoints — research-freshness state machine (illustrative).

Portable sketch of a lifecycle checkpoint: when is recorded research still
fresh enough to act on?

Semantics (each pinned by a test):

1. A research receipt goes STALE once ANY question in its scope is answered
   afterwards — answering a NEW requirement question invalidates earlier
   research recorded before that answer, exactly as an answer to the
   researched question itself would. A merely PENDING question invalidates
   nothing.
2. Batch boundaries fence the whole scope: ``start_batch`` opens batch
   PREPARATION (it is not a worker-dispatch event — dispatch timing is the
   adapter's responsibility, and fresh research is expected between
   preparation start and execution dispatch); ``complete_batch`` marks work
   done. BOTH timestamps are fences: receipts recorded before a boundary are
   stale after it, so a final review after completion requires a research
   refresh recorded after completion. This also covers the external-worker
   case — a worker's receipts from before the parent's batch began never
   count as that batch's research.
3. A FAILED research run is never fresh evidence.
4. Everything is isolated per (repo, session) scope: a question, receipt or
   batch in one scope is invisible in another, and an answer in scope A
   never invalidates receipts in scope B.

This module is a reference fixture for upstream discussion. It is NOT
integrated with any agent harness, does not parse transcripts, and does NOT
claim that "fresh" evidence means good semantic-search quality — freshness
here is purely timestamp bookkeeping.

MIT License. (c) 2026 Dr. Marcis Gasuns. Drafted with GLM 5.3, November 2026.
"""
import itertools
import time
from collections import namedtuple

OK = "ok"
FAILED = "failed"

Scope = namedtuple("Scope", ["repo", "session"])
Question = namedtuple("Question", ["qid", "scope", "text", "asked_at",
                                   "answered_at", "answer"])
Batch = namedtuple("Batch", ["bid", "scope", "purpose", "started_at",
                             "completed_at"])
Receipt = namedtuple("Receipt", ["rid", "scope", "question", "summary",
                                 "status", "created_at"])


class Ledger:
    """In-memory ledger of questions, batches and research receipts.

    ``clock`` is injectable and must return a comparable timestamp
    (tests use a manual counter; the default is ``time.monotonic``).
    """

    def __init__(self, clock=None):
        self._clock = clock or time.monotonic
        self._ids = itertools.count(1)
        self._questions = {}   # (scope, qid) -> Question
        self._batches = {}     # (scope, bid) -> Batch
        self._receipts = []    # [Receipt] in record order

    # -- questions ---------------------------------------------------

    def ask_question(self, scope, text):
        """Register a question as PENDING. Invalidates nothing."""
        qid = self._next_id("q")
        self._questions[(scope, qid)] = Question(
            qid, scope, text, self._clock(), None, "")
        return qid

    def answer_question(self, scope, qid, answer=""):
        """Mark a question ANSWERED. This raises the scope-wide answer
        fence: EVERY receipt in the scope recorded before this moment
        (for any question) becomes stale. Unknown scope/qid raises
        KeyError — scope isolation is enforced, not advisory."""
        key = (scope, qid)
        if key not in self._questions:
            raise KeyError("question %s not found in scope %r" % (qid, scope))
        q = self._questions[key]
        self._questions[key] = q._replace(answered_at=self._clock(),
                                          answer=answer)

    # -- batches -----------------------------------------------------

    def start_batch(self, scope, purpose=""):
        """Open a batch's PREPARATION window. Its start timestamp fences
        the WHOLE scope (external-worker batches included). This is not a
        dispatch event: the adapter dispatches workers afterwards, and
        fresh research is expected between preparation start and dispatch."""
        bid = self._next_id("b")
        self._batches[(scope, bid)] = Batch(
            bid, scope, purpose, self._clock(), None)
        return bid

    def complete_batch(self, scope, bid):
        """Mark work done. The completion timestamp is ALSO a fence: a
        final review after completion requires research refreshed after
        it — pre-implementation receipts do not survive to closure."""
        key = (scope, bid)
        if key not in self._batches:
            raise KeyError("batch %s not found in scope %r" % (bid, scope))
        b = self._batches[key]
        self._batches[key] = b._replace(completed_at=self._clock())

    # -- research ----------------------------------------------------

    def record_research(self, scope, qid, summary, status=OK):
        """Record one research receipt. ``status`` is ``ok`` or ``failed``;
        a failed run is stored for audit but is never fresh evidence."""
        if status not in (OK, FAILED):
            raise ValueError("status must be %r or %r" % (OK, FAILED))
        if (scope, qid) not in self._questions:
            raise KeyError("question %s not found in scope %r" % (qid, scope))
        rid = self._next_id("r")
        self._receipts.append(Receipt(
            rid, scope, qid, summary, status, self._clock()))
        return rid

    # -- freshness ---------------------------------------------------

    def _boundary(self, scope):
        """Latest invalidation timestamp in a scope: the most recent answer
        to ANY question in the scope, and every batch start and completion
        timestamp in the scope."""
        fences = [q.answered_at for q in self._questions.values()
                  if q.scope == scope and q.answered_at is not None]
        for b in self._batches.values():
            if b.scope == scope:
                fences.append(b.started_at)
                if b.completed_at is not None:
                    fences.append(b.completed_at)
        return max(fences) if fences else None

    def fresh_receipts(self, scope, qid):
        """OK receipts for ``qid`` recorded AFTER the scope's latest
        invalidation fence (any answer, any batch start or completion)."""
        fence = self._boundary(scope)
        out = []
        for r in self._receipts:
            if r.scope != scope or r.question != qid:
                continue
            if r.status != OK:
                continue
            if fence is not None and r.created_at <= fence:
                continue
            out.append(r)
        return out

    def research_is_fresh(self, scope, qid):
        return bool(self.fresh_receipts(scope, qid))

    def status(self, scope, qid):
        """Diagnostics for one question: pending/answered, fresh and
        stale/failed receipt counts."""
        key = (scope, qid)
        if key not in self._questions:
            raise KeyError("question %s not found in scope %r" % (qid, scope))
        q = self._questions[key]
        total = [r for r in self._receipts
                 if r.scope == scope and r.question == qid]
        fresh = self.fresh_receipts(scope, qid)
        return {"question": qid,
                "state": "answered" if q.answered_at is not None else "pending",
                "fresh": len(fresh),
                "stale_or_failed": len(total) - len(fresh),
                "fresh_now": bool(fresh)}

    def _next_id(self, prefix):
        return "%s-%d" % (prefix, next(self._ids))
