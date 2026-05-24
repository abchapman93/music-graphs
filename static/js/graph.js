// graph.js — vis-network rendering + side-panel for the /graph/<slug> view.
// Expects window.GRAPH_SLUG to be set by the server-rendered template.

(function () {
  "use strict";

  const SLUG = window.GRAPH_SLUG;
  // Static-build mode: when MG_STATIC is set, API endpoints live as .json
  // files under a build-time base path (e.g., "/music-graphs"). Write-only
  // endpoints (PUT/POST) don't exist, so edit + new-note UIs are hidden.
  const MG_STATIC = !!window.MG_STATIC;
  const MG_BASE = (window.MG_BASE || "").replace(/\/+$/, "");
  const J = MG_STATIC ? ".json" : "";
  function api(path) { return MG_BASE + path + J; }
  if (MG_STATIC) document.body.classList.add("mg-static");
  const graphMount = document.getElementById("graph");
  const panel = document.getElementById("card-panel-content");
  const directoryPanel = document.getElementById("directory-panel-content");
  const cardPanelAside = document.getElementById("card-panel");
  const directoryPanelAside = document.getElementById("directory-panel");
  const searchInput = document.getElementById("search-input");
  const searchResults = document.getElementById("search-results");

  // Type → background color (Neon Atlas palette, parallel to CSS --type-* tokens).
  const TYPE_COLOR = {
    person:   "#5dd4ff",
    group:    "#ff5fb8",
    album:    "#9bff5f",
    track:    "#ffd34d",
    song:     "#c590ff",
    location: "#ff8a3d",
    genre:    "#b39dff",
    note:     "#ffe066",
    memory:   "#ff5b6e",
  };

  // ── Mini-card SVG node renderer ────────────────────────────────────────
  // Each node is drawn as a tiny rounded rectangle "card" with a type-colored
  // cover tile on the left and name + type label on the right. The SVG is
  // returned as a data URL so vis-network can use it via shape: "image".
  // Cache keyed by id+state so we don't regenerate on every redraw.
  const nodeImageCache = new Map();

  function escapeXml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function truncate(s, n) {
    s = String(s == null ? "" : s);
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  function nodeImage(node, state) {
    const id = node.id;
    const cacheKey = `${id}|${state.selected ? 1 : 0}|${state.hovered ? 1 : 0}|${state.pinned ? 1 : 0}`;
    const cached = nodeImageCache.get(cacheKey);
    if (cached) return cached;

    const type = node.group || (id.split(":")[0] || "person");
    const name = node.label || id;
    const pinned = !!state.pinned;
    const w = pinned ? 150 : 110;
    const h = pinned ? 50 : 36;
    const color = TYPE_COLOR[type] || "#7c5cff";
    let outline, outlineW;
    if (state.selected) {
      outline = color; outlineW = 3;
    } else if (state.hovered) {
      outline = "rgba(160,170,220,0.55)"; outlineW = 2;
    } else {
      outline = "rgba(120,130,180,0.35)"; outlineW = 1;
    }
    const coverSize = h - 6;
    const labelX = coverSize + 9;
    const nameSize = pinned ? 13 : 10;
    const typeSize = pinned ? 9 : 8;
    const nameY = pinned ? 22 : h * 0.46;
    const typeY = pinned ? 36 : h * 0.78;
    const maxChars = pinned ? 18 : 14;
    const safeName = escapeXml(truncate(name, maxChars));
    const safeType = escapeXml(type.toUpperCase());

    const svg =
      `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">` +
      `<rect x="0.5" y="0.5" width="${w - 1}" height="${h - 1}" rx="8" ry="8" ` +
        `fill="#0f1124" stroke="${outline}" stroke-width="${outlineW}"/>` +
      `<rect x="3" y="3" width="${coverSize}" height="${coverSize}" rx="5" ry="5" fill="${color}"/>` +
      `<text x="${labelX}" y="${nameY}" fill="#f0f1ff" ` +
        `font-family="Inter, Helvetica Neue, sans-serif" font-size="${nameSize}" font-weight="600">${safeName}</text>` +
      `<text x="${labelX}" y="${typeY}" fill="rgba(220,225,255,0.62)" ` +
        `font-family="JetBrains Mono, monospace" font-size="${typeSize}" letter-spacing="0.6">${safeType}</text>` +
      `</svg>`;

    const dataUrl = "data:image/svg+xml;utf8," + encodeURIComponent(svg);
    nodeImageCache.set(cacheKey, dataUrl);
    return dataUrl;
  }

  // Track which node is the "subject" (largest mini-card) and per-node state.
  let pinnedNodeId = null;
  const hoveredById = new Set();
  const selectedById = new Set();
  // Cached node sizes so we can compute outgoing edge endpoints on the rect.
  const nodeSize = new Map(); // id → { w, h }

  function applyNodeImage(id) {
    if (!network) return;
    const data = network.body.data.nodes.get(id);
    if (!data) return;
    const state = {
      selected: selectedById.has(id),
      hovered: hoveredById.has(id),
      pinned: id === pinnedNodeId,
    };
    const img = nodeImage(data, state);
    const { w, h } = imageDims(state.pinned);
    nodeSize.set(id, { w, h });
    network.body.data.nodes.update({ id, image: img, shape: "image", size: Math.max(w, h) / 2 });
  }

  function imageDims(pinned) {
    return pinned ? { w: 150, h: 50 } : { w: 110, h: 36 };
  }

  // ── Focus / hover dim ──────────────────────────────────────────────────
  // Two pieces of state, with hover taking precedence:
  //   focusedNodeId: persists across mouse-outs; set by clicking a node or
  //     selecting one via search/directory. Cleared by clicking empty canvas.
  //   hoveredFocusId: live mouse-hover; reverts to the focused node on blur.
  // The "effective focus" used to dim non-neighbors is hovered || focused.
  let focusedFocusId = null;
  let hoveredFocusId = null;
  const adjacency = new Map();
  function buildAdjacency(edges) {
    adjacency.clear();
    for (const e of edges) {
      if (!adjacency.has(e.from)) adjacency.set(e.from, new Set());
      if (!adjacency.has(e.to))   adjacency.set(e.to,   new Set());
      adjacency.get(e.from).add(e.to);
      adjacency.get(e.to).add(e.from);
    }
  }
  function effectiveFocus() {
    return hoveredFocusId != null ? hoveredFocusId : focusedFocusId;
  }
  function applyFocusDim() {
    if (!network) return;
    const id = effectiveFocus();
    const updates = [];
    if (id == null) {
      network.body.data.nodes.forEach(n => updates.push({ id: n.id, opacity: 1 }));
    } else {
      const neighbors = adjacency.get(id) || new Set();
      network.body.data.nodes.forEach(n => {
        const keep = n.id === id || neighbors.has(n.id);
        updates.push({ id: n.id, opacity: keep ? 1 : 0.32 });
      });
    }
    network.body.data.nodes.update(updates);
    // Edge overlay reads the same effective focus from hoveredNodeForEdges.
    hoveredNodeForEdges = id;
    scheduleEdgeRedraw();
  }

  function refreshAllNodeImages() {
    if (!network) return;
    const ids = network.body.data.nodes.getIds();
    ids.forEach(applyNodeImage);
  }

  // ── Edge overlay (gradient + glow) ─────────────────────────────────────
  // vis-network's edge rendering doesn't support gradient strokes; we draw
  // them ourselves in an absolutely-positioned SVG layer over the canvas.
  // Redrawn on every vis-network "afterDrawing" tick using getPositions +
  // canvasToDOM for screen-space coords.
  const SVG_NS = "http://www.w3.org/2000/svg";
  let edgeOverlay = null;        // <svg> element
  let edgeDefs = null;           // <defs> child for linearGradients
  let edgeGlowLayer = null;      // <g> (glow strokes — blurred by CSS filter)
  let edgeMainLayer = null;      // <g> (sharp strokes on top)
  const edgeNeighborMap = new Map(); // nodeId → Set(edgeIndex)
  let edgeListCached = [];
  let hoveredNodeForEdges = null;
  // Persistent SVG element refs — built once per edge, mutated per frame so
  // we never reparse innerHTML in the hot path.
  let edgeEls = []; // [{ grad, glow, main }, …] index-aligned with edgeListCached
  let edgeRedrawPending = false;

  function ensureEdgeOverlay() {
    if (edgeOverlay) return edgeOverlay;
    const wrap = graphMount;
    if (!wrap) return null;
    edgeOverlay = document.createElementNS(SVG_NS, "svg");
    edgeOverlay.setAttribute("class", "edge-overlay");
    Object.assign(edgeOverlay.style, {
      position: "absolute",
      top: "0", left: "0",
      width: "100%", height: "100%",
      pointerEvents: "none",
      zIndex: "1",
    });
    const cs = window.getComputedStyle(wrap);
    if (cs.position === "static") wrap.style.position = "relative";
    edgeDefs = document.createElementNS(SVG_NS, "defs");
    edgeGlowLayer = document.createElementNS(SVG_NS, "g");
    edgeMainLayer = document.createElementNS(SVG_NS, "g");
    // CSS blur is GPU-accelerated and applied once to the whole layer,
    // rather than a per-path SVG <filter> reapplied to each of 384 strokes.
    edgeGlowLayer.style.filter = "blur(4px)";
    edgeOverlay.appendChild(edgeDefs);
    edgeOverlay.appendChild(edgeGlowLayer);
    edgeOverlay.appendChild(edgeMainLayer);
    wrap.appendChild(edgeOverlay);
    return edgeOverlay;
  }

  // Build persistent SVG elements for each edge once. Later frames just
  // mutate attributes (no innerHTML, no reparsing, no DOM churn).
  function rebuildEdgeDom() {
    if (!edgeOverlay) return;
    while (edgeDefs.firstChild) edgeDefs.removeChild(edgeDefs.firstChild);
    while (edgeGlowLayer.firstChild) edgeGlowLayer.removeChild(edgeGlowLayer.firstChild);
    while (edgeMainLayer.firstChild) edgeMainLayer.removeChild(edgeMainLayer.firstChild);
    edgeEls = new Array(edgeListCached.length);
    for (let i = 0; i < edgeListCached.length; i++) {
      const grad = document.createElementNS(SVG_NS, "linearGradient");
      grad.setAttribute("id", "eo-g-" + i);
      grad.setAttribute("gradientUnits", "userSpaceOnUse");
      const s0 = document.createElementNS(SVG_NS, "stop");
      s0.setAttribute("offset", "0%");
      const s1 = document.createElementNS(SVG_NS, "stop");
      s1.setAttribute("offset", "100%");
      grad.appendChild(s0); grad.appendChild(s1);
      edgeDefs.appendChild(grad);

      const glow = document.createElementNS(SVG_NS, "path");
      glow.setAttribute("fill", "none");
      glow.setAttribute("stroke", "url(#eo-g-" + i + ")");
      glow.setAttribute("stroke-width", "6");
      glow.setAttribute("stroke-linecap", "round");
      edgeGlowLayer.appendChild(glow);

      const main = document.createElementNS(SVG_NS, "path");
      main.setAttribute("fill", "none");
      main.setAttribute("stroke", "url(#eo-g-" + i + ")");
      main.setAttribute("stroke-linecap", "round");
      edgeMainLayer.appendChild(main);

      edgeEls[i] = { grad, s0, s1, glow, main };
    }
  }

  // Compute the intersection of the segment center→external with the rect of
  // half-width hw and half-height hh centered at (0,0). Returns the offset
  // from the rect center to the intersection point.
  function rectEdgeOffset(dx, dy, hw, hh) {
    if (dx === 0 && dy === 0) return { x: 0, y: 0 };
    const adx = Math.abs(dx), ady = Math.abs(dy);
    const sx = adx === 0 ? Infinity : hw / adx;
    const sy = ady === 0 ? Infinity : hh / ady;
    const s = Math.min(sx, sy);
    return { x: dx * s, y: dy * s };
  }

  function typeOfId(id) {
    const n = network && network.body.data.nodes.get(id);
    return (n && n.group) || (id.split(":")[0] || "person");
  }

  function buildEdgeIndex(edges) {
    edgeListCached = edges;
    edgeNeighborMap.clear();
    edges.forEach((e, i) => {
      let s = edgeNeighborMap.get(e.from);
      if (!s) { s = new Set(); edgeNeighborMap.set(e.from, s); }
      s.add(i);
      s = edgeNeighborMap.get(e.to);
      if (!s) { s = new Set(); edgeNeighborMap.set(e.to, s); }
      s.add(i);
    });
    rebuildEdgeDom();
  }

  // Coalesce many afterDrawing events per animation frame into a single paint.
  function scheduleEdgeRedraw() {
    if (edgeRedrawPending) return;
    edgeRedrawPending = true;
    requestAnimationFrame(() => {
      edgeRedrawPending = false;
      redrawEdgeOverlay();
    });
  }

  // Per-edge cached stroke colors (only recompute when edge list changes).
  let edgeColorsCached = []; // [{ ca, cb }]
  function recomputeEdgeColors() {
    edgeColorsCached = edgeListCached.map(e => ({
      ca: TYPE_COLOR[typeOfId(e.from)] || "#7c5cff",
      cb: TYPE_COLOR[typeOfId(e.to)]   || "#7c5cff",
    }));
  }

  function redrawEdgeOverlay() {
    if (!network || !edgeOverlay) return;
    const n = edgeListCached.length;
    if (!n) return;
    if (edgeColorsCached.length !== n) recomputeEdgeColors();

    const rect = graphMount.getBoundingClientRect();
    edgeOverlay.setAttribute("viewBox", "0 0 " + rect.width + " " + rect.height);

    const ids = network.body.data.nodes.getIds();
    const canvasPos = network.getPositions(ids);
    const scale = network.getScale();

    // Project all nodes to DOM coords up front (avoid the per-edge map lookup).
    const domPos = Object.create(null);
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      const p = canvasPos[id];
      if (p) domPos[id] = network.canvasToDOM(p);
    }

    const hi = hoveredNodeForEdges;
    const hiEdges = hi != null ? edgeNeighborMap.get(hi) : null;

    for (let i = 0; i < n; i++) {
      const e = edgeListCached[i];
      const els = edgeEls[i];
      if (!els) continue;
      const a = domPos[e.from], b = domPos[e.to];
      if (!a || !b) {
        els.glow.style.display = "none";
        els.main.style.display = "none";
        continue;
      }
      const sizeA = nodeSize.get(e.from) || { w: 110, h: 36 };
      const sizeB = nodeSize.get(e.to)   || { w: 110, h: 36 };
      const dx = b.x - a.x, dy = b.y - a.y;
      if (dx === 0 && dy === 0) {
        els.glow.style.display = "none";
        els.main.style.display = "none";
        continue;
      }
      els.glow.style.display = "";
      els.main.style.display = "";

      const offA = rectEdgeOffset(dx, dy, (sizeA.w * scale) / 2, (sizeA.h * scale) / 2);
      const offB = rectEdgeOffset(-dx, -dy, (sizeB.w * scale) / 2, (sizeB.h * scale) / 2);
      const x1 = a.x + offA.x, y1 = a.y + offA.y;
      const x2 = b.x + offB.x, y2 = b.y + offB.y;
      const len = Math.hypot(x2 - x1, y2 - y1) || 1;
      const px = -(y2 - y1) / len, py = (x2 - x1) / len;
      const bend = len * 0.12 < 28 ? len * 0.12 : 28;
      const cx = (x1 + x2) / 2 + px * bend;
      const cy = (y1 + y2) / 2 + py * bend;

      const colors = edgeColorsCached[i];
      els.grad.setAttribute("x1", x1);
      els.grad.setAttribute("y1", y1);
      els.grad.setAttribute("x2", x2);
      els.grad.setAttribute("y2", y2);
      els.s0.setAttribute("stop-color", colors.ca);
      els.s1.setAttribute("stop-color", colors.cb);

      let glowOpacity = 0.25, mainOpacity = 0.55, mainWidth = 1.4;
      if (hi != null) {
        if (hiEdges && hiEdges.has(i)) {
          glowOpacity = 0.55; mainOpacity = 1.0; mainWidth = 2.5;
        } else {
          glowOpacity = 0.05; mainOpacity = 0.12; mainWidth = 1.0;
        }
      }

      const d = "M" + x1 + " " + y1 + " Q" + cx + " " + cy + " " + x2 + " " + y2;
      els.glow.setAttribute("d", d);
      els.glow.setAttribute("opacity", glowOpacity);
      els.main.setAttribute("d", d);
      els.main.setAttribute("opacity", mainOpacity);
      els.main.setAttribute("stroke-width", mainWidth);
    }
  }

  // Directory render order (anything else falls to the end alphabetically).
  const DIRECTORY_TYPE_ORDER = [
    "person", "group", "album", "song", "track",
    "location", "genre", "note", "memory",
  ];

  // Cache of /api/cards/<slug> for both search + directory.
  let cardIndex = [];
  let activeDirectorySlug = null;
  let searchActiveIdx = -1;
  let searchCurrentResults = [];

  // Track the currently rendered card so the Edit button can find its body_md
  // and slug without a re-fetch. Reset whenever a new card is rendered.
  let currentCard = null;
  let editing = false;
  let savedNotice = false;

  // Node styling per project_spec.md "Architecture decisions" table.
  // shape + color by card type. Used via vis-network groups config.
  const GROUPS = {
    person:   { shape: "dot",      color: { background: "#3b82f6", border: "#1d4ed8" } },
    group:    { shape: "square",   color: { background: "#3b82f6", border: "#1d4ed8" } },
    album:    { shape: "square",   color: { background: "#22c55e", border: "#15803d" } },
    track:    { shape: "triangle", color: { background: "#16a34a", border: "#14532d" } },
    song:     { shape: "triangle", color: { background: "#86efac", border: "#15803d" } },
    location: { shape: "diamond",  color: { background: "#f59e0b", border: "#b45309" } },
    genre:    { shape: "hexagon",  color: { background: "#a855f7", border: "#6b21a8" } },
    note:     { shape: "star",     color: { background: "#facc15", border: "#a16207" } },
    memory:   { shape: "star",     color: { background: "#ef4444", border: "#991b1b" } },
  };

  const ZOOM_STEP = 1.25;

  let network = null;

  // ── Persistent Spotify player ──────────────────────────────────────────
  // One Spotify iframe lives at the top of the page; per-card UI sends URIs
  // to it via the Spotify IFrame API so music persists across card clicks.
  const playerEl = document.getElementById("persistent-player");
  const playerEmbedMount = document.getElementById("persistent-player-embed");
  const playerTitleEl = document.getElementById("persistent-player-title");
  let spotifyController = null;
  let spotifyControllerPending = []; // queued URIs before controller is ready
  let currentPlayerUri = null;

  function embedUrlToUri(embedUrl) {
    // https://open.spotify.com/embed/<kind>/<id> → spotify:<kind>:<id>
    if (!embedUrl) return null;
    const m = embedUrl.match(/\/embed\/([a-z]+)\/([A-Za-z0-9]+)/);
    if (!m) return null;
    return `spotify:${m[1]}:${m[2]}`;
  }

  function spotifyUrlToUri(url) {
    // https://open.spotify.com/<kind>/<id>[/?...] → spotify:<kind>:<id>
    if (!url) return null;
    const m = String(url).match(/open\.spotify\.com\/(?:embed\/)?([a-z]+)\/([A-Za-z0-9]+)/);
    if (!m) return null;
    return `spotify:${m[1]}:${m[2]}`;
  }

  function playInPersistentPlayer(uri, label) {
    if (!uri) return;
    currentPlayerUri = uri;
    if (playerEl) playerEl.hidden = false;
    if (playerTitleEl) playerTitleEl.textContent = label || "";
    if (spotifyController) {
      try {
        spotifyController.loadUri(uri);
        spotifyController.play();
      } catch (_) {}
    } else {
      spotifyControllerPending.push(uri);
    }
  }

  // Auto-load the graph's canonical playlist (if any) into the persistent
  // player on first init, so navigating to a graph starts music by default.
  // Browser autoplay policies may still require user interaction to actually
  // begin playback — we call play() but the iframe decides whether to honor.
  const canonicalPlaylistUrl = (window.GRAPH_SPOTIFY_PLAYLIST_URL || "").trim();
  const canonicalPlaylistUri = canonicalPlaylistUrl
    ? spotifyUrlToUri(canonicalPlaylistUrl)
    : null;
  if (canonicalPlaylistUri) {
    const label = `${window.GRAPH_NAME || "Graph"} — canonical playlist`;
    playInPersistentPlayer(canonicalPlaylistUri, label);
  }

  window.onSpotifyIframeApiReady = function (IFrameAPI) {
    if (!playerEmbedMount) return;
    const initialUri = canonicalPlaylistUri || "";
    const opts = { width: "100%", height: 80, uri: initialUri };
    IFrameAPI.createController(playerEmbedMount, opts, (controller) => {
      spotifyController = controller;
      // Drain any URIs queued before the controller was ready. The last URI
      // wins (latest user click or the canonical playlist if nothing else).
      if (spotifyControllerPending.length) {
        const last = spotifyControllerPending[spotifyControllerPending.length - 1];
        spotifyControllerPending = [];
        try {
          controller.loadUri(last);
          controller.play();
        } catch (_) {}
      }
    });
  };

  function escapeText(s) {
    if (s == null) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderCard(card) {
    currentCard = card;
    editing = false;
    const TALL = new Set(["album", "playlist", "show"]);
    const isTall = card.spotify_kind && TALL.has(card.spotify_kind);
    const parts = [];
    const canEdit = typeof card.body_md === "string";
    const editDisabled = canEdit ? "" : "disabled";
    const editTitle = canEdit ? "Edit card body" : "frontmatter parse failed — edit manually";
    parts.push(
      `<div class="card-toolbar">` +
      `<button type="button" class="card-edit-btn" data-card-edit ${editDisabled} ` +
      `title="${escapeText(editTitle)}">Edit</button>` +
      `<button type="button" class="card-note-btn" data-card-note ` +
      `title="Add a note linked to this card">+ Note</button>` +
      (savedNotice
        ? `<span class="card-saved-notice" data-saved-notice>uncommitted edit on disk ` +
          `<button type="button" data-saved-dismiss aria-label="Dismiss">×</button></span>`
        : "") +
      `</div>`
    );
    if (card.image) {
      parts.push(`<img class="card-image" src="${escapeText(card.image)}" alt="">`);
    }
    parts.push(`<h1 class="card-name">${escapeText(card.name)}</h1>`);
    parts.push(`<p class="card-type">${escapeText(card.type)}</p>`);
    const fm = card.display_frontmatter || {};
    const keys = Object.keys(fm);
    if (keys.length) {
      parts.push('<dl class="card-fm">');
      for (const k of keys) {
        parts.push(`<dt>${escapeText(k)}</dt><dd>${escapeText(fm[k])}</dd>`);
      }
      parts.push("</dl>");
    }
    // body_html is server-rendered + sanitized at authoring time (trusted local content).
    parts.push(`<div class="card-body">${card.body_html || ""}</div>`);
    if (card.spotify_embed_url) {
      const uri = embedUrlToUri(card.spotify_embed_url);
      const label = `${card.name}${card.type ? " (" + card.type + ")" : ""}`;
      parts.push(
        `<div class="card-spotify">` +
        `<button type="button" class="card-spotify-play" data-card-play ` +
        `data-spotify-uri="${escapeText(uri || "")}" ` +
        `data-spotify-label="${escapeText(label)}" ` +
        `title="Play in persistent player at top of page">` +
        `▶ Play in player` +
        `</button>` +
        `<a class="card-spotify-link" href="${escapeText(card.spotify_embed_url.replace("/embed/", "/"))}" ` +
        `target="_blank" rel="noopener" title="Open on Spotify">Open on Spotify ↗</a>` +
        `</div>`
      );
    }
    panel.innerHTML = parts.join("");
  }

  function loadCard(nodeId) {
    // node id shape: "<type>:<slug>"
    const idx = nodeId.indexOf(":");
    if (idx < 0) return;
    const cardSlug = nodeId.slice(idx + 1);
    // Dismiss saved-notice and exit edit mode when switching cards.
    savedNotice = false;
    editing = false;
    fetch(api(`/api/card/${encodeURIComponent(SLUG)}/${encodeURIComponent(cardSlug)}`))
      .then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(renderCard)
      .catch(e => {
        panel.innerHTML = `<p class="muted">Failed to load card: ${escapeText(e.message)}</p>`;
      });
  }

  function focusNode(id) {
    if (!network) return;
    try {
      network.selectNodes([id]);
      network.focus(id, { scale: 1.2, animation: true });
    } catch (_) {}
  }

  // Used by both search-hit selection and directory clicks. Centers the node
  // and opens the right panel via the existing card-loading path.
  function selectNode(typeAndSlug) {
    // typeAndSlug shape: "<type>:<slug>" — same node id form used by vis-network.
    if (!typeAndSlug) return;
    if (network) {
      try {
        network.selectNodes([typeAndSlug]);
        network.focus(typeAndSlug, { scale: 1.5, animation: true });
      } catch (_) {}
      const prev = Array.from(selectedById);
      selectedById.clear();
      selectedById.add(typeAndSlug);
      prev.forEach(applyNodeImage);
      applyNodeImage(typeAndSlug);
      focusedFocusId = typeAndSlug;
      applyFocusDim();
    }
    loadCard(typeAndSlug);
    // Sync directory active state.
    const idx = typeAndSlug.indexOf(":");
    if (idx >= 0) {
      const cardSlug = typeAndSlug.slice(idx + 1);
      setActiveDirectoryRow(cardSlug);
    }
  }

  // ── Directory panel ────────────────────────────────────────────────────
  function renderDirectory() {
    if (!directoryPanel) return;
    if (!cardIndex.length) {
      directoryPanel.innerHTML = '<p class="muted directory-empty">No cards.</p>';
      return;
    }
    // Group cards by type.
    const groups = new Map();
    for (const c of cardIndex) {
      if (!groups.has(c.type)) groups.set(c.type, []);
      groups.get(c.type).push(c);
    }
    // Order: DIRECTORY_TYPE_ORDER first, then any leftover alphabetically.
    const seen = new Set();
    const orderedTypes = [];
    for (const t of DIRECTORY_TYPE_ORDER) {
      if (groups.has(t)) { orderedTypes.push(t); seen.add(t); }
    }
    for (const t of Array.from(groups.keys()).sort()) {
      if (!seen.has(t)) orderedTypes.push(t);
    }

    const out = [];
    for (const t of orderedTypes) {
      const rows = groups.get(t);
      const color = TYPE_COLOR[t] || "#888";
      out.push('<details class="directory-group" open>');
      out.push(
        `<summary>${escapeText(t)}<span class="directory-count">${rows.length}</span></summary>`
      );
      out.push('<ul class="directory-list">');
      for (const r of rows) {
        out.push(
          `<li class="directory-row" data-card-row data-slug="${escapeText(r.slug)}" ` +
          `data-type="${escapeText(r.type)}" title="${escapeText(r.slug)}">` +
          `<span class="type-dot" style="background:${color}"></span>` +
          `<span class="directory-row-label">${escapeText(r.name)}</span>` +
          "</li>"
        );
      }
      out.push("</ul>");
      out.push("</details>");
    }
    directoryPanel.innerHTML = out.join("");
    if (activeDirectorySlug) setActiveDirectoryRow(activeDirectorySlug);
  }

  function setActiveDirectoryRow(cardSlug) {
    activeDirectorySlug = cardSlug;
    if (!directoryPanel) return;
    const rows = directoryPanel.querySelectorAll(".directory-row");
    rows.forEach(row => {
      if (row.getAttribute("data-slug") === cardSlug) {
        row.classList.add("active");
      } else {
        row.classList.remove("active");
      }
    });
  }

  function wireDirectory() {
    if (!directoryPanel) return;
    directoryPanel.addEventListener("click", function (ev) {
      const row = ev.target.closest("[data-card-row]");
      if (!row) return;
      const slug = row.getAttribute("data-slug");
      const type = row.getAttribute("data-type");
      if (!slug || !type) return;
      selectNode(`${type}:${slug}`);
    });
  }

  // ── Search ─────────────────────────────────────────────────────────────
  function rankSearchHits(query) {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    const exact = [];
    const prefix = [];
    const substr = [];
    for (const c of cardIndex) {
      const name = (c.name || "").toLowerCase();
      const slug = (c.slug || "").toLowerCase();
      if (name === q || slug === q) {
        exact.push(c);
      } else if (name.startsWith(q) || slug.startsWith(q)) {
        prefix.push(c);
      } else if (name.includes(q) || slug.includes(q)) {
        substr.push(c);
      }
    }
    return exact.concat(prefix).concat(substr).slice(0, 12);
  }

  function renderSearchResults(hits) {
    searchCurrentResults = hits;
    searchActiveIdx = hits.length ? 0 : -1;
    if (!hits.length) {
      searchResults.innerHTML = "";
      searchResults.removeAttribute("data-open");
      return;
    }
    const out = [];
    hits.forEach((c, i) => {
      const color = TYPE_COLOR[c.type] || "#888";
      out.push(
        `<div class="search-result-item${i === 0 ? " active" : ""}" ` +
        `data-id="${escapeText(c.type)}:${escapeText(c.slug)}" data-idx="${i}">` +
        `<span class="search-result-dot" style="background:${color}"></span>` +
        `<span class="search-result-label">${escapeText(c.name)}</span>` +
        `<span class="search-result-slug">${escapeText(c.slug)}</span>` +
        `<span class="search-result-type">${escapeText(c.type)}</span>` +
        "</div>"
      );
    });
    searchResults.innerHTML = out.join("");
    searchResults.setAttribute("data-open", "1");
  }

  function updateSearchActiveClass() {
    const items = searchResults.querySelectorAll(".search-result-item");
    items.forEach((el, i) => {
      if (i === searchActiveIdx) el.classList.add("active");
      else el.classList.remove("active");
    });
  }

  function clearSearch() {
    if (!searchInput) return;
    searchInput.value = "";
    searchResults.innerHTML = "";
    searchResults.removeAttribute("data-open");
    searchCurrentResults = [];
    searchActiveIdx = -1;
  }

  function wireSearch() {
    if (!searchInput || !searchResults) return;
    searchInput.addEventListener("input", () => {
      const hits = rankSearchHits(searchInput.value);
      renderSearchResults(hits);
    });
    searchInput.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        clearSearch();
        searchInput.blur();
        return;
      }
      if (!searchCurrentResults.length) return;
      if (ev.key === "ArrowDown") {
        ev.preventDefault();
        searchActiveIdx = Math.min(searchActiveIdx + 1, searchCurrentResults.length - 1);
        updateSearchActiveClass();
      } else if (ev.key === "ArrowUp") {
        ev.preventDefault();
        searchActiveIdx = Math.max(searchActiveIdx - 1, 0);
        updateSearchActiveClass();
      } else if (ev.key === "Enter") {
        ev.preventDefault();
        if (searchActiveIdx < 0) return;
        const pick = searchCurrentResults[searchActiveIdx];
        if (!pick) return;
        selectNode(`${pick.type}:${pick.slug}`);
        clearSearch();
      }
    });
    searchResults.addEventListener("click", (ev) => {
      const item = ev.target.closest(".search-result-item");
      if (!item) return;
      const id = item.getAttribute("data-id");
      if (!id) return;
      selectNode(id);
      clearSearch();
    });
    // Close dropdown when clicking outside.
    document.addEventListener("click", (ev) => {
      if (!searchInput.parentElement.contains(ev.target)) {
        searchResults.removeAttribute("data-open");
      }
    });
    searchInput.addEventListener("focus", () => {
      if (searchCurrentResults.length) searchResults.setAttribute("data-open", "1");
    });
  }

  function loadCardIndex() {
    return fetch(api(`/api/cards/${encodeURIComponent(SLUG)}`))
      .then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(data => {
        cardIndex = Array.isArray(data) ? data : [];
        renderDirectory();
      })
      .catch(e => {
        if (directoryPanel) {
          directoryPanel.innerHTML =
            `<p class="muted directory-empty">Failed to load directory: ${escapeText(e.message)}</p>`;
        }
      });
  }

  function zoomBy(factor) {
    if (!network) return;
    const cur = network.getScale();
    network.moveTo({ scale: cur * factor, animation: { duration: 150 } });
  }

  function fitView() {
    if (!network) return;
    network.fit({ animation: { duration: 200 } });
  }

  // ── Spacing slider ───────────────────────────────────────────────────
  const SPACING_KEY = "mg-spacing";
  const SPACING_DEFAULT = 1.0;
  function loadSpacing() {
    try {
      const v = parseFloat(localStorage.getItem(SPACING_KEY));
      if (Number.isFinite(v) && v >= 0.6 && v <= 2.0) return v;
    } catch (_) {}
    return SPACING_DEFAULT;
  }
  function saveSpacing(v) {
    try { localStorage.setItem(SPACING_KEY, String(v)); } catch (_) {}
  }
  let currentSpacing = loadSpacing();

  // Briefly unfreeze, let the layout settle, then re-sync to the freeze
  // checkbox. Uses a timeout because `stabilizationIterationsDone` is tied to
  // the initial stabilization phase and doesn't reliably fire on later
  // physics runs triggered via setOptions.
  let reheatTimer = null;
  function reheatPhysics() {
    if (!network) return;
    network.setOptions({ physics: { enabled: true } });
    if (reheatTimer) clearTimeout(reheatTimer);
    reheatTimer = setTimeout(() => {
      reheatTimer = null;
      const freeze = document.getElementById("freeze-toggle");
      const shouldFreeze = !!(freeze && freeze.checked);
      if (shouldFreeze && network) network.setOptions({ physics: { enabled: false } });
    }, 1500);
  }

  function applySpacing(spacing, { reheat = true } = {}) {
    if (!network) return;
    network.setOptions({
      physics: {
        forceAtlas2Based: {
          springLength: 120 * spacing,
          gravitationalConstant: -50 * spacing,
        },
      },
    });
    if (reheat) reheatPhysics();
  }

  function wireControls() {
    const zin = document.getElementById("zoom-in");
    const zout = document.getElementById("zoom-out");
    const zfit = document.getElementById("zoom-fit");
    const relayout = document.getElementById("relayout");
    const freeze = document.getElementById("freeze-toggle");
    const spacingInput = document.getElementById("spacing-slider");
    const spacingValue = document.getElementById("spacing-value");
    if (zin) zin.addEventListener("click", () => zoomBy(ZOOM_STEP));
    if (zout) zout.addEventListener("click", () => zoomBy(1 / ZOOM_STEP));
    if (zfit) zfit.addEventListener("click", fitView);
    if (relayout) {
      relayout.addEventListener("click", reheatPhysics);
    }
    if (freeze) {
      freeze.addEventListener("change", () => {
        if (!network) return;
        network.setOptions({ physics: { enabled: !freeze.checked } });
      });
    }
    if (spacingInput) {
      spacingInput.value = String(currentSpacing);
      if (spacingValue) spacingValue.textContent = currentSpacing.toFixed(2) + "×";
      // Live preview during drag (no reheat for every step), reheat on change.
      spacingInput.addEventListener("input", () => {
        currentSpacing = parseFloat(spacingInput.value);
        if (spacingValue) spacingValue.textContent = currentSpacing.toFixed(2) + "×";
      });
      spacingInput.addEventListener("change", () => {
        currentSpacing = parseFloat(spacingInput.value);
        saveSpacing(currentSpacing);
        applySpacing(currentSpacing, { reheat: true });
      });
    }
  }

  // Delegate wikilink clicks inside the panel.
  panel.addEventListener("click", function (ev) {
    const a = ev.target.closest("[data-wikilink]");
    if (!a) return;
    ev.preventDefault();
    const targetId = a.getAttribute("data-wikilink");
    if (!targetId) return;
    focusNode(targetId);
    loadCard(targetId);
    const idx = targetId.indexOf(":");
    if (idx >= 0) setActiveDirectoryRow(targetId.slice(idx + 1));
  });

  // ── Edit mode ──────────────────────────────────────────────────────────
  function enterEditMode() {
    if (!currentCard || editing) return;
    if (typeof currentCard.body_md !== "string") return;
    editing = true;
    const bodyDiv = panel.querySelector(".card-body");
    if (!bodyDiv) return;
    const editor = document.createElement("div");
    editor.className = "card-editor";
    editor.setAttribute("data-card-editor", "");
    editor.innerHTML =
      `<div class="card-editor-error" data-editor-error hidden></div>` +
      `<textarea class="card-editor-textarea" data-editor-ta spellcheck="false"></textarea>` +
      `<div class="card-editor-actions">` +
      `<button type="button" class="card-editor-save" data-editor-save>Save</button>` +
      `<button type="button" class="card-editor-cancel" data-editor-cancel>Cancel</button>` +
      `</div>`;
    bodyDiv.replaceWith(editor);
    const ta = editor.querySelector("[data-editor-ta]");
    ta.value = currentCard.body_md;
    ta.focus();
    // Disable the Edit button while editing.
    const editBtn = panel.querySelector("[data-card-edit]");
    if (editBtn) editBtn.disabled = true;
  }

  function exitEditMode() {
    editing = false;
    if (currentCard) renderCard(currentCard);
  }

  function showSaveError(msg) {
    const errEl = panel.querySelector("[data-editor-error]");
    if (!errEl) return;
    errEl.textContent = msg;
    errEl.hidden = false;
  }

  function saveEdit() {
    if (!currentCard) return;
    const ta = panel.querySelector("[data-editor-ta]");
    if (!ta) return;
    const body = ta.value;
    const saveBtn = panel.querySelector("[data-editor-save]");
    const cancelBtn = panel.querySelector("[data-editor-cancel]");
    if (saveBtn) saveBtn.disabled = true;
    if (cancelBtn) cancelBtn.disabled = true;
    fetch(`/api/cards/${encodeURIComponent(SLUG)}/${encodeURIComponent(currentCard.slug)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body: body }),
    })
      .then(async r => {
        const data = await r.json().catch(() => ({}));
        if (r.ok) {
          savedNotice = true;
          renderCard(data);
          return;
        }
        if (r.status === 404) {
          showSaveError("Card file not found on disk — it may have been deleted.");
        } else if (r.status === 422) {
          const lint = (data.stdout || data.error || "save failed").trim();
          showSaveError("Lint failed; changes reverted:\n" + lint);
        } else {
          showSaveError(`Save failed (HTTP ${r.status}): ${data.error || ""}`);
        }
        if (saveBtn) saveBtn.disabled = false;
        if (cancelBtn) cancelBtn.disabled = false;
      })
      .catch(e => {
        showSaveError("Save failed: " + e.message);
        if (saveBtn) saveBtn.disabled = false;
        if (cancelBtn) cancelBtn.disabled = false;
      });
  }

  // ── New note modal (Track R) ───────────────────────────────────────────
  const noteModal = document.getElementById("note-modal");

  function openNoteModal() {
    if (!noteModal || !currentCard) return;
    const titleEl = noteModal.querySelector("[data-note-title]");
    const bodyEl = noteModal.querySelector("[data-note-body]");
    const errEl = noteModal.querySelector("[data-note-error]");
    const srcEl = noteModal.querySelector("[data-note-source]");
    const radios = noteModal.querySelectorAll('input[name="note-type"]');
    if (titleEl) titleEl.value = "";
    if (bodyEl) bodyEl.value = "";
    if (errEl) { errEl.hidden = true; errEl.textContent = ""; }
    radios.forEach(r => { r.checked = r.value === "note"; });
    if (srcEl) {
      srcEl.textContent =
        `Will be linked from ${currentCard.type}: ${currentCard.name}`;
    }
    noteModal.hidden = false;
    noteModal.setAttribute("aria-hidden", "false");
    setTimeout(() => { if (titleEl) titleEl.focus(); }, 0);
  }

  function closeNoteModal() {
    if (!noteModal) return;
    noteModal.hidden = true;
    noteModal.setAttribute("aria-hidden", "true");
  }

  function showNoteError(msg) {
    if (!noteModal) return;
    const errEl = noteModal.querySelector("[data-note-error]");
    if (!errEl) return;
    errEl.textContent = msg;
    errEl.hidden = false;
  }

  function submitNote() {
    if (!noteModal || !currentCard) return;
    const titleEl = noteModal.querySelector("[data-note-title]");
    const bodyEl = noteModal.querySelector("[data-note-body]");
    const createBtn = noteModal.querySelector("[data-note-create]");
    const cancelBtn = noteModal.querySelector("[data-note-cancel]");
    const typeRadio = noteModal.querySelector('input[name="note-type"]:checked');
    const title = (titleEl && titleEl.value || "").trim();
    const body = (bodyEl && bodyEl.value || "").trim();
    const noteType = typeRadio ? typeRadio.value : "note";
    if (title.length < 3) {
      showNoteError("Title must be at least 3 characters.");
      return;
    }
    if (body.length < 1) {
      showNoteError("Body is required.");
      return;
    }
    if (createBtn) createBtn.disabled = true;
    if (cancelBtn) cancelBtn.disabled = true;

    fetch(`/api/notes/${encodeURIComponent(SLUG)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: noteType,
        title: title,
        body: body,
        source_slug: currentCard.slug,
        source_type: currentCard.type,
      }),
    })
      .then(async r => {
        const data = await r.json().catch(() => ({}));
        if (r.ok) {
          closeNoteModal();
          // Refresh canvas + directory; auto-select the new node.
          const newId = `${data.type}:${data.slug}`;
          Promise.all([refreshGraph(), loadCardIndex()]).then(() => {
            selectNode(newId);
          });
          return;
        }
        if (r.status === 422) {
          const lint = (data.stdout || data.error || "create failed").trim();
          showNoteError("Lint failed; changes reverted:\n" + lint);
        } else {
          showNoteError(`Create failed (HTTP ${r.status}): ${data.error || ""}`);
        }
        if (createBtn) createBtn.disabled = false;
        if (cancelBtn) cancelBtn.disabled = false;
      })
      .catch(e => {
        showNoteError("Create failed: " + e.message);
        if (createBtn) createBtn.disabled = false;
        if (cancelBtn) cancelBtn.disabled = false;
      });
  }

  function refreshGraph() {
    return fetch(MG_BASE + `/api/graph/${encodeURIComponent(SLUG)}` + J)
      .then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(data => {
        if (!network) return;
        const styled = (data.nodes || []).map(n => {
          const state = { selected: false, hovered: false, pinned: n.id === pinnedNodeId };
          const img = nodeImage(n, state);
          const { w, h } = imageDims(state.pinned);
          nodeSize.set(n.id, { w, h });
          return Object.assign({}, n, {
            shape: "image",
            image: img,
            size: Math.max(w, h) / 2,
            font: { color: "rgba(0,0,0,0)", size: 0 },
          });
        });
        const nodes = new vis.DataSet(styled);
        const edges = new vis.DataSet(data.edges || []);
        network.setData({ nodes: nodes, edges: edges });
        buildEdgeIndex(data.edges || []);
        buildAdjacency(data.edges || []);
        scheduleEdgeRedraw();
      })
      .catch(() => {});
  }

  if (noteModal) {
    noteModal.addEventListener("click", ev => {
      if (ev.target.closest("[data-note-cancel]")) {
        ev.preventDefault();
        closeNoteModal();
        return;
      }
      if (ev.target.closest("[data-note-create]")) {
        ev.preventDefault();
        submitNote();
        return;
      }
    });
    document.addEventListener("keydown", ev => {
      if (noteModal.hidden) return;
      if (ev.key === "Escape") {
        ev.preventDefault();
        closeNoteModal();
      }
    });
  }

  panel.addEventListener("click", function (ev) {
    const playBtn = ev.target.closest("[data-card-play]");
    if (playBtn) {
      ev.preventDefault();
      const uri = playBtn.getAttribute("data-spotify-uri");
      const label = playBtn.getAttribute("data-spotify-label") || "";
      playInPersistentPlayer(uri, label);
      return;
    }
    if (ev.target.closest("[data-card-edit]")) {
      ev.preventDefault();
      enterEditMode();
      return;
    }
    if (ev.target.closest("[data-card-note]")) {
      ev.preventDefault();
      openNoteModal();
      return;
    }
    if (ev.target.closest("[data-editor-cancel]")) {
      ev.preventDefault();
      exitEditMode();
      return;
    }
    if (ev.target.closest("[data-editor-save]")) {
      ev.preventDefault();
      saveEdit();
      return;
    }
    if (ev.target.closest("[data-saved-dismiss]")) {
      ev.preventDefault();
      savedNotice = false;
      const el = panel.querySelector("[data-saved-notice]");
      if (el) el.remove();
      return;
    }
  });

  // ── Panel state: resize, collapse, persistence ─────────────────────────
  const PANEL_STATE_KEY = "mg-panel-state";
  const PANEL_MIN = 200;
  const PANEL_MAX = 480;
  const PANEL_DEFAULTS = { leftWidth: 240, rightWidth: 320, leftCollapsed: false, rightCollapsed: false };
  const stage = document.getElementById("graph-stage");

  function loadPanelState() {
    try {
      const raw = localStorage.getItem(PANEL_STATE_KEY);
      if (!raw) return Object.assign({}, PANEL_DEFAULTS);
      const parsed = JSON.parse(raw);
      return Object.assign({}, PANEL_DEFAULTS, parsed);
    } catch (_) {
      return Object.assign({}, PANEL_DEFAULTS);
    }
  }

  function savePanelState(s) {
    try { localStorage.setItem(PANEL_STATE_KEY, JSON.stringify(s)); } catch (_) {}
  }

  function clampWidth(w) {
    if (!Number.isFinite(w)) return PANEL_DEFAULTS.leftWidth;
    return Math.max(PANEL_MIN, Math.min(PANEL_MAX, Math.round(w)));
  }

  const panelState = loadPanelState();
  panelState.leftWidth = clampWidth(panelState.leftWidth);
  panelState.rightWidth = clampWidth(panelState.rightWidth);

  function applyPanelState() {
    if (!stage) return;
    stage.style.setProperty("--left-w", panelState.leftWidth + "px");
    stage.style.setProperty("--right-w", panelState.rightWidth + "px");
    stage.classList.toggle("left-collapsed", !!panelState.leftCollapsed);
    stage.classList.toggle("right-collapsed", !!panelState.rightCollapsed);
  }

  function redrawNetwork() {
    if (!network) return;
    try { network.redraw(); } catch (_) {}
  }

  function toggleCollapse(side) {
    if (side === "left") panelState.leftCollapsed = !panelState.leftCollapsed;
    else if (side === "right") panelState.rightCollapsed = !panelState.rightCollapsed;
    applyPanelState();
    savePanelState(panelState);
    // Wait for grid transition before redrawing vis-network.
    setTimeout(redrawNetwork, 200);
  }

  function wirePanelButtons() {
    if (!stage) return;
    stage.querySelectorAll("[data-collapse]").forEach(btn => {
      btn.addEventListener("click", ev => {
        ev.stopPropagation();
        toggleCollapse(btn.getAttribute("data-collapse"));
      });
    });
    stage.querySelectorAll("[data-expand]").forEach(btn => {
      btn.addEventListener("click", ev => {
        ev.stopPropagation();
        toggleCollapse(btn.getAttribute("data-expand"));
      });
    });
  }

  function wirePanelResize() {
    if (!stage) return;
    stage.querySelectorAll("[data-resize]").forEach(handle => {
      handle.addEventListener("mousedown", ev => {
        ev.preventDefault();
        const side = handle.getAttribute("data-resize");
        const startX = ev.clientX;
        const startW = side === "left" ? panelState.leftWidth : panelState.rightWidth;
        handle.classList.add("dragging");
        document.body.classList.add("panel-resizing");

        function onMove(e) {
          const dx = e.clientX - startX;
          const raw = side === "left" ? startW + dx : startW - dx;
          const w = clampWidth(raw);
          if (side === "left") {
            panelState.leftWidth = w;
            stage.style.setProperty("--left-w", w + "px");
          } else {
            panelState.rightWidth = w;
            stage.style.setProperty("--right-w", w + "px");
          }
        }
        function onUp() {
          document.removeEventListener("mousemove", onMove);
          document.removeEventListener("mouseup", onUp);
          handle.classList.remove("dragging");
          document.body.classList.remove("panel-resizing");
          savePanelState(panelState);
          redrawNetwork();
        }
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
      });
    });
  }

  // ESC: re-expand the right panel back to user's saved width (not hard-coded).
  document.addEventListener("keydown", ev => {
    if (ev.key !== "Escape") return;
    // Don't fight the search input's local ESC (it clears search & blurs).
    if (document.activeElement === searchInput) return;
    if (panelState.rightCollapsed) {
      panelState.rightCollapsed = false;
      applyPanelState();
      savePanelState(panelState);
      setTimeout(redrawNetwork, 200);
    }
  });

  // Apply restored state BEFORE first network render (called below).
  applyPanelState();
  wirePanelButtons();
  wirePanelResize();

  wireControls();
  wireSearch();
  wireDirectory();
  loadCardIndex();

  fetch(api(`/api/graph/${encodeURIComponent(SLUG)}`))
    .then(r => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(data => {
      // Choose the highest-degree node as the "subject" (pinned, larger card).
      const deg = new Map();
      for (const e of (data.edges || [])) {
        deg.set(e.from, (deg.get(e.from) || 0) + 1);
        deg.set(e.to,   (deg.get(e.to)   || 0) + 1);
      }
      let hubId = null, hubDeg = -1;
      for (const n of (data.nodes || [])) {
        const d = deg.get(n.id) || 0;
        if (d > hubDeg) { hubDeg = d; hubId = n.id; }
      }
      pinnedNodeId = hubId;

      // Pre-render each node as a mini-card image. Hide vis-network's label.
      const styledNodes = (data.nodes || []).map(n => {
        const state = { selected: false, hovered: false, pinned: n.id === pinnedNodeId };
        const img = nodeImage(n, state);
        const { w, h } = imageDims(state.pinned);
        nodeSize.set(n.id, { w, h });
        return Object.assign({}, n, {
          shape: "image",
          image: img,
          size: Math.max(w, h) / 2,
          font: { color: "rgba(0,0,0,0)", size: 0 },
        });
      });

      const nodes = new vis.DataSet(styledNodes);
      const edges = new vis.DataSet(data.edges || []);
      network = new vis.Network(
        graphMount,
        { nodes: nodes, edges: edges },
        {
          nodes: {
            shape: "image",
            // Use the SVG's natural width/height so 110×36 mini-cards don't
            // get stretched into a 110×110 square footprint.
            shapeProperties: { useImageSize: true, useBorderWithImage: false },
          },
          // Edge color is intentionally transparent — gradient/glow edges are
          // drawn by the overlay SVG via on("afterDrawing", …).
          edges: {
            color: { color: "rgba(0,0,0,0)", hover: "rgba(0,0,0,0)", inherit: false },
            width: 0,
            smooth: { type: "continuous" },
          },
          physics: {
            enabled: true,  // run once to lay out, then freeze after stabilization
            solver: "forceAtlas2Based",
            forceAtlas2Based: {
              gravitationalConstant: -50 * currentSpacing,
              springLength: 120 * currentSpacing,
              avoidOverlap: 0.5,
            },
            stabilization: { iterations: 200 },
          },
          interaction: {
            hover: true,
            tooltipDelay: 200,
            dragNodes: true,
            zoomView: true,
            dragView: true,
          },
        }
      );
      network.on("click", params => {
        if (params.nodes.length === 0) {
          // Clicking empty canvas clears selection AND persistent focus.
          const prev = Array.from(selectedById);
          selectedById.clear();
          prev.forEach(applyNodeImage);
          focusedFocusId = null;
          applyFocusDim();
          return;
        }
        const id = params.nodes[0];
        const prev = Array.from(selectedById);
        selectedById.clear();
        selectedById.add(id);
        prev.forEach(applyNodeImage);
        applyNodeImage(id);
        focusedFocusId = id;
        applyFocusDim();
        loadCard(id);
        const idx = id.indexOf(":");
        if (idx >= 0) setActiveDirectoryRow(id.slice(idx + 1));
      });
      network.on("hoverNode", params => {
        hoveredById.add(params.node);
        applyNodeImage(params.node);
        hoveredFocusId = params.node;
        applyFocusDim();
      });
      network.on("blurNode", params => {
        hoveredById.delete(params.node);
        applyNodeImage(params.node);
        if (hoveredFocusId === params.node) hoveredFocusId = null;
        applyFocusDim();
      });

      // Edge overlay — gradient/glow strokes drawn over the canvas every frame.
      ensureEdgeOverlay();
      buildEdgeIndex(data.edges || []);
      buildAdjacency(data.edges || []);
      network.on("afterDrawing", scheduleEdgeRedraw);
      window.addEventListener("resize", scheduleEdgeRedraw);

      // Freeze physics once initial layout is stable. The toggle starts checked
      // (Frozen); the user clicks it to release physics.
      network.once("stabilizationIterationsDone", () => {
        network.setOptions({ physics: { enabled: false } });
        const first = (data.nodes || [])[0];
        if (first) focusNode(first.id);
      });

      // Initial card load so the panel is never empty.
      const first = (data.nodes || [])[0];
      if (first) {
        loadCard(first.id);
        const idx = first.id.indexOf(":");
        if (idx >= 0) setActiveDirectoryRow(first.id.slice(idx + 1));
      } else {
        panel.innerHTML = '<p class="muted">This graph has no cards yet.</p>';
      }
    })
    .catch(e => {
      graphMount.innerHTML = `<p class="muted">Failed to load graph: ${escapeText(e.message)}</p>`;
    });
})();
