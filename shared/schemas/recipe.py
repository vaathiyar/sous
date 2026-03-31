from __future__ import annotations
from pydantic import BaseModel, Field


class RecipeMetadata(BaseModel):
    cuisine: str | None = Field(
        None,
        description="Infer from the dish, ingredients, and context. Single common word only: indian, chinese, italian, mexican, american, thai, japanese, etc. Null if genuinely ambiguous.",
    )
    region_notes: str | None = Field(
        None,
        description="What makes this version regionally or stylistically distinct, per the author.",
    )
    servings: str | None = Field(
        None,
        description="As the author states it: 'serves 4', 'a large pot', etc.",
    )
    total_time: str | None = Field(
        None,
        description="As the author states it. None if not mentioned.",
    )


class StepIngredient(BaseModel):
    """An ingredient as it appears in a specific step."""

    name: str = Field(
        description="Preserve regional terms (seeraga samba, kashmiri mirchi). Translate to common name only if the original is obscure."
    )
    quantity: str | None = Field(
        None,
        description="As the author states it: '2 cups', 'a handful', 'enough to coat'. None if not specified.",
    )
    prep: str | None = Field(
        None,
        description="How the author says to prepare this ingredient for this step. None if not stated.",
    )
    author_note: str | None = Field(
        None,
        description="Author's commentary on this ingredient in this context — why it matters, what not to substitute, what to look for.",
    )


class CommonMistake(BaseModel):
    """Only mistakes the author explicitly warns about."""

    mistake: str
    consequence: str | None = None
    fix: str | None = None


class Step(BaseModel):
    step: int
    title: str = Field(description="Short descriptive title for the step")
    instruction: str = Field(
        description="What to do in this step. Faithful to the author's intent, technique, and level of detail.",
    )
    duration: str | None = Field(
        None,
        description=(
            "How the author describes timing for this step. "
            "Can be precise ('10 minutes'), approximate ('about 8-10 minutes'), "
            "or open-ended ('until the raw smell goes away'). None if not indicated."
        ),
    )
    is_passive: bool = Field(
        False,
        description="True if step involves hands-off waiting: marinating, simmering, soaking, etc.",
    )
    ingredients: list[StepIngredient] = Field(
        default_factory=list,
        description="Ingredients introduced or used in this step, with step-specific context.",
    )
    sensory_checkpoint: str | None = Field(
        None,
        description="How the dish should look, smell, or taste at the end of this step, per the author. None if not described.",
    )
    author_tips: list[str] = Field(
        default_factory=list,
        description="Advice, emphasis, or warnings the author gives during this step.",
    )
    common_mistakes: list[CommonMistake] = Field(
        default_factory=list,
        description="Only mistakes the author explicitly warns about. Usually empty.",
    )
    equipment: list[str] = Field(
        default_factory=list,
        description="Equipment the author mentions for this step.",
    )


class AuthorSubstitution(BaseModel):
    """A substitution the author explicitly suggests."""

    original: str = Field(description="Ingredient being substituted")
    substitute: str = Field(description="What the author suggests instead")
    context: str | None = Field(
        None,
        description="Author's commentary: when to use it, tradeoffs, what changes.",
    )


class ExtractedRecipe(BaseModel):
    """
    Pass 1 output: faithful extraction of author-stated information only.

    Structured representation of the recipe as the author presents it.
    Rewritten for clarity, but no inference or enrichment.
    If the author didn't say it, it's not here.
    """

    id: str = Field(
        description="kebab-case slug, e.g. 'ambur-chicken-biryani' with author/channel/source name"
    )
    title: str = Field(description="Recipe title as the author names it")
    metadata: RecipeMetadata
    steps: list[Step]
    substitutions: list[AuthorSubstitution] = Field(default_factory=list)
    cultural_context: list[str] = Field(
        default_factory=list,
        description=(
            "Author's commentary on the dish's identity: origin, history, "
            "regional significance, family connection, what makes this version "
            "distinct, how it should be served/eaten."
        ),
    )
    sensory_target: list[str] = Field(
        default_factory=list,
        description=(
            "Author's descriptions of what the finished dish should "
            "taste, feel, or look like. The target the cook is aiming for."
        ),
    )


class ExtractedRecipes(BaseModel):
    extracted_recipes: list[ExtractedRecipe]


class RecipeIngredient(BaseModel):
    """A deduplicated ingredient entry for the full recipe — shopping list view."""

    name: str = Field(
        description=(
            "Canonical name as the author uses it. Preserve regional terms. "
            "Deduplicate across steps — same ingredient appearing in multiple steps is one entry."
        )
    )
    quantity: str | None = Field(
        None,
        description=(
            "Total quantity needed. Aggregate across steps if the same unit is used "
            "('1 cup' in step 1 + '½ cup' in step 3 = '1½ cups'). "
            "If units differ or aggregation is ambiguous, use the author's original phrasings joined. "
            "None if never specified."
        ),
    )
    optional: bool = Field(
        False,
        description="True only if the author explicitly marks this ingredient as optional.",
    )
    notes: str | None = Field(
        None,
        description="Author's note about this ingredient relevant across the whole recipe. None if not stated.",
    )


class PrepItem(BaseModel):
    task: str = Field(
        description=(
            "What the cook needs to do or have ready. Include quantity as stated in the recipe "
            "(e.g. 'Soak 2 cups basmati rice in cold water', not just 'Soak rice')."
        )
    )
    duration: str | None = Field(
        None,
        description="As the author states it ('30 minutes', 'overnight'). None if not stated — never estimate.",
    )
    ingredients: list[str] = Field(
        default_factory=list,
        description="Ingredient names involved in this prep task.",
    )
    notes: str | None = Field(
        None,
        description="Author-specific guidance relevant to this task. None if not stated.",
    )


class PreCookBriefing(BaseModel):
    """
    Generated from ExtractedRecipe. Surfaces what the cook needs to know and prepare
    before the cooking session begins. Shown as reading material in the pre-cook screen.
    """

    summary: str = Field(
        description=(
            "2-3 sentences: what the dish is, the overall cooking approach, "
            "and the one thing the cook must not mess up. Practical, not poetic."
        )
    )
    active_time: str | None = Field(
        None,
        description=(
            "Total hands-on cooking time, aggregated from step durations where explicitly stated. "
            "Use author's phrasing. None if no durations are stated — never estimate."
        ),
    )
    passive_time: str | None = Field(
        None,
        description=(
            "Total hands-off waiting time (marination, soaking, simmering), "
            "aggregated from step durations where explicitly stated. "
            "Use author's phrasing. None if not stated."
        ),
    )
    prep_items: list[PrepItem] = Field(
        default_factory=list,
        description=(
            "Ordered list of things to prepare before step 1. "
            "Longest-duration items first, instant prep last."
        ),
    )
