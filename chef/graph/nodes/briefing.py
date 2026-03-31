import logging
from typing import Union

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END
from langgraph.types import Command
from pydantic import BaseModel, Field

from chef.graph.chat_models import response_model, route_model  # response_model: intro only
from chef.graph.nodes.node_names import NodeNames
from chef.graph.prompts import BRIEFING_INTRO_PROMPT, BRIEFING_ROUTE_PROMPT
from chef.graph.state import ChefState
from chef.graph.state.enums import DeviationType

logger = logging.getLogger(__name__)


class BriefingDeviation(BaseModel):
    deviation_type: DeviationType
    is_confirmation: bool = Field(
        False,
        description="True only when the user is confirming a change that was already proposed earlier.",
    )


class BriefingQuery(BaseModel):
    """User has a question about the recipe, ingredients, technique, or timing."""


class BriefingReady(BaseModel):
    """User signals they are ready to start cooking — 'ready', 'let's go', 'let's start',
    'all good', 'I'm set', or short affirmatives ('yes', 'ok') when there is no pending
    deviation proposal in the conversation."""


class BriefingRouteOutput(BaseModel):
    result: Union[BriefingDeviation, BriefingQuery, BriefingReady]


async def briefing(state: ChefState) -> Command:
    """Handles the entire pre-cook briefing phase (step 0).

    First turn (no messages): generates the opening intro using PreCookBriefing.
    Subsequent turns: classifies user intent and routes to deviation nodes,
    answers queries inline, or transitions to step 1 when the user is ready.
    """
    messages = state.get("messages", [])
    recipe = state["base_recipe"]
    briefing_data = state.get("precook_briefing")
    routing = state["routing"]

    # --- First turn: no user input yet — generate the opening intro ---
    if not messages:
        summary = briefing_data.summary if briefing_data else f"Today we're making {recipe.title}."

        prompt = BRIEFING_INTRO_PROMPT.format(
            recipe_title=recipe.title,
            summary=summary,
        )

        response_text = ""
        async for chunk in response_model.astream([SystemMessage(content=prompt)]):
            c = chunk.content
            response_text += c if isinstance(c, str) else "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in c
            )

        logger.info("briefing intro generated (%d chars)", len(response_text))
        return Command(
            goto=END,
            update={
                "response_message": response_text,
                "messages": [AIMessage(content=response_text)],
            },
        )

    # --- Subsequent turns: classify user intent ---
    summary = briefing_data.summary if briefing_data else ""
    summary_section = f"\nRecipe overview: {summary}" if summary else ""

    raw: BriefingRouteOutput = await route_model.with_structured_output(BriefingRouteOutput).ainvoke(
        [SystemMessage(content=BRIEFING_ROUTE_PROMPT.format(
            recipe_title=recipe.title,
            summary_section=summary_section,
        ))] + messages
    )
    result = raw.result
    logger.info("briefing classified as: %s", result.__class__.__name__)

    if isinstance(result, BriefingDeviation):
        target = NodeNames.CONFIRMATION_COMPUTE if result.is_confirmation else NodeNames.NEW_PROPOSAL
        return Command(
            goto=target,
            update={"routing": {**routing, "deviation_type": result.deviation_type}},
        )

    elif isinstance(result, BriefingReady):
        return Command(
            goto=NodeNames.STEP_CHANGE_RESPONSE,
            update={"routing": {**routing, "new_step": 1}},
        )

    else:  # BriefingQuery — delegate to simple_query_response
        # build_system_prompt includes briefing context at step 0, so no extra wiring needed
        return Command(goto=NodeNames.SIMPLE_QUERY_RESPONSE)
