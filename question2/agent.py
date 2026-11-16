
from __future__ import annotations

import json
from dataclasses import dataclass

from shared.billing import CostSession
from shared.llm import ChatMessage, LlmClient
from shared.tools import format_thread, get_order, get_ticket
from shared.kb import load_article
from shared.policy_engine import decide_policy, PolicyDecision

from question1.agent import parse_resolution


@dataclass
class TicketResolution:
    action: str
    kb_article: str


class SupportPipeline:

    def __init__(self, session: CostSession | None = None):
        self.session = session or CostSession()
        self.llm = LlmClient(self.session)

    # NODE 1: TRIAGE
    # Extract compact information from the ticket.
    def _triage(self, thread: str) -> dict:

        text = thread.lower()

        if any(word in text for word in ["refund", "money back"]):
            intent = "refund"

        elif any(word in text for word in ["replace", "replacement"]):
            intent = "replacement"

        elif any(word in text for word in ["damaged", "cracked", "broken"]):
            intent = "damage"

        else:
            intent = "general_support"

        return {
            "intent": intent,
            "message_count": len(thread.splitlines()),
            "thread": thread
        }

    # NODE 2: RETRIEVE
    # Select the relevant policy and retrieve its article.
    def _retrieve(self, order: dict) -> tuple[PolicyDecision, str]:

        decision = decide_policy(order)

        article = load_article(decision.kb_article)

        return decision, article

    # NODE 3: COMPOSE
    # One compact LLM call generates the structured resolution.
    def _compose(
        self,
        ticket_id: str,
        triage: dict,
        order: dict,
        decision: PolicyDecision,
        article: str,
    ) -> str:

        snapshot = json.dumps(order, separators=(",", ":"))

        system_prompt = (
            "You are ShopAssist, an e-commerce support resolution agent. "
            "Return valid JSON only with action and kb_article. "
            "Use the supplied policy decision and article evidence. "
            "Do not add reasoning or extra fields."
        )

        user_prompt = (
            f"TICKET_ID: {ticket_id}\n"
            f"INTENT: {triage['intent']}\n"
            f"THREAD: {triage['thread']}\n"
            f"POLICY_ACTION: {decision.action}\n"
            f"POLICY_ARTICLE: {decision.kb_article}\n"
            f"POLICY_REASON: {decision.reason}\n"
            f"ARTICLE_EVIDENCE: {article}\n"
            f"ORDER_SNAPSHOT:\n{snapshot}\n"
            "END_SNAPSHOT"
        )

        messages = [
            ChatMessage("system", system_prompt),
            ChatMessage("user", user_prompt),
        ]

        return self.llm.chat("compose", messages)

    # NODE 4: AUDIT
    # Verify the generated resolution against deterministic policy.    
    def _audit(
        self,
        completion: str,
        decision: PolicyDecision,
    ) -> TicketResolution:

        valid_actions = {
            "REFUND",
            "REPLACE",
            "SEND_ARTICLE",
            "ESCALATE_TIER2",
        }

        try:
            parsed = parse_resolution(completion)

            if (
                parsed.action in valid_actions
                and parsed.action == decision.action
                and parsed.kb_article == decision.kb_article
            ):
                return TicketResolution(
                    parsed.action,
                    parsed.kb_article,
                )

        except (ValueError, KeyError, TypeError):
            pass

        # Safe fallback if parsing or validation fails.
        return TicketResolution(
            decision.action,
            decision.kb_article,
        )


    def handle_ticket(self, ticket_id: str) -> TicketResolution:

        ticket = get_ticket(ticket_id)
        order = get_order(ticket["order_id"])
        thread = format_thread(ticket)

        # Four logical processing stages.
        triage = self._triage(thread)

        decision, article = self._retrieve(order)

        completion = self._compose(
            ticket_id,
            triage,
            order,
            decision,
            article
        )

        final = self._audit(
            completion,
            decision
        )

        return final
