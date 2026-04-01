from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.voice import router as voice_router
from backend.config import settings

app = FastAPI(title="Sous API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
