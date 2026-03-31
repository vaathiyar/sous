import logging

from langchain_core.messages import AIMessage, SystemMessage

from chef.graph.state import ChefState
from chef.graph.chat_models import reasoning_model
from chef.graph.prompts import NEW_DEVIATION_PROMPT
from chef.graph.utils import format_deviations

logger = logging.getLogger(__name__)


async def new_proposal(state: ChefState) -> dict:
    """Proposes a deviation (substitution or amendment) and asks the user to confirm. Streams response."""
    routing = state["routing"]
    recipe = state["base_recipe"]
    dish = state["dish_state"]
    deviation_type = routing.get("deviation_type")

    prompt = NEW_DEVIATION_PROMPT.format(
        recipe_title=recipe.title,
        current_step=dish["current_step"],
        total_steps=len(recipe.steps),
        deviation_type=deviation_type.value if deviation_type else "unknown",
        prior_deviations=format_deviations(state),
        base_recipe=recipe.model_dump_json(indent=2),
    )

    response_text = ""
    async for chunk in reasoning_model.astream(
        [SystemMessage(content=prompt)] + state["messages"]
    ):
        c = chunk.content
        response_text += c if isinstance(c, str) else "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)

    logger.info("new_proposal complete (%d chars)", len(response_text))

    return {
        "response_message": response_text,
        "messages": [AIMessage(content=response_text)],
    }
