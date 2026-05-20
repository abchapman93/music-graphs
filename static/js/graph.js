// graph.js — vis-network rendering + side-panel for the /graph/<slug> view.
// Expects window.GRAPH_SLUG to be set by the server-rendered template.

(function () {
  "use strict";

  const SLUG = window.GRAPH_SLUG;
  const graphMount = document.getElementById("graph");
  const panel = document.getElementById("card-panel-content");
  const directoryPanel = document.getElementById("directory-panel-content");
  const cardPanelAside = document.getElementById("card-panel");
  const directoryPanelAside = document.getElementById("directory-panel");
  const searchInput = document.getElementById("search-input");
  const searchResults = document.getElementById("search-results");

  // Type → background color, parallel to GROUPS but in plain CSS form for dots.
  const TYPE_COLOR = {
    person: "#3b82f6",
    group: "#3b82f6",
    album: "#22c55e",
    track: "#16a34a",
    song: "#86efac",
    location: "#f59e0b",
    genre: "#a855f7",
    note: "#facc15",
    memory: "#ef4444",
  };

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
      const height = isTall ? 352 : 152;
      parts.push(
        `<div class="card-spotify">` +
        `<iframe src="${escapeText(card.spotify_embed_url)}" ` +
        `data-spotify-kind="${escapeText(card.spotify_kind || "")}" ` +
        `height="${height}" frameborder="0" allowtransparency="true" allow="encrypted-media">` +
        `</iframe></div>`
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
    fetch(`/api/card/${encodeURIComponent(SLUG)}/${encodeURIComponent(cardSlug)}`)
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
    return fetch(`/api/cards/${encodeURIComponent(SLUG)}`)
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

  function wireControls() {
    const zin = document.getElementById("zoom-in");
    const zout = document.getElementById("zoom-out");
    const zfit = document.getElementById("zoom-fit");
    const freeze = document.getElementById("freeze-toggle");
    if (zin) zin.addEventListener("click", () => zoomBy(ZOOM_STEP));
    if (zout) zout.addEventListener("click", () => zoomBy(1 / ZOOM_STEP));
    if (zfit) zfit.addEventListener("click", fitView);
    if (freeze) {
      freeze.addEventListener("change", () => {
        if (!network) return;
        // checkbox checked == "Frozen" (physics disabled)
        network.setOptions({ physics: { enabled: !freeze.checked } });
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

  panel.addEventListener("click", function (ev) {
    if (ev.target.closest("[data-card-edit]")) {
      ev.preventDefault();
      enterEditMode();
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

  fetch(`/api/graph/${encodeURIComponent(SLUG)}`)
    .then(r => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(data => {
      const nodes = new vis.DataSet(data.nodes || []);
      const edges = new vis.DataSet(data.edges || []);
      network = new vis.Network(
        graphMount,
        { nodes: nodes, edges: edges },
        {
          groups: GROUPS,
          nodes: { font: { size: 13, color: "#1a1a1a" }, size: 16 },
          edges: { color: { color: "#9ca3af" }, smooth: { type: "dynamic" } },
          physics: {
            enabled: true,  // run once to lay out, then freeze after stabilization
            solver: "forceAtlas2Based",
            forceAtlas2Based: { gravitationalConstant: -50, springLength: 120, avoidOverlap: 0.5 },
            stabilization: { iterations: 200 },
          },
          interaction: { hover: true, tooltipDelay: 200, dragNodes: true },
        }
      );
      network.on("click", params => {
        if (params.nodes.length === 0) return;
        const id = params.nodes[0];
        loadCard(id);
        const idx = id.indexOf(":");
        if (idx >= 0) setActiveDirectoryRow(id.slice(idx + 1));
      });

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
