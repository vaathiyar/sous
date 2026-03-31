from enum import StrEnum


class NodeNames(StrEnum):
    BRIEFING = "briefing"
    SUMMARIZE_IF_NEEDED = "summarize_if_needed"
    EXTRACT_AND_ROUTE = "extract_and_route"
    SIMPLE_QUERY_RESPONSE = "simple_query_response"
    STEP_CHANGE_RESPONSE = "step_change_response"
    NEW_PROPOSAL = "new_proposal"
    CONFIRMATION_COMPUTE = "confirmation_compute"
    CONFIRMATION_ACK = "confirmation_ack"
