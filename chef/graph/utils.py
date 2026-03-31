import json

from chef.graph.state import ChefState
from chef.graph.prompts import SYSTEM_PROMPT


def format_deviations(state: ChefState, empty: str = "None") -> str:
    deviations = state.get("deviations", [])
    content = (
        json.dumps([d.model_dump(mode="json") for d in deviations], indent=2)
        if deviations
        else empty
    )
    return f"## Active Deviations\n{content}"


def format_briefing(state: ChefState) -> str:
    briefing = state.get("precook_briefing")
    if not briefing or state["dish_state"]["current_step"] != 0:
        return ""
    prep_lines = ""
    if briefing.prep_items:
        items = "\n".join(
            f"- {p.task}" + (f" ({p.duration})" if p.duration else "") + (f" — {p.notes}" if p.notes else "")
            for p in briefing.prep_items
        )
        prep_lines = f"\nPrep items:\n{items}"
    return f"## Pre-cook Briefing\n{briefing.summary}{prep_lines}"


def build_system_prompt(state: ChefState) -> str:
    recipe = state["base_recipe"]
    dish = state["dish_state"]
    summary = state.get("conversation_summary", "")
    summary_section = f"## Earlier Conversation Summary\n{summary}" if summary else ""

    return SYSTEM_PROMPT.format(
        recipe_title=recipe.title,
        current_step=dish["current_step"],
        total_steps=len(recipe.steps),
        step_status=dish["step_status"].value,
        deviations_section=format_deviations(state, empty="No deviations from the base recipe so far."),
        conversation_summary_section=summary_section,
        briefing_section=format_briefing(state),
        base_recipe=recipe.model_dump_json(indent=2),
    )
