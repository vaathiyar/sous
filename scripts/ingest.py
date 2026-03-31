import argparse
import json
import os

from pydantic import BaseModel

from recipe_ingest.agent import preprocess_and_invoke_agent
from shared.constants import ARTIFACTS_DIR
from shared.db import create_tables, upsert_recipe

OUTPUT_DIR = f"{ARTIFACTS_DIR}/outputs"


def _pydantic_serializer(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def cmd_ingest(args: argparse.Namespace) -> None:
    """Run the recipe_ingest pipeline on a YouTube URL and persist to DB and local disk."""
    create_tables()

    agent_result = preprocess_and_invoke_agent(args.url)
    recipes = agent_result["recipe_details"]["recipes"]
    briefings = agent_result["recipe_details"].get("precook_briefings", [])
    all_ingredients = agent_result["recipe_details"].get("required_ingredients", [])
    source_url = agent_result.get("video_url")

    for i, recipe in enumerate(recipes):
        briefing = briefings[i] if i < len(briefings) else None
        ingredients = all_ingredients[i] if i < len(all_ingredients) else None
        upsert_recipe(recipe, source_url=source_url, precook_briefing=briefing, ingredients=ingredients)
        print(f"Recipe saved to DB: {recipe.id} — {recipe.title}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for recipe in recipes:
        out_path = f"{OUTPUT_DIR}/{recipe.id}.json"
        with open(out_path, "w") as f:
            json.dump(agent_result, f, indent=2, default=_pydantic_serializer)
        print(f"Recipe also saved locally: {out_path}")
