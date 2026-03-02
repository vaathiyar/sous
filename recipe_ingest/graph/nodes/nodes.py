from enum import StrEnum
from langchain_core.messages import HumanMessage, SystemMessage

from recipe_ingest.services.youtube import download_audio
from recipe_ingest.graph.chat_models import model, model_with_tools
from recipe_ingest.graph.tools import transcription_tools_by_name

from shared.schemas.recipe import ExtractedRecipes


class NodeNames(StrEnum):
    TRANSCRIBE_RECIPE_AUDIO = "transcribe_recipe_audio"
    FORMAT_REQUIRED_INGREDIENTS = "format_required_ingredients"
    EXTRACT_RECIPE_FROM_TRANSCRIPT = "extract_recipe_from_transcript"


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


def format_required_ingredients(state):
    # No-op for now. implement to extract ingredients from the extracted recipes.
    return state


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
            "recipe_details": result,
        }
    }
