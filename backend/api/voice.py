import json
import os
import uuid

from fastapi import APIRouter, HTTPException
from livekit import api
from pydantic import BaseModel

from backend.config import settings

router = APIRouter(prefix="/api/voice")

OUTPUTS_DIR = f"{settings.artifacts_dir}/outputs"


# ADR: The data store is localhost for now and we'll move to an SQL DB eventually.
# All recipe functions should be modular enough so it's contract does not change when we move to SQL.
@router.get("/recipes")
async def list_recipes() -> list[dict]:
    """List all ingested recipes available for a cooking session."""
    if not os.path.isdir(OUTPUTS_DIR):
        return []

    recipes = []
    for fname in sorted(os.listdir(OUTPUTS_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(OUTPUTS_DIR, fname)
        try:
            with open(fpath) as f:
                data = json.load(f)
            recipe_list = data.get("recipe_details", {}).get("recipes", [])
            if recipe_list:
                r = recipe_list[0]
                recipes.append(
                    {
                        "id": r.get("id", fname),
                        "title": r.get("title", fname),
                        "file": fpath,
                    }
                )
        except Exception:
            continue

    return recipes


class TokenRequest(BaseModel):
    recipe_file: str


class TokenResponse(BaseModel):
    token: str
    livekit_url: str
    room_name: str


@router.post("/token", response_model=TokenResponse)
async def create_token(req: TokenRequest) -> TokenResponse:
    """
    Entry point for starting a voice cooking session.

    LiveKit works like this:
      1. Your backend creates a room on the LiveKit server.
      2. Your backend dispatches an agent worker to that room.
      3. Your backend issues a signed JWT (token) to the frontend.
      4. The frontend uses that token to join the same room via WebRTC.
      5. The agent worker and the user are now in the same room, exchanging audio.

    The JWT is essentially a short-lived credential — it scopes what the bearer
    can do (join a specific room) without exposing your API secret to the client.
    """
    if not os.path.isfile(req.recipe_file):
        raise HTTPException(status_code=404, detail="Recipe file not found")

    room_name = f"sous-{uuid.uuid4().hex[:8]}"

    livekit_api = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )

    # Dispatch the agent worker to the room.
    # - The room is created automatically by LiveKit if it doesn't exist yet.
    # - agent_name="sous-chef" matches the name registered in WorkerOptions —
    #   this is how LiveKit knows which worker pool to pull from.
    # - metadata is a freeform string passed to ctx.job.metadata in the worker,
    #   used here to tell the agent which recipe file to load.
    await livekit_api.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="sous-chef",
            room=room_name,
            metadata=json.dumps({"recipe_file": req.recipe_file}),
        )
    )

    # Generate a JWT for the frontend participant.
    # VideoGrants scopes the token: room_join=True lets the bearer join,
    # room=room_name restricts them to this specific room only.
    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity("user")
        .with_name("User")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    await livekit_api.aclose()

    return TokenResponse(
        token=token,
        livekit_url=settings.livekit_url,
        room_name=room_name,
    )
