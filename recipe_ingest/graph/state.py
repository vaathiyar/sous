from typing_extensions import TypedDict, Annotated
from langchain.messages import AnyMessage
import operator

from shared.schemas.recipe import ExtractedRecipe, PreCookBriefing, RecipeIngredient


class VideoMetadata(TypedDict):
    title: str
    description: str
    language: str
    tags: list[str]


class RecipeDetails(TypedDict):
    recipe_raw_text: str
    recipes: list[ExtractedRecipe]                      # one source may yield multiple recipes
    precook_briefings: list[PreCookBriefing]            # parallel to recipes, index i ↔ recipes[i]
    required_ingredients: list[list[RecipeIngredient]]  # parallel to recipes, index i ↔ recipes[i]


class RecipeExtractorState(TypedDict):
    video_metadata: VideoMetadata
    recipe_details: RecipeDetails
    video_url: str
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
