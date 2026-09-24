/**
 * ModeManager — orchestrates switching between Canvas Mode and Tree Mode.
 *
 * Canvas Mode: the AI whiteboard (HTML5 canvas) is fully visible.
 * Tree Mode:   the SVG tree overlay is shown; the canvas dims behind it.
 *
 * Usage (after both TreeVisualizer and CanvasWhiteboard are constructed):
 *   const treeViz = new TreeVisualizer(document.getElementById('tree-svg'));
 *   const modeManager = new ModeManager(whiteboard, treeViz);
 *   window.modeManager = modeManager;
 */
class ModeManager {
    constructor(canvasWhiteboard, treeVisualizer) {
        this.canvas      = canvasWhiteboard;
        this.tree        = treeVisualizer;
        this.currentMode = 'canvas';

        // DOM references (may be null if rendered before DOM is ready)
        this._canvasWrapper = document.querySelector('.canvas-wrapper');
        this._treeOverlay   = document.getElementById('tree-overlay');
        this._badge         = document.getElementById('mode-badge');
        this._restoreTimer  = null;
    }

    // ─────────────────────────────────────────────────────────
    //  Public API
    // ─────────────────────────────────────────────────────────

    /**
     * Show the tree overlay and render `treeData`.
     * If already in tree mode, just re-renders with new data.
     * @param {Object} treeData  — { root, children: [...] }
     */
    switchToTree(treeData) {
        // Cancel any pending canvas-restore
        if (this._restoreTimer) {
            clearTimeout(this._restoreTimer);
            this._restoreTimer = null;
        }

        const wasInTree = this.currentMode === 'tree';
        this.currentMode = 'tree';

        // Dim the canvas
        if (this._canvasWrapper) {
            this._canvasWrapper.classList.add('tree-active');
        }

        // Render tree data (before showing overlay so layout metrics are valid)
        this.tree.render(treeData);

        // Show overlay
        if (this._treeOverlay) {
            this._treeOverlay.classList.add('visible');
        }

        // Update mode badge
        this._setBadge('Tree', true);

        if (!wasInTree) {
            console.log('🌳 ModeManager → Tree Mode');
        }
    }

    /**
     * Hide the tree overlay and restore the canvas.
     * Clears the SVG tree after the fade-out completes (400 ms).
     */
    switchToCanvas() {
        if (this.currentMode === 'canvas') return;
        this.currentMode = 'canvas';

        // Fade out overlay
        if (this._treeOverlay) {
            this._treeOverlay.classList.remove('visible');
        }

        // After fade completes: restore canvas and clear SVG
        this._restoreTimer = setTimeout(() => {
            if (this._canvasWrapper) {
                this._canvasWrapper.classList.remove('tree-active');
            }
            this.tree.clear();
            this._restoreTimer = null;
        }, 420);   // slightly longer than the 0.4s CSS transition

        // Update mode badge immediately
        this._setBadge('Canvas', false);

        console.log('🎨 ModeManager → Canvas Mode');
    }

    // ─────────────────────────────────────────────────────────
    //  Internal helpers
    // ─────────────────────────────────────────────────────────

    _setBadge(label, isTree) {
        if (!this._badge) return;
        this._badge.textContent = label;
        if (isTree) {
            this._badge.classList.add('tree-mode');
        } else {
            this._badge.classList.remove('tree-mode');
        }
    }
}
