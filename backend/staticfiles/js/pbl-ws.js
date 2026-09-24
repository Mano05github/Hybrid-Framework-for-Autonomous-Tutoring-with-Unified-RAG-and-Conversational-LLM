/**
 * pbl-ws.js — PBL WebSocket Manager
 * Manages the /ws/pbl/{session_id}/ connection with auto-reconnect,
 * typed event dispatch, and barge-in (interrupt) support.
 */

class PBLWebSocket {
  constructor() {
    this._ws                 = null;
    this._sessionId          = null;
    this._reconnectAttempts  = 0;
    this._maxReconnects      = 5;
    this._baseDelay          = 1000;
    this._isManualClose      = false;
    this._isConnecting       = false;
    this._handlers           = {};   // type → [callback, ...]
    this._connectCallbacks   = [];
    this._disconnectCallbacks = [];
    this._errorCallbacks     = [];
  }

  /* ── Connection ─────────────────────────────────────── */

  connect(sessionId) {
    if (this._isConnecting || this.isConnected()) {
      console.warn('[PBL-WS] Already connected or connecting');
      return;
    }
    this._sessionId         = sessionId;
    this._isConnecting      = true;
    this._isManualClose     = false;

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url   = `${proto}//${window.location.host}/ws/pbl/${sessionId}/`;
    console.log(`[PBL-WS] Connecting → ${url}`);

    try {
      this._ws = new WebSocket(url);
      this._attach();
    } catch (err) {
      console.error('[PBL-WS] Failed to create socket:', err);
      this._isConnecting = false;
      this._scheduleReconnect();
    }
  }

  disconnect() {
    this._isManualClose = true;
    if (this._ws) {
      this._ws.close(1000, 'Client disconnect');
      this._ws = null;
    }
    this._sessionId = null;
    this._reconnectAttempts = 0;
  }

  isConnected() {
    return this._ws && this._ws.readyState === WebSocket.OPEN;
  }

  /* ── Sending ────────────────────────────────────────── */

  /** Send JSON message to backend */
  send(type, payload = {}) {
    if (!this.isConnected()) {
      console.warn('[PBL-WS] Not connected — dropping message:', type);
      return false;
    }
    try {
      this._ws.send(JSON.stringify({ type, ...payload }));
      return true;
    } catch (err) {
      console.error('[PBL-WS] Send error:', err);
      return false;
    }
  }

  /** Send raw binary (audio blob) */
  sendBinary(blob) {
    if (!this.isConnected()) return false;
    try { this._ws.send(blob); return true; }
    catch (err) { console.error('[PBL-WS] Binary send error:', err); return false; }
  }

  /** Interrupt AI speech (barge-in) */
  interrupt() {
    this.send('interrupt');
  }

  /* ── Event registration ─────────────────────────────── */

  /** Register handler for a specific inbound message type */
  on(type, callback) {
    if (!this._handlers[type]) this._handlers[type] = [];
    this._handlers[type].push(callback);
  }

  onConnect(cb)    { this._connectCallbacks.push(cb); }
  onDisconnect(cb) { this._disconnectCallbacks.push(cb); }
  onError(cb)      { this._errorCallbacks.push(cb); }

  /* ── Internal ───────────────────────────────────────── */

  _attach() {
    this._ws.onopen = () => {
      console.log('[PBL-WS] Connected ✅');
      this._isConnecting      = false;
      this._reconnectAttempts = 0;
      this._connectCallbacks.forEach(cb => cb());
    };

    this._ws.onmessage = (event) => {
      if (event.data instanceof Blob) {
        // Raw binary audio — dispatch as 'raw_audio'
        this._dispatch('raw_audio', event.data);
        return;
      }
      try {
        const data = JSON.parse(event.data);
        this._dispatch(data.type, data);
      } catch (err) {
        console.error('[PBL-WS] Parse error:', err, event.data);
      }
    };

    this._ws.onerror = (err) => {
      console.error('[PBL-WS] Error:', err);
      this._isConnecting = false;
      this._errorCallbacks.forEach(cb => cb(err));
    };

    this._ws.onclose = (evt) => {
      console.log(`[PBL-WS] Closed (code=${evt.code})`);
      this._isConnecting = false;
      this._disconnectCallbacks.forEach(cb => cb(evt));
      if (!this._isManualClose) this._scheduleReconnect();
    };
  }

  _dispatch(type, data) {
    const handlers = this._handlers[type];
    if (handlers && handlers.length > 0) {
      handlers.forEach(cb => { try { cb(data); } catch (e) { console.error(`[PBL-WS] Handler error for "${type}":`, e); } });
    } else {
      // Uncomment for debugging unknown message types:
      // console.log('[PBL-WS] Unhandled message type:', type, data);
    }
  }

  _scheduleReconnect() {
    if (this._reconnectAttempts >= this._maxReconnects) {
      console.error('[PBL-WS] Max reconnect attempts reached');
      return;
    }
    this._reconnectAttempts++;
    const delay = this._baseDelay * Math.pow(2, this._reconnectAttempts - 1);
    console.log(`[PBL-WS] Reconnecting in ${delay}ms (attempt ${this._reconnectAttempts}/${this._maxReconnects})`);
    setTimeout(() => {
      if (this._sessionId && !this._isManualClose) {
        this.connect(this._sessionId);
      }
    }, delay);
  }
}

// ── Single global instance ───────────────────────────────
window.pblWS = new PBLWebSocket();
