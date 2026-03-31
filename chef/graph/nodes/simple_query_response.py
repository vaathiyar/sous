import logging

from langchain_core.messages import AIMessage, SystemMessage

from chef.graph.state import ChefState
from chef.graph.chat_models import response_model
from chef.graph.utils import build_system_prompt

logger = logging.getLogger(__name__)


async def simple_query_response(state: ChefState) -> dict:
    """Handles questions, clarifications, and general recipe chat. Streams response."""
    system_prompt = build_system_prompt(state)

    response_text = ""
    async for chunk in response_model.astream(
        [SystemMessage(content=system_prompt)] + state["messages"]
    ):
        c = chunk.content
        response_text += (
            c
            if isinstance(c, str)
            else "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in c
            )
        )

    logger.info("simple_query_response complete (%d chars)", len(response_text))

    return {
        "response_message": response_text,
        "messages": [AIMessage(content=response_text)],
    }
