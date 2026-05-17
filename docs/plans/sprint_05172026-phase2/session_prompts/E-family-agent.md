# Track E — Family-friendly graph-building agent

**Sprint:** `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/`
**Branch:** `sprint/family-agent`
**Worktree path (PM pre-creates):** `/private/tmp/mg-wt-E`
**Wave:** 3 (parallel with F, G)
**Dependencies:** Tracks A, B, C, D merged to main.

## How to work on this branch

PM has pre-created the worktree off `main` after A–D merged. You do NOT call `EnterWorktree`. Use `git -C /private/tmp/mg-wt-E <git-op>`.

## Goal

Create a specialized Claude agent definition (under `.claude/agents/`) that lets Clare and Jeremiah build out the three graphs through a conversational UX, without ever seeing YAML, markdown frontmatter, or wikilink syntax. The agent wraps the four skills (`retrieve-spotify-song`, `add-node`, `add-edge`, `expand-graph`) and adds friendly defaults, error handling, and onboarding language.

Target environments: **claude.ai/code (cloud, primary)** and **local Claude Code (fallback)**. The agent and skills must behave identically in both.

## Context files to read

- `/Users/alecchapman/Code/music-graphs/docs/plans/sprint_05172026-phase2/project_spec.md` — sections "Audience" and "B. Family-friendly graph-building agent" (behavior requirements are listed there).
- Each of the four SKILL.md files at `.claude/skills/{retrieve-spotify-song,add-node,add-edge,expand-graph}/SKILL.md`.
- Example agent definitions (find in repo or under `~/.claude/agents/` for format reference; use whatever is current).
- `/Users/alecchapman/Code/music-graphs/README.md` — for tone/voice and to know what setup docs already exist for users.

## Definition of done

- [ ] `.claude/agents/music-graphs-builder.md` (or `.json`, per the current agent definition format) exists with:
  - **System prompt** that establishes the agent's role: graph-building assistant for music-graphs, audience is non-technical, never expose YAML/markdown to the user.
  - **Greeting flow:** lists the three current graphs, their node counts, and example existing nodes; asks the user which graph they want to work on.
  - **Mutation flow:** every node/edge mutation goes through the four skills. Agent never writes a card file directly. Agent never proposes a Spotify URL without verifying via `retrieve-spotify-song`.
  - **Suggestion behavior:** when the user mentions an entity that matches an existing card's `name` field (fuzzy), agent surfaces that card as a likely target/source for wikilinks before creating anything new.
  - **Error handling:** if a skill fails (lint error, MCP unavailable, etc.), agent explains the failure in plain language and offers next steps. Never dumps a stack trace.
- [ ] **Cross-environment parity.** Agent and skills work identically on claude.ai/code (cloud) and local Claude Code. No environment-specific branches. If the Spotify MCP is unavailable in one environment, the agent detects it and gracefully degrades (skill returns its "MCP unavailable" message; agent relays it).
- [ ] **Setup docs.** Create `docs/family-setup.md` covering:
  - Option (c): cloud path — "Open the repo on claude.ai/code, start a conversation with the music-graphs-builder agent."
  - Option (a): local path — "Install Claude Code, clone the repo, run `claude` in the repo, ask for the music-graphs-builder agent."
  - Spotify MCP configuration (one-time, per machine) with link to the official setup doc if available.
  - Three-step "your first card" walkthrough.
- [ ] **End-to-end test (manual, but rehearsable).** Run through the M1/M2 checks from the test registry: from a fresh chat with the agent, add one new node + one new edge to a graph. Capture a transcript and append it to the HANDOFF block. Repeat for both environments.
- [ ] No new Python code unless absolutely necessary. The agent is configuration + system prompt; the skills already do all the work.

## Not in scope

- Do NOT modify the four skills. If a skill has a usability gap, file it as a follow-up; this track does not edit Tracks A–D.
- Do NOT build a custom UI. The "UI" is the Claude conversation.
- Do NOT add hosting / deployment / auth. The agent runs in Claude Code or claude.ai/code — that's the surface.
- Do NOT touch `lib/` or `app.py`.

## Test protocol

This track is mostly configuration + docs; the "tests" are the M1 and M2 manual checks. Record their outcomes (passed/failed + transcript) in the HANDOFF block. If you write any Python helpers, sink pytest to `/tmp/test_results_track-e.txt` and confirm FAIL=0.

## Handoff protocol

```
HANDOFF (Track E):
- Agent definition path: <absolute>
- Setup docs path: docs/family-setup.md
- Cross-environment parity: verified on <claude.ai/code | local CC | both>
- M1 transcript excerpt: <2-4 lines showing successful node + edge add via agent>
- M2 transcript excerpt: <same, on the other environment>
- Spotify MCP availability check: <how the agent detects and reports>
- /tmp/test_results_track-e.txt (if applicable): FAIL=<count>
- Integration gotchas for Alec demo: <e.g., "MCP setup is the gating step on the cloud surface — verify before family install">
- Deviations: <none / list>
```

## Close-out

```
git -C /private/tmp/mg-wt-E add .
git -C /private/tmp/mg-wt-E commit -m "feat(agents): music-graphs-builder family agent + setup docs"
```
Report SHA + HANDOFF to PM.
