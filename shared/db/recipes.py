import uuid

from sqlalchemy.dialects.postgresql import insert

from shared.db.engine import get_session
from shared.db.models import RecipeRow
from shared.schemas.recipe import ExtractedRecipe, PreCookBriefing, RecipeIngredient


def upsert_recipe(
    recipe: ExtractedRecipe,
    source_url: str | None = None,
    precook_briefing: PreCookBriefing | None = None,
    ingredients: list[RecipeIngredient] | None = None,
) -> str:
    """
    Upsert a recipe. Conflict strategy:
    - source_url provided → conflict on source_url (stable, URL-based identity)
    - source_url absent   → conflict on slug (fallback)
    Returns the UUID id.
    """
    precook_dump = precook_briefing.model_dump() if precook_briefing else None
    ingredients_dump = [i.model_dump() for i in ingredients] if ingredients else None
    update_fields = dict(
        slug=recipe.id,
        title=recipe.title,
        cuisine=recipe.metadata.cuisine,
        full_recipe=recipe.model_dump(),
        precook_data=precook_dump,
        ingredients_data=ingredients_dump,
        source_url=source_url,
    )
    conflict_target = "source_url" if source_url else "slug"

    session = get_session()
    try:
        stmt = (
            insert(RecipeRow)
            .values(id=uuid.uuid4(), **update_fields)
            .on_conflict_do_update(
                index_elements=[conflict_target],
                set_=update_fields,
            )
            .returning(RecipeRow.id)
        )
        result = session.execute(stmt)
        session.commit()
        return str(result.scalar())
    finally:
        session.close()


def list_recipes() -> list[dict]:
    session = get_session()
    try:
        rows = session.query(RecipeRow.id, RecipeRow.slug, RecipeRow.title, RecipeRow.cuisine).all()
        return [
            {"id": str(r.id), "slug": r.slug, "title": r.title, "cuisine": r.cuisine}
            for r in rows
        ]
    finally:
        session.close()


def _fetch_row(session, recipe_id: str):
    """Fetch a RecipeRow by UUID id or slug."""
    try:
        uid = uuid.UUID(recipe_id)
        return session.query(RecipeRow).filter(RecipeRow.id == uid).first()
    except ValueError:
        return session.query(RecipeRow).filter(RecipeRow.slug == recipe_id).first()


def get_recipe(recipe_id: str) -> tuple[ExtractedRecipe, PreCookBriefing | None] | None:
    """Fetch recipe and precook briefing in one query. Returns None if not found."""
    session = get_session()
    try:
        row = _fetch_row(session, recipe_id)
        if row is None:
            return None
        recipe = ExtractedRecipe(**row.full_recipe)
        briefing = PreCookBriefing(**row.precook_data) if row.precook_data else None
        return recipe, briefing
    finally:
        session.close()
