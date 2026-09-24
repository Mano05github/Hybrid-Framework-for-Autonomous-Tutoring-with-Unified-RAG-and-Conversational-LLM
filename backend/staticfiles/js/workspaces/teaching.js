/**
 * Teaching Workspace — Vaathiyar Socratic Tutor
 * ===============================================
 * Khan Academy-style teaching workspace.
 *
 * Layout:
 *  ┌────────────────────────────────┐
 *  │  PROBLEM PANEL                 │
 *  │  (displays topic problem)      │
 *  ├────────────────────────────────┤
 *  │                                │
 *  │  STUDENT DRAWING CANVAS        │
 *  │  (user writes here, not AI)    │
 *  │                                │
 *  │  [Pen][Highlighter][Erase][🗑️] │
 *  └────────────────────────────────┘
 *
 * The AI watches via canvas snapshots — it does NOT draw here.
 */

// ── Problem Bank ──────────────────────────────────────────────────────────────
// One problem per topic, shown as the question the student must solve.

const PROBLEMS = {
    binary_search: {
        title: "Binary Search",
        question: "An array is: [2, 5, 8, 13, 21, 34, 55, 89]. Use Binary Search to find the number 34. Show each step — what is low, high, and mid at each stage?",
        hint: "Start with low=0, high=7. Calculate mid = Math.floor((low+high)/2) and compare.",
        difficulty: "Intermediate",
    },
    avl_tree: {
        title: "AVL Tree",
        question: "Insert the values 30, 20, 40, 10, 25 into an AVL Tree one by one. After each insertion, check the balance factor. Show any rotations needed.",
        hint: "Balance Factor = Height(Left subtree) − Height(Right subtree). If |BF| > 1, rotate.",
        difficulty: "Advanced",
    },
    bubble_sort: {
        title: "Bubble Sort",
        question: "Sort this array using Bubble Sort: [64, 34, 25, 12, 22, 11, 90]. Show each complete pass through the array and which elements get swapped.",
        hint: "In each pass, compare adjacent pairs. Swap if left > right. The largest element bubbles to the end.",
        difficulty: "Beginner",
    },
    bst: {
        title: "Binary Search Tree",
        question: "Insert these values into a BST in order: 50, 30, 70, 20, 40, 60, 80. Draw the resulting tree. Then, show how you would search for the value 40.",
        hint: "For each value: if it's less than current node, go left. If greater, go right.",
        difficulty: "Intermediate",
    },
    stacks: {
        title: "Stacks",
        question: "Using a stack, evaluate this expression: push(5), push(3), pop(), push(8), pop(), pop(). What values are popped in what order? What is left in the stack?",
        hint: "A Stack is LIFO — Last In, First Out. Draw the stack state after each operation.",
        difficulty: "Beginner",
    },
    queues: {
        title: "Queues",
        question: "Using a Queue: enqueue(A), enqueue(B), enqueue(C), dequeue(), enqueue(D), dequeue(). What is the order of elements dequeued? What remains in the queue?",
        hint: "A Queue is FIFO — First In, First Out. The first element added is the first to leave.",
        difficulty: "Beginner",
    },
    insertion_sort: {
        title: "Insertion Sort",
        question: "Sort this array using Insertion Sort: [12, 11, 13, 5, 6]. Show how the sorted portion grows with each step and which element (key) you are inserting at each pass.",
        hint: "Start from index 1. Each element is the 'key'. Shift all larger elements right, then insert the key.",
        difficulty: "Beginner",
    },
};

// ── Difficulty colours ────────────────────────────────────────────────────────
const DIFFICULTY_COLOR = {
    Beginner:     "rgba(0, 220, 130, 0.25)",
    Intermediate: "rgba(0, 180, 255, 0.25)",
    Advanced:     "rgba(255, 100, 100, 0.25)",
};

// ── TeachingWorkspace Class ───────────────────────────────────────────────────

class TeachingWorkspace {
    constructor(containerId, topicId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error("TeachingWorkspace: container not found:", containerId);
            return;
        }

        this.topicId   = topicId || "binary_search";
        this.problem   = PROBLEMS[this.topicId] || PROBLEMS["binary_search"];

        // Drawing state
        this.canvas    = null;
        this.ctx       = null;
        this.isDrawing = false;
        this.tool      = "pen";
        this.color     = "#00d4ff";
        this.lineWidth = 2.5;
        this.lastX     = 0;
        this.lastY     = 0;

        // Track snapshot debounce
        this._snapshotTimer = null;

        this._build();
    }

    // ── Build the full workspace HTML ─────────────────────────────────────────

    _build() {
        this.container.innerHTML = "";
        this.container.style.display    = "flex";
        this.container.style.flexDirection = "column";
        this.container.style.height     = "100%";
        this.container.style.overflow   = "hidden";
        this.container.style.background = "rgba(6, 8, 18, 0.95)";

        // 1. Problem Panel
        this._buildProblemPanel();

        // 2. Canvas area
        this._buildCanvasArea();

        // 3. Toolbar
        this._buildToolbar();

        // Init icons
        if (window.lucide) window.lucide.createIcons();

        // Resize handling
        this._setupResize();

        console.log(`📚 TeachingWorkspace ready | topic: ${this.topicId}`);
    }

    _buildProblemPanel() {
        const diff = this.problem.difficulty;
        const diffColor = DIFFICULTY_COLOR[diff] || "rgba(0,180,255,0.15)";

        const panel = document.createElement("div");
        panel.className = "problem-panel";
        panel.style.cssText = `
            flex-shrink: 0;
            background: rgba(15, 18, 35, 0.9);
            border-bottom: 1px solid rgba(0, 200, 255, 0.15);
            padding: 1.2rem 1.5rem;
            user-select: none;
        `;

        panel.innerHTML = `
            <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.8rem;">
                <span style="
                    font-family:'Space Grotesk',sans-serif;
                    font-size:0.7rem;
                    font-weight:700;
                    letter-spacing:2px;
                    text-transform:uppercase;
                    color:rgba(0,220,255,0.7);
                ">📌 PROBLEM</span>
                <span style="
                    font-size:0.65rem;
                    font-weight:600;
                    letter-spacing:1px;
                    text-transform:uppercase;
                    background:${diffColor};
                    border: 1px solid ${diffColor.replace('0.25','0.5')};
                    padding:0.2rem 0.6rem;
                    border-radius:20px;
                    color:#fff;
                ">${diff}</span>
                <span style="
                    margin-left:auto;
                    font-family:'Space Grotesk',sans-serif;
                    font-size:0.95rem;
                    font-weight:700;
                    color:#fff;
                    letter-spacing:-0.3px;
                ">${this.problem.title}</span>
            </div>
            <p style="
                font-family:'Inter',sans-serif;
                font-size:0.9rem;
                line-height:1.65;
                color:rgba(255,255,255,0.9);
                margin:0 0 0.6rem 0;
            ">${this.problem.question}</p>
            <details style="margin-top:0.4rem; cursor:pointer;">
                <summary style="
                    font-size:0.75rem;
                    color:rgba(0,220,255,0.6);
                    font-family:'Inter',sans-serif;
                    letter-spacing:0.5px;
                    list-style:none;
                    cursor:pointer;
                    user-select:none;
                ">💡 Hint (click to reveal)</summary>
                <p style="
                    font-size:0.8rem;
                    color:rgba(255,220,100,0.85);
                    margin:0.5rem 0 0 0.5rem;
                    font-family:'Inter',sans-serif;
                    line-height:1.5;
                ">${this.problem.hint}</p>
            </details>
        `;

        this.container.appendChild(panel);
        this.problemPanel = panel;
    }

    _buildCanvasArea() {
        const wrapper = document.createElement("div");
        wrapper.style.cssText = `
            flex: 1;
            position: relative;
            overflow: hidden;
            background: #0a0d1a;
        `;

        // Guide text (disappears on first draw)
        this._guide = document.createElement("div");
        this._guide.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            pointer-events: none;
            opacity: 0.35;
            transition: opacity 0.5s ease;
            z-index: 1;
        `;
        this._guide.innerHTML = `
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">✏️</div>
            <div style="font-family:'Inter',sans-serif; font-size:0.9rem; color:#a0b0c0; letter-spacing:0.5px;">
                Work out the problem here<br>
                <span style="font-size:0.75rem; opacity:0.7;">The AI is watching — ask it questions anytime</span>
            </div>
        `;
        wrapper.appendChild(this._guide);

        // Canvas
        this.canvas = document.createElement("canvas");
        this.canvas.id = "student-canvas";
        this.canvas.style.cssText = `
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            cursor: crosshair;
            display: block;
            z-index: 2;
        `;

        this.ctx = this.canvas.getContext("2d");
        this.ctx.lineCap  = "round";
        this.ctx.lineJoin = "round";

        wrapper.appendChild(this.canvas);
        this.container.appendChild(wrapper);
        this.canvasWrapper = wrapper;

        this._bindDrawingEvents();
    }

    _buildToolbar() {
        const bar = document.createElement("div");
        bar.style.cssText = `
            flex-shrink: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.6rem 1rem;
            background: rgba(10, 12, 25, 0.95);
            border-top: 1px solid rgba(255,255,255,0.06);
        `;

        bar.innerHTML = `
            <button class="tw-btn active" data-tool="pen" title="Pen (freehand)">
                <i data-lucide="pen-tool"></i>
            </button>
            <button class="tw-btn" data-tool="highlighter" title="Highlighter">
                <i data-lucide="highlighter"></i>
            </button>
            <button class="tw-btn" data-tool="eraser" title="Eraser">
                <i data-lucide="eraser"></i>
            </button>
            <div style="width:1px;height:24px;background:rgba(255,255,255,0.1);margin:0 0.3rem;"></div>
            <div style="position:relative; display:flex; align-items:center;" title="Pen colour">
                <input type="color" id="tw-color-pick" value="#00d4ff"
                    style="opacity:0; position:absolute; width:100%; height:100%; cursor:pointer; border:none;">
                <div id="tw-color-preview" style="
                    width:22px; height:22px;
                    border-radius:50%;
                    background:#00d4ff;
                    border:2px solid rgba(255,255,255,0.3);
                    cursor:pointer;
                "></div>
            </div>
            <div style="flex:1;"></div>
            <button class="tw-btn" id="tw-snap-btn" title="Send canvas to AI for feedback" style="color: #00ffa0;">
                <i data-lucide="eye"></i>
                <span style="font-size:0.7rem; margin-left:4px; font-family:'Inter',sans-serif;">Ask AI</span>
            </button>
            <button class="tw-btn" id="tw-clear-btn" title="Clear canvas" style="color:#ff6060;">
                <i data-lucide="trash-2"></i>
            </button>
        `;

        this.container.appendChild(bar);
        this.toolbar = bar;
        this._bindToolbarEvents();
    }

    // ── Event Bindings ────────────────────────────────────────────────────────

    _bindDrawingEvents() {
        const cv = this.canvas;

        // Mouse
        cv.addEventListener("mousedown",  (e) => this._startDraw(e));
        cv.addEventListener("mousemove",  (e) => this._draw(e));
        cv.addEventListener("mouseup",    ()  => this._stopDraw());
        cv.addEventListener("mouseleave", ()  => this._stopDraw());

        // Touch
        cv.addEventListener("touchstart", (e) => { e.preventDefault(); this._startDraw(e.touches[0]); }, { passive: false });
        cv.addEventListener("touchmove",  (e) => { e.preventDefault(); this._draw(e.touches[0]); },      { passive: false });
        cv.addEventListener("touchend",   (e) => { e.preventDefault(); this._stopDraw(); });
    }

    _bindToolbarEvents() {
        // Tool buttons
        const toolBtns = this.toolbar.querySelectorAll(".tw-btn[data-tool]");
        toolBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                this.tool = btn.dataset.tool;
                toolBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this._updateCursor();
            });
        });

        // Color
        const colorPick    = this.toolbar.querySelector("#tw-color-pick");
        const colorPreview = this.toolbar.querySelector("#tw-color-preview");
        colorPick.addEventListener("input", (e) => {
            this.color = e.target.value;
            colorPreview.style.background = e.target.value;
        });

        // Clear
        const clearBtn = this.toolbar.querySelector("#tw-clear-btn");
        clearBtn.addEventListener("click", () => {
            if (confirm("Clear your work?")) this.clearCanvas();
        });

        // Send canvas to AI
        const snapBtn = this.toolbar.querySelector("#tw-snap-btn");
        snapBtn.addEventListener("click", () => this._sendSnapshotToAI("Can you check what I have drawn?"));
    }

    _updateCursor() {
        const cursors = { pen:"crosshair", highlighter:"crosshair", eraser:"grab" };
        this.canvas.style.cursor = cursors[this.tool] || "crosshair";
    }

    // ── Drawing Logic ─────────────────────────────────────────────────────────

    _startDraw(e) {
        this.isDrawing = true;
        const { x, y } = this._getPos(e);
        this.lastX = x;
        this.lastY = y;

        // Hide guide on first stroke
        if (this._guide) {
            this._guide.style.opacity = "0";
        }
    }

    _draw(e) {
        if (!this.isDrawing) return;
        const { x, y } = this._getPos(e);
        const ctx = this.ctx;

        ctx.beginPath();
        ctx.moveTo(this.lastX, this.lastY);
        ctx.lineTo(x, y);

        if (this.tool === "eraser") {
            ctx.globalCompositeOperation = "destination-out";
            ctx.lineWidth  = 18;
            ctx.strokeStyle = "rgba(0,0,0,1)";
            ctx.globalAlpha = 1;
        } else if (this.tool === "highlighter") {
            ctx.globalCompositeOperation = "source-over";
            ctx.globalAlpha = 0.28;
            ctx.lineWidth   = 12;
            ctx.strokeStyle = this.color;
        } else {
            ctx.globalCompositeOperation = "source-over";
            ctx.globalAlpha = 1;
            ctx.lineWidth   = this.lineWidth;
            ctx.strokeStyle = this.color;
        }

        ctx.stroke();
        this.lastX = x;
        this.lastY = y;

        // Debounce: auto-send snapshot to AI 3 seconds after last stroke (passive watch)
        this._schedulePassiveSnapshot();
    }

    _stopDraw() {
        this.isDrawing = false;
        if (this.ctx) {
            this.ctx.globalAlpha = 1;
            this.ctx.globalCompositeOperation = "source-over";
        }
    }

    _getPos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left) * (this.canvas.width  / rect.width),
            y: (e.clientY - rect.top)  * (this.canvas.height / rect.height),
        };
    }

    // ── Canvas Utilities ──────────────────────────────────────────────────────

    clearCanvas() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        if (this._guide) this._guide.style.opacity = "0.35";
    }

    getSnapshot() {
        if (!this.canvas) return null;
        return this.canvas.toDataURL("image/png");
    }

    // ── AI Integration: Send canvas snapshot ─────────────────────────────────

    _schedulePassiveSnapshot() {
        // Send canvas view to AI 3s after user stops drawing (passive watching)
        if (this._snapshotTimer) clearTimeout(this._snapshotTimer);
        this._snapshotTimer = setTimeout(() => {
            // Only send if user has drawn something
            if (!this._isCanvasBlank()) {
                this._sendSnapshotToAI(null, /* passive */ true);
            }
        }, 3000);
    }

    _isCanvasBlank() {
        if (!this.canvas || !this.ctx) return true;
        const data = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height).data;
        return !data.some(channel => channel !== 0);
    }

    _sendSnapshotToAI(userMessage, passive = false) {
        if (!window.wsClient || !window.wsClient.isConnected) return;

        const snapshot = this.getSnapshot();
        if (!snapshot) return;

        const payload = {
            type: "context_update",
            event_type: "chat_message",
            message: userMessage || "I've been working on the problem.",
            context: {
                topic: this.topicId,
                problem: this.problem.question,
                canvas_snapshot: snapshot,
                passive: passive,
            }
        };

        window.wsClient.sendMessage(payload);

        if (!passive) {
            console.log("📸 Sent canvas snapshot to AI (manual)");
        }
    }

    // ── Resize ────────────────────────────────────────────────────────────────

    _setupResize() {
        const setSize = () => {
            if (!this.canvas || !this.canvasWrapper) return;
            const w = this.canvasWrapper.clientWidth;
            const h = this.canvasWrapper.clientHeight;
            if (w === 0 || h === 0) return;

            // Save existing drawing
            let saved = null;
            if (this.canvas.width > 0 && this.canvas.height > 0) {
                saved = document.createElement("canvas");
                saved.width  = this.canvas.width;
                saved.height = this.canvas.height;
                saved.getContext("2d").drawImage(this.canvas, 0, 0);
            }

            this.canvas.width  = w;
            this.canvas.height = h;

            // Restore drawing
            if (saved) {
                this.ctx.drawImage(saved, 0, 0);
            }
            this.ctx.lineCap  = "round";
            this.ctx.lineJoin = "round";
        };

        setSize();
        window.addEventListener("resize", setSize);
        new ResizeObserver(setSize).observe(this.canvasWrapper);
    }

    // ── Legacy API (for workspace-manager.js compatibility) ───────────────────

    handleCommand(cmd) {
        // Old AI drawing commands are ignored in the new Socratic model.
        // The student draws — the AI only guides via voice/text.
        console.log("[TeachingWorkspace] AI draw cmd ignored (Socratic mode):", cmd?.action);
    }

    destroy() {
        if (this._snapshotTimer) clearTimeout(this._snapshotTimer);
        if (this.container) this.container.innerHTML = "";
    }
}

// ── Topic-Aware Factory ───────────────────────────────────────────────────────

/**
 * Create a TeachingWorkspace for a given topic.
 * Called by voice-supervisor.html when user clicks a topic card.
 *
 * @param {string} containerId - DOM id of the workspace-content div
 * @param {string} topicId     - e.g. "binary_search"
 */
function createTeachingWorkspace(containerId, topicId) {
    return new TeachingWorkspace(containerId, topicId);
}

// Expose globally
window.TeachingWorkspace    = TeachingWorkspace;
window.createTeachingWorkspace = createTeachingWorkspace;
window.TEACHING_PROBLEMS    = PROBLEMS;
