# Voice-Based AI Cooking Assistant — Context Document

## What I'm Building
A real-time voice-based AI cooking agent. The user talks to it hands-free while cooking, and it guides them through a recipe step by step. Voice layer is LiveKit (WebRTC) with STT/TTS — handled separately. I need to design the runtime agent using LangGraph.

## Core Principle
"Respect the base recipe as much as possible. Any modifications should come from the base recipe's POV."

This is NOT a generic AI recipe generator. Each session is anchored to a specific recipe from a specific source (a YouTube creator, a blog author). The agent is a faithful interpreter of that recipe — it doesn't freelance, inject opinions, or deviate unless the user's circumstances require it (substitutions, mistakes, dietary needs). Every adaptation should be as faithful to the original recipe's intent as possible.

## What's Already Built — Ingestion Pipeline
Recipes are ingested from YouTube transcripts/blog posts/etc via a pipeline:

**Pass 1 (Extraction) — BUILT:** An LLM extracts only what the author explicitly stated into a structured Pydantic schema. No inference. The output is rewritten for clarity but never enriched beyond what the source contains.

**Pass 2 (Enrichment) — NOT YET BUILT:** A second pass will add derived metadata — ingredient properties (cook times, roles, scaling behavior), substitution rules with step-level adjustments, sensory cues where the author didn't provide them, common mistakes from general culinary knowledge. All enriched fields tagged with `source: "derived"`.

For now, the agent works with Pass 1 output only (base recipe + whatever the agent can figure out at runtime). Schema is designed to accommodate Pass 2 when it arrives.

### Schema Design — Key Points
- **Steps are the spine.** Ingredients, equipment, sensory cues — everything nested inside steps, not flat top-level lists.
- **Provenance matters.** Every piece of data is `author` (from source), `derived` (AI-enriched at ingestion), or `runtime` (agent figures it out live). Agent's tone and confidence shifts based on provenance.
- **Sensory checkpoints per step.** What the dish should look/smell/taste like at end of each step.
- **Sensory target for the dish.** Top-level field capturing the author's description of the final dish.
- **Cultural context.** Author's commentary on origin, regional significance, what makes this version distinct.
- **Substitution rules** (when Pass 2 exists): Step-level adjustments and tradeoff descriptions.
- Schema is cuisine-agnostic (not tailored to one cuisine). Indian culinary examples may appear but the design is open-ended.

## Agent Behavioral Model

**Provenance-based communication:**
- Author data → relay confidently, attribute ("the recipe says...")
- Derived data → state as inference, no false attribution ("based on the recipe, this should take about...")
- Runtime reasoning → transparent ("the recipe doesn't cover this, but generally...")

**Decision hierarchy for substitutions/questions:**
1. Explicit substitution rule in schema → use it
2. Enough info in ingredient properties + step metadata to reason → do so, flag confidence
3. Requires general culinary knowledge → use it, be transparent
4. Genuinely uncertain → ask the user, don't guess

**Zero opinion on the base recipe.** No unprompted improvements or alternatives. Adapts only when user's situation demands it.

## Product Decisions Already Made

**The agent is a companion, not a commander.** It doesn't proactively interrogate the user about progress or mandate they follow its steps. It's reactive — responds to what the user brings. It helps people without cooking experience (or without context of a regional cuisine/technique) understand the dish and adapt when things go wrong.

**Step advancement is inferred, not explicit.** The user doesn't have to say "next step." The agent infers from context ("ok I've added the onions" → they've moved past chopping). If unsure, it asks.

## Session Lifecycle
- **Pre-cook:** Load recipe, walk through mise en place, surface dietary flags, handle substitutions before cooking starts.
- **Active cooking:** Step-by-step guidance. Handle interrupts (questions, mistakes, substitutions). Track parallel steps. Proactive check-ins during passive waits (simmering, marinating).
- **Post-cook:** Session summary, modifications made, option to save modified version.

## State — What the Agent Needs to Track
These are the things the LLM cannot reliably maintain on its own across a long session:
- **base_recipe** — immutable, the full extracted recipe
- **dish_state** — current step, step status (in_progress/complete). Lean — just position tracking.
- **deviations[]** — finalized substitutions/amendments with downstream effects. Each deviation has: step it was performed in, reason, description of change, optional swapped ingredients, and affected downstream steps.
- **active_interaction** — when a deviation (or uncertain step change) needs user confirmation before finalizing. This is for pending state mutations only, not general conversational follow-ups.
- **conversation_history** — recent messages + summarized/truncated older messages for long sessions.
- **context_note** — short string breadcrumb from state-mutating logic for the response generation (e.g., "Proposed substitution: cashew paste for cream. Awaiting confirmation.")

## Key Concepts About Deviations
- Deviations are a **patch stack on a linear sequence**, not a tree. The recipe never branches — steps are still the same steps, just potentially modified.
- The canonical recipe is immutable. Deviations layer on top as ordered mutations consulted when rendering any step.
- Two types: **substitutions** (ingredient swap) and **amendments** (corrective actions, timing changes, additions — no swap involved).
- Pre-cook deviations (dietary, missing ingredients) are known upfront and affect all downstream steps.
- Mid-cook deviations (ran out of something, corrective action, taste adjustment) affect remaining steps.
- When computing a new deviation's downstream effects, the LLM needs the recipe + ALL prior deviations (not just the canonical recipe), because deviations can interact.
- Deviations should not be finalized without user confirmation. A proposed deviation lives in `active_interaction` until confirmed, then moves to `deviations[]`.

## Key Concepts About Step Changes
- Steps can go forward or backward (agent might misconstrue input, user might need to redo something).
- Low-confidence step changes should be confirmed with the user before applying.

## Context Window Considerations
- For voice, latency is critical. Time-to-first-token budget is under 2 seconds ideally.
- Full recipe + all deviations + conversation history can get large for complex recipes (30+ steps, 2-hour sessions, 100+ exchanges).
- Conversation history needs a truncation/summary strategy for long sessions.
- There's a distinction between **state** (always preserved — dish_state, deviations) and **conversation history** (can be truncated/summarized). State is what must survive truncation. Intermediate sensory observations and cooking updates live in conversation history, not structured state.

## What I Need
Design the LangGraph agent. After extensive discussion, the key learnings about architecture are:

1. **Don't over-engineer the graph topology.** The routing/classification between query types (question, step change, deviation) might not need separate nodes — an LLM can classify implicitly while responding.
2. **Start with the simplest possible graph and split nodes only when you observe actual failures** (prompt too complex, LLM dropping balls on deviation reasoning, etc.).
3. **The behavioral model (provenance, tone, recipe faithfulness) belongs in the system prompt, not in graph structure or state schemas.**
4. **The graph's job is state management and routing, not communication design.** Trust the LLM for how to talk. Use the graph for what to remember.
5. **Deviation handling is the most complex part** — it involves multi-turn confirmation, downstream effect computation, and interaction with prior deviations. If anything deserves its own node, it's this.

## P2 (Don't Overbuild For Now)
- Multi-recipe sessions
- User profiles (dietary preferences, skill level, equipment)
