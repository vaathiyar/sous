import logging

from langchain_core.messages import SystemMessage
from pydantic import BaseModel

from chef.graph.state import ChefState, Deviation
from chef.graph.chat_models import reasoning_model
from chef.graph.prompts import CONFIRM_DEVIATION_PROMPT
from chef.graph.utils import format_deviations

logger = logging.getLogger(__name__)


class DeviationNodeOutput(Deviation):
    """Extends Deviation with the confirmation flag. Spoken response is handled by confirmation_ack."""

    is_genuine_deviation: bool


async def confirmation_compute(state: ChefState) -> dict:
    """Structured call to reconstruct and commit the confirmed deviation. No speech output."""
    routing = state["routing"]
    recipe = state["base_recipe"]
    dish = state["dish_state"]
    deviation_type = routing.get("deviation_type")

    prompt = CONFIRM_DEVIATION_PROMPT.format(
        recipe_title=recipe.title,
        current_step=dish["current_step"],
        total_steps=len(recipe.steps),
        deviation_type=deviation_type.value if deviation_type else "unknown",
        prior_deviations=format_deviations(state),
        base_recipe=recipe.model_dump_json(indent=2),
    )

    response: DeviationNodeOutput = await reasoning_model.with_structured_output(
        DeviationNodeOutput
    ).ainvoke([SystemMessage(content=prompt)] + state["messages"])

    result: dict = {
        "context_note": "",
    }

    if response.is_genuine_deviation:
        new_deviation = Deviation(
            deviation_type=response.deviation_type,
            introduced_step=response.introduced_step,
            reason=response.reason,
            description=response.description,
            swapped_ingredients=response.swapped_ingredients,
            impacted_steps=response.impacted_steps,
        )
        result["deviations"] = state.get("deviations", []) + [new_deviation]
        result["context_note"] = response.description
        logger.info("Deviation confirmed and committed: %s", response.deviation_type)
    else:
        logger.info("confirmation_compute: not a genuine deviation")

    return result
