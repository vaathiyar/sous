from langgraph.graph import START, StateGraph, END

from chef.graph.state import ChefState
from chef.graph.nodes import (
    NodeNames,
    briefing,
    summarize_if_needed,
    extract_and_route,
    simple_query_response,
    step_change_response,
    new_proposal,
    confirmation_compute,
    confirmation_ack,
)


def _start_router(state: ChefState) -> str:
    """Route to briefing phase (step 0) or normal cooking flow (step 1+)."""
    if state["dish_state"]["current_step"] == 0:
        return NodeNames.BRIEFING
    return NodeNames.SUMMARIZE_IF_NEEDED


# --- Graph Construction ---

agent_builder = StateGraph(ChefState)

# Add nodes
agent_builder.add_node(NodeNames.BRIEFING, briefing)
agent_builder.add_node(NodeNames.SUMMARIZE_IF_NEEDED, summarize_if_needed)
agent_builder.add_node(NodeNames.EXTRACT_AND_ROUTE, extract_and_route)
agent_builder.add_node(NodeNames.SIMPLE_QUERY_RESPONSE, simple_query_response)
agent_builder.add_node(NodeNames.STEP_CHANGE_RESPONSE, step_change_response)
agent_builder.add_node(NodeNames.NEW_PROPOSAL, new_proposal)
agent_builder.add_node(NodeNames.CONFIRMATION_COMPUTE, confirmation_compute)
agent_builder.add_node(NodeNames.CONFIRMATION_ACK, confirmation_ack)

# Conditional start: briefing (step 0) vs cooking (step 1+)
agent_builder.add_conditional_edges(START, _start_router)

# Fixed path for cooking phase
agent_builder.add_edge(NodeNames.SUMMARIZE_IF_NEEDED, NodeNames.EXTRACT_AND_ROUTE)

# Terminal edges for single-node response paths
agent_builder.add_edge(NodeNames.SIMPLE_QUERY_RESPONSE, END)
agent_builder.add_edge(NodeNames.STEP_CHANGE_RESPONSE, END)
agent_builder.add_edge(NodeNames.NEW_PROPOSAL, END)

# Deviation confirmation path: compute state first, then stream ack
agent_builder.add_edge(NodeNames.CONFIRMATION_COMPUTE, NodeNames.CONFIRMATION_ACK)
agent_builder.add_edge(NodeNames.CONFIRMATION_ACK, END)

# Compile
chef_agent = agent_builder.compile()
