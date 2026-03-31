import json
import logging
from enum import StrEnum
from codetiming import Timer
from langchain_core.messages import HumanMessage, SystemMessage

from recipe_ingest.services.youtube import download_audio
from recipe_ingest.graph.chat_models import model, model_with_tools
from recipe_ingest.graph.tools import transcription_tools_by_name

from pydantic import BaseModel as PydanticBaseModel
from shared.schemas.recipe import ExtractedRecipes, PreCookBriefing, RecipeIngredient

logger = logging.getLogger(__name__)


class _RecipeIngredientList(PydanticBaseModel):
    ingredients: list[RecipeIngredient]


class NodeNames(StrEnum):
    TRANSCRIBE_RECIPE_AUDIO = "transcribe_recipe_audio"
    EXTRACT_RECIPE_FROM_TRANSCRIPT = "extract_recipe_from_transcript"
    GENERATE_PRECOOK_BRIEFING = "generate_precook_briefing"
    COMPILE_REQUIRED_INGREDIENTS = "compile_required_ingredients"


@Timer(name="transcribe_recipe_audio", text="[transcribe_recipe_audio] finished in {:.2f}s", logger=logger.info)
def transcribe_recipe_audio(state):
    audio_path = download_audio(state["video_url"], state["video_metadata"]["title"])
    tags = state["video_metadata"]["tags"]
    language = state["video_metadata"]["language"]

    # ADR: Ideally, the below decision should be backed up with another tool that figures out the language from the audio to make it robust.
    # But I guess this is fine for now and we deal with that problem if the tags are not enough.
    # Also this could be really done without the model reasoning about tools, but hey im just learning langgraph so WHY NOT ?
    selected_tools = model_with_tools.invoke(
        [
            HumanMessage(
                content=(
                    "Carefully reason and choose the right language-tool to transcribe (and translate) the audio based on the following metadata: \n"
                    f"tags: {tags}\n"
                    f"language: {language}\n"
                    f"saved_audio_path: {audio_path}"
                )
            ),
        ]
    )

    # ADR: Don't feel too good about relying on a tool_calls truthy-check to determine if a tool was selected. Kinda feels hacky (maybe cuz I come from Java lmao).
    # I would prefer a flag or something more concrete but then I guess this is how things are done in python and it's just fine.
    if not selected_tools.tool_calls:
        raise Exception(f"No suitable tool found for the given tags: {tags}")

    tool_call = selected_tools.tool_calls[0]
    tool = transcription_tools_by_name[tool_call["name"]]
    transcribed_text = tool.invoke(tool_call["args"])

    return {"recipe_details": {"recipe_raw_text": transcribed_text}}


@Timer(name="extract_recipe_from_transcript", text="[extract_recipe_from_transcript] finished in {:.2f}s", logger=logger.info)
def extract_recipe_from_transcript(state):
    recipe_raw_text = state["recipe_details"]["recipe_raw_text"]
    video_metadata = state["video_metadata"]

    result = model.with_structured_output(ExtractedRecipes).invoke(
        [
            SystemMessage(
                content="""You are a recipe extraction engine. Convert raw recipe text into structured data following the provided schema. Rules: 

                        1. Extract only information the author provides. If the author didn't say it, the field is null or empty. Never infer, enrich, or fill gaps with general cooking knowledge.

                        2. Rewrite for clarity, not for content. The input may be a spoken transcript or informal blog - rephrase for readability but do not add/remove information beyond what the author stated.

                        3. The input may be messy (especially audio transcripts): filler words, repetition, corrections, tangents, sponsor segments. Extract the recipe, ignore the noise.

                        4. Step boundaries - use the author's own pacing signals in the text:
                           - A new step begins when the author uses transitional language indicating a previous action is complete ("once...", "now...", "when...is done", etc) or describes a result/checkpoint/sensory cue before moving to the next action.
                           - Ingredients or actions listed together without any transitional break belong to the same step.
                           - Do NOT merge actions that span across transitional phrases into one step just because they happen in the same vessel or context."""
            ),
            HumanMessage(
                content=f"""Extract the recipe from the following raw text.
                <raw_text>
                {recipe_raw_text}
                </raw_text>

                <video_description>
                Watch out for any additional information in the video description provided below:
                {video_metadata.get("description")}
                </video_description>

                <other_metadata>
                title: {video_metadata.get("title")}
                </other_metadata>
                <tags>
                tags: {video_metadata.get("tags")}
                </tags>
                """
            ),
        ]
    )

    return {
        "recipe_details": {
            **state["recipe_details"],
            "recipes": result.extracted_recipes,
        }
    }


_PRECOOK_SYSTEM_PROMPT = """You are a pre-cook briefing generator. Given a fully structured recipe, \
produce a PreCookBriefing that a home cook reads before starting their cooking session.

Rules:

SUMMARY
- 2-3 sentences only: what the dish is, the overall cooking approach, and the ONE critical thing \
the cook must not mess up.
- Practical, not poetic. The reader is about to cook this — not reading a menu.
- Draw the critical warning from common_mistakes, author_tips, and sensory_checkpoints in the recipe.

ACTIVE TIME / PASSIVE TIME
- Aggregate only from step durations that are explicitly stated by the author.
- Preserve the author's own phrasing ("about 10 minutes", "until golden").
- active_time: hands-on steps only. passive_time: hands-off waiting only (soaking, marination, \
simmering unattended).
- If no durations are stated anywhere, use null — never estimate or invent a number.

PREP ITEMS
Include an item ONLY if it satisfies ALL of the following:
1. The cook must have it done or ready before step 1 begins. If they can do it live during \
the voice session, it does not belong here.
2. It is NOT already a numbered step in the recipe. Do not duplicate steps — even step 1, \
even if the author words it as "let's start by...". The voice agent will handle all steps.
3. Include both explicit prep tasks AND implied ingredient states \
(e.g. "day-old rice", "room temperature butter", "beaten egg yolks").
4. Include the quantity as it appears in the recipe. Write "Soak 2 cups basmati rice", not "Soak rice".
5. Duration: use the author's own phrasing. null only if genuinely unstated.
6. Order: longest-duration items first (items with a duration), instant prep tasks last.
7. Derive only from the recipe. Do not add generic mise en place advice not grounded in this recipe."""


@Timer(name="generate_precook_briefing", text="[generate_precook_briefing] finished in {:.2f}s", logger=logger.info)
def generate_precook_briefing(state) -> dict:
    recipes = state["recipe_details"]["recipes"]
    briefings = []

    for i, recipe in enumerate(recipes):
        logger.info(f"[precook_briefing] generating briefing {i + 1}/{len(recipes)}: '{recipe.title}'")
        briefing = model.with_structured_output(PreCookBriefing).invoke(
            [
                SystemMessage(content=_PRECOOK_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Generate a PreCookBriefing for the following recipe.\n\n"
                        f"<recipe>\n{json.dumps(recipe.model_dump(), indent=2)}\n</recipe>"
                    )
                ),
            ]
        )
        logger.info(f"[precook_briefing] done: '{recipe.title}'")
        briefings.append(briefing)

    return {
        "recipe_details": {
            **state["recipe_details"],
            "precook_briefings": briefings,
        }
    }


_INGREDIENTS_SYSTEM_PROMPT = """You are a recipe ingredient compiler. Given a structured recipe, \
produce a complete, deduplicated list of every ingredient used.

Rules:
1. One entry per ingredient — if the same ingredient appears in multiple steps, merge into one entry.
2. Canonical name: use the author's own name for the ingredient. Preserve regional terms \
(seeraga samba, kashmiri mirchi). Do not translate unless the original is truly obscure.
3. Quantity: aggregate across steps where the same unit is used. If units differ or aggregation \
is ambiguous, list each occurrence separated by " + ". None if never specified.
4. optional: true ONLY if the author explicitly says so ("optional", "if you have it", "you can skip this"). \
Do not infer optionality.
5. notes: include only author-stated notes about the ingredient relevant to the whole recipe \
(what to look for, what not to substitute). None if not stated.
6. Include every ingredient — spices, oils, garnishes, masalas, everything. \
Do not omit anything used in any step."""


@Timer(name="compile_required_ingredients", text="[compile_required_ingredients] finished in {:.2f}s", logger=logger.info)
def compile_required_ingredients(state) -> dict:
    recipes = state["recipe_details"]["recipes"]
    all_ingredients = []

    for i, recipe in enumerate(recipes):
        logger.info(f"[required_ingredients] compiling {i + 1}/{len(recipes)}: '{recipe.title}'")
        result = model.with_structured_output(_RecipeIngredientList).invoke(
            [
                SystemMessage(content=_INGREDIENTS_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Compile the full ingredient list for the following recipe.\n\n"
                        f"<recipe>\n{json.dumps(recipe.model_dump(), indent=2)}\n</recipe>"
                    )
                ),
            ]
        )
        logger.info(f"[required_ingredients] done: {len(result.ingredients)} ingredients for '{recipe.title}'")
        all_ingredients.append(result.ingredients)

    return {
        "recipe_details": {
            **state["recipe_details"],
            "required_ingredients": all_ingredients,
        }
    }
