
import pytest

from shared.policy_engine import decide_policy


@pytest.mark.parametrize(
    "order, expected_action, expected_article",
    [
        # Subscription boundary conditions
        (
            {"product_type": "subscription", "subscription_age_days": 30},
            "REFUND",
            "subscription-cooling-off",
        ),
        (
            {"product_type": "subscription", "subscription_age_days": 31},
            "SEND_ARTICLE",
            "subscription-cooling-off",
        ),

        # Missing subscription age
        (
            {"product_type": "subscription"},
            "ESCALATE_TIER2",
            "subscription-cooling-off",
        ),

        # Damage replacement boundary conditions
        (
            {
                "product_type": "physical",
                "damage_reported": True,
                "customized": False,
                "delivered_days_ago": 7,
                "opened": True,
            },
            "REPLACE",
            "damage-replacement-7-days",
        ),
        (
            {
                "product_type": "physical",
                "damage_reported": True,
                "customized": False,
                "delivered_days_ago": 8,
                "opened": True,
            },
            "ESCALATE_TIER2",
            "returns-within-30-days",
        ),

        # Physical product return boundary conditions
        (
            {
                "product_type": "physical",
                "opened": False,
                "delivered_days_ago": 30,
            },
            "REFUND",
            "returns-within-30-days",
        ),
        (
            {
                "product_type": "physical",
                "opened": False,
                "delivered_days_ago": 31,
            },
            "ESCALATE_TIER2",
            "returns-within-30-days",
        ),

        # Customized damaged product
        (
            {
                "product_type": "physical",
                "customized": True,
                "damage_reported": True,
                "delivered_days_ago": 2,
            },
            "ESCALATE_TIER2",
            "custom-items-no-replace",
        ),
    ],
)
def test_policy_engine_edge_cases(order, expected_action, expected_article):
    decision = decide_policy(order)

    assert decision.action == expected_action
    assert decision.kb_article == expected_article
