import uuid

from sqlalchemy.dialects.postgresql import insert

from shared.db.engine import get_session
from shared.db.models import RecipeRow
from shared.schemas.recipe import ExtractedRecipe


def upsert_recipe(recipe: ExtractedRecipe, source_url: str | None = None) -> str:
    """Upsert a recipe by slug. Returns the UUID id."""
    session = get_session()
    try:
        stmt = (
            insert(RecipeRow)
            .values(
                id=uuid.uuid4(),
                slug=recipe.id,
                title=recipe.title,
                cuisine=recipe.metadata.cuisine,
                full_recipe=recipe.model_dump(),
                source_url=source_url,
            )
            .on_conflict_do_update(
                index_elements=["slug"],
                set_=dict(
                    title=recipe.title,
                    cuisine=recipe.metadata.cuisine,
                    full_recipe=recipe.model_dump(),
                    source_url=source_url,
                ),
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


def get_recipe(recipe_id: str) -> ExtractedRecipe | None:
    """Fetch by UUID id or slug."""
    session = get_session()
    try:
        try:
            uid = uuid.UUID(recipe_id)
            row = session.query(RecipeRow).filter(RecipeRow.id == uid).first()
        except ValueError:
            row = session.query(RecipeRow).filter(RecipeRow.slug == recipe_id).first()
        if row is None:
            return None
        return ExtractedRecipe(**row.full_recipe)
    finally:
        session.close()
