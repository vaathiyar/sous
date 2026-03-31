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
    recipe = agent_result["recipe_details"]["recipes"][0]
    source_url = agent_result.get("video_url")

    upsert_recipe(recipe, source_url=source_url)
    print(f"Recipe saved to DB: {recipe.id} — {recipe.title}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = f"{OUTPUT_DIR}/{recipe.id}.json"
    with open(out_path, "w") as f:
        json.dump(agent_result, f, indent=2, default=_pydantic_serializer)
    print(f"Recipe also saved locally: {out_path}")
