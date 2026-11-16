
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from shared.billing import CostSession
from shared.llm import ChatMessage, LlmClient
from shared.tools import format_thread, get_order, get_ticket


@dataclass
class TicketResolution:
    action: str
    kb_article: str
    customer_reply: str
    raw_completion: str


def parse_resolution(text: str) -> TicketResolution:
    match = re.search(r"\{[\s\S]*\}", text)

    if not match:
        raise ValueError(f"No JSON in model output:\n{text[:400]}")

    data = json.loads(match.group())

    return TicketResolution(
        action=str(data["action"]).upper(),
        kb_article=str(data["kb_article"]),
        customer_reply=str(data.get("customer_reply", "")),
        raw_completion=text,
    )


SYSTEM_PROMPT = """
You are ShopAssist, an e-commerce support decision agent.

Select the appropriate action using order facts and company policies.

POLICIES:
1. Unopened physical products delivered within 30 days:
   REFUND -> returns-within-30-days

2. Digital products with revealed licenses:
   SEND_ARTICLE -> digital-license-no-refund

3. Customized products with reported damage:
   ESCALATE_TIER2 -> custom-items-no-replace

4. Non-customized products with reported damage within 7 days:
   REPLACE -> damage-replacement-7-days

5. Subscriptions within 30 days:
   REFUND -> subscription-cooling-off

6. Older subscriptions:
   SEND_ARTICLE -> subscription-cooling-off

7. Unmatched or unsupported cases:
   ESCALATE_TIER2

Return valid JSON with these fields:
{
  "action": "ACTION_NAME",
  "kb_article": "article-id"
}

Allowed actions:
REFUND, REPLACE, SEND_ARTICLE, ESCALATE_TIER2

Return JSON only. Do not include additional fields.
"""


class SupportCopilot:

    def __init__(self, session: CostSession | None = None):
        self.session = session or CostSession()
        self.llm = LlmClient(self.session)

    def build_messages(self, ticket_id: str) -> list[ChatMessage]:

        ticket = get_ticket(ticket_id)
        order = get_order(ticket["order_id"])

        thread = format_thread(ticket)
        snapshot = json.dumps(order, separators=(",", ":"))

        user_prompt = (
            f"TICKET_ID: {ticket_id}\n"
            f"THREAD:\n{thread}\n"
            f"ORDER_SNAPSHOT:\n{snapshot}\n"
            "END_SNAPSHOT"
        )

        return [
            ChatMessage("system", SYSTEM_PROMPT),
            ChatMessage("user", user_prompt),
        ]

    def handle_ticket(self, ticket_id: str) -> TicketResolution:

        messages = self.build_messages(ticket_id)

        completion = self.llm.chat(
            "handle_ticket",
            messages
        )

        return parse_resolution(completion)
