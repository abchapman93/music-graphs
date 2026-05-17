# Family setup — music-graphs builder

A short guide for Clare and Jeremiah (or anyone else) to start adding to the music graphs. Pick **Option C (cloud)** if you can; it's the smoother path.

---

## What this is

There are three graphs in this repo:

- **Band X** — Los Angeles punk band X and the people/albums in their orbit.
- **Bowie Covers** — cross-genre artists who've covered David Bowie songs (and a few Bowie covers of others).
- **Pittsburgh Jazz** — mid-century jazz musicians from Pittsburgh.

You'll be talking to a Claude agent called **`music-graphs-builder`**. It knows the graphs, it knows how to add people, albums, tracks, and connections to them, and it never asks you to write code or YAML. You just have a conversation: *"Add Dave Alvin's album Ashgrove to Band X, linked to him."*

The agent handles everything — finding the Spotify link, writing the card, connecting it to the right existing nodes, and double-checking that everything is consistent.

---

## Option C — cloud (recommended)

1. **Open the repo on claude.ai/code.**
   - Go to <https://claude.ai/code>.
   - Connect this GitHub repo (`music-graphs`). Alec can share access if you don't have it already.
   - Open the repo in a new session.
2. **Start a conversation with the `music-graphs-builder` agent.**
   - In the new session, ask: *"Use the music-graphs-builder agent."*
   - The agent should greet you and list the three graphs with current node counts and example nodes.
3. **Set up the Spotify connection** (one-time, per account — see "Spotify MCP" below).
4. You're ready. Skip to "Your first card."

---

## Option A — local (fallback)

If the cloud path doesn't work for any reason:

1. **Install Claude Code.**
   - macOS / Linux: <https://docs.claude.com/claude-code> — follow the install instructions.
2. **Clone the repo:**
   ```bash
   git clone <repo-url> music-graphs
   cd music-graphs
   ```
3. **Set up the Python environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Run Claude Code in the repo:**
   ```bash
   claude
   ```
5. **Ask for the agent:** *"Use the music-graphs-builder agent."*
6. **Set up the Spotify connection** (one-time, per machine — see below).

The agent behaves identically in both environments. The only thing that differs is how the Spotify MCP is configured.

---

## Spotify MCP (one-time setup)

The agent needs access to Spotify search to find verified links for albums and tracks. This goes through a Claude MCP server.

- **On claude.ai/code (cloud):** check your account's connected MCP servers and make sure Spotify is connected. If it isn't, ask Alec — the setup is account-level and one-time.
- **On Claude Code (local):** the Spotify MCP is configured in your Claude Code settings. The official setup doc lives in the Claude Code docs under "MCP servers"; the short version is: install the Spotify MCP server, give it your Spotify credentials, and it'll show up as an available tool the next time you start Claude Code.

**What if it's not set up?** The agent will tell you at the start of the session:

> *Heads up: the Spotify MCP isn't connected in this session — I can still add cards, but I won't be able to attach verified Spotify links.*

You can keep working — the cards just won't have Spotify embeds until the MCP is wired up and you (or Alec) come back to fill them in. The agent will **never** make up a Spotify link from memory.

---

## Your first card — a three-step walkthrough

Once the agent has greeted you:

### 1. Pick a graph and name what you want to add

> **You:** Let's add to Band X. I want to add Dave Alvin's album *Ashgrove*.

The agent will mirror back what it heard:

> **Agent:** Got it — you want to add **Ashgrove** (Dave Alvin's 2004 solo album) to **Band X**. He already has a card in the graph, so I'll just create the album and connect it to him. Sound right?

### 2. Confirm the Spotify link

> **You:** Yes.

The agent searches Spotify, shows you the candidates (numbered), and asks you to pick:

> **Agent:** I found these on Spotify — which one is the right *Ashgrove*?
>
> 1. *Ashgrove* — Dave Alvin, 2004 (album)
> 2. *Ashgrove (Live)* — Dave Alvin, 2014 (album)
>
> Pick a number, or say "none" if neither is right.

### 3. Approve the card and you're done

> **You:** 1.

The agent writes the card, connects it to Dave Alvin, runs a quality check, and confirms:

> **Agent:** Done — added **Ashgrove** to Band X, linked to Dave Alvin. Want to add another?

That's the whole loop. You never see a file path, never type any YAML, never touch a markdown file. The agent does all of that for you behind the scenes.

---

## What if something goes wrong?

The agent translates errors into plain English. The most common ones:

- **"The Spotify connection isn't set up in this session"** — the MCP isn't wired up. See "Spotify MCP" above. You can still add cards without Spotify links.
- **"Something went wrong saving that card"** — the agent's quality check rejected the write. The card has already been cleaned up (nothing is broken). The agent will tell you why and offer to retry.
- **"Looks like X and Y are already linked"** — you tried to add a connection that's already there. Just pick something else.
- **"I'd need to create [target] first before linking to it"** — you tried to link to something that doesn't exist yet. Say yes, and the agent will create it.

If anything still feels broken or confusing, text Alec. The agent's job is to keep the technical mess hidden from you; if any of it leaks, that's a bug.

---

## Tips

- **Specific is better than fuzzy.** "Add Dave Alvin's album Ashgrove" works better than "add a Dave Alvin record" — but the agent will ask if it's unsure.
- **Bigger jobs:** ask the agent to "find more X for graph Y" and it'll surface 5 suggestions at a time for you to approve. Good for filling out a graph quickly.
- **You can pause anytime.** The agent saves each card as soon as you approve it, so you can stop whenever and pick up later.
- **Look at what's already there.** Browsing `graphs/band-x/cards/` (or the others) in the repo gives you a sense of the kinds of things that fit. Or just ask: *"What's in Band X right now?"*

Have fun.
