from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage
from livekit.agents import llm, APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS

from chef.agent import chef_agent
from chef.graph.state.enums import StepStatus
from shared.schemas.recipe import ExtractedRecipe


class ChefLLMStream(llm.LLMStream):
    """
    Handles a single LLM turn — one user utterance → one agent response.

    LiveKit's STT transcribes the user's speech, then calls ChefLLM.chat()
    which returns one of these stream objects. The framework then calls _run()
    and reads ChatChunk events off the internal channel to feed into TTS.

    The "stream" abstraction exists so LLMs can emit tokens incrementally
    (good for latency). We emit a single chunk since LangGraph returns a
    complete response, not a token stream.
    """

    def __init__(
        self,
        chef_llm: "ChefLLM",
        chat_ctx: llm.ChatContext,
        tools: list,
        conn_options: APIConnectOptions,
    ):
        super().__init__(chef_llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._chef_llm = chef_llm

    async def _run(self) -> None:
        # chat_ctx is LiveKit's view of the conversation history (all turns).
        # We only care about the latest user message — our LangGraph agent
        # maintains its own state and message history independently.
        # chat_ctx.items is a list[ChatItem] — items can be messages, function
        # calls, or handoffs. We filter to the latest user ChatMessage only.
        user_text = ""
        for item in reversed(self.chat_ctx.items):
            if item.type == "message" and item.role == "user":
                user_text = item.text_content
                break

        if not user_text:
            return

        # Append the user's utterance to the LangGraph state, then invoke.
        # asyncio.to_thread offloads the synchronous graph.invoke() onto a
        # thread pool so we don't block the event loop during graph execution.
        self._chef_llm._state["messages"] = self._chef_llm._state.get(
            "messages", []
        ) + [HumanMessage(content=user_text)]

        result = await asyncio.to_thread(chef_agent.invoke, self._chef_llm._state)
        self._chef_llm._state = result

        response = result.get("response_message", "")
        if not response:
            return

        # Push the response into the channel as a ChatChunk.
        # The framework reads from this channel and pipes the text to TTS.
        self._event_ch.send_nowait(
            llm.ChatChunk(
                id=self._chef_llm.label,
                delta=llm.ChoiceDelta(
                    role="assistant",
                    content=response,
                ),
            )
        )


class ChefLLM(llm.LLM):
    """
    Adapts the LangGraph chef agent to LiveKit's LLM plugin interface.

    LiveKit expects an LLM to implement chat() → LLMStream. We satisfy that
    contract here while delegating all actual intelligence to the stateful
    LangGraph graph. The _state dict is the LangGraph ChefState — it persists
    across turns for the lifetime of the session (recipe progress, deviations, etc.).
    """

    def __init__(self, recipe: ExtractedRecipe):
        super().__init__()
        # Initial ChefState — mirrors what main.py sets up for the CLI chat mode.
        self._state = {
            "base_recipe": recipe,
            "dish_state": {"current_step": 0, "step_status": StepStatus.IN_PROGRESS},
            "deviations": [],
            "messages": [],
            "conversation_summary": "",
            "routing": {"deviation_flag": None, "deviation_type": None},
            "context_note": "",
            "response_message": "",
        }

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        **_ignored,  # drop tool_choice, parallel_tool_calls, etc. — we don't use them
    ) -> ChefLLMStream:
        # Called by the framework once per user turn.
        return ChefLLMStream(self, chat_ctx=chat_ctx, tools=tools or [], conn_options=conn_options)
