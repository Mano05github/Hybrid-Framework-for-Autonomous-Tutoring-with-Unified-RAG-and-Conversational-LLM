/**
 * pbl-canvas.js — Tldraw + Monaco Code Block Integration
 *
 * Responsibilities:
 *  - Mount Tldraw on #tldraw-mount
 *  - Provide toolbar tool switching
 *  - Insert draggable Monaco code block widgets onto the canvas
 *  - captureSnapshot() → Base64 PNG → sends canvas_snapshot via WS
 *  - applyHighlight({region, color, duration_ms}) → renders translucent overlay
 *  - getActiveCode() → returns code from the most recently focused Monaco block
 */

class PBLCanvas {
  constructor() {
    this._editor          = null;   // Tldraw editor instance (if Tldraw API available)
    this._codeBlocks      = [];     // list of {id, el, iframeWin, code}
    this._activeCodeId    = null;   // id of currently focused Monaco block
    this._snapshotTimer   = null;
    this._canvasEl        = document.getElementById('canvas-area');
    this._mountEl         = document.getElementById('tldraw-mount');
    this._highlightEl     = document.getElementById('highlight-container');
    this._pendingHighlights = [];
    this._currentTool     = 'draw';
    this._strokeColor     = '#63b3ed';

    // Fallback canvas state (used when TLDraw editor is unavailable)
    this._fallbackCanvas    = null;
    this._fallbackCtx       = null;
    this._isFallbackDrawing = false;
    this._fallbackLastPoint = null;
    this._fallbackHistory   = [];
    this._fallbackRedoStack = [];

    // Listen for messages from Monaco iframe
    window.addEventListener('message', (e) => this._handleIframeMessage(e));
  }

  /* ── Initialisation ─────────────────────────────────── */

  init() {
    this._mountTldraw();
    this._bindToolbarButtons();
    this._startAutoSnapshot();
  }

  _mountTldraw() {
    // Tldraw v2 UMD exposes window.Tldraw
    if (window.Tldraw) {
      try {
        const container = this._mountEl;
        // Tldraw v2: mount via Tldraw.createTLStore + mount API
        // We use a lightweight wrapper that creates a Tldraw app
        const tldrawRoot = document.createElement('div');
        tldrawRoot.style.cssText = 'width:100%;height:100%;';
        container.appendChild(tldrawRoot);

        // Tldraw v2 React-based: use script injection approach
        // since we're not in a React component context here, we use
        // the lower-level createTLStore + TldrawEditor approach
        if (window.ReactDOM && window.React && window.Tldraw) {
          this._mountWithReact(tldrawRoot);
        } else {
          // Fallback: plain canvas grid background without Tldraw SDK
          this._mountFallbackCanvas(container);
        }
      } catch (err) {
        console.warn('[Canvas] Tldraw mount failed, using fallback:', err);
        this._mountFallbackCanvas(this._mountEl);
      }
    } else {
      this._mountFallbackCanvas(this._mountEl);
    }
  }

  _mountWithReact(container) {
    const { React, ReactDOM, Tldraw } = window;

    const App = () => {
      const editorRef = React.useRef(null);
      React.useEffect(() => {
        if (editorRef.current) {
          // Store reference so other methods can access the editor
          window._tldrawEditor = editorRef.current;
          this._editor = editorRef.current;
          console.log('[Canvas] Tldraw editor ready');
        }
      }, []);
      return React.createElement(Tldraw.Tldraw, {
        onMount: (editor) => {
          window._tldrawEditor = editor;
          this._editor = editor;
          console.log('[Canvas] Tldraw mounted ✅');
        },
        hideUi: false,
        autoFocus: true,
      });
    };

    // Tldraw v2 needs React 18
    if (ReactDOM.createRoot) {
      ReactDOM.createRoot(container).render(React.createElement(App));
    } else {
      ReactDOM.render(React.createElement(App), container);
    }
  }

  _mountFallbackCanvas(container) {
    // Lightweight dot-grid canvas when Tldraw is unavailable
    container.innerHTML = '';
    const canvas = document.createElement('canvas');
    canvas.id = 'fallback-canvas';
    canvas.style.cssText = 'width:100%;height:100%;cursor:crosshair;';
    container.appendChild(canvas);

    const resize = () => {
      canvas.width  = container.offsetWidth;
      canvas.height = container.offsetHeight;
      this._drawGrid(canvas);
    };
    resize();
    new ResizeObserver(resize).observe(container);

    this._fallbackCanvas = canvas;
    this._fallbackCtx = canvas.getContext('2d');
    this._fallbackHistory = [];
    this._fallbackRedoStack = [];

    this._bindFallbackPointerEvents();
    this._setActiveTool(this._currentTool);
  }

  _drawGrid(canvas) {
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#111113';
    ctx.fillRect(0, 0, W, H);
    const STEP = 24;
    ctx.fillStyle = 'rgba(255,255,255,0.06)';
    for (let x = 0; x < W; x += STEP) {
      for (let y = 0; y < H; y += STEP) {
        ctx.fillRect(x, y, 1.5, 1.5);
      }
    }
  }

  _bindFallbackPointerEvents() {
    const canvas = this._fallbackCanvas;
    if (!canvas) return;

    const start = (e) => {
      if (!['draw', 'eraser'].includes(this._currentTool)) return;
      const point = this._pointFromEvent(e, canvas);
      if (!point) return;

      this._pushFallbackSnapshot();
      this._isFallbackDrawing = true;
      this._fallbackLastPoint = point;
      e.preventDefault();
    };

    const move = (e) => {
      if (!this._isFallbackDrawing || !this._fallbackLastPoint) return;
      const point = this._pointFromEvent(e, canvas);
      if (!point) return;

      this._drawFallbackSegment(this._fallbackLastPoint, point);
      this._fallbackLastPoint = point;
      window.pblEventTracker?.onCanvasDraw();
      e.preventDefault();
    };

    const end = () => {
      this._isFallbackDrawing = false;
      this._fallbackLastPoint = null;
    };

    canvas.addEventListener('mousedown', start);
    canvas.addEventListener('mousemove', move);
    canvas.addEventListener('mouseup', end);
    canvas.addEventListener('mouseleave', end);

    canvas.addEventListener('touchstart', start, { passive: false });
    canvas.addEventListener('touchmove', move, { passive: false });
    canvas.addEventListener('touchend', end, { passive: true });
    canvas.addEventListener('touchcancel', end, { passive: true });
  }

  _pointFromEvent(e, canvas) {
    const rect = canvas.getBoundingClientRect();
    let clientX = null;
    let clientY = null;

    if (e.touches && e.touches[0]) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else if (typeof e.clientX === 'number' && typeof e.clientY === 'number') {
      clientX = e.clientX;
      clientY = e.clientY;
    }

    if (clientX === null || clientY === null) return null;
    return { x: clientX - rect.left, y: clientY - rect.top };
  }

  _drawFallbackSegment(from, to) {
    if (!this._fallbackCtx) return;
    const ctx = this._fallbackCtx;

    ctx.save();
    if (this._currentTool === 'eraser') {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.lineWidth = 18;
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = this._strokeColor;
      ctx.lineWidth = 3;
    }
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
    ctx.restore();
  }

  _pushFallbackSnapshot() {
    if (!this._fallbackCtx || !this._fallbackCanvas) return;
    const img = this._fallbackCtx.getImageData(0, 0, this._fallbackCanvas.width, this._fallbackCanvas.height);
    this._fallbackHistory.push(img);
    if (this._fallbackHistory.length > 100) this._fallbackHistory.shift();
    this._fallbackRedoStack = [];
  }

  _fallbackUndo() {
    if (!this._fallbackCtx || !this._fallbackCanvas || this._fallbackHistory.length === 0) return;
    const current = this._fallbackCtx.getImageData(0, 0, this._fallbackCanvas.width, this._fallbackCanvas.height);
    const previous = this._fallbackHistory.pop();
    this._fallbackRedoStack.push(current);
    this._fallbackCtx.putImageData(previous, 0, 0);
  }

  _fallbackRedo() {
    if (!this._fallbackCtx || !this._fallbackCanvas || this._fallbackRedoStack.length === 0) return;
    const current = this._fallbackCtx.getImageData(0, 0, this._fallbackCanvas.width, this._fallbackCanvas.height);
    const next = this._fallbackRedoStack.pop();
    this._fallbackHistory.push(current);
    this._fallbackCtx.putImageData(next, 0, 0);
  }

  _clearFallbackCanvas() {
    if (!this._fallbackCanvas || !this._fallbackCtx) return;
    this._pushFallbackSnapshot();
    this._drawGrid(this._fallbackCanvas);
  }

  _setActiveTool(toolName) {
    this._currentTool = toolName;

    const idByTool = {
      draw: 'tool-draw',
      eraser: 'tool-eraser',
      text: 'tool-text',
      arrow: 'tool-arrow',
      select: 'tool-select',
    };

    Object.values(idByTool).forEach((id) => document.getElementById(id)?.classList.remove('active'));
    document.getElementById(idByTool[toolName])?.classList.add('active');

    const cursorByTool = {
      draw: 'crosshair',
      eraser: 'cell',
      text: 'text',
      arrow: 'crosshair',
      select: 'default',
    };
    if (this._fallbackCanvas) {
      this._fallbackCanvas.style.cursor = cursorByTool[toolName] ?? 'crosshair';
    }

    if (this._editor) {
      const tlTool = {
        draw: 'draw',
        eraser: 'eraser',
        text: 'text',
        arrow: 'arrow',
        select: 'select',
      }[toolName];
      if (tlTool) {
        try { this._editor.setCurrentTool(tlTool); } catch (e) {}
      }
    }
  }

  undo() {
    if (this._editor) {
      try { this._editor.undo(); return; } catch (e) {}
    }
    this._fallbackUndo();
  }

  redo() {
    if (this._editor) {
      try { this._editor.redo(); return; } catch (e) {}
    }
    this._fallbackRedo();
  }

  /* ── Toolbar tool switching ─────────────────────────── */

  _bindToolbarButtons() {
    const toolMap = {
      'tool-draw':   'draw',
      'tool-eraser': 'eraser',
      'tool-text':   'text',
      'tool-arrow':  'arrow',
      'tool-select': 'select',
    };

    Object.entries(toolMap).forEach(([btnId, toolName]) => {
      const btn = document.getElementById(btnId);
      if (!btn) return;
      btn.addEventListener('click', () => {
        this._setActiveTool(toolName);
      });
    });

    document.getElementById('pen-color-picker')?.addEventListener('input', (e) => {
      this._strokeColor = e.target.value || '#63b3ed';
      // Selecting a color implies drawing mode for immediate use.
      if (this._currentTool === 'eraser') {
        this._setActiveTool('draw');
      }
    });

    // Undo/Redo
    document.getElementById('undo-btn')?.addEventListener('click', () => {
      this.undo();
    });
    document.getElementById('redo-btn')?.addEventListener('click', () => {
      this.redo();
    });

    // Clear canvas
    document.getElementById('clear-canvas-btn')?.addEventListener('click', () => {
      if (!confirm('Clear the canvas? This cannot be undone.')) return;
      if (this._editor) {
        try {
          const shapeIds = [...(this._editor.getCurrentPageShapeIds?.() ?? [])];
          if (shapeIds.length > 0) this._editor.deleteShapes(shapeIds);
        } catch(e) {}
      } else {
        this._clearFallbackCanvas();
      }
      // Also remove all code blocks
      this._codeBlocks.forEach(b => b.el.remove());
      this._codeBlocks = [];
      this._activeCodeId = null;
    });

    // Add Code Block
    document.getElementById('add-code-block-btn')?.addEventListener('click', () => {
      this.addCodeBlock();
    });

    // Analyze canvas (Voice tab button)
    document.getElementById('analyze-canvas-btn')?.addEventListener('click', () => {
      this.captureAndSend('manual');
    });
  }

  /* ── Code Block Management ──────────────────────────── */

  /**
   * Inserts a draggable Monaco code block over the canvas.
   * Monaco is loaded inside an iframe for isolation.
   */
  addCodeBlock(startX = null, startY = null) {
    const canvasRect = this._canvasEl.getBoundingClientRect();
    const id = 'cb-' + Date.now();

    // Default position: center-ish of visible canvas area
    const x = startX ?? (canvasRect.width  * 0.25 + Math.random() * 40 - 20);
    const y = startY ?? (canvasRect.height * 0.15 + Math.random() * 40 - 20);

    // Wrapper div (positioned absolute over canvas)
    const wrapper = document.createElement('div');
    wrapper.className = 'monaco-block-wrapper';
    wrapper.id = id;
    wrapper.style.cssText = `left:${x}px; top:${y}px; width:420px; height:220px;`;

    // Header bar
    const header = document.createElement('div');
    header.className = 'monaco-block-header';
    header.innerHTML = `
      <span>⌨ Python Code</span>
      <span style="margin-left:auto; display:flex; gap:6px; align-items:center;">
        <span class="run-icon" data-id="${id}" title="Run code">▶ Run</span>
        <span class="close-icon" data-id="${id}" title="Remove">✕</span>
      </span>
    `;

    // Monaco iframe
    const iframe = document.createElement('iframe');
    iframe.className = 'monaco-block-iframe';
    iframe.title = 'Code Editor';
    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
    iframe.srcdoc = this._monacoIframeHTML(id);

    wrapper.appendChild(header);
    wrapper.appendChild(iframe);
    this._canvasEl.appendChild(wrapper);

    // Store reference
    const block = { id, el: wrapper, iframe, code: '' };
    this._codeBlocks.push(block);
    this._activeCodeId = id;

    // Make draggable
    this._makeDraggable(wrapper, header);

    // Header button events (run + close)
    header.querySelector('.run-icon').addEventListener('click', (e) => {
      e.stopPropagation();
      const b = this._blockById(id);
      if (b) window.pblSession?.runCode(b.code);
    });
    header.querySelector('.close-icon').addEventListener('click', (e) => {
      e.stopPropagation();
      wrapper.remove();
      this._codeBlocks = this._codeBlocks.filter(b => b.id !== id);
      if (this._activeCodeId === id) this._activeCodeId = this._codeBlocks[this._codeBlocks.length - 1]?.id ?? null;
    });

    // When iframe receives focus → mark as active block
    iframe.addEventListener('focus', () => { this._activeCodeId = id; });

    console.log('[Canvas] Code block added:', id);
    window.pblEventTracker?.onCodeBlockAdded(id);
    return id;
  }

  _monacoIframeHTML(blockId) {
    return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body,#editor-container { width:100%; height:100%; background:#1e1e1e; overflow:hidden; }
</style>
</head>
<body>
<div id="editor-container"></div>
<script>
  const BLOCK_ID = '${blockId}';
  // Load Monaco from CDN
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.js';
  script.onload = () => {
    require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs' } });
    require(['vs/editor/editor.main'], () => {
      const editor = monaco.editor.create(document.getElementById('editor-container'), {
        value: '# Write your Python code here\\n',
        language: 'python',
        theme: 'vs-dark',
        fontSize: 13,
        fontFamily: "'Fira Code', 'Cascadia Code', monospace",
        fontLigatures: true,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        lineNumbers: 'on',
        renderLineHighlight: 'line',
        padding: { top: 8, bottom: 8 },
        automaticLayout: true,
      });

      // Send code changes to parent window
      editor.onDidChangeModelContent(() => {
        const code = editor.getValue();
        parent.postMessage({ type: 'code_change', blockId: BLOCK_ID, content: code }, '*');
      });

      // Prevent Tldraw/parent keyboard shortcuts from firing inside editor
      editor.getDomNode()?.addEventListener('keydown', (e) => { e.stopPropagation(); }, true);
      editor.getDomNode()?.addEventListener('keyup',   (e) => { e.stopPropagation(); }, true);

      // Expose editor for external reads
      window._editor = editor;

      // Listen for set-value commands from parent
      window.addEventListener('message', (e) => {
        if (e.data?.type === 'set_code' && e.data?.blockId === BLOCK_ID) {
          editor.setValue(e.data.code);
        }
        if (e.data?.type === 'get_code' && e.data?.blockId === BLOCK_ID) {
          parent.postMessage({ type: 'code_value', blockId: BLOCK_ID, content: editor.getValue() }, '*');
        }
      });
    });
  };
  document.head.appendChild(script);
<\/script>
</body>
</html>`;
  }

  _makeDraggable(wrapper, handle) {
    let ox = 0, oy = 0, dragging = false;
    handle.style.cursor = 'move';
    handle.addEventListener('mousedown', (e) => {
      if (e.target.closest('.run-icon, .close-icon')) return;
      dragging = true;
      const rect = wrapper.getBoundingClientRect();
      const parentRect = this._canvasEl.getBoundingClientRect();
      ox = e.clientX - (rect.left - parentRect.left);
      oy = e.clientY - (rect.top  - parentRect.top);
      e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const parentRect = this._canvasEl.getBoundingClientRect();
      wrapper.style.left = `${e.clientX - parentRect.left - ox}px`;
      wrapper.style.top  = `${e.clientY - parentRect.top  - oy}px`;
    });
    document.addEventListener('mouseup', () => { dragging = false; });
  }

  _handleIframeMessage(event) {
    const { type, blockId, content } = event.data || {};
    if (!type || !blockId) return;

    if (type === 'code_change') {
      const block = this._blockById(blockId);
      if (block) {
        block.code = content;
        this._activeCodeId = blockId;
        window.pblEventTracker?.onCodeChange(content);
      }
    }
    if (type === 'code_value') {
      const block = this._blockById(blockId);
      if (block) block.code = content;
    }
  }

  _blockById(id) {
    return this._codeBlocks.find(b => b.id === id) ?? null;
  }

  /* ── Code access ────────────────────────────────────── */

  /** Returns code from the active (last-focused) Monaco block */
  getActiveCode() {
    if (!this._activeCodeId) return '';
    const block = this._blockById(this._activeCodeId);
    return block?.code ?? '';
  }

  /** Returns code from the most recently created block */
  getLatestCode() {
    if (this._codeBlocks.length === 0) return '';
    return this._codeBlocks[this._codeBlocks.length - 1].code;
  }

  /**
   * Returns a structured JSON snapshot of the canvas for the AI tutor.
   * The AI only observes — it never writes to the canvas.
   * @returns {{ text_blocks: string[], drawings: string[], notes: string[] }}
   */
  getStructuredState() {
    const text_blocks = this._codeBlocks
      .map(b => b.code)
      .filter(c => c && c.trim().length > 0);
    const notes = [];
    const drawings = [];
    if (this._editor) {
      try {
        const shapes = this._editor.getCurrentPageShapes();
        shapes.forEach(shape => {
          if (shape.type === 'text' || shape.type === 'note') {
            const t = shape.props?.text?.trim();
            if (t) notes.push(t);
          } else if (shape.type === 'draw') {
            drawings.push('freehand drawing');
          } else if (shape.type === 'arrow') {
            drawings.push('arrow');
          } else if (shape.type === 'geo') {
            drawings.push(shape.props?.geo ?? 'shape');
          }
        });
      } catch (e) {
        // TLDraw editor not available (fallback canvas active)
      }
    }
    return { text_blocks, drawings, notes };
  }

  /* ── Snapshot ───────────────────────────────────────── */

  /**
   * Captures the canvas area as a Base64 PNG and sends it via WebSocket.
   * @param {string} trigger - 'auto' | 'manual' | 'submit'
   */
  async captureAndSend(trigger = 'auto') {
    try {
      const base64 = await this._captureBase64();
      if (!base64) return;
      window.pblWS?.send('canvas_snapshot', { image: base64, trigger });
      window.pblEventTracker?.onCanvasSnapshot(trigger);
      console.log(`[Canvas] Snapshot sent (${trigger})`);
    } catch (err) {
      console.error('[Canvas] Snapshot error:', err);
    }
  }

  async _captureBase64() {
    // Prefer Tldraw's export if available
    if (this._editor) {
      try {
        const shapeIds = this._editor.getCurrentPageShapeIds();
        if (shapeIds.size > 0) {
          const blob = await this._editor.toBlob({ shapeIds: [...shapeIds], type: 'image/png', scale: 1 });
          if (blob) return await this._blobToBase64(blob);
        }
      } catch (e) {
        console.warn('[Canvas] Tldraw export failed, falling back to html2canvas:', e);
      }
    }

    // Fallback: screenshot the canvas area DOM element via canvas drawImage
    return await this._domToBase64();
  }

  async _domToBase64() {
    return new Promise((resolve) => {
      try {
        const el   = this._canvasEl;
        const W    = el.offsetWidth;
        const H    = el.offsetHeight;
        const cvs  = document.createElement('canvas');
        cvs.width  = W;
        cvs.height = H;
        const ctx  = cvs.getContext('2d');
        ctx.fillStyle = '#111113';
        ctx.fillRect(0, 0, W, H);
        // Draw the fallback canvas if present
        const fc = document.getElementById('fallback-canvas');
        if (fc) ctx.drawImage(fc, 0, 0);
        resolve(cvs.toDataURL('image/png'));
      } catch (err) {
        console.error('[Canvas] DOM capture failed:', err);
        resolve(null);
      }
    });
  }

  _blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload  = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  _startAutoSnapshot() {
    // Take passive snapshot every 15 seconds and send to AI (no response expected)
    this._snapshotTimer = setInterval(() => {
      if (window.pblWS?.isConnected()) {
        this.captureAndSend('auto');
      }
    }, 15000);
  }

  stopAutoSnapshot() {
    if (this._snapshotTimer) {
      clearInterval(this._snapshotTimer);
      this._snapshotTimer = null;
    }
  }

  /* ── Highlight Overlays (AI-controlled) ─────────────── */

  /**
   * Draws a translucent highlight rectangle over a canvas region.
   * @param {{region:{x,y,w,h}, color:string, duration_ms:number, reason:string}} opts
   *   - region: normalized 0–1 coordinates
   *   - color: CSS color string e.g. 'rgba(252,129,129,0.35)'
   *   - duration_ms: how long the highlight stays visible
   */
  applyHighlight({ region, color = 'rgba(252,200,100,0.35)', duration_ms = 4000, reason = '' }) {
    const canvasRect = this._canvasEl.getBoundingClientRect();
    const W = canvasRect.width;
    const H = canvasRect.height;

    // region coords are normalized (0–1)
    const x = (region.x ?? 0) * W;
    const y = (region.y ?? 0) * H;
    const w = (region.w ?? 0.2) * W;
    const h = (region.h ?? 0.1) * H;

    const el = document.createElement('div');
    el.className = 'highlight-overlay';
    el.style.cssText = `
      left: ${x}px;
      top: ${y}px;
      width: ${w}px;
      height: ${h}px;
      background: ${color};
      border: 2px solid ${color.replace(/[\d.]+\)$/, '0.8)')};
      --hl-duration: ${duration_ms}ms;
    `;
    if (reason) el.title = reason;
    this._highlightEl.appendChild(el);

    // Remove after animation completes
    setTimeout(() => el.remove(), duration_ms + 100);
    console.log('[Canvas] Highlight applied:', { region, color, duration_ms, reason });
  }

  clearAllHighlights() {
    this._highlightEl.innerHTML = '';
  }
}

// ── Global instance ──────────────────────────────────────
window.pblCanvas = new PBLCanvas();
