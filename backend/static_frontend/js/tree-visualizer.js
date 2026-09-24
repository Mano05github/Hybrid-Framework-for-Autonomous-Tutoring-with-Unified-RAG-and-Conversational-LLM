/**
 * TreeVisualizer — SVG-based top-down animated concept tree
 * Renders backend tree_data JSON as an interactive expandable tree
 * overlaid on top of the AI whiteboard canvas.
 *
 * Tree data shape:
 *   { root: "Concept", children: [{ label: "Sub", children: [...] }] }
 */
class TreeVisualizer {
    constructor(svgEl) {
        this.svg = svgEl;
        this._nodeMap = new Map();   // nodeId → { node, el }
        this._linksGroup = null;
        this._nodesGroup = null;
        this._idCounter = 0;
    }

    // ─────────────────────────────────────────────────────────
    //  Public API
    // ─────────────────────────────────────────────────────────

    /** Render a fresh tree from treeData. Clears any previous render. */
    render(treeData) {
        this.clear();
        if (!treeData || !treeData.root) return;

        // 1. Build logical tree with subtree widths
        const root = this._buildLogical(treeData, 0);

        // 2. Assign x,y coordinates (top-down layout)
        const svgRect = this.svg.getBoundingClientRect();
        const svgW = svgRect.width  || 800;
        const svgH = svgRect.height || 600;
        this._assignPositions(root, 0);   // relative to root at x=0

        const shiftX = svgW / 2;          // center root horizontally
        const shiftY = svgH * 0.12;       // 12% padding from top

        // 3. Create SVG groups
        this._linksGroup = this._makeSVGEl('g', { class: 'tree-links' });
        this._nodesGroup = this._makeSVGEl('g', { class: 'tree-nodes' });
        this.svg.appendChild(this._linksGroup);
        this.svg.appendChild(this._nodesGroup);

        // 4. Draw links first (so they sit below nodes)
        this._drawLinks(root, shiftX, shiftY, 0);

        // 5. Draw nodes
        this._drawNodes(root, shiftX, shiftY, 0, true);
    }

    /** Pulse the node whose label matches `label` (case-insensitive). */
    highlightNode(label) {
        this.svg.querySelectorAll('.tree-node.active')
            .forEach(el => el.classList.remove('active'));

        const target = label.toLowerCase();
        for (const [, entry] of this._nodeMap) {
            if (entry.node.label.toLowerCase() === target) {
                entry.el.classList.add('active');
                break;
            }
        }
    }

    /** Remove all SVG content and reset state. */
    clear() {
        while (this.svg.firstChild) this.svg.removeChild(this.svg.firstChild);
        this._nodeMap.clear();
        this._linksGroup = null;
        this._nodesGroup = null;
        this._idCounter = 0;
    }

    // ─────────────────────────────────────────────────────────
    //  Layout computation
    // ─────────────────────────────────────────────────────────

    /** Recursively build a plain JS object with layout metadata. */
    _buildLogical(data, depth) {
        const label = typeof data === 'string'
            ? data
            : (data.root || data.label || '?');

        const rawChildren = Array.isArray(data.children) ? data.children : [];
        const children = rawChildren.map(ch => this._buildLogical(ch, depth + 1));

        // subtreeWidth: minimum "column slots" this subtree occupies
        const subtreeWidth = children.length
            ? children.reduce((sum, c) => sum + c.subtreeWidth, 0)
            : 1;

        return {
            id: this._idCounter++,
            label,
            depth,
            children,
            subtreeWidth,
            collapsed: false,
            x: 0,
            y: 0
        };
    }

    /** Assign (x, y) to every node — root starts at x=0, y=0. */
    _assignPositions(node, xCenter) {
        const ROW_HEIGHT  = 115;   // px between depth levels
        const COL_WIDTH   = 155;   // px per subtree slot

        node.x = xCenter;
        node.y = node.depth * ROW_HEIGHT;

        if (node.children.length === 0) return;

        const totalW = node.children.reduce((s, c) => s + c.subtreeWidth, 0) * COL_WIDTH;
        let cursor = xCenter - totalW / 2;

        for (const child of node.children) {
            const childW = child.subtreeWidth * COL_WIDTH;
            this._assignPositions(child, cursor + childW / 2);
            cursor += childW;
        }
    }

    // ─────────────────────────────────────────────────────────
    //  SVG rendering — links
    // ─────────────────────────────────────────────────────────

    _drawLinks(node, shiftX, shiftY, orderIndex) {
        for (let i = 0; i < node.children.length; i++) {
            const child = node.children[i];

            const x1 = node.x  + shiftX,  y1 = node.y  + shiftY;
            const x2 = child.x + shiftX,  y2 = child.y + shiftY;

            // Bezier curve: control points pull midway down
            const midY = (y1 + y2) / 2;
            const d = `M${x1},${y1} C${x1},${midY} ${x2},${midY} ${x2},${y2}`;

            const len = Math.ceil(Math.hypot(x2 - x1, y2 - y1) * 1.4);
            const delay = (orderIndex + i) * 70;

            const path = this._makeSVGEl('path', {
                d,
                class: 'tree-link',
                'data-link-id': `${node.id}-${child.id}`
            });
            path.style.setProperty('--link-len',   String(len));
            path.style.setProperty('--link-delay', `${delay}ms`);

            this._linksGroup.appendChild(path);

            // Recurse
            this._drawLinks(child, shiftX, shiftY,
                orderIndex + node.children.length + i);
        }
    }

    // ─────────────────────────────────────────────────────────
    //  SVG rendering — nodes
    // ─────────────────────────────────────────────────────────

    /**
     * Returns the next available order index (for stagger timing).
     * BFS-style: left-to-right, depth-first.
     */
    _drawNodes(node, shiftX, shiftY, orderIndex, isRoot) {
        const cx    = node.x + shiftX;
        const cy    = node.y + shiftY;
        const r     = isRoot ? 38 : node.depth === 1 ? 30 : 24;
        const delay = orderIndex * 60;

        // <g class="tree-node [root-node] [has-children]">
        const classes = ['tree-node'];
        if (isRoot)                  classes.push('root-node');
        if (node.children.length)    classes.push('has-children');

        const gNode = this._makeSVGEl('g', {
            class: classes.join(' '),
            'data-node-id': node.id
        });

        // -- Circle --
        const circle = this._makeSVGEl('circle', { cx, cy, class: isRoot ? 'root-circle' : '' });
        circle.style.setProperty('--node-r',     String(r));
        circle.style.setProperty('--node-delay', `${delay}ms`);
        gNode.appendChild(circle);

        // -- Label (word-wrapped, max 2 lines) --
        const lines = this._wrapLabel(node.label, r * 1.8);
        lines.forEach((line, li) => {
            const offsetY = (li - (lines.length - 1) / 2) * 15;
            const text = this._makeSVGEl('text', {
                x: cx,
                y: cy + offsetY,
                class: isRoot ? 'root-text' : ''
            });
            text.style.setProperty('--text-delay', `${delay + 90}ms`);
            text.textContent = line;
            gNode.appendChild(text);
        });

        // -- Toggle indicator (+/−) --
        if (node.children.length > 0 && !isRoot) {
            const ind = this._makeSVGEl('text', {
                x: cx + r - 2,
                y: cy - r + 3,
                class: 'toggle-indicator',
                'data-toggle-for': node.id
            });
            ind.style.setProperty('--text-delay', `${delay + 90}ms`);
            ind.textContent = '−';
            gNode.appendChild(ind);
        }

        // -- Click to toggle collapse --
        if (node.children.length > 0) {
            gNode.addEventListener('click', (e) => {
                e.stopPropagation();
                this._toggleNode(node.id);
            });
        }

        this._nodesGroup.appendChild(gNode);
        this._nodeMap.set(node.id, { node, el: gNode });

        // Recurse into children
        let next = orderIndex + 1;
        for (const child of node.children) {
            next = this._drawNodes(child, shiftX, shiftY, next, false);
        }
        return next;
    }

    // ─────────────────────────────────────────────────────────
    //  Collapse / expand
    // ─────────────────────────────────────────────────────────

    _toggleNode(nodeId) {
        const entry = this._nodeMap.get(nodeId);
        if (!entry) return;

        entry.node.collapsed = !entry.node.collapsed;

        // Update indicator text
        const ind = entry.el.querySelector(`[data-toggle-for="${nodeId}"]`);
        if (ind) ind.textContent = entry.node.collapsed ? '+' : '−';

        this._setSubtreeVisible(entry.node, !entry.node.collapsed);
    }

    _setSubtreeVisible(node, visible) {
        for (const child of node.children) {
            // Node element
            const childEntry = this._nodeMap.get(child.id);
            if (childEntry) {
                childEntry.el.style.display = visible ? '' : 'none';
            }

            // Connecting link
            if (this._linksGroup) {
                const link = this._linksGroup.querySelector(
                    `[data-link-id="${node.id}-${child.id}"]`
                );
                if (link) link.style.display = visible ? '' : 'none';
            }

            // Recurse: if restoring visibility, only show if the child
            // itself is not collapsed; if hiding, always hide descendants.
            if (!visible || !child.collapsed) {
                this._setSubtreeVisible(child, visible);
            }
        }
    }

    // ─────────────────────────────────────────────────────────
    //  Helpers
    // ─────────────────────────────────────────────────────────

    _wrapLabel(label, maxPx) {
        const approxCharPx = 7.8;
        const maxChars = Math.max(6, Math.floor(maxPx / approxCharPx));
        if (label.length <= maxChars) return [label];

        const words = label.split(' ');
        const lines = [];
        let current = '';

        for (const word of words) {
            const candidate = current ? `${current} ${word}` : word;
            if (candidate.length > maxChars) {
                if (current) lines.push(current);
                current = word;
            } else {
                current = candidate;
            }
        }
        if (current) lines.push(current);
        return lines.slice(0, 2);
    }

    _makeSVGEl(tag, attrs = {}) {
        const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
        for (const [k, v] of Object.entries(attrs)) {
            el.setAttribute(k, v);
        }
        return el;
    }
}
