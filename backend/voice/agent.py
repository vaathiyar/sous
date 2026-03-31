import json
import logging

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import google, silero

from backend.config import settings
from backend.voice.chef_llm import ChefLLM
from shared.db import get_recipe

logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    # ctx.job.metadata is the JSON string passed in the dispatch request.
    # This is how the API layer tells the agent which recipe to load.
    metadata = json.loads(ctx.job.metadata or "{}")
    recipe_id = metadata.get("recipe_id")
    if not recipe_id:
        logger.error("No recipe_id in job metadata")
        return

    recipe = get_recipe(recipe_id)
    if recipe is None:
        logger.error(f"Recipe '{recipe_id}' not found in DB")
        return

    logger.info(f"Starting session for recipe: {recipe.title}")

    creds = {}
    if settings.google_credentials_file_path:
        creds["credentials_file"] = settings.google_credentials_file_path

    # AgentSession is the LiveKit pipeline orchestrator.
    # It wires together the four stages of a voice agent:
    #   VAD  → detects when the user is speaking (silence vs. speech)
    #   STT  → transcribes speech to text
    #   LLM  → generates a text response (our ChefLLM wraps the LangGraph agent)
    #   TTS  → synthesises the text response back into audio
    # Each stage is a plugin; swap any one out without touching the others.
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=google.STT(
            model=settings.stt_model, location=settings.stt_location, **creds
        ),
        llm=ChefLLM(recipe=recipe),
        tts=google.TTS(model_name="chirp_3", voice_name=settings.tts_voice, **creds),
    )

    # Agent holds the persona / instructions passed to the LLM system prompt.
    # Our ChefLLM manages its own state and largely ignores this, but the
    # Agent object is required by the framework to start a session.
    agent = Agent(
        instructions="You are a helpful sous chef guiding the user through a recipe step by step."
    )

    # session.start() connects the agent to the LiveKit room and begins
    # processing audio. It handles room connection internally — no ctx.connect()
    # needed when using AgentSession.
    await session.start(room=ctx.room, agent=agent)


if __name__ == "__main__":
    # WorkerOptions registers this process as an agent worker with the LiveKit server.
    # agent_name="sous-chef" enables explicit dispatch mode — the agent only joins
    # rooms when explicitly dispatched (via the API), not every room that's created.
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="sous-chef",
            ws_url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
    )
