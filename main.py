import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Sous — AI cooking assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ingest
    ingest_parser = subparsers.add_parser("ingest", help="Extract a recipe from a YouTube video")
    ingest_parser.add_argument("url", help="YouTube URL to process")
    ingest_parser.set_defaults(func=lambda args: __import__("scripts.ingest", fromlist=["cmd_ingest"]).cmd_ingest(args))

    # chat
    chat_parser = subparsers.add_parser("chat", help="Chat with the chef agent over a recipe")
    chat_parser.add_argument("recipe_id", help="Recipe ID (slug) from the DB")
    chat_parser.set_defaults(func=lambda args: __import__("scripts.chat", fromlist=["cmd_chat"]).cmd_chat(args))

    # list
    list_parser = subparsers.add_parser("list", help="List all ingested recipes")
    list_parser.set_defaults(func=lambda args: __import__("scripts.chat", fromlist=["cmd_list"]).cmd_list(args))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
