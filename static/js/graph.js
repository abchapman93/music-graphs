// graph.js — vis-network rendering + side-panel for the /graph/<slug> view.
// Expects window.GRAPH_SLUG to be set by the server-rendered template.

(function () {
  "use strict";

  const SLUG = window.GRAPH_SLUG;
  const graphMount = document.getElementById("graph");
  const panel = document.getElementById("card-panel");

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
    const TALL = new Set(["album", "playlist", "show"]);
    const isTall = card.spotify_kind && TALL.has(card.spotify_kind);
    const parts = [];
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

  // Delegate wikilink clicks inside the panel.
  panel.addEventListener("click", function (ev) {
    const a = ev.target.closest("[data-wikilink]");
    if (!a) return;
    ev.preventDefault();
    const targetId = a.getAttribute("data-wikilink");
    if (!targetId) return;
    focusNode(targetId);
    loadCard(targetId);
  });

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
      });

      // Initial load: focus + load the first node so the panel is never empty.
      const first = (data.nodes || [])[0];
      if (first) {
        network.once("stabilizationIterationsDone", () => focusNode(first.id));
        loadCard(first.id);
      } else {
        panel.innerHTML = '<p class="muted">This graph has no cards yet.</p>';
      }
    })
    .catch(e => {
      graphMount.innerHTML = `<p class="muted">Failed to load graph: ${escapeText(e.message)}</p>`;
    });
})();
