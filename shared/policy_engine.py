
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    kb_article: str
    reason: str


def safe_days(value):
    """Return a valid non-negative day count, otherwise None."""
    try:
        days = int(value)
        return days if days >= 0 else None
    except (TypeError, ValueError):
        return None


def decide_policy(order: dict) -> PolicyDecision:

    product_type = order.get("product_type")

    # 1. Subscription policy
    if product_type == "subscription":
        days = safe_days(order.get("subscription_age_days"))

        if days is None:
            return PolicyDecision(
                "ESCALATE_TIER2",
                "subscription-cooling-off",
                "Subscription age is missing or invalid."
            )

        if days <= 30:
            return PolicyDecision(
                "REFUND",
                "subscription-cooling-off",
                "Subscription is within the cooling-off period."
            )

        return PolicyDecision(
            "SEND_ARTICLE",
            "subscription-cooling-off",
            "Subscription is outside the cooling-off period."
        )

    # 2. Digital license policy
    if order.get("license_revealed"):
        return PolicyDecision(
            "SEND_ARTICLE",
            "digital-license-no-refund",
            "Digital license has already been revealed."
        )

    # 3. Customized damaged products
    if order.get("customized") and order.get("damage_reported"):
        return PolicyDecision(
            "ESCALATE_TIER2",
            "custom-items-no-replace",
            "Customized damaged products require specialist review."
        )

    # 4. Non-customized damaged products
    if order.get("damage_reported") and not order.get("customized"):
        days = safe_days(order.get("delivered_days_ago"))

        if days is not None and days <= 7:
            return PolicyDecision(
                "REPLACE",
                "damage-replacement-7-days",
                "Non-customized product was damaged within seven days."
            )

    # 5. Unopened physical products
    if product_type == "physical" and not order.get("opened"):
        days = safe_days(order.get("delivered_days_ago"))

        if days is not None and days <= 30:
            return PolicyDecision(
                "REFUND",
                "returns-within-30-days",
                "Unopened physical product is within the return period."
            )

    # 6. Default escalation
    return PolicyDecision(
        "ESCALATE_TIER2",
        "returns-within-30-days",
        "No automatic resolution rule applies."
    )
