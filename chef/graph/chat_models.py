from langchain.chat_models import init_chat_model

import shared.config  # noqa: F401 — ensures GOOGLE_API_KEY is in os.environ
from chef.constants import REASONING_MODEL, RESPONSE_MODEL, SUMMARIZATION_MODEL, ROUTE_MODEL

reasoning_model = init_chat_model(REASONING_MODEL, temperature=0)  # deviation nodes — Gemini 3 Flash with thinking
response_model = init_chat_model(RESPONSE_MODEL, temperature=0)    # simple/step nodes — Gemini 3.1 Flash Lite
summarization_model = init_chat_model(SUMMARIZATION_MODEL, temperature=0)
route_model = init_chat_model(ROUTE_MODEL, temperature=0)
