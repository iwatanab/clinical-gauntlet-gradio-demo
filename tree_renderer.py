"""
tree_renderer.py — stateless HTML renderer for the live argument tree.

Public API:
  update_pairs(pairs, event)          mutate flat state dict from a pipeline event
  render_tree_html(pairs, verdict)    produce a self-contained HTML string
  get_direct_children(pairs, path, prefix)
"""
import html as _html
import json as _json

# ---------------------------------------------------------------------------
# Embedded CSS — tree styles scoped under .gauntlet-tree; modal styles global
# ---------------------------------------------------------------------------

_CSS = """<style>
.gauntlet-tree *, .gauntlet-tree *::before, .gauntlet-tree *::after {
  box-sizing: border-box;
}
.gauntlet-tree {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 13px;
  line-height: 1.5;
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 12px;
  min-height: 80px;
}

/* ── Loading ── */
.gauntlet-tree .loading-msg {
  color: #64748b;
  font-size: 14px;
  text-align: center;
  padding: 32px 0;
}

/* ── Pair container ── */
.gauntlet-tree .pair-container {
  margin-bottom: 6px;
}

/* ── Node + rival side by side ── */
.gauntlet-tree .pair-row {
  display: flex;
  gap: 6px;
  align-items: stretch;
}

/* ── Node card base ── */
.gauntlet-tree .node-card {
  flex: 1;
  min-width: 0;
  border-radius: 8px;
  padding: 10px 12px;
  border: 1px solid;
  cursor: pointer;
  position: relative;
  transition: filter 0.12s;
}
.gauntlet-tree .node-card:hover { filter: brightness(1.15); }
.gauntlet-tree .node-type-node  { background: #1e3a5f; border-color: #3b82f6; }
.gauntlet-tree .node-type-rival { background: #431407; border-color: #f97316; }

/* ── Role label ── */
.gauntlet-tree .role-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 4px;
  opacity: 0.65;
}
.gauntlet-tree .node-type-node  .role-label { color: #93c5fd; }
.gauntlet-tree .node-type-rival .role-label { color: #fdba74; }

/* ── Claim text ── */
.gauntlet-tree .claim-text {
  font-size: 12px;
  font-weight: 500;
  color: #f1f5f9;
  margin-bottom: 8px;
  word-break: break-word;
}

/* ── Click hint ── */
.gauntlet-tree .click-hint {
  font-size: 9px;
  color: #475569;
  margin-top: 5px;
  font-style: italic;
}

/* ── Stage badges ── */
.gauntlet-tree .badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  min-height: 20px;
}
.gauntlet-tree .badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 600;
  border: 1px solid;
  white-space: nowrap;
  line-height: 1.4;
}
.gauntlet-tree .badge-done   { background:#14532d; color:#86efac; border-color:#22c55e; }
.gauntlet-tree .badge-active { background:#1e293b; color:#93c5fd; border-color:#3b82f6; }

/* ── Spinner ── */
@keyframes gauntlet-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.gauntlet-tree .spin {
  display: inline-block;
  animation: gauntlet-spin 0.75s linear infinite;
}

/* ── Arbiter strip ── */
.gauntlet-tree .arbiter-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  padding: 5px 10px;
  background: #2d1b69;
  border: 1px solid #7c3aed;
  border-radius: 6px;
}
.gauntlet-tree .arbiter-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #c4b5fd;
  flex-shrink: 0;
}
.gauntlet-tree .arbiter-summary {
  font-size: 11px;
  color: #a78bfa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

/* ── Depth label ── */
.gauntlet-tree .depth-label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #334155;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.gauntlet-tree .depth-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #1e293b;
}

/* ── Children ── */
.gauntlet-tree .children-row {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  padding-left: 14px;
  border-left: 2px solid #334155;
  margin-left: 6px;
}
.gauntlet-tree .children-col {
  flex: 1;
  min-width: 0;
}
.gauntlet-tree .children-col > .pair-container + .pair-container {
  margin-top: 6px;
}

/* ── Verdict banner ── */
.gauntlet-tree .verdict-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding: 14px 18px;
  border-radius: 10px;
  border: 1px solid;
}
.gauntlet-tree .verdict-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.65;
  color: #ffffff !important;
}
.gauntlet-tree .verdict-value {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #ffffff !important;
}
.gauntlet-tree .verdict-survives { background:#14532d; border-color:#22c55e; }
.gauntlet-tree .verdict-defeated { background:#450a0a; border-color:#ef4444; }
.gauntlet-tree .verdict-impasse  { background:#422006; border-color:#f59e0b; }

/* ── Modal overlay (global — not scoped) ── */
.gauntlet-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.78);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.gauntlet-modal-box {
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 12px;
  max-width: 640px;
  width: 100%;
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 64px rgba(0,0,0,0.85);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 13px;
  color: #e2e8f0;
}
.gauntlet-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #334155;
  flex-shrink: 0;
}
.gauntlet-modal-title { font-size: 11px; font-weight: 700; letter-spacing: 0.06em; }
.gauntlet-modal-close {
  background: none;
  border: none;
  color: #64748b;
  font-size: 16px;
  cursor: pointer;
  padding: 2px 6px;
  line-height: 1;
  border-radius: 4px;
}
.gauntlet-modal-close:hover { color: #e2e8f0; background: #334155; }
.gauntlet-modal-body { overflow-y: auto; padding: 14px 16px; flex: 1; }
.gauntlet-modal-section {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #1e3a5f44;
}
.gauntlet-modal-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.gauntlet-modal-section-label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: #64748b;
  margin-bottom: 5px;
}
.gauntlet-modal-section-value {
  font-size: 12px;
  color: #e2e8f0;
  line-height: 1.65;
}
.gauntlet-modal-section-value p { margin: 0 0 5px 0; }
.gauntlet-modal-section-value p:last-child { margin-bottom: 0; }
.gauntlet-modal-section-desc {
  font-size: 10px;
  color: #475569;
  font-style: italic;
  margin-top: 5px;
  line-height: 1.4;
}
.gauntlet-modal-ul {
  margin: 3px 0 0 0;
  padding-left: 16px;
  font-size: 12px;
  color: #e2e8f0;
  line-height: 1.6;
}
.gauntlet-modal-ul li { margin-bottom: 3px; }
.gauntlet-modal-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 700;
  border: 1px solid;
  letter-spacing: 0.04em;
}
.modal-badge-node    { background:#1e3a5f; color:#93c5fd; border-color:#3b82f6; }
.modal-badge-rival   { background:#431407; color:#fdba74; border-color:#f97316; }
.modal-badge-arbiter { background:#2d1b69; color:#c4b5fd; border-color:#7c3aed; }
.gauntlet-modal-cite-link { color: #60a5fa; text-decoration: none; }
.gauntlet-modal-cite-link:hover { text-decoration: underline; }
.gauntlet-modal-spawn-allowed { color: #86efac; font-weight: 600; }
.gauntlet-modal-spawn-halted  { color: #fca5a5; font-weight: 600; }
</style>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(s) -> str:
    return _html.escape(str(s)) if s is not None else ""


def _modal_json(data: dict) -> str:
    """JSON-encode and HTML-attribute-escape for embedding in data-modal."""
    return _html.escape(_json.dumps(data, ensure_ascii=False), quote=True)


_STATUS_ORDER = ["constructor", "questioner", "arbiter", "complete"]


def _stage(status: str) -> int:
    try:
        return _STATUS_ORDER.index(status)
    except ValueError:
        return 0


def _render_badge_row(status: str) -> str:
    """Short agent name badges — no path (path shown in modal)."""
    stage = _stage(status)
    parts = []
    for i, label in enumerate(["Constructor", "Questioner", "Arbiter"]):
        if i < stage:
            parts.append(f'<span class="badge badge-done">&#10003; {label}</span>')
        elif i == stage:
            parts.append(
                f'<span class="badge badge-active">'
                f'<span class="spin">&#8635;</span> {label}'
                f'</span>'
            )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Node card
# ---------------------------------------------------------------------------

def _render_node_card(entry: dict, role: str, path: str) -> str:
    if role == "node":
        claim     = entry.get("claim") or ""
        warrant   = entry.get("node_warrant")
        backing   = entry.get("node_backing")
        cits      = entry.get("node_citations") or []
        questions = entry.get("node_questions") or []
        spawned   = entry.get("node_spawned_claims") or []
        allowed   = entry.get("node_allowed")
    else:
        claim     = entry.get("rival_claim") or ""
        warrant   = entry.get("rival_warrant")
        backing   = entry.get("rival_backing")
        cits      = entry.get("rival_citations") or []
        questions = entry.get("rival_questions") or []
        spawned   = entry.get("rival_spawned_claims") or []
        allowed   = entry.get("rival_allowed")

    if not claim:
        return ""

    role_label = "ARGUMENT" if role == "node" else "RIVAL ARGUMENT"
    card_class = "node-type-node" if role == "node" else "node-type-rival"
    truncated  = (claim[:100] + "…") if len(claim) > 100 else claim
    badges     = _render_badge_row(entry.get("status", "constructor"))

    modal_data = {
        "path":              path,
        "role":              role,
        "status":            entry.get("status", "constructor"),
        "claim":             claim,
        "goal":              entry.get("goal"),
        "grounds":           entry.get("grounds"),
        "warrant":           warrant,
        "backing":           backing,
        "citations":         cits,
        "questions":         questions,
        "arbiter_reasoning": entry.get("arbiter_reasoning"),
        "spawned_claims":    spawned,
        "spawn_allowed":     allowed,
    }

    return (
        f'<div class="node-card {card_class}"'
        f' data-modal="{_modal_json(modal_data)}">'
        f'<div class="role-label">{role_label}</div>'
        f'<div class="claim-text">{_esc(truncated)}</div>'
        f'<div class="badge-row">{badges}</div>'
        f'<div class="click-hint">click for details</div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Arbiter strip
# ---------------------------------------------------------------------------

def _render_arbiter_strip(entry: dict) -> str:
    status = entry.get("status", "")
    if status not in ("arbiter", "complete"):
        return ""

    node_allowed  = entry.get("node_allowed")
    rival_allowed = entry.get("rival_allowed")
    has_rival     = entry.get("rival_claim") is not None

    parts = []
    if node_allowed:
        nc = len(entry.get("node_spawned_claims") or [])
        parts.append(f"Arg &#8594; {nc} sub-arg{'s' if nc != 1 else ''}")
    else:
        parts.append("Arg &#8594; halted")

    if has_rival:
        if rival_allowed:
            rc = len(entry.get("rival_spawned_claims") or [])
            parts.append(f"Rival &#8594; {rc} sub-arg{'s' if rc != 1 else ''}")
        else:
            parts.append("Rival &#8594; halted")

    summary = " &nbsp;&#183;&nbsp; ".join(parts)
    spinner = (
        f'<span class="spin" style="margin-right:3px">&#8635;</span>'
        if status == "arbiter" else ""
    )

    return (
        f'<div class="arbiter-strip">'
        f'<span class="arbiter-label">&#9878; Arbiter</span>'
        f'<span class="arbiter-summary">{spinner}{summary}</span>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Verdict banner
# ---------------------------------------------------------------------------

def _render_verdict_banner(verdict: str) -> str:
    v = verdict.lower()
    css_class = {"survives": "verdict-survives", "defeated": "verdict-defeated"}.get(
        v, "verdict-impasse"
    )
    icon = {"survives": "&#10003;", "defeated": "&#10007;"}.get(v, "~")
    return (
        f'<div class="verdict-banner {css_class}">'
        f'<span class="verdict-label">Verdict</span>'
        f'<span class="verdict-value">{icon} {_esc(verdict.upper())}</span>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Tree traversal
# ---------------------------------------------------------------------------

def get_direct_children(pairs: dict, parent_path: str, prefix: str) -> list[str]:
    """Return immediate child paths matching parent_path.prefix{n}, sorted by index."""
    results = []
    prefix_key = parent_path + "." + prefix
    for key in pairs:
        if not key.startswith(prefix_key):
            continue
        tail = key[len(parent_path) + 1:]
        if "." not in tail:
            results.append(key)
    return sorted(
        results,
        key=lambda k: int(k.rsplit(".", 1)[-1][1:]) if "." in k else int(k[len(parent_path) + 2:])
    )


def _render_pair_html(pairs: dict, path: str) -> str:
    entry = pairs.get(path)
    if entry is None:
        return ""

    node_card  = _render_node_card(entry, "node", path)
    rival_card = _render_node_card(entry, "rival", path) if entry.get("rival_claim") else ""
    arb_strip  = _render_arbiter_strip(entry)

    depth     = entry.get("depth", 0)
    depth_lbl = f'<div class="depth-label">Depth {depth}</div>'
    pair_row  = f'{depth_lbl}<div class="pair-row">{node_card}{rival_card}</div>'

    node_children  = get_direct_children(pairs, path, "n")
    rival_children = get_direct_children(pairs, path, "r")

    children_html = ""
    if node_children or rival_children:
        node_col  = "".join(_render_pair_html(pairs, cp) for cp in node_children)
        rival_col = "".join(_render_pair_html(pairs, cp) for cp in rival_children)
        if node_col or rival_col:
            children_html = (
                f'<div class="children-row">'
                f'<div class="children-col">{node_col}</div>'
                f'<div class="children-col">{rival_col}</div>'
                f'</div>'
            )

    return f'<div class="pair-container">{pair_row}{arb_strip}{children_html}</div>'


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def update_pairs(pairs: dict, event: dict) -> None:
    """Mutate the flat pairs state dict from a single pipeline event."""
    path = event["path"]
    t    = event["type"]
    data = event.get("data") or {}

    if t == "pair_started":
        pairs[path] = {
            "depth":       event["depth"],
            "claim":       data.get("claim", ""),
            "rival_claim": data.get("rival_claim"),
            "goal":        data.get("goal"),
            "grounds":     data.get("grounds"),
            "status":      "constructor",
            "node_warrant": None, "node_backing": None, "node_citations": [],
            "rival_warrant": None, "rival_backing": None, "rival_citations": [],
            "node_questions": [], "rival_questions": None,
            "arbiter_reasoning": None,
            "node_spawned_claims": [], "rival_spawned_claims": [],
            "node_allowed": None, "rival_allowed": None,
        }

    elif t == "constructor_done":
        entry = pairs.setdefault(path, {
            "depth": event["depth"], "claim": "", "rival_claim": None,
            "goal": None, "grounds": None, "status": "constructor",
        })
        na = data.get("node_argument") or {}
        ra = data.get("rival_argument") or {}
        entry.update({
            "node_warrant":    na.get("warrant"),
            "node_backing":    na.get("backing"),
            "node_citations":  na.get("citations") or [],
            "rival_warrant":   ra.get("warrant")   if ra else None,
            "rival_backing":   ra.get("backing")   if ra else None,
            "rival_citations": ra.get("citations") or [] if ra else [],
            "status": "questioner",
        })
        if not entry.get("claim") and na.get("claim"):
            entry["claim"] = na["claim"]
        if not entry.get("rival_claim") and ra and ra.get("claim"):
            entry["rival_claim"] = ra["claim"]

    elif t == "questioner_done":
        entry = pairs.setdefault(path, {})
        entry.update({
            "node_questions":  data.get("node_questions") or [],
            "rival_questions": data.get("rival_questions"),
            "status": "arbiter",
        })

    elif t == "arbiter_done":
        entry = pairs.setdefault(path, {})
        entry.update({
            "arbiter_reasoning":    data.get("arbiter_reasoning", ""),
            "node_spawned_claims":  data.get("node_spawned_claims") or [],
            "rival_spawned_claims": data.get("rival_spawned_claims") or [],
            "node_allowed":  data.get("node_allowed"),
            "rival_allowed": data.get("rival_allowed"),
            "status": "arbiter",
        })

    elif t == "pair_complete":
        entry = pairs.setdefault(path, {})
        entry["status"] = "complete"


def render_tree_html(pairs: dict, verdict: str | None = None) -> str:
    """Return a self-contained HTML string for the current tree state."""
    if not pairs:
        return (
            _CSS
            + '<div class="gauntlet-tree">'
            + '<div class="loading-msg">Building argument tree&#8230;</div>'
            + '</div>'
        )

    tree   = _render_pair_html(pairs, "root")
    banner = _render_verdict_banner(verdict) if verdict else ""
    return _CSS + f'<div class="gauntlet-tree">{tree}{banner}</div>'
