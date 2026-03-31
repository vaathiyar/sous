import argparse
import asyncio

from langchain_core.messages import HumanMessage

from chef.agent import chef_agent
from chef.graph.state.enums import StepStatus
from shared.db import get_recipe, list_recipes


def cmd_chat(args: argparse.Namespace) -> None:
    """Interactive chat session with the chef agent over a recipe loaded from DB."""
    result = get_recipe(args.recipe_id)
    if result is None:
        print(f"Recipe '{args.recipe_id}' not found in DB. Run 'ingest' first.")
        return

    print(f"\nLoaded: {result.title}")
    print(f"   {len(result.recipe.steps)} steps")
    print(f"\nType your messages below. Ctrl+C or 'quit' to exit.\n")

    state = {
        "base_recipe": result.recipe,
        "precook_briefing": result.precook_briefing,
        "dish_state": {"current_step": 0, "step_status": StepStatus.IN_PROGRESS},
        "deviations": [],
        "messages": [],
        "conversation_summary": "",
        "routing": {"deviation_type": None, "new_step": None},
        "context_note": "",
        "response_message": "",
    }

    # Trigger the opening briefing before the input loop
    state = asyncio.run(chef_agent.ainvoke(state))
    response = state.get("response_message", "")
    if response:
        print(f"\nChef: {response}\n")

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

        state["messages"] = state.get("messages", []) + [HumanMessage(content=user_input)]
        result = asyncio.run(chef_agent.ainvoke(state))
        state = result

        response = result.get("response_message", "")
        if response:
            print(f"\nChef: {response}\n")
        else:
            print("\n(No response generated)\n")


def cmd_list(args: argparse.Namespace) -> None:
    """List all ingested recipes in the DB."""
    recipes = list_recipes()
    if not recipes:
        print("No recipes found. Run 'ingest' first.")
        return
    print(f"\n{len(recipes)} recipe(s) in DB:\n")
    for r in recipes:
        cuisine = f"  [{r['cuisine']}]" if r.get("cuisine") else ""
        print(f"  {r['id']}{cuisine}")
        print(f"    {r['title']}")
