
from shared.billing import CostSession
from question1.agent import SupportCopilot
from question2.agent import SupportPipeline

TICKETS = ["T-1001", "T-1002", "T-1003", "T-1004", "T-1091"]


def print_breakdown(name, session):
    print(f"\n{name}")
    print("-" * 75)

    for call in session.calls:
        cached = min(call.cached_prefix_tokens, call.input_tokens)
        uncached = call.input_tokens - cached

        print(f"\nNode: {call.label}")
        print(f"Input tokens:        {call.input_tokens}")
        print(f"Cached input tokens: {cached}")
        print(f"Uncached input:      {uncached}")
        print(f"Output tokens:       {call.output_tokens}")
        print(f"Call cost:           {call.points()} points")

    print(f"\nTOTAL: {session.total_points()} points")


for question, Agent in [
    ("QUESTION 1 - OPTIMIZED", SupportCopilot),
    ("QUESTION 2 - OPTIMIZED", SupportPipeline),
]:
    print(f"\n{'=' * 75}")
    print(question)
    print("=" * 75)

    for ticket in TICKETS:
        session = CostSession()
        agent = Agent(session=session)

        result = agent.handle_ticket(ticket)

        print(f"\nTicket: {ticket}")
        print(f"Decision: {result.action}")
        print(f"Article: {result.kb_article}")

        print_breakdown(ticket, session)
