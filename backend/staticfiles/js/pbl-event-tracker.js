/**
 * pbl-event-tracker.js — Telemetry & Behaviour Tracking
 *
 * Captures learning-behaviour signals and batches them for the backend:
 *  - Code changes in Monaco blocks
 *  - Canvas drawing activity
 *  - Idle detection (30-second threshold)
 *  - Canvas snapshot events
 *  - Code block additions
 *
 * All events are sent via window.pblWS.send('telemetry_event', payload).
 * Batching is used so we don't flood the WebSocket.
 */

class PBLEventTracker {
  constructor() {
    this._sessionId     = null;
    this._batch         = [];          // buffered events
    this._flushInterval = null;
    this._idleTimer     = null;
    this._isIdle        = false;
    this._lastActivity  = Date.now();

    // Batch flush every 10 seconds
    this._FLUSH_INTERVAL_MS = 10000;
    // Idle threshold
    this._IDLE_THRESHOLD_MS = 30000;
    // Debounce delay for code-change events (avoid flooding on each keystroke)
    this._codeChangeDebounce = null;
    this._CODE_DEBOUNCE_MS  = 1500;
  }

  /* ── Lifecycle ──────────────────────────────────────── */

  start(sessionId) {
    this._sessionId = sessionId;

    // Flush batch at regular intervals
    this._flushInterval = setInterval(() => this._flush(), this._FLUSH_INTERVAL_MS);

    // Idle detection — watch all meaningful user input
    this._startIdleDetection();

    console.log('[EventTracker] Started for session:', sessionId);
  }

  stop() {
    if (this._flushInterval) { clearInterval(this._flushInterval); this._flushInterval = null; }
    if (this._idleTimer)     { clearTimeout(this._idleTimer);      this._idleTimer     = null; }
    if (this._codeChangeDebounce) { clearTimeout(this._codeChangeDebounce); this._codeChangeDebounce = null; }
    this._flush(); // Send remaining events
    console.log('[EventTracker] Stopped');
  }

  /* ── Event Hooks (called by other modules) ──────────── */

  /** Called when Monaco block content changes */
  onCodeChange(code) {
    this._touchActivity();

    clearTimeout(this._codeChangeDebounce);
    this._codeChangeDebounce = setTimeout(() => {
      this._record('code_change', {
        code_length: code.length,
        has_syntax_attempt: code.trim().length > 0,
      });
    }, this._CODE_DEBOUNCE_MS);
  }

  /** Called when user draws on canvas */
  onCanvasDraw() {
    this._touchActivity();
    this._record('canvas_draw', { ts: Date.now() });
  }

  /** Called when a snapshot is taken */
  onCanvasSnapshot(trigger) {
    this._record('canvas_snapshot', { trigger });
  }

  /** Called when a code block is added */
  onCodeBlockAdded(blockId) {
    this._touchActivity();
    this._record('code_block_added', { block_id: blockId });
  }

  /** Called when user requests a hint */
  onHintRequested() {
    this._touchActivity();
    this._record('hint_requested', { ts: Date.now() });
  }

  /** Called when code is submitted for evaluation */
  onCodeSubmitted(code) {
    this._touchActivity();
    this._record('code_submitted', {
      code_length: code.length,
      ts: Date.now(),
    });
  }

  /** Called when user runs code (not submit) */
  onCodeRun(code) {
    this._touchActivity();
    this._record('code_run', {
      code_length: code.length,
      ts: Date.now(),
    });
  }

  /** Called when voice recording starts/stops */
  onVoiceEvent(action) {
    this._touchActivity();
    this._record('voice_event', { action });
  }

  /** Called when user switches tabs */
  onTabSwitch(tabName) {
    this._touchActivity();
    this._record('tab_switch', { tab: tabName });
  }

  /* ── Internal ───────────────────────────────────────── */

  _record(eventType, data = {}) {
    this._batch.push({
      event_type: eventType,
      timestamp: new Date().toISOString(),
      session_id: this._sessionId,
      ...data,
    });

    // If batch exceeds 25 events, flush immediately
    if (this._batch.length >= 25) this._flush();
  }

  _flush() {
    if (this._batch.length === 0) return;
    if (!window.pblWS?.isConnected()) return;

    const events = this._batch.splice(0);   // drain without replacing reference
    window.pblWS.send('telemetry_event', {
      session_id: this._sessionId,
      events,
    });
  }

  /** Returns seconds since the last recorded user interaction. */
  getTimeSinceLastAction() {
    return (Date.now() - this._lastActivity) / 1000;
  }

  _touchActivity() {
    this._lastActivity = Date.now();
    if (this._isIdle) {
      this._isIdle = false;
      this._record('idle_end', { idle_duration_ms: Date.now() - this._lastActivity });
      window.pblWS?.send('idle_status', { idle: false });
    }
    // Reset idle countdown
    this._scheduleIdleCheck();
  }

  _startIdleDetection() {
    const interactionEvents = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];
    interactionEvents.forEach(evt => {
      document.addEventListener(evt, () => this._touchActivity(), { passive: true });
    });
    this._scheduleIdleCheck();
  }

  _scheduleIdleCheck() {
    clearTimeout(this._idleTimer);
    this._idleTimer = setTimeout(() => {
      this._isIdle = true;
      this._record('idle_start', { duration_threshold_ms: this._IDLE_THRESHOLD_MS });
      window.pblWS?.send('idle_status', { idle: true });
      console.log('[EventTracker] User is idle');
    }, this._IDLE_THRESHOLD_MS);
  }
}

// ── Global instance ──────────────────────────────────────
window.pblEventTracker = new PBLEventTracker();
