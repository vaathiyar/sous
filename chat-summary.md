# Sous — Product Requirements Document

## 1. Product Vision

**Sous** is a real-time, voice-based AI cooking assistant. The user talks to it hands-free while cooking, and it guides them through a recipe step by step.

This is **not** a generic recipe generator or cooking chatbot. Each session is anchored to a **specific recipe from a specific human creator** — a YouTube chef, a blog author, a family cookbook, etc. The agent is a **faithful interpreter** of that recipe. It doesn't freelance, inject opinions, or deviate unless the user's real-world circumstances demand it. Every adaptation should honor the original recipe's intent as closely as possible.

### Core Principle

> "Respect the base recipe as much as possible. Any modifications should come from the base recipe's POV."

### Who Is This For?

People cooking at home - potentially without significant cooking experience or without context for a regional cuisine or technique - who want guided, hands-free help understanding and executing a specific recipe. The agent helps when things go wrong, explains unfamiliar techniques, and adapts when the user's situation requires it.

---

## 2. Product Personality

### Companion, Not Commander

The agent is **reactive**, not proactive. It does not interrogate the user about progress or mandate they follow steps. It responds to what the user brings. It is a helpful presence in the kitchen - available when needed, quiet when not.

### Provenance-Based Communication

Every piece of information has a source, and the agent's tone should reflect that:

| Source | Tone | Example |
|---|---|---|
| **Author-stated** (from the recipe) | Confident, attributed | *"The recipe says to add cumin seeds first and fry until golden brown."* |
| **Derived** (AI-enriched at ingestion, or obvious inference) | Stated as inference | *"Based on the recipe, this should take about 10 minutes."* |
| **Runtime reasoning** (general knowledge, not in recipe) | Transparent, hedged | *"The recipe doesn't cover this, but generally you'd want to reduce heat here."* |

This matters because trust is the product. If the agent presents general knowledge as if the recipe author said it, and the user later discovers that's wrong, credibility is destroyed. Attribution preserves trust.

### Zero Unsolicited Opinion

The agent never offers unprompted improvements, alternatives, or commentary on the base recipe. It does not say *"you could also try..."* unless the user's situation requires adaptation. The recipe author's version is the canonical truth.

---

## 3. Decision Hierarchy

When the user asks a question, needs a substitution, or encounters a problem, the agent follows a strict priority order:

1. **Explicit substitution rule in the recipe schema** → Use it directly.
2. **Enough information in the recipe's ingredients/steps to reason** → Do so, flag confidence level.
3. **Requires general culinary knowledge** → Use it, be transparent that it's not from the recipe.
4. **Genuinely uncertain** → Ask the user. Do not guess.

This hierarchy ensures the agent exhausts recipe-specific knowledge before falling back to general knowledge, and never fabricates confidence.

---

## 4. Session Lifecycle

A cooking session has three phases. The agent's behavior shifts across them:

### Pre-Cook
- Load the recipe and walk through mise en place (ingredient prep).
- Surface dietary flags or missing ingredients.
- Handle pre-cook substitutions before cooking starts. These deviations are "known upfront" and affect all downstream steps.

### Active Cooking
- Step-by-step guidance through the recipe.
- Handle interruptions: questions, mistakes, substitutions, technique clarifications.
- Track deviations as they occur.
- **Step advancement is inferred, not explicit.** The user does not have to say "next step." The agent infers from conversational context (*"ok I've added the onions"* → they've moved past the chopping step). If the agent is unsure, it asks.

### Post-Cook
- Session summary: what was cooked, what modifications were made.
- Option to save the modified version (P2).

---

## 5. Deviations — The Core Complexity

Deviations are the most product-critical concept in Sous. They represent any departure from the base recipe — and the system must handle them carefully because deviations **cascade**.

### What Is a Deviation?

Any change to the base recipe that the user makes (deliberately or forced by circumstance):

| Type | Definition | Examples |
|---|---|---|
| **Substitution** | An ingredient swap | *"I don't have cream" → cashew paste* |
| **Amendment** | A corrective action, timing change, or addition — no direct swap | *"I accidentally added too much salt"*, *"I want to make it spicier"* |

### Deviations Are a Patch Stack, Not a Tree

The recipe is a linear sequence of steps. It never branches. Deviations are **ordered mutations layered on top** of the canonical recipe. When the agent renders any step, it consults the deviation stack and adjusts guidance accordingly.

The canonical recipe is **immutable**. It is never modified in place. Deviations are stored separately and applied at render time.

### Downstream Effects

This is why deviations are complex: changing step 3 may affect steps 5, 7, and 9. When computing a new deviation, the agent must consider:
- The base recipe
- **ALL prior deviations** (because deviations interact - a previous substitution may change what's possible now)
- The specific step the deviation was introduced at

### Two-Phase Confirmation

Deviations are never finalized without user confirmation:

1. **Propose:** The agent identifies a deviation, double-checks it's genuine (not a misclassified question), and proposes it - explaining what would change, which steps are affected, and any tradeoffs (taste, texture, technique). It asks the user if they want to proceed.
2. **Confirm:** If the user agrees, the agent computes the full deviation - including all impacted downstream steps - and records it in state. From this point forward, affected steps are rendered with the deviation applied.

This exists because deviations have consequences. A substitution that sounds fine in isolation might ruin the dish three steps later. The two-phase flow gives the agent time to reason about downstream effects and gives the user the chance to reconsider.

### Why a Dedicated Deviation Node?

Deviation handling is isolated in its own LLM call (separate from the main reasoning node) because:
- The prompt is specialized - it needs the full recipe, all prior deviations, and specific instructions about downstream reasoning.
- Combining deviation reasoning with general Q&A in a single prompt leads to the LLM "dropping balls" - cutting corners on downstream effect computation.
- Deviations are infrequent (most turns are simple queries), so the extra LLM call is only incurred when needed.

---

## 6. Step Changes

Step tracking is lean: just the current step number and a status (in-progress / complete).

### Forward and Backward

Steps can go in either direction. The agent might misconstrue user input and jump ahead; the user might need to redo something. Both directions are supported.

### Obvious vs. Ambiguous

- **Obvious:** *"Done, what's next?"* → Advance and describe the next step.
- **Ambiguous:** *"Let's do the masalas"* (could be step 4 or 5) → Ask for clarification. No state change until resolved.

The agent should confirm step changes when confidence is low, and apply them silently when confidence is high. The user is cooking — unnecessary confirmation prompts are friction.

---

## 7. Conversation Management

### The Problem

Voice sessions can be long (1–2 hours for complex recipes), producing 100+ message exchanges. The full conversation history can exceed the LLM's effective context window and increase latency.

### The Solution

**State vs. History distinction:** There is a critical difference between *state* (must survive forever) and *conversation history* (can be compressed).

| Category | Survives truncation? | Examples |
|---|---|---|
| **State** | Always | `dish_state`, `deviations[]`, `base_recipe` |
| **History** | Summarized | Intermediate sensory observations, casual exchanges, resolved Q&A |

The system maintains a **token budget** (~8K tokens, adjustable). When conversation history exceeds the budget, the older half is summarized by an LLM into a concise narrative and the original messages are deleted. The summary is accumulated across multiple truncation cycles.

The summary prompt is **product-aware** — it focuses on cooking progress, decisions made, user preferences, observations, and pending questions. It discards greetings, filler, and conversational niceties.

### Latency Budget

For voice, time-to-first-token is critical. The target is **under 2 seconds**. This constrains:
- How much context is included in prompts
- Model selection (currently Gemini 3 Flash Preview — optimized for speed)
- Whether to use structured output (adds latency but improves reliability)

---

## 8. Recipe Ingestion Pipeline

Recipes enter the system through a two-pass pipeline. The agent consumes the output.

### Pass 1: Extraction (BUILT)

An LLM extracts only what the recipe author **explicitly stated** into a structured Pydantic schema. No inference. No enrichment. The output is rewritten for clarity but never goes beyond what the source contains. If the author didn't say it, it's not here.

Key schema design decisions:
- **Steps are the spine.** Ingredients, equipment, sensory cues — everything is nested inside steps, not in flat top-level lists. This reflects how recipes are actually followed.
- **Sensory checkpoints per step.** What the dish should look/smell/taste like at the end of each step, per the author.
- **Regional terms preserved.** *"Seeraga samba"* stays *"seeraga samba"*, not *"short-grain rice."* Translation only if the original is genuinely obscure.
- **Author's voice for quantities.** *"A handful"*, *"enough to coat"*, *"2 cups"* — preserved as-is. No normalization.
- **Cultural context.** Author's commentary on the dish's identity, origin, what makes this version distinct.

### Pass 2: Enrichment (NOT YET BUILT)

A second pass will add derived metadata:
- Ingredient properties (cook times, roles, scaling behavior)
- Substitution rules with step-level adjustments
- Sensory cues where the author didn't provide them
- Common mistakes from general culinary knowledge

All enriched fields will be tagged with `source: "derived"` to support the provenance-based communication model. The schema is designed to accommodate Pass 2 when it arrives.

---

## 9. Design Principles (for Implementers)

These are principles that emerged from the design process and should guide future work:

1. **Don't over-engineer the graph topology.** Start with the simplest possible graph and split nodes only when you observe actual failures — prompts too complex, LLM dropping balls, etc.

2. **The behavioral model belongs in the system prompt, not in graph structure or state schemas.** Provenance rules, tone, recipe faithfulness — these are LLM instructions, not code.

3. **The graph's job is state management and routing.** Trust the LLM for *how* to talk. Use the graph for *what* to remember.

4. **State should be minimal.** Only track what the LLM cannot reliably maintain on its own across a long session. Don't structure what can live in conversation history.

5. **Deviation handling is the exception to "keep it simple."** It's the one area complex enough to justify isolation — separate prompt, separate node, separate reasoning.

---

## 10. What's Built vs. What's Not

| Component | Status | Notes |
|---|---|---|
| Recipe ingestion — Pass 1 (extraction) | ✅ Built | YouTube → transcript → structured recipe |
| Recipe ingestion — Pass 2 (enrichment) | ❌ Not built | Derived metadata, substitution rules |
| Chef agent — graph + state | ✅ Built | 3 nodes + conditional routing |
| Chef agent — prompts | ✅ Built | System, summarization, deviation (proposal + confirm) |
| CLI (ingest + chat modes) | ✅ Built | `main.py` with argparse |
| Voice layer (LiveKit/WebRTC) | ❌ Not built | STT/TTS handled separately |
| Multi-recipe sessions | ❌ P2 | One recipe per session for now |
| User profiles | ❌ P2 | Dietary preferences, skill level, equipment |
| Post-cook session save | ❌ P2 | Save modified recipe version |

---

## 11. P2 Considerations

These were explicitly deferred:

- **Multi-recipe sessions:** Supporting multiple recipes in one session (e.g., a multi-course meal).
- **User profiles:** Persisting dietary restrictions, equipment availability, skill level across sessions.
- **Modified recipe export:** Saving the recipe-as-cooked (base + deviations applied) for future use.
- **Proactive check-ins during passive waits:** Timer-based nudges during simmering/marinating steps. Currently the agent is purely reactive.
