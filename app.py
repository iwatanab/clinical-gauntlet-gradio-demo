import os
import queue
import threading
from dotenv import load_dotenv
load_dotenv()  # must run before pipeline import — MAX_DEPTH is read at pipeline module level

import log_config
log_config.configure()

import gradio as gr
from models import Argument
from pipeline import run_pipeline
from tree_renderer import update_pairs, render_tree_html
from examples.af_ich import CLAIM as DEFAULT_CLAIM, GOAL as DEFAULT_GOAL, GROUNDS as DEFAULT_GROUNDS


_BTN_RUNNING = gr.update(interactive=False, value="Running\u2026")
_BTN_READY   = gr.update(interactive=True,  value="Run Gauntlet")


def submit(claim: str, goal: str, grounds: str, warrant: str, backing: str):
    # yields: (tree_html, verdict, justification, recommendation, references, btn)
    if not claim.strip() or not goal.strip() or not grounds.strip():
        raise gr.Error("Claim, Goal, and Grounds are required.")

    argument = Argument(
        claim=claim,
        goal=goal,
        grounds=grounds,
        warrant=warrant if warrant.strip() else None,
        backing=backing if backing.strip() else None,
    )

    event_queue: queue.Queue = queue.Queue()
    pairs: dict = {}
    result_holder: dict = {}
    error_holder: list = [None]

    def run():
        try:
            result_holder.update(run_pipeline(argument, on_event=event_queue.put))
        except Exception as exc:
            error_holder[0] = exc
        finally:
            event_queue.put({"type": "_done", "path": "", "depth": 0, "data": None})

    threading.Thread(target=run, daemon=True).start()

    # Initial yield — disable button, show placeholder
    yield render_tree_html(pairs), "", "", "", [], _BTN_RUNNING

    while True:
        evt = event_queue.get()
        if evt["type"] == "_done":
            break
        if evt["type"] == "pipeline_complete":
            yield render_tree_html(pairs, verdict=evt["data"]["verdict"]), "", "", "", [], gr.update()
        else:
            update_pairs(pairs, evt)
            yield render_tree_html(pairs), "", "", "", [], gr.update()

    if error_holder[0] is not None:
        raise gr.Error(f"Pipeline error: {error_holder[0]}")

    # Final yield — re-enable button, populate all text outputs
    yield (
        render_tree_html(pairs, verdict=result_holder.get("verdict")),
        result_holder.get("verdict", ""),
        result_holder.get("justification", ""),
        result_holder.get("recommendation", ""),
        result_holder.get("references", []),
        _BTN_READY,
    )


_MODAL_JS = """
(function () {
  /* Escape key to close modal */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      var o = document.getElementById('gauntlet-modal-overlay');
      if (o) o.remove();
    }
  });

  /* Event delegation — catches clicks on [data-modal] cards even after re-render */
  document.addEventListener('click', function (e) {
    if (e.target.closest('#gauntlet-modal-overlay')) return;
    var card = e.target.closest('[data-modal]');
    if (!card) return;
    e.stopPropagation();
    _gauntletOpen(card);
  });

  window.gauntletCloseModal = function () {
    var el = document.getElementById('gauntlet-modal-overlay');
    if (el) el.remove();
  };

  function _gauntletOpen(card) {
    window.gauntletCloseModal();
    var raw = card.getAttribute('data-modal');
    if (!raw) return;
    var d;
    try { d = JSON.parse(raw); } catch (ex) { return; }

    var overlay = document.createElement('div');
    overlay.id = 'gauntlet-modal-overlay';
    overlay.className = 'gauntlet-modal-overlay';
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) window.gauntletCloseModal();
    });
    overlay.innerHTML = _buildHTML(d);
    overlay.querySelector('.gauntlet-modal-box')
           .addEventListener('click', function (e) { e.stopPropagation(); });
    overlay.querySelector('.gauntlet-modal-close')
           .addEventListener('click', window.gauntletCloseModal);
    document.body.appendChild(overlay);
  }

  function _e(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function _sec(label, html) {
    return '<div class="gauntlet-modal-section">'
         + '<div class="gauntlet-modal-section-label">' + label + '</div>'
         + '<div class="gauntlet-modal-section-value">' + html + '</div>'
         + '</div>';
  }

  function _agentSec(name, path, bClass, content, desc) {
    return '<div class="gauntlet-modal-section">'
         + '<div class="gauntlet-modal-section-label">'
         + '<span class="gauntlet-modal-badge ' + bClass + '">'
         + name + ' &middot; ' + _e(path) + '</span></div>'
         + '<div class="gauntlet-modal-section-value">' + content + '</div>'
         + '<div class="gauntlet-modal-section-desc">' + _e(desc) + '</div>'
         + '</div>';
  }

  function _buildHTML(d) {
    var isNode    = (d.role === 'node');
    var roleLabel = isNode ? 'ARGUMENT' : 'RIVAL ARGUMENT';
    var bClass    = isNode ? 'modal-badge-node' : 'modal-badge-rival';
    var sections  = '';

    sections += _sec('Claim',   _e(d.claim   || '\u2014'));
    if (d.goal)    sections += _sec('Goal',    _e(d.goal));
    if (d.grounds) sections += _sec('Grounds', _e(d.grounds));

    /* Constructor */
    var cHTML = '';
    if (d.warrant) cHTML += '<p><strong>Warrant:</strong> ' + _e(d.warrant) + '</p>';
    if (d.backing) cHTML += '<p><strong>Backing:</strong> ' + _e(d.backing) + '</p>';
    if (d.citations && d.citations.length) {
      cHTML += '<p><strong>Citations (' + d.citations.length + '):</strong></p>'
             + '<ul class="gauntlet-modal-ul">';
      d.citations.forEach(function (c) {
        var src = c.url
          ? '<a class="gauntlet-modal-cite-link" href="' + _e(c.url) + '" target="_blank">' + _e(c.source) + '</a>'
          : _e(c.source);
        cHTML += '<li>' + src
               + (c.year   ? ' (' + _e(c.year)   + ')'          : '')
               + (c.target ? ' [' + _e(c.target) + ']'          : '')
               + ': ' + _e(c.finding) + '</li>';
      });
      cHTML += '</ul>';
    }
    sections += _agentSec('Constructor', d.path, bClass,
      cHTML || '<span style="color:#475569">Pending\u2026</span>',
      'Searched the web and built the warrant, backing, and citations that ground this argument.');

    /* Questioner */
    var qHTML = '';
    if (d.questions && d.questions.length) {
      qHTML = '<ul class="gauntlet-modal-ul">';
      d.questions.forEach(function (q) { qHTML += '<li>' + _e(q) + '</li>'; });
      qHTML += '</ul>';
    }
    sections += _agentSec('Questioner', d.path, bClass,
      qHTML || '<span style="color:#475569">Pending\u2026</span>',
      "Identified the Walton argumentation scheme in play and raised critical questions to probe this argument\u2019s weaknesses.");

    /* Arbiter */
    var aHTML = '';
    if (d.arbiter_reasoning) aHTML += '<p>' + _e(d.arbiter_reasoning) + '</p>';
    if (d.spawned_claims && d.spawned_claims.length) {
      aHTML += '<p><strong>Spawned sub-arguments (' + d.spawned_claims.length + '):</strong></p>'
             + '<ul class="gauntlet-modal-ul">';
      d.spawned_claims.forEach(function (c) { aHTML += '<li>' + _e(c) + '</li>'; });
      aHTML += '</ul>';
    }
    if (d.spawn_allowed !== null && d.spawn_allowed !== undefined) {
      aHTML += '<p>' + (d.spawn_allowed
        ? '<span class="gauntlet-modal-spawn-allowed">&#10003; Permitted to spawn sub-arguments</span>'
        : '<span class="gauntlet-modal-spawn-halted">&#10007; Halted \u2014 no further sub-arguments</span>')
        + '</p>';
    }
    sections += _agentSec('Arbiter', d.path, 'modal-badge-arbiter',
      aHTML || '<span style="color:#475569">Pending\u2026</span>',
      'Evaluated both arguments cross-sibling and decided whether each has sufficient merit to spawn deeper sub-arguments.');

    var headerBadge = '<span class="gauntlet-modal-badge ' + bClass + '">'
                    + roleLabel + ' &middot; ' + _e(d.path) + '</span>';

    return '<div class="gauntlet-modal-box">'
         + '<div class="gauntlet-modal-header">'
         + '<div class="gauntlet-modal-title">' + headerBadge + '</div>'
         + '<button class="gauntlet-modal-close" title="Close (Esc)">\u2715</button>'
         + '</div>'
         + '<div class="gauntlet-modal-body">' + sections + '</div>'
         + '</div>';
  }
})();

/* ── Run timer ── */
(function () {
  var _timerInt = null, _startMs = null, _timerEl = null, _running = false;

  function _wrap() { return document.getElementById('gauntlet-submit-btn'); }
  function _btn()  { var w = _wrap(); return w ? w.querySelector('button') : null; }

  function _pad(n, w) {
    var s = String(n);
    while (s.length < w) s = ' ' + s;
    return s;
  }
  function _fmt(ms) {
    var m = Math.floor(ms / 60000);
    var s = Math.floor((ms % 60000) / 1000);
    var r = ms % 1000;
    return (m > 0 ? m + 'm ' : '') + _pad(s, 2) + 's ' + _pad(r, 3) + 'ms';
  }

  function _ensureTimer() {
    if (_timerEl && _timerEl.isConnected) return _timerEl;
    var w = _wrap(); if (!w) return null;
    /* Absolutely positioned inside the button wrapper — no extra flow space */
    w.style.position = 'relative';
    w.style.overflow  = 'visible';
    _timerEl = document.createElement('div');
    _timerEl.style.cssText = 'position:absolute;bottom:-14px;right:2px;'
      + 'font-size:10px;color:#64748b;line-height:1;'
      + 'font-family:monospace;white-space:pre;'
      + 'pointer-events:none;display:none;z-index:10;';
    w.appendChild(_timerEl);
    return _timerEl;
  }

  function _startTimer(el) {
    _startMs = Date.now();
    el.style.display = 'block';
    el.textContent = _fmt(0);
    _timerInt = setInterval(function () {
      el.textContent = _fmt(Date.now() - _startMs);
    }, 100);
  }

  function _finish(el) {
    _running = false;
    if (_timerInt) { clearInterval(_timerInt); _timerInt = null; }
    if (el && _startMs !== null)
      el.textContent = 'Completed in ' + _fmt(Date.now() - _startMs);
  }

  document.addEventListener('click', function (e) {
    var w = _wrap();
    if (!w || !w.contains(e.target) || _running) return;
    _running = true;

    var el = _ensureTimer();
    if (el) _startTimer(el);

    /* Poll the button's disabled state — more reliable than MutationObserver in
       Gradio's React DOM where the <button> element may be replaced entirely.
       Phase 1: wait for button to become disabled (first yield sets interactive=False).
       Phase 2: wait for button to become enabled again (final yield sets interactive=True). */
    var phase = 'wait_disabled';
    var watchdog = setInterval(function () {
      var cur = _btn();
      if (!cur) return;
      var off = cur.disabled || cur.getAttribute('aria-disabled') === 'true';
      if (phase === 'wait_disabled' && off) {
        phase = 'wait_enabled';
      } else if (phase === 'wait_enabled' && !off) {
        clearInterval(watchdog);
        _finish(el);
      }
    }, 300);
  });
})();
"""


_CSS = """
/* Suppress the orange streaming-border animation on output components */
.generating { border-color: transparent !important; animation: none !important; }
"""

with gr.Blocks() as demo:
    gr.Markdown("# Clinical Gauntlet — Educational Demo")
    gr.Markdown(
        "**Gauntlet** is a recursive deliberation harness built on argumentation theory. "
        "It stress-tests a claim by constructing a full adversarial argument tree, then synthesises a verdict."
    )
    with gr.Accordion("How it works", open=False):
        gr.Markdown(
            """
Each claim is paired with its negation and both sides pass through three agents in sequence:

- **Constructor** — advocates unconditionally, searching clinical guidelines, RCTs, and systematic reviews \
to build the argument's *warrant* (the inference rule), *backing* (evidence base), and *citations*
- **Questioner** — identifies the Walton argumentation scheme instantiated by the warrant and raises \
critical questions probing the argument's internal logic
- **Arbiter** — cross-examines both sides against each other using those questions, decides which have \
sufficient merit to recurse, and distils the sub-claims worth pursuing deeper

The Arbiter's sub-claims restart the cycle at the next depth level, building a tree of dialectical pairs. \
Once the full tree is complete, the **Resolver** surveys the entire structure and delivers a verdict — \
*survives*, *defeated*, or *impasse* — with justification and recommendation.
"""
        )
    gr.Markdown(
        "> **Disclaimer:** This tool is for educational purposes only — outputs are AI-generated, "
        "may be inaccurate, and must not be used as a substitute for professional judgement in "
        "healthcare or any other domain."
    )
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                claim = gr.Textbox(label="Claim *", lines=3, value=DEFAULT_CLAIM,
                    info="The specific action or decision being argued for. "
                         "Like a verdict: narrow, falsifiable, one thing. "
                         "e.g. 'This patient should receive a blood thinner.'")
                goal = gr.Textbox(label="Goal *", lines=2, value=DEFAULT_GOAL,
                    info="The outcome you are trying to achieve — the 'why bother' behind the claim. "
                         "Like a judge asking 'what are you trying to accomplish?' "
                         "e.g. 'Prevent a stroke.'")
                grounds = gr.Textbox(label="Grounds *", lines=5, value=DEFAULT_GROUNDS,
                    info="The specific facts of this case from which the claim is drawn, independent "
                         "of whether the warrant is accepted — e.g. irregular heartbeat, prior stroke, "
                         "clotting risk score of 6.")
                warrant = gr.Textbox(label="Warrant (Optional)", lines=2,
                    info="A general authorisation that bridges patient facts to claim — "
                         "e.g. 'Patients with an irregular heartbeat and a clotting risk score ≥2 "
                         "should receive a blood thinner.' Gauntlet will derive this from guidelines "
                         "if left blank.")
                backing = gr.Textbox(label="Backing (Optional)", lines=2,
                    info="The body of established evidence that certifies the warrant is sound — "
                         "e.g. ACC/AHA atrial fibrillation guidelines, ARISTOTLE trial. "
                         "Gauntlet will retrieve this from authoritative sources if left blank.")

        with gr.Column(scale=3):
            submit_btn = gr.Button("Run Gauntlet", variant="primary", elem_id="gauntlet-submit-btn")
            tree_output = gr.HTML(label="Argument Tree")
            verdict_output = gr.Textbox(label="Verdict", interactive=False)
            justification_output = gr.Textbox(label="Justification", lines=4, interactive=False)
            recommendation_output = gr.Textbox(label="Recommendation", lines=6, interactive=False)
            references_output = gr.JSON(label="References")

    submit_btn.click(
        fn=submit,
        inputs=[claim, goal, grounds, warrant, backing],
        outputs=[tree_output, verdict_output, justification_output,
                 recommendation_output, references_output, submit_btn],
    )

demo.queue()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)),
                js=_MODAL_JS, css=_CSS)
