from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

from shared.schemas.recipe import ExtractedRecipe, PreCookBriefing
from chef.graph.state.types import DishState, Deviation, RoutingContext


class ChefState(TypedDict):
    # Immutable
    base_recipe: ExtractedRecipe
    precook_briefing: PreCookBriefing | None

    # Core tracking
    dish_state: DishState
    deviations: list[Deviation]

    # Conversation (top-level for LangGraph reducer)
    messages: Annotated[list[AnyMessage], add_messages]
    conversation_summary: str

    # Intermediate routing (set by process_request, consumed by classify_request / handle_deviation)
    routing: RoutingContext

    # Inter-node communication
    context_note: str

    # Output for LiveKit
    response_message: str
