/**
 * pbl-session.js — PBL Session Lifecycle Manager
 *
 * Orchestrates:
 *  - URL param parsing (?subject=)
 *  - Auth guard check
 *  - POST /api/pbl/session/start/ → receive session_id + problem
 *  - WebSocket connection + all message handlers
 *  - 3-tab panel switching
 *  - Voice recording (MediaRecorder → PCM chunks or WebM)
 *  - Waveform visualizer (Web Audio API)
 *  - TTS playback (AudioContext)
 *  - AI message rendering
 *  - Problem panel population
 *  - Run / Submit / Hint button handlers
 *  - Toast notifications
 */

// ── Constants ────────────────────────────────────────────
const STAR_FILLED = '★';
const STAR_EMPTY  = '☆';

class PBLSession {
  constructor() {
    this._sessionId     = null;
    this._subjectSlug   = null;
    this._problem       = null;
    this._currentTab    = 'ai';   // 'problem' | 'ai' | 'voice'
    this._isRecording   = false;
    this._mediaRecorder = null;
    this._audioChunks   = [];
    this._audioCtx      = null;
    this._analyser      = null;
    this._waveAnim      = null;
    this._ttsQueue      = [];     // pending audio blobs for TTS
    this._ttsPlaying    = false;
    this._currentAudio  = null;   // active Audio object for interrupt
    this._voiceTurnId   = null;
    this._archMode      = 'new';
    this._hintCount     = 0;
    this._attemptCount  = 0;

    // VAD — Voice Activity Detection (persistent voice session)
    this._vadActive       = false;
    this._vadState        = 'idle';  // 'idle' | 'speaking' | 'sending' | 'ai_responding'
    this._vadSilenceStart = null;    // performance.now() when silence began
    this._vadStream       = null;    // persistent MediaStream (stays open whole session)
    this._vadAnimFrame    = null;    // requestAnimationFrame id for VAD loop
    this._utteranceStart  = null;    // performance.now() when speech began (min duration gate)

    // DOM refs
    this._dom = {};
  }

  /* ── Entry point ────────────────────────────────────── */

  async init() {
    // 1. Auth guard
    if (window.AuthGuard) {
      try { await window.AuthGuard.checkAuth(); }
      catch (e) { return; }
    }

    // 2. Bind DOM
    this._bindDOM();

    // 3. Parse URL
    const params       = new URLSearchParams(window.location.search);
    this._subjectSlug  = params.get('subject') || params.get('subject_id') || '';
    this._topicId      = params.get('topic_id') || '';
    this._topicName    = params.get('topic') || '';
    if (!this._subjectSlug && !this._topicId) {
      this._showError('No subject or topic specified. Please return to the subject page.');
      return;
    }

    // 4. Show loading
    this._setLoading(true);

    // 5. Init canvas
    window.pblCanvas?.init();

    // 6. Bind button handlers
    this._bindButtons();

    // 7. Bind tab handlers
    this._bindTabs();

    // 8. Start session via REST
    await this._startSession();
  }

  /* ── DOM Binding ────────────────────────────────────── */

  _bindDOM() {
    const ids = [
      'pbl-loading', 'tldraw-mount', 'canvas-area',
      'tab-btn-problem', 'tab-btn-ai', 'tab-btn-voice',
      'tab-problem', 'tab-ai', 'tab-voice',
      'pcc-title', 'concept-badge', 'concept-name', 'difficulty-stars',
      'problem-title', 'problem-statement', 'attempt-count', 'hint-count',
      'run-code-btn', 'submit-btn', 'hint-btn',
      'code-result-box',
      'ai-messages', 'typing-indicator', 'ai-text-input', 'ai-send-btn',
      'voice-waveform', 'speak-btn', 'voice-status',
      'toast-container',
    ];
    ids.forEach(id => {
      const key = id.replace(/-([a-z])/g, (_, c) => c.toUpperCase()); // camelCase
      this._dom[key] = document.getElementById(id);
    });
  }

  /* ── Session start ──────────────────────────────────── */

  async _startSession() {
    try {
      const resp = await fetch('/api/pbl/session/start/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this._getCsrf(),
        },
        body: JSON.stringify({
          subject:  this._subjectSlug,
          topic_id: this._topicId || undefined,
        }),
        credentials: 'include',
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      this._sessionId = data.session_id;

      // Populate problem panel if included in start response
      if (data.problem) this._populateProblem(data.problem);

      // Connect WebSocket
      this._connectWS();

      // Start event tracker
      window.pblEventTracker?.start(this._sessionId);

    } catch (err) {
      console.error('[Session] Start failed:', err);
      this._showError(`Could not start session: ${err.message}`);
      this._setLoading(false);
    }
  }

  /* ── WebSocket ──────────────────────────────────────── */

  _connectWS() {
    const ws = window.pblWS;
    if (!ws) { console.error('[Session] pblWS not found'); return; }

    ws.onConnect(() => {
      console.log('[Session] WS connected');
      this._setLoading(false);
      this._showTab('ai');
    });

    ws.onDisconnect(() => {
      console.warn('[Session] WS disconnected');
      this._showToast('Connection lost. Reconnecting…', 'warning');
    });

    ws.onError(() => {
      this._showToast('Connection error.', 'error');
    });

    // ── Message handlers ────────────────────────────────
    ws.on('problem',         (data) => this._onProblem(data));
    ws.on('ai_voice',        (data) => this._onAIVoice(data));
    ws.on('ai_text',         (data) => this._onAIText(data));
    ws.on('highlight',       (data) => this._onHighlight(data));
    ws.on('code_result',     (data) => this._onCodeResult(data));
    ws.on('mastery_update',  (data) => this._onMasteryUpdate(data));
    ws.on('session_end',     (data) => this._onSessionEnd(data));
    ws.on('error',           (data) => this._onWSError(data));
    ws.on('raw_audio',       (blob) => this._enqueueTTS(blob));
    ws.on('typing_start',    ()     => this._showTypingIndicator(true));
    ws.on('typing_stop',     ()     => this._showTypingIndicator(false));
    ws.on('hint_response',   (data) => this._onHintResponse(data));
    ws.on('state_sync',      (data) => this._onStateSync(data));
    ws.on('interim_transcript', (data) => this._onInterimTranscript(data));
    ws.on('final_transcript', (data) => this._onFinalTranscript(data));
    ws.on('ai_text_delta',   (data) => this._onAITextDelta(data));

    ws.connect(this._sessionId);
  }

  /* ── WS Message Handlers ────────────────────────────── */

  _onProblem(data) {
    this._problem = data;
    this._populateProblem(data);
    this._showTab('problem');
    this._showToast('New problem loaded!', 'success');
  }

  _populateProblem(data) {
    const d = this._dom;
    if (d.pccTitle)        d.pccTitle.textContent       = data.subject_name ?? '';
    if (d.conceptName)     d.conceptName.textContent    = data.concept_name ?? '';
    if (d.problemTitle)    d.problemTitle.textContent   = data.title ?? 'Problem';
    if (d.problemStatement) d.problemStatement.innerHTML = this._sanitize(data.statement ?? '');
    if (d.difficultyStars) d.difficultyStars.textContent = this._starsFor(data.difficulty ?? 1);
    if (d.attemptCount)    d.attemptCount.textContent   = this._attemptCount;
    if (d.hintCount)       d.hintCount.textContent      = this._hintCount;
  }

  _starsFor(level) {
    level = Math.min(5, Math.max(1, level));
    return STAR_FILLED.repeat(level) + STAR_EMPTY.repeat(5 - level);
  }

  _onAIText(data) {
    this._showTypingIndicator(false);
    if (data.text) this._appendAIMessage(data.text, 'ai');
  }

  _onAIVoice(data) {
    this._showTypingIndicator(false);
    if (data.transcript) this._appendAIMessage(data.transcript, 'ai');
    // Signal VAD that AI is about to speak (binary audio arrives shortly after)
    if (this._vadActive && this._vadState === 'sending') {
      this._vadState = 'ai_responding';
      this._setVadStatus('ai_responding');
    }
  }

  _onHighlight(data) {
    if (data.region) {
      window.pblCanvas?.applyHighlight({
        region:      data.region,
        color:       data.color ?? 'rgba(252,200,100,0.35)',
        duration_ms: data.duration_ms ?? 4000,
        reason:      data.reason ?? '',
      });
    }
  }

  _onCodeResult(data) {
    const box = this._dom.codeResultBox;
    if (!box) return;
    box.style.display = 'block';
    box.className = 'code-result-box ' + (data.success ? 'success' : 'error');
    box.textContent = data.output ?? (data.success ? 'Code ran successfully.' : 'Error in code.');

    if (data.ai_feedback) this._appendAIMessage(data.ai_feedback, 'ai');
  }

  _onMasteryUpdate(data) {
    console.log('[Session] Mastery update:', data);
    // Update the difficulty stars if level changed
    if (data.new_difficulty && this._dom.difficultyStars) {
      this._dom.difficultyStars.textContent = this._starsFor(data.new_difficulty);
    }
    if (data.message) this._showToast(data.message, 'success');
  }

  _onSessionEnd(data) {
    window.pblEventTracker?.stop();
    window.pblCanvas?.stopAutoSnapshot();

    this._appendAIMessage('Great work! This session is complete.', 'system');
    this._showToast('Session ended. Well done!', 'success');

    // Disable submit/run buttons
    ['runCodeBtn', 'submitBtn', 'hintBtn'].forEach(k => {
      if (this._dom[k]) this._dom[k].disabled = true;
    });

    if (data.summary) {
      setTimeout(() => {
        window.location.href = `/dashboard.html?session_summary=${this._sessionId}`;
      }, 3000);
    }
  }

  _onHintResponse(data) {
    this._hintCount++;
    if (this._dom.hintCount) this._dom.hintCount.textContent = this._hintCount;
    if (data.hint) this._appendAIMessage(`💡 ${data.hint}`, 'hint');
  }

  _onWSError(data) {
    console.error('[Session] WS error:', data);
    this._showToast(data.message || 'An error occurred.', 'error');
  }

  _onStateSync(data) {
    if (data?.arch_mode) this._archMode = data.arch_mode;
    const state = data?.turn_state;
    if (!state || !this._vadActive) return;

    if (state === 'listening') this._setVadStatus('listening');
    else if (state === 'transcribing' || state === 'reasoning') this._setVadStatus('sending');
    else if (state === 'speaking') {
      this._vadState = 'ai_responding';
      this._setVadStatus('ai_responding');
    }
  }

  _onInterimTranscript(data) {
    const text = data?.text?.trim();
    if (!text) return;
    const statusEl = document.getElementById('voice-status-text');
    if (statusEl) statusEl.textContent = `You: ${text}`;
  }

  _onFinalTranscript(data) {
    const text = data?.text?.trim();
    if (!text) return;
    this._appendAIMessage(text, 'user');
  }

  _onAITextDelta(data) {
    const text = data?.text?.trim();
    if (!text) return;
    if (!data?.is_final) {
      const statusEl = document.getElementById('voice-status-text');
      if (statusEl) statusEl.textContent = `AI: ${text}`;
    }
  }

  /* ── Action buttons ─────────────────────────────────── */

  _bindButtons() {
    // Run code
    this._dom.runCodeBtn?.addEventListener('click', () => {
      const code = window.pblCanvas?.getActiveCode() || window.pblCanvas?.getLatestCode();
      if (!code?.trim()) { this._showToast('No code to run.', 'warning'); return; }
      this.runCode(code);
    });

    // Submit
    this._dom.submitBtn?.addEventListener('click', async () => {
      const code = window.pblCanvas?.getActiveCode() || window.pblCanvas?.getLatestCode();
      if (!code?.trim()) { this._showToast('Write some code first!', 'warning'); return; }
      this._attemptCount++;
      if (this._dom.attemptCount) this._dom.attemptCount.textContent = this._attemptCount;
      window.pblEventTracker?.onCodeSubmitted(code);

      // Capture canvas snapshot for context
      await window.pblCanvas?.captureAndSend('submit');

      window.pblWS?.send('submit_solution', {
        code,
        session_id: this._sessionId,
        attempt_number: this._attemptCount,
      });
      this._showTypingIndicator(true);
    });

    // Hint
    this._dom.hintBtn?.addEventListener('click', async () => {
      window.pblEventTracker?.onHintRequested();
      const code = window.pblCanvas?.getActiveCode() || '';
      await window.pblCanvas?.captureAndSend('hint');
      window.pblWS?.send('request_hint', {
        session_id: this._sessionId,
        current_code: code,
        hint_number: this._hintCount + 1,
      });
      this._showTypingIndicator(true);
    });

    // AI text send
    this._dom.aiSendBtn?.addEventListener('click', () => this._sendTextMessage());
    this._dom.aiTextInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this._sendTextMessage(); }
    });

    // Voice session toggle (persistent VAD — one tap to start, one to stop)
    this._dom.speakBtn?.addEventListener('click', () => {
      if (this._vadActive) this._endVoiceSession();
      else this._startVoiceSession();
    });
  }

  _sendTextMessage() {
    const input = this._dom.aiTextInput;
    const text  = input?.value?.trim();
    if (!text) return;
    input.value = '';

    this._appendAIMessage(text, 'user');
    this._callAIChat(text);
  }

  /**
   * Sends a conversational message to the AI tutor via REST.
   * Canvas state and inactivity time are attached automatically.
   * @param {string} query - The student's message
   * @param {string} [speechTranscript=''] - Raw STT transcript if voice-originated
   */
  async _callAIChat(query, speechTranscript = '') {
    this._showTypingIndicator(true);
    const canvas_state = window.pblCanvas?.getStructuredState() ?? null;
    const time_since_last_action_seconds = window.pblEventTracker?.getTimeSinceLastAction() ?? 0;
    const code = window.pblCanvas?.getActiveCode() ?? '';
    try {
      const resp = await fetch('/api/ai/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this._getCsrf(),
        },
        credentials: 'include',
        body: JSON.stringify({
          query,
          session_id: this._sessionId,
          pbl_session_id: this._sessionId,
          canvas_state,
          code,
          speech_transcript: speechTranscript,
          time_since_last_action_seconds,
        }),
      });
      this._showTypingIndicator(false);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        this._appendAIMessage(`Error: ${err.error || resp.status}`, 'ai');
        return;
      }
      const data = await resp.json();
      this._appendAIMessage(data.response ?? '…', 'ai');
    } catch (err) {
      this._showTypingIndicator(false);
      console.error('[Session] AI chat error:', err);
      this._appendAIMessage('Could not reach the AI tutor. Please try again.', 'ai');
    }
  }

  /** Called by code block Run icon */
  runCode(code) {
    if (!code?.trim()) return;
    window.pblEventTracker?.onCodeRun(code);
    window.pblWS?.send('run_code', {
      session_id: this._sessionId,
      code,
    });
    // Show running state
    const box = this._dom.codeResultBox;
    if (box) {
      box.style.display = 'block';
      box.className = 'code-result-box running';
      box.textContent = 'Running…';
    }
  }

  /* ── Tab switching ──────────────────────────────────── */

  _bindTabs() {
    ['problem', 'ai', 'voice'].forEach(tab => {
      const btn = this._dom[`tabBtn${tab.charAt(0).toUpperCase() + tab.slice(1)}`];
      btn?.addEventListener('click', () => {
        window.pblEventTracker?.onTabSwitch(tab);
        this._showTab(tab);
      });
    });
  }

  _showTab(name) {
    this._currentTab = name;
    ['problem', 'ai', 'voice'].forEach(tab => {
      const panelKey = `tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`;
      const btnKey   = `tabBtn${tab.charAt(0).toUpperCase() + tab.slice(1)}`;
      this._dom[panelKey]?.classList.toggle('active',  tab === name);
      this._dom[btnKey]  ?.classList.toggle('active',  tab === name);
    });
  }

  /* ── AI message feed ────────────────────────────────── */

  /**
   * @param {string} text
   * @param {'ai'|'user'|'hint'|'system'} role
   */
  _appendAIMessage(text, role = 'ai') {
    const container = this._dom.aiMessages;
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = `ai-message ${role}`;

    const content = document.createElement('div');
    content.className = 'ai-message-content';
    content.innerHTML = this._formatMessage(text);

    bubble.appendChild(content);
    container.appendChild(bubble);

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;

    // Auto-switch to AI tab if a new AI message arrives while on voice tab
    if (role === 'ai' && this._currentTab === 'problem') {
      this._showTab('ai');
    }
  }

  _formatMessage(text) {
    // Escape HTML then apply basic Markdown-like formatting
    const escaped = this._sanitize(text);
    return escaped
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  _showTypingIndicator(visible) {
    const el = this._dom.typingIndicator;
    if (!el) return;
    el.style.display = visible ? 'flex' : 'none';
    if (visible) {
      const container = this._dom.aiMessages;
      if (container) container.scrollTop = container.scrollHeight;
    }
  }

  /* ── Voice Session — Persistent VAD ────────────────── */
  /*
   * Design: one tap → mic stays open the whole session.
   * Web Audio AnalyserNode measures RMS every animation frame.
   * State machine: idle → speaking → sending → ai_responding → idle
   * Student can interrupt AI mid-sentence at any time.
   */

  async _startVoiceSession() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 },
      });
      this._vadStream = stream;
      this._vadActive = true;
      this._vadState  = 'idle';
      this._vadSilenceStart = null;

      // Shared AudioContext for both VAD analysis and waveform drawing
      this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      this._analyser = this._audioCtx.createAnalyser();
      this._analyser.fftSize = 512;
      this._analyser.smoothingTimeConstant = 0.3;
      const source = this._audioCtx.createMediaStreamSource(stream);
      source.connect(this._analyser);

      this._dom.speakBtn?.classList.add('vad-active');
      this._setVadStatus('listening');
      this._showTab('voice');
      this._vadLoop();

      window.pblEventTracker?.onVoiceEvent('session_start');
      console.log('[Session] Voice session started');
    } catch (err) {
      this._showToast('Microphone access denied.', 'error');
      console.error('[Session] getUserMedia error:', err);
    }
  }

  _endVoiceSession() {
    this._vadActive = false;
    if (this._vadAnimFrame) { cancelAnimationFrame(this._vadAnimFrame); this._vadAnimFrame = null; }

    // Stop any in-flight MediaRecorder
    if (this._mediaRecorder && this._mediaRecorder.state !== 'inactive') {
      this._mediaRecorder.stop();
    }
    this._mediaRecorder = null;
    this._isRecording   = false;

    // Release the persistent mic stream
    if (this._vadStream) { this._vadStream.getTracks().forEach(t => t.stop()); this._vadStream = null; }

    // Close AudioContext
    if (this._audioCtx) { this._audioCtx.close().catch(() => {}); this._audioCtx = null; }
    this._analyser = null;

    // Clear waveform canvas
    const canvas = this._dom.voiceWaveform;
    if (canvas) { const c = canvas.getContext('2d'); c.clearRect(0, 0, canvas.width, canvas.height); }

    this._vadState = 'idle';
    this._dom.speakBtn?.classList.remove('vad-active');
    this._setVadStatus('off');
    window.pblEventTracker?.onVoiceEvent('session_end');
    console.log('[Session] Voice session ended');
  }

  _vadLoop() {
    if (!this._vadActive) return;
    this._vadAnimFrame = requestAnimationFrame(() => this._vadLoop());

    // Draw live waveform every frame
    this._drawWaveformFrame();

    if (!this._analyser) return;

    // Calculate RMS (root-mean-square) of audio signal
    const buf = new Uint8Array(this._analyser.frequencyBinCount);
    this._analyser.getByteTimeDomainData(buf);
    let sumSq = 0;
    for (let i = 0; i < buf.length; i++) {
      const n = (buf[i] - 128) / 128;
      sumSq += n * n;
    }
    const rms = Math.sqrt(sumSq / buf.length);

    const now          = performance.now();
    const SPEECH_START = 0.030;  // RMS to start recording (raised from 0.015 — rejects fan/keyboard)
    const SPEECH_STOP  = 0.015;  // RMS to start silence timer
    const SPEECH_INTR  = 0.035;  // RMS to interrupt AI mid-speech
    const SILENCE_MS   = 1500;   // ms of silence = utterance complete
    const MIN_SPEECH_MS = 600;   // minimum speaking duration before sending

    if (this._vadState === 'idle') {
      if (rms > SPEECH_START) this._beginUtterance();

    } else if (this._vadState === 'speaking') {
      if (rms < SPEECH_STOP) {
        if (!this._vadSilenceStart) this._vadSilenceStart = now;
        else if (now - this._vadSilenceStart > SILENCE_MS) {
          // Only send if student actually spoke for at least MIN_SPEECH_MS
          const spokenMs = this._utteranceStart ? now - this._utteranceStart : 0;
          if (spokenMs >= MIN_SPEECH_MS) {
            this._endUtterance();
          } else {
            // Too short — background noise burst, abort silently
            this._abortUtterance();
          }
        }
      } else {
        this._vadSilenceStart = null; // still speaking — reset timer
      }

    } else if (this._vadState === 'ai_responding') {
      // Student speaks while AI is responding → interrupt and listen
      if (rms > SPEECH_INTR) {
        this._interruptAI();
        this._beginUtterance();
      }
    }
    // 'sending' state: waiting for server — don't react to audio
  }

  _beginUtterance() {
    if (!this._vadStream) return;
    this._audioChunks = [];
    this._voiceTurnId = this._nextVoiceTurnId();
    const isNewMode = this._archMode === 'new';
    const voiceContext = this._buildVoiceContext();
    window.pblWS?.send('voice_context', { payload: voiceContext, turn_id: this._voiceTurnId });
    if (isNewMode) {
      window.pblWS?.send('voice_start', { turn_id: this._voiceTurnId });
    }
    this._utteranceStart = performance.now();
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus' : 'audio/webm';
    this._mediaRecorder = new MediaRecorder(this._vadStream, { mimeType });
    this._mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this._audioChunks.push(e.data);
        if (isNewMode) {
          window.pblWS?.sendBinary(e.data);
        }
      }
    };
    this._mediaRecorder.onstop = () => {
      const turnId = this._voiceTurnId;
      this._voiceTurnId = null;
      if (isNewMode) {
        window.pblWS?.send('voice_end', { turn_id: turnId });
      } else {
        const blob = new Blob(this._audioChunks, { type: 'audio/webm' });
        this._sendAudioBlob(blob);
      }
    };
    this._mediaRecorder.start(250);
    this._isRecording     = true;
    this._vadState        = 'speaking';
    this._vadSilenceStart = null;
    this._setVadStatus('speaking');
    window.pblEventTracker?.onVoiceEvent('utterance_start');
  }

  /** Abort a too-short utterance (noise burst) without sending. */
  _abortUtterance() {
    if (this._mediaRecorder && this._mediaRecorder.state !== 'inactive') {
      // Override onstop so the blob is silently discarded
      this._mediaRecorder.onstop = () => {};
      this._mediaRecorder.stop();
    }
    this._isRecording     = false;
    this._utteranceStart  = null;
    this._vadState        = 'idle';
    this._vadSilenceStart = null;
    this._setVadStatus('listening');
  }

  _endUtterance() {
    if (this._mediaRecorder && this._mediaRecorder.state !== 'inactive') {
      this._mediaRecorder.stop();
    }
    this._isRecording     = false;
    this._vadState        = 'sending';
    this._vadSilenceStart = null;
    this._setVadStatus('sending');
    window.pblEventTracker?.onVoiceEvent('utterance_end');
  }

  _interruptAI() {
    // Drain TTS queue and stop current playback immediately
    this._ttsQueue = [];
    if (this._currentAudio) {
      this._currentAudio.pause();
      if (this._currentAudio._url) URL.revokeObjectURL(this._currentAudio._url);
      this._currentAudio = null;
    }
    this._ttsPlaying = false;
    window.pblWS?.send('interrupt', { turn_id: this._voiceTurnId || null });
    console.log('[Session] AI interrupted by student');
  }

  _nextVoiceTurnId() {
    return `${this._sessionId}:voice:${Date.now()}`;
  }

  _sendAudioBlob(blob) {
    if (!window.pblWS?.isConnected()) {
      this._showToast('Not connected.', 'error');
      // If VAD active, go back to listening so user can try again
      if (this._vadActive) { this._vadState = 'idle'; this._setVadStatus('listening'); }
      return;
    }

    // Keep voice and text tutoring paths aligned by sending rich context
    // immediately before the binary utterance.
    const voiceContext = this._buildVoiceContext();
    window.pblWS.send('voice_context', {
      payload: voiceContext,
    });

    window.pblWS.sendBinary(blob);
    this._showTypingIndicator(true);
    // Note: DO NOT call interrupt() here — we just sent new audio, backend handles it
  }

  _buildVoiceContext() {
    const canvas_state = window.pblCanvas?.getStructuredState() ?? null;
    const current_code = window.pblCanvas?.getActiveCode()
      || window.pblCanvas?.getLatestCode()
      || '';
    const time_since_last_action_seconds = window.pblEventTracker?.getTimeSinceLastAction() ?? 0;

    return {
      canvas_state,
      current_code,
      time_since_last_action_seconds,
      session_id: this._sessionId,
      problem_title: this._problem?.title ?? '',
      problem_statement: this._problem?.statement ?? '',
    };
  }

  /**
   * Updates the voice status indicator and button appearance.
   * @param {'off'|'listening'|'speaking'|'sending'|'ai_responding'} state
   */
  _setVadStatus(state) {
    const STATUS = {
      off:           { text: 'Tap to start voice session', cls: 'idle'        },
      listening:     { text: 'Listening... 🎙️',            cls: 'listening'   },
      speaking:      { text: 'Hearing you...',              cls: 'speaking'    },
      sending:       { text: 'Got it, thinking...',         cls: 'sending'     },
      ai_responding: { text: 'AI is responding...',         cls: 'responding'  },
    };
    const cfg = STATUS[state] ?? STATUS.off;
    const el  = this._dom.voiceStatus;
    if (el) el.className = `voice-status ${cfg.cls}`;
    const txt = document.getElementById('voice-status-text');
    if (txt) txt.textContent = cfg.text;
  }

  /* ── Waveform visualizer ────────────────────────────── */

  /** Single-frame waveform draw — called by _vadLoop every rAF tick. */
  _drawWaveformFrame() {
    const canvas = this._dom.voiceWaveform;
    if (!canvas || !this._analyser) return;
    try {
      const ctx  = canvas.getContext('2d');
      const data = new Uint8Array(this._analyser.frequencyBinCount);
      this._analyser.getByteTimeDomainData(data);
      const W = canvas.width, H = canvas.height;
      ctx.clearRect(0, 0, W, H);
      ctx.beginPath();
      const sliceW = W / data.length;
      let x = 0;
      for (let i = 0; i < data.length; i++) {
        const v = data[i] / 128;
        const y = (v * H) / 2;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        x += sliceW;
      }
      // Waveform colour reflects current state
      const COLORS = {
        idle: '#7c6af7', speaking: '#22c55e',
        sending: '#f59e0b', ai_responding: '#3b82f6',
      };
      ctx.strokeStyle = COLORS[this._vadState] ?? '#7c6af7';
      ctx.lineWidth = 2;
      ctx.stroke();
    } catch (_) { /* non-fatal */ }
  }

  /* ── TTS Playback ───────────────────────────────────── */

  _enqueueTTS(payload) {
    this._ttsQueue.push(payload);
    if (!this._ttsPlaying) this._playNextTTS();
  }

  _coerceAudioBlob(payload) {
    if (!payload) return null;
    if (payload instanceof Blob) return payload;
    if (payload instanceof ArrayBuffer) return new Blob([payload], { type: 'audio/mpeg' });
    if (payload?.buffer instanceof ArrayBuffer) return new Blob([payload.buffer], { type: 'audio/mpeg' });
    return null;
  }

  async _playNextTTS() {
    if (this._ttsQueue.length === 0) {
      this._ttsPlaying   = false;
      this._currentAudio = null;
      // VAD: AI finished speaking → return mic to listening state
      if (this._vadActive && this._vadState === 'ai_responding') {
        this._vadState = 'idle';
        this._setVadStatus('listening');
      }
      return;
    }
    this._ttsPlaying = true;

    // VAD: ensure state shows AI is speaking
    if (this._vadActive && this._vadState !== 'ai_responding') {
      this._vadState = 'ai_responding';
      this._setVadStatus('ai_responding');
    }

    const payload = this._ttsQueue.shift();
    const blob = this._coerceAudioBlob(payload);
    if (!blob) {
      console.error('[Session] Invalid TTS payload format; skipping chunk');
      this._ttsPlaying = false;
      if (this._vadActive) {
        this._vadState = 'idle';
        this._setVadStatus('listening');
      }
      this._playNextTTS();
      return;
    }
    const url   = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio._url  = url;          // store for cleanup on interrupt
    this._currentAudio = audio;

    audio.onended = () => {
      URL.revokeObjectURL(url);
      this._currentAudio = null;
      this._playNextTTS();
    };
    audio.onerror = (e) => {
      console.error('[Session] TTS playback error:', e);
      URL.revokeObjectURL(url);
      this._currentAudio = null;
      this._playNextTTS();
    };

    try { await audio.play(); }
    catch (e) { console.error('[Session] Audio play blocked:', e); this._playNextTTS(); }
  }

  /* ── Loading / Error states ─────────────────────────── */

  _setLoading(visible) {
    if (this._dom.pblLoading) {
      this._dom.pblLoading.style.display = visible ? 'flex' : 'none';
    }
  }

  _showError(msg) {
    this._setLoading(false);
    this._showToast(msg, 'error');
    console.error('[Session]', msg);
  }

  /* ── Toast notifications ────────────────────────────── */

  /** @param {string} message @param {'success'|'error'|'warning'|'info'} type */
  _showToast(message, type = 'info') {
    const container = this._dom.toastContainer || document.getElementById('toast-container');
    if (!container) { console.warn('[Toast]', message); return; }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => toast.classList.add('show'));

    // Remove after 3.5s
    setTimeout(() => {
      toast.classList.remove('show');
      toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    }, 3500);
  }

  /* ── Utility ────────────────────────────────────────── */

  _getCsrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  }

  /**
   * Basic HTML sanitizer — strips tags from user content.
   * Only called on AI responses (trusted), NOT on raw user input
   * that would be inserted into the DOM directly.
   */
  _sanitize(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// ── Boot on DOMContentLoaded ─────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  window.pblSession = new PBLSession();
  window.pblSession.init();
});
