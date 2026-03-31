import uuid

from sqlalchemy import Column, Text, TIMESTAMP, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RecipeRow(Base):
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(Text, unique=True, nullable=False)  # LLM-generated kebab slug, for URLs/debug
    title = Column(Text, nullable=False)
    cuisine = Column(Text, nullable=True)
    full_recipe = Column(JSONB, nullable=False)
    precook_data = Column(JSONB, nullable=True)
    ingredients_data = Column(JSONB, nullable=True)
    source_url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        # Partial unique index: enforce uniqueness on source_url only when not null.
        # Multiple null source_urls are allowed (recipes ingested without a URL).
        UniqueConstraint("source_url", name="uq_recipes_source_url"),
    )
