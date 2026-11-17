"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.trace import Trace

SHAPE = "orchestrator"


def run_claim(
   claim_id: str,
   *,
   seed: int,
   store_path: str,
   crash_at: str | None = None,
) -> RunResult:
   conn = connect(store_path)
   try:
      return _run(conn, claim_id, seed=seed, crash_at=crash_at)
   finally:
      conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
   budget = Budget()
   trace = Trace(make_run_id(SHAPE, claim_id, seed))

   def done(status: str, proposal: int = 0, reason: str | None = None) -> RunResult:
      """Every return path goes through here, so every branch writes a trace via finish()."""
      trace.add("decision", {"status": status, "proposal_amount": int(proposal), "reason": reason})
      return finish(
         conn,
         shape=SHAPE,
         claim_id=claim_id,
         seed=seed,
         status=status,
         proposal_amount=proposal,
         budget=budget,
         trace=trace,
         error_reason=reason,
      )

   # TODO CP2 bước 2: get_claim_view -> unknown_claim (failed) / thiếu order_id (needs_info).
   # TODO CP2 bước 3: make_handoff (tool read-only) -> run_readonly_investigators -> escalated nếu order không visible.
   # TODO CP2 bước 4: compute_compensation -> denied nếu quote 0, ngược lại issue_refund với quote đầy đủ.
   # TODO CP3: truyền crash_at vào durability.issue_refund, không bắt InjectedCrash.
   del crash_at
   return done("failed", reason="not_implemented")
