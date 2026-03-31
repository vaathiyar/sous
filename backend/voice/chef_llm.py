from __future__ import annotations

from langchain_core.messages import HumanMessage, AIMessageChunk
from livekit.agents import llm, APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS

from chef.agent import chef_agent
from chef.graph.nodes.node_names import NodeNames
from chef.graph.state.enums import StepStatus
from shared.schemas.recipe import ExtractedRecipe


# Nodes that produce spoken output — their tokens are streamed to TTS
SPEECH_NODES = {
    NodeNames.SIMPLE_QUERY_RESPONSE,
    NodeNames.STEP_CHANGE_RESPONSE,
    NodeNames.NEW_PROPOSAL,
    NodeNames.CONFIRMATION_ACK,
}


class ChefLLMStream(llm.LLMStream):
    """
    Handles a single LLM turn — one user utterance → one agent response.

    LiveKit's STT transcribes the user's speech, then calls ChefLLM.chat()
    which returns one of these stream objects. The framework then calls _run()
    and reads ChatChunk events off the internal channel to feed into TTS.

    astream with stream_mode=["values","messages"] yields two event types:
      ("values", full_state)         — emitted after each node completes
      ("messages", (chunk, metadata)) — emitted per token during a node's LLM call

    We push tokens to _event_ch only from SPEECH_NODES so TTS starts on the
    first token of the response rather than waiting for the full graph to finish.
    State is persisted via "values" events, making interruptions safe.
    """

    def __init__(
        self,
        chef_llm: "ChefLLM",
        chat_ctx: llm.ChatContext,
        tools: list,
        conn_options: APIConnectOptions,
    ):
        super().__init__(
            chef_llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options
        )
        self._chef_llm = chef_llm

    async def _run(self) -> None:
        user_text = ""
        for item in reversed(self.chat_ctx.items):
            if item.type == "message" and item.role == "user":
                user_text = item.text_content
                break

        if not user_text:
            return

        self._chef_llm._state["messages"] = self._chef_llm._state.get(
            "messages", []
        ) + [HumanMessage(content=user_text)]

        async for chunk_type, data in chef_agent.astream(
            self._chef_llm._state, stream_mode=["values", "messages"]
        ):
            if chunk_type == "values":
                # Full state snapshot after each node — keeps state current even if interrupted
                self._chef_llm._state = data
            elif chunk_type == "messages":
                msg, metadata = data
                node = metadata.get("langgraph_node", "")
                if (
                    isinstance(msg, AIMessageChunk)
                    and node in SPEECH_NODES
                    and msg.content
                ):
                    # ADR: This patch introducing some tight coupling between model provider (gemini) and livekit.
                    # Gemini returns a list of content parts, but Claude/OpenAI expect a string.
                    # We'll be just using gemini for now, so not putting much effort into this fix.
                    # Will probably create a proper interface to avoid coupling later. Will fix it when the problem arises.
                    content = msg.content
                    if isinstance(content, list):
                        content = "".join(
                            p.get("text", "") for p in content if isinstance(p, dict)
                        )
                    if content:
                        self._event_ch.send_nowait(
                            llm.ChatChunk(
                                id=self._chef_llm.label,
                                delta=llm.ChoiceDelta(
                                    role="assistant",
                                    content=content,
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
            "routing": {"deviation_type": None, "new_step": None},
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
        return ChefLLMStream(
            self, chat_ctx=chat_ctx, tools=tools or [], conn_options=conn_options
        )
