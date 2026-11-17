
"""Shape A — deterministic refund workflow.

A fixed sequence of Python steps.
The workflow does not use an LLM to decide refund amounts.
The host is the only component allowed to commit refunds.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import (
    compute_compensation,
    get_claim_view,
    lookup_order,
    tool_cost,
)
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Entry point required by the shared shape interface."""

    conn = connect(store_path)

    try:
        return _run(
            conn,
            claim_id,
            seed=seed,
            crash_at=crash_at,
        )
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:

    # Initialize shared execution context.
    budget = Budget()

    run_id = make_run_id("workflow", claim_id, seed)
    trace = Trace(run_id)

    trace.add(
        "workflow_started",
        {
            "claim_id": claim_id,
            "shape": "workflow",
        },
    )

    # --------------------------------------------------
    # STEP 1: Retrieve claim information
    # --------------------------------------------------

    budget.add_tool(tool_cost())

    claim = get_claim_view(conn, claim_id)

    if not claim["found"]:
        trace.add(
            "claim_lookup",
            {"found": False},
        )

        return finish(
            conn,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    # Only use the required claim fields.
    principal_id = claim["principal_id"]
    order_id = claim["order_id"]

    trace.add(
        "claim_lookup",
        {
            "found": True,
            "has_order_id": bool(order_id),
        },
    )

    # --------------------------------------------------
    # STEP 2: Check whether order_id exists
    # --------------------------------------------------

    if not order_id:
        trace.add(
            "decision",
            {
                "status": "needs_info",
                "reason": "missing_order_id",
            },
        )

        return finish(
            conn,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    # --------------------------------------------------
    # STEP 3: Look up the order
    # --------------------------------------------------

    budget.add_tool(tool_cost())

    order_result = lookup_order(
        conn,
        order_id,
        principal_id,
    )

    if not order_result["visible"]:
        reason = order_result["reason"]

        trace.add(
            "order_lookup",
            {
                "visible": False,
                "reason": reason,
            },
        )

        return finish(
            conn,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    order = order_result["order"]

    trace.add(
        "order_lookup",
        {
            "visible": True,
            "order_id": order["order_id"],
            "status": order["status"],
            "delay_days": order["delay_days"],
            "damage_verified": order["damage_verified"],
        },
    )

    # --------------------------------------------------
    # STEP 4: Calculate compensation
    # --------------------------------------------------

    budget.add_tool(tool_cost())

    quote = compute_compensation(
        conn,
        order,
    )

    proposal_amount = int(quote["amount_vnd"])

    trace.add(
        "compensation_calculated",
        {
            "proposal_amount": proposal_amount,
            "reason": quote["reason"],
            "clause_ids": quote["clause_ids"],
        },
    )

    # --------------------------------------------------
    # STEP 5: Check compensation eligibility
    # --------------------------------------------------

    if proposal_amount <= 0:
        trace.add(
            "decision",
            {
                "status": "denied",
                "reason": quote["reason"],
            },
        )

        return finish(
            conn,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote["reason"],
        )

    # --------------------------------------------------
    # STEP 6: Request refund from the host
    # --------------------------------------------------

    trace.add(
        "refund_requested",
        {
            "proposal_amount": proposal_amount,
        },
    )

    # IMPORTANT:
    # Pass the FULL quote.
    # The host handles approval, idempotency and per-order cap.
    # Do not calculate the remaining refund amount here.

    outcome = issue_refund(
        conn,
        claim_id,
        proposal_amount,
        crash_at=crash_at,
    )

    # --------------------------------------------------
    # STEP 7: Handle host authorization result
    # --------------------------------------------------

    if not outcome["ok"]:

        reason = outcome["reason"]

        status = (
            "failed"
            if outcome["conflict"]
            else "denied"
        )

        trace.add(
            "refund_result",
            {
                "status": status,
                "reason": reason,
            },
        )

        return finish(
            conn,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    # --------------------------------------------------
    # STEP 8: Refund successfully committed
    # --------------------------------------------------

    trace.add(
        "refund_result",
        {
            "status": "resolved",
            "reason": outcome["reason"],
        },
    )

    return finish(
        conn,
        shape="workflow",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal_amount,
        budget=budget,
        trace=trace,
        error_reason=None,
    )
