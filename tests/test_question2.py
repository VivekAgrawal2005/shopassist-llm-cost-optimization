from __future__ import annotations

import pytest
from shared.policy_engine import PolicyDecision


from shared.kb import expanded_help_center_blob
from shared.tokens import count_tokens
from eval.reference import TICKET_EXPECTATIONS
from question2.agent import SupportPipeline

PUBLIC = ["T-1001", "T-1002", "T-1003", "T-1004"]


def test_help_center_exceeds_context():
    assert count_tokens(expanded_help_center_blob()) > 200_000


def test_pipeline_resolves_public_tickets():
    pipe = SupportPipeline()
    for tid in PUBLIC:
        expected = TICKET_EXPECTATIONS[tid]
        got = pipe.handle_ticket(tid)
        assert got.action == expected.action
        assert got.kb_article == expected.kb_article


def test_optimized_cost_is_within_budget():
    pipe = SupportPipeline()

    for tid in PUBLIC:
        pipe.handle_ticket(tid)

    for call in pipe.session.calls:
        assert call.points() <= 2500


@pytest.mark.parametrize(
    "completion",
    [
        "This is not valid JSON",
        '{"action": "REFUND"}',
        '{"action": "DELETE", "kb_article": "returns-within-30-days"}',
        '{"action": "REPLACE", "kb_article": "damage-replacement-7-days"}',
    ],
)
def test_audit_falls_back_on_invalid_output(completion):
    pipe = SupportPipeline()

    decision = PolicyDecision(
        action="REFUND",
        kb_article="returns-within-30-days",
        reason="Test policy decision",
    )

    result = pipe._audit(completion, decision)

    assert result.action == decision.action
    assert result.kb_article == decision.kb_article


def test_audit_accepts_valid_matching_output():
    pipe = SupportPipeline()

    decision = PolicyDecision(
        action="REFUND",
        kb_article="returns-within-30-days",
        reason="Test policy decision",
    )

    completion = (
        '{"action": "REFUND", '
        '"kb_article": "returns-within-30-days"}'
    )

    result = pipe._audit(completion, decision)

    assert result.action == "REFUND"
    assert result.kb_article == "returns-within-30-days"
