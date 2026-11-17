"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import json

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))
    conn = connect(store_path)
    try:
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        trace.add("claim_lookup", {"found": claim["found"]})
        order = None

        def decide(observation):
            nonlocal order
            complete(
                budget, seed=seed, purpose="decide",
                prompt=json.dumps(observation, ensure_ascii=False, sort_keys=True),
            )
            if not claim["found"]:
                action = {"final": {"status": "failed", "error_reason": "unknown_claim"}}
            elif not claim.get("order_id"):
                action = {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}
            elif "last_tool" not in observation:
                action = {
                    "tool": "lookup_order",
                    "args": {"order_id": claim["order_id"], "principal_id": claim["principal_id"]},
                }
            elif observation["last_tool"] == "lookup_order":
                result = observation["last_result"]
                if not result["visible"]:
                    action = {"final": {"status": "escalated", "error_reason": result["reason"]}}
                else:
                    order = result["order"]
                    action = {
                        "tool": "lookup_refund_history",
                        "args": {"order_id": claim["order_id"], "principal_id": claim["principal_id"]},
                    }
            elif observation["last_tool"] == "lookup_refund_history":
                action = {"tool": "compute_compensation", "args": {"order": order}}
            else:
                action = {"final": {"quote": observation["last_result"]}}
            trace.add("agent_action", {"tool": action.get("tool"), "final": "final" in action})
            return action

        result = run_react(
            conn, budget, observation={"claim": claim}, decide=decide, max_steps=8,
        )
        final = result["final"]
        proposal_amount = 0
        status = final.get("status", "failed")
        error_reason = final.get("error_reason")
        if "quote" in final and order is not None:
            budget.add_tool(tool_cost())
            quote = compute_compensation(conn, order)
            if final["quote"] != quote:
                status, error_reason = "failed", "invalid_quote"
            else:
                proposal_amount = int(quote["amount_vnd"])
                if proposal_amount <= 0:
                    status, error_reason = "denied", quote["reason"]
                else:
                    outcome = issue_refund(conn, claim_id, proposal_amount, crash_at=crash_at)
                    status = "resolved" if outcome["ok"] else ("failed" if outcome["conflict"] else "denied")
                    error_reason = None if outcome["ok"] else outcome["reason"]
        trace.add("decision", {"status": status, "proposal_amount": proposal_amount, "reason": error_reason})
        return finish(
            conn, shape="single", claim_id=claim_id, seed=seed, status=status,
            proposal_amount=proposal_amount, budget=budget, trace=trace,
            error_reason=error_reason,
        )
    finally:
        conn.close()
