# music-graphs Phase 2 — Project Spec

**Sprint:** `sprint_05172026-phase2`
**Builds on:** `v0.1-phase1-demo` (commit `92a4955`)
**Demo date:** 2026-06-07 (3 weeks from kickoff)
**Status:** LOCKED 2026-05-17 — open questions resolved (see bottom).

---

## Goal

Turn music-graphs from a single-author Flask app into a **collaborative graph-building tool** that Alec, Clare, and Jeremiah can use to grow the three Phase 1 graphs (and eventually new ones) without hand-editing YAML. Dogfood the new tooling by expanding all three existing graphs to the criteria Alec provided in the kickoff conversation.

## Non-goals

- Rewriting any Phase 1 architecture. Card schema, module APIs, route shapes, slug derivation are all **locked**.
- Authentication, multi-user write conflicts, deployment beyond local Flask.
- Making the family agent able to *render* graphs (browsing the app stays a local-Flask thing for now).
- New graph topics outside the three existing ones (band-x, bowie-covers, pittsburgh-jazz).

---

## Audience

| User | Skill level | Environment |
|---|---|---|
| Alec | Builds the tooling | Claude Code, local dev |
| Clare (sister) | Some Claude experience | TBD — cloud (claude.ai) preferred, Claude Code acceptable |
| Jeremiah (brother) | Some Claude experience | TBD — cloud preferred, Claude Code acceptable |

The family agent must be usable by Clare and Jeremiah with **minimal setup friction**. Cloud-based is the stretch target; Claude Code with a clone of the repo is the floor.

---

## Deliverables

### A. Reusable skills (under `.claude/skills/` in the repo)

Each is an Anthropic-style skill: a `SKILL.md` with frontmatter (name, description, triggers), plus optional helper scripts/templates. Skills are repo-local so anyone who clones the repo gets them via Claude Code skill discovery.

1. **`retrieve-spotify-song`** — Given an artist/album/track query, call the Spotify MCP search tool, surface candidate matches, and return a canonical `open.spotify.com` URL. Foundation skill — every other skill that touches Spotify links uses this. Must fail loudly (no training-data guesses) if the MCP is unavailable.
2. **`add-node`** — Given a node name, type (person/band/album/track/place/work/other), and target graph slug, generate a card file at `graphs/<slug>/cards/<type>-<filename>.md` with valid frontmatter (slug, name, type, optional spotify_url via the song skill, optional wikilinks). Runs `tools/lint_graphs.py` on the result and refuses to write if lint fails.
3. **`add-edge`** — Given two existing slugs in the same graph (or one existing + one being created) and an optional relationship label, add a wikilink in the appropriate card body. Handles both directions if symmetric (e.g., "member of" / "has member"). Detects and warns on dangling wikilinks.
4. **`expand-graph`** — Given a graph slug + expansion criterion ("find more Bowie covers", "find Pittsburgh-jazz albums for each artist"), the skill searches (web + Spotify MCP) for candidate additions, presents them to the user for approval, and runs `add-node` + `add-edge` on accepted candidates. This is the bowie-covers test case.

**Skill contract (locked):**
- All skills work on the repo from CWD; no global state.
- All Spotify lookups go through `retrieve-spotify-song`. No skill embeds Spotify search logic directly.
- All node writes go through `add-node`. No skill writes card files directly.
- All skills run `tools/lint_graphs.py <graph>` before reporting success.
- Skills do not invoke `EnterWorktree`. They edit on the current branch.

### B. Family-friendly graph-building agent

A specialized Claude agent (subagent definition under `.claude/agents/` or equivalent) that wraps the four skills above with a conversational UX. Tuned for Clare and Jeremiah.

**Behavior requirements:**
- Greets the user, asks which graph they want to work on, shows the current node count + a few example existing nodes for context.
- Never asks the user to write YAML or markdown directly. Always wraps file-edit operations behind questions like "Should I add a card for Dave Alvin as a person, linked to Ashgrove (his solo album)?"
- Suggests wikilinks to existing nodes whenever a new node mentions an existing entity.
- Verifies Spotify URLs via MCP at every step; never accepts a URL the user pastes without verifying it resolves.
- On error or ambiguity, defers to the user with concrete choices, not jargon.

**Surface:** Open question #1 below — claude.ai vs Claude Code vs both.

### C. Graph expansion (dogfooded through the new skills)

The graph expansions below are **mandatory deliverables**. They are also the acceptance test for the skills: if the skills aren't ergonomic enough to make these expansions feel easy, the skills aren't done.

**C1. band-x — at least one solo/side-project album per current member**

Add one album card (type: album) per person, with:
- `spotify_url` verified via MCP
- A wikilink edge between the person card and the new album card
- Brief body paragraph (Wikipedia-sourced) describing the album

| Person | Album | Spotify |
|---|---|---|
| Exene Cervenka | TBD (skill picks; family-favorite preferred if known) | verify via MCP |
| John Doe | TBD (skill picks; family-favorite preferred if known) | verify via MCP |
| Dave Alvin | **Ashgrove** | `https://open.spotify.com/album/2At5ShihdUNDdc33Ztp7RX` |
| DJ Bonebrake | (provided) | `https://open.spotify.com/album/5DooqGxu4t3H80JkEaIxIw` |
| Billy Zoom | (provided) | `https://open.spotify.com/album/32SOzQ2vEFAlWjKLDotWNP` |

Also fold in the Phase 1 fixup: rename `person-troy-gilkyson.md` → `person-tony-gilkyson.md` and update all wikilinks. (Tony is correct — real X guitarist 1986–1995.)

**C2. bowie-covers — general expansion, used as the `expand-graph` skill test case**

Goal: a few more hits. The skill should:
- Search for additional notable covers of Bowie songs (or Bowie covers of others' songs — match the existing graph's scope by reading the README/cards).
- Surface 5–10 candidates with Wikipedia/Spotify evidence.
- Let Alec approve / reject each.
- Add approved candidates as full cards (album + track type as appropriate) with verified Spotify URLs.

Also fold in the Phase 1 fixup: manual Spotify lookup for Nirvana's *MTV Unplugged in New York* (`graphs/bowie-covers/cards/album-unplugged-in-new-york.md` currently has no `spotify_url`).

**C3. pittsburgh-jazz — at least one album per artist (lead or sideman)**

For every current person card in the graph, add one album they appear on. Specific albums Alec provided:

| Album | Linked artists | Spotify | Notes |
|---|---|---|---|
| Gene Harris Trio Plus One | Stanley Turrentine, Ray Brown | `https://open.spotify.com/album/2AglF11Jys2hkEy44XBlBR` | |
| Sean Jones (album TBD by skill) | Sean Jones | `https://open.spotify.com/album/3ucQJ8hwxcOFrFvdL3YN9j` | **Note on Sean Jones card:** Alec studied with him at Duquesne University in Pittsburgh. |
| Maureen Budway (album TBD by skill) | Maureen Budway, Sean Jones (on "Sweet Lover No More") | `https://open.spotify.com/album/2PoDg7kkMyCOASqSIAReuV` | **Note on Maureen Budway card:** Alec accompanied her voice lessons when she worked at Duquesne. The album was recorded shortly before her death — the Stephen Foster track "Hard Times Come Again No More" is especially poignant in that context. **Edge:** Sean Jones plays on the track "Sweet Lover No More" — add a wikilink between Sean Jones's card and this album, with a body sentence on the Maureen Budway card noting his appearance on that track. |

For all other person cards in pittsburgh-jazz (those without an album yet), the `add-node` / `expand-graph` skill should propose an album they appear on (lead or sideman); Alec approves.

### D. Phase 1 polish (deferred items)

**D1.** M12 — cover images on home page. All three graph READMEs currently have `cover_image: null`. Per the Phase 1 image policy: hotlink Wikipedia URLs in frontmatter, download key images to `graphs/<slug>/images/`. Pick one representative image per graph.

**D2.** Already covered above as fixups inside C1 (Tony Gilkyson rename) and C2 (Nirvana Spotify URL).

---

## Architectural decisions (locked)

These cannot be re-litigated by sessions:

1. **Skills live in the repo** at `.claude/skills/<skill-name>/SKILL.md` (so cloning gets them automatically). They follow Anthropic skill format: frontmatter + body with triggers and instructions.
2. **Spotify MCP is the only Spotify source.** No training-data IDs. If the MCP can't surface a track, the skill says so and asks the user.
3. **Skills do not use `EnterWorktree`.** They mutate the working tree on the current branch. Worktree discipline applies only to SWE tracks building the skills.
4. **All graph mutations go through `add-node` / `add-edge`.** No skill or agent writes a card file by hand. This guarantees lint-clean output.
5. **The family agent is a wrapper, not a re-implementation.** It calls the four skills above. If the agent needs new behavior, that behavior gets added to a skill, not to the agent itself.
6. **`tools/lint_graphs.py` is the canonical pre-commit check.** Every skill runs it before reporting success.
7. **Existing Phase 1 seams are preserved:** card slug = filename-after-first-hyphen; `app.py` attaches `spotify_embed_url` at request time; `parse_card()` returns deduped wikilinks.

---

## Definition of done

Sprint is demo-ready when **all** of the below are green:

**Automated:**
- All 4 skills exist with `SKILL.md` and pass a smoke test (round-trip: add a fake node + edge to a scratch graph, lint passes, then revert).
- `tools/lint_graphs.py` reports 0 errors across all 3 graphs.
- pytest still green (Phase 1's 51 tests + any new ones for skill helpers).
- All graph expansions in section C are committed (band-x: 5 new albums + Tony rename; bowie-covers: 5+ new covers + Nirvana URL fixed; pittsburgh-jazz: ≥1 album per artist including the 3 specific ones with notes).
- All Spotify URLs in newly added cards verified via MCP.
- Home page cover images appear (M12).

**Manual (Alec signs off):**
- Family-agent end-to-end: a fresh session with the agent can add at least one node + one edge to one of the graphs without the user ever seeing YAML or being asked to write markdown.
- Cover images render on `/` for all 3 graphs.
- Each of the 3 specific albums in C3 has the contextual notes Alec specified.
- Sean-Jones-plays-on-Sweet-Lover-No-More edge is in the graph and clickable.

---

## Track structure (proposed — confirm at sign-off)

Wave 1 (foundation, parallel):
- **A — `retrieve-spotify-song` skill**
- **B — `add-node` skill** (depends on A signature only, not implementation; can develop in parallel against a mock)

Wave 2 (build on Wave 1):
- **C — `add-edge` skill** (depends on B)
- **D — `expand-graph` skill** (depends on A, B, C)

Wave 3 (agent + dogfood, parallel):
- **E — Family-friendly agent definition** (depends on A–D)
- **F — band-x expansion** (depends on A, B, C; dogfoods them)
- **G — pittsburgh-jazz expansion** (depends on A, B, C; dogfoods them)

Wave 4:
- **H — bowie-covers expansion** (depends on D specifically; this is the `expand-graph` test case)
- **I — M12 cover images** (independent, can slot anywhere; cheap)

Pre-sprint fixups (PM does, before Wave 1):
- Tony Gilkyson rename in band-x (mechanical; not worth a track)
- Nirvana MTV Unplugged Spotify URL (manual MCP lookup; not worth a track)

---

## Out of scope

- New graph topics. Stick to band-x, bowie-covers, pittsburgh-jazz.
- Hosting the Flask app remotely. Family runs it locally if they want to browse; the agent does the building.
- Replacing or extending `lib/cards.py`, `lib/graph.py`, `lib/spotify.py`, `app.py`. If a skill needs a helper, it gets a private helper inside the skill folder.
- In-browser editing.
- Authentication.
- Anything not on the deliverables list above.

---

## Resolved (formerly open questions)

1. **Family-agent execution environment.** Target **(c) Claude Code on web (claude.ai/code) with GitHub integration**; fallback **(a) local Claude Code with repo clone**. Track E must produce setup docs covering both surfaces. The agent and skills must work identically in both — no surface-specific branches.

2. **Demo date.** **2026-06-07 (3 weeks).** Sufficient runway for full MVP including D (`expand-graph`). `expand-graph` is in MVP, not stretch.

3. **Spotify URL granularity.** **Album-only by default.** Add a track card only when there's a narrative reason — e.g., Maureen Budway's "Sweet Lover No More" (cross-artist appearance) or a Stephen Foster cover with biographical weight. Skill `add-node` accepts `type=track` but should not propose tracks unprompted.

4. **Exene & John Doe albums.** Skill proposes top Wikipedia candidate; Alec approves at expansion time. No pre-pick by PM.

5. **`expand-graph` candidate ceiling.** **5–10 per run.** After surfacing, the skill pauses for user approval before any writes.

---

## Risks

- **Spotify MCP availability in non-Alec environments.** If Clare/Jeremiah's Claude Code installs don't have the Spotify MCP configured, the family agent degrades to "ask Alec to verify URLs." Mitigation: detect MCP absence early and tell the user.
- **Skill ergonomics.** If `add-node` requires too many arguments, the family agent becomes a YAML-by-proxy. The dogfood tracks (F, G, H) are the real test — if Alec writes prompts in the form "here's the exact frontmatter, write the file," the skills failed even if they technically work.
- **`expand-graph` rabbit holes.** Web search for "more Bowie covers" can balloon. The candidate ceiling (open question 5) is the brake.
