from dotenv import load_dotenv

load_dotenv()

import argparse
import json
import os

from pydantic import BaseModel

from shared.constants import ARTIFACTS_DIR

OUTPUT_DIR = f"{ARTIFACTS_DIR}/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def pydantic_serializer(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# --- Subcommands ---


def cmd_ingest(args: argparse.Namespace) -> None:
    """Run the recipe_ingest pipeline on a YouTube URL."""
    from recipe_ingest.agent import preprocess_and_invoke_agent

    agent_result = preprocess_and_invoke_agent(args.url)

    recipe_id = agent_result['recipe_details']['recipes'][0].id
    out_path = f"{OUTPUT_DIR}/{recipe_id}.json"
    with open(out_path, "w") as f:
        json.dump(agent_result, f, indent=2, default=pydantic_serializer)

    print(f"Recipe saved to: {out_path}")


def cmd_chat(args: argparse.Namespace) -> None:
    """Interactive chat session with the chef agent over a pre-ingested recipe."""
    from langchain_core.messages import HumanMessage

    from chef.agent import agent
    from chef.graph.state.enums import StepStatus
    from shared.schemas.recipe import ExtractedRecipe

    # Load recipe from JSON
    with open(args.recipe_file) as f:
        data = json.load(f)

    recipes = data["recipe_details"]["recipes"]

    if len(recipes) == 1:
        recipe_data = recipes[0]
    else:
        print(f"\nFound {len(recipes)} recipes:")
        for i, r in enumerate(recipes):
            print(f"  {i + 1}. {r.get('title', f'Recipe {i + 1}')}")
        choice = int(input("Select recipe number: ")) - 1
        recipe_data = recipes[choice]

    recipe = ExtractedRecipe(**recipe_data)
    print(f"\n🍳 Loaded: {recipe.title}")
    print(f"   {len(recipe.steps)} steps")
    print(f"\nType your messages below. Ctrl+C or 'quit' to exit.\n")

    # Initialize state
    state = {
        "base_recipe": recipe,
        "dish_state": {"current_step": 0, "step_status": StepStatus.IN_PROGRESS},
        "deviations": [],
        "messages": [],
        "conversation_summary": "",
        "routing": {"deviation_flag": None, "deviation_type": None},
        "context_note": "",
        "response_message": "",
    }

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        # Add user message and invoke
        state["messages"] = state.get("messages", []) + [
            HumanMessage(content=user_input)
        ]

        result = agent.invoke(state)

        # Update state for next turn
        state = result

        # Print response
        response = result.get("response_message", "")
        if response:
            print(f"\nChef: {response}\n")
        else:
            print("\n(No response generated)\n")


# --- CLI ---


def main():
    parser = argparse.ArgumentParser(
        description="Sous — AI cooking assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ingest
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Extract a recipe from a YouTube video",
    )
    ingest_parser.add_argument("url", help="YouTube URL to process")
    ingest_parser.set_defaults(func=cmd_ingest)

    # chat
    chat_parser = subparsers.add_parser(
        "chat",
        help="Chat with the chef agent over a pre-ingested recipe",
    )
    chat_parser.add_argument(
        "recipe_file",
        help="Path to a recipe JSON file (from artifacts/outputs/)",
    )
    chat_parser.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
