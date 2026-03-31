import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chef.graph.state import ChefState
from chef.graph.chat_models import response_model
from chef.graph.prompts import CONFIRMATION_ACK_PROMPT

logger = logging.getLogger(__name__)


async def confirmation_ack(state: ChefState) -> dict:
    """Streams a brief spoken acknowledgement after a deviation is committed."""
    deviation_description = state.get("context_note", "")

    if not deviation_description:
        # Not a genuine deviation — give a brief neutral response
        response_text = "Alright, let's keep going — what's next?"
    else:
        prompt = CONFIRMATION_ACK_PROMPT.format(
            deviation_description=deviation_description
        )
        response_text = ""
        async for chunk in response_model.astream([HumanMessage(content=prompt)]):
            c = chunk.content
            response_text += c if isinstance(c, str) else "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)

    logger.info("confirmation_ack complete")

    return {
        "response_message": response_text,
        "messages": [AIMessage(content=response_text)],
        "context_note": "",
    }
