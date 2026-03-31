import json
import uuid

from fastapi import APIRouter, HTTPException
from livekit import api
from pydantic import BaseModel

from backend.config import settings
from shared.db import create_tables, get_recipe, list_recipes

router = APIRouter(prefix="/api/voice")

create_tables()


@router.get("/recipes")
async def list_recipes_endpoint() -> list[dict]:
    """List all ingested recipes available for a cooking session."""
    return list_recipes()


class TokenRequest(BaseModel):
    recipe_id: str


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
    """
    if get_recipe(req.recipe_id) is None:
        raise HTTPException(status_code=404, detail=f"Recipe '{req.recipe_id}' not found")

    room_name = f"sous-{uuid.uuid4().hex[:8]}"

    livekit_api = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )

    await livekit_api.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="sous-chef",
            room=room_name,
            metadata=json.dumps({"recipe_id": req.recipe_id}),
        )
    )

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
