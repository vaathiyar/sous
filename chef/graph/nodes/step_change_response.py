import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chef.graph.state import ChefState
from chef.graph.chat_models import response_model
from chef.graph.prompts import STEP_CHANGE_PROMPT
from chef.graph.utils import format_deviations

logger = logging.getLogger(__name__)


def _format_step_ingredients(step) -> str:
    if not step.ingredients:
        return "none specified"
    parts = []
    for ing in step.ingredients:
        s = ing.name
        if ing.quantity:
            s += f" ({ing.quantity})"
        if ing.prep:
            s += f", {ing.prep}"
        parts.append(s)
    return "; ".join(parts)


async def step_change_response(state: ChefState) -> dict:
    """Handles step advancement/backtracking. Streams a description of the new step."""
    routing = state["routing"]
    new_step = routing.get("new_step")
    recipe = state["base_recipe"]

    dish_state = {**state["dish_state"]}
    if new_step is not None:
        dish_state["current_step"] = new_step

    step_index = dish_state["current_step"]
    # step numbers are 1-based; index 0 = pre-cook
    step = recipe.steps[step_index - 1] if 0 < step_index <= len(recipe.steps) else None

    if step:
        prompt = STEP_CHANGE_PROMPT.format(
            recipe_title=recipe.title,
            current_step=step_index,
            total_steps=len(recipe.steps),
            step_title=step.title,
            step_instruction=step.instruction,
            step_ingredients=_format_step_ingredients(step),
            step_duration=step.duration or "not specified",
            deviations_section=format_deviations(
                {**state, "dish_state": dish_state},
                empty="No active deviations.",
            ),
        )
        messages = [SystemMessage(content=prompt)] + state["messages"]
    else:
        # Pre-cook or out-of-range — fall back to conversation context
        from chef.graph.utils import build_system_prompt
        messages = [SystemMessage(content=build_system_prompt({**state, "dish_state": dish_state}))] + state["messages"]

    response_text = ""
    async for chunk in response_model.astream(messages):
        c = chunk.content
        response_text += c if isinstance(c, str) else "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)

    logger.info("step_change_response complete, new_step=%s", new_step)

    result: dict = {
        "response_message": response_text,
        "messages": [AIMessage(content=response_text)],
        "routing": {**routing, "new_step": None},
    }
    if new_step is not None:
        result["dish_state"] = dish_state
    return result
