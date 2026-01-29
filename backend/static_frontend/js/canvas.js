// ===================================
// CANVAS WHITEBOARD FUNCTIONALITY
// ===================================

class CanvasWhiteboard {
    constructor() {
        this.canvas = document.getElementById('drawingCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Create overlay canvas for current stroke (performance optimization)
        this.overlayCanvas = document.createElement('canvas');
        this.overlayCtx = this.overlayCanvas.getContext('2d');
        
        // Infinite canvas viewport
        this.offsetX = 0;
        this.offsetY = 0;
        this.scale = 1;
        this.minScale = 0.1;
        this.maxScale = 5;
        
        // Pan state
        this.isPanning = false;
        this.panStartX = 0;
        this.panStartY = 0;
        this.lastOffsetX = 0;
        this.lastOffsetY = 0;
        
        // Drawing state
        this.isDrawing = false;
        this.currentTool = 'pen';
        this.currentColor = '#00d4ff';
        this.currentThickness = 3;
        
        // Drawing path for current stroke
        this.currentPath = [];
        
        // History for undo/redo (stores drawing commands)
        this.history = [];
        this.historyStep = -1;
        
        // All drawn paths
        this.paths = [];
        
        // DOM elements
        this.toolBtns = document.querySelectorAll('[data-tool]');
        this.colorPicker = document.getElementById('colorPicker');
        this.thicknessSlider = document.getElementById('thicknessSlider');
        this.thicknessValue = document.getElementById('thicknessValue');
        this.undoBtn = document.getElementById('undoBtn');
        this.redoBtn = document.getElementById('redoBtn');
        this.exportBtn = document.getElementById('exportBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.floatingToolbar = document.getElementById('floatingToolbar');
        
        this.init();
    }
    
    init() {
        // Set canvas size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Tool selection
        this.toolBtns.forEach(btn => {
            btn.addEventListener('click', () => this.selectTool(btn.dataset.tool));
        });
        
        // Color picker
        this.colorPicker.addEventListener('change', (e) => {
            this.currentColor = e.target.value;
        });
        
        // Thickness slider
        this.thicknessSlider.addEventListener('input', (e) => {
            this.currentThickness = e.target.value;
            this.thicknessValue.textContent = `${e.target.value}px`;
        });
        
        // Drawing events
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        this.canvas.addEventListener('mouseleave', () => this.handleMouseUp());
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        this.canvas.addEventListener('touchend', () => this.handleMouseUp());
        
        // Zoom with mouse wheel
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
        
        // Undo/Redo
        this.undoBtn.addEventListener('click', () => this.undo());
        this.redoBtn.addEventListener('click', () => this.redo());
        
        // Export and clear
        this.exportBtn.addEventListener('click', () => this.exportCanvas());
        this.clearBtn.addEventListener('click', () => this.clearCanvas());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'z') {
                e.preventDefault();
                this.undo();
            }
            if (e.ctrlKey && e.key === 'y') {
                e.preventDefault();
                this.redo();
            }
            // Tool shortcuts
            if (e.key === 'p') this.selectTool('pen');
            if (e.key === 'e') this.selectTool('eraser');
            if (e.key === 's') this.selectTool('shapes');
        });
        
        // Make toolbar draggable
        this.makeToolbarDraggable();
        
        // Initial render
        this.render();
        
        console.log('✨ Canvas Whiteboard initialized (Infinite Canvas Mode)');
    }
    
    resizeCanvas() {
        const wrapper = this.canvas.parentElement;
        this.canvas.width = wrapper.offsetWidth;
        this.canvas.height = wrapper.offsetHeight;
        
        // Match overlay canvas size
        this.overlayCanvas.width = this.canvas.width;
        this.overlayCanvas.height = this.canvas.height;
        
        this.render();
    }
    
    // Transform screen coordinates to world coordinates
    screenToWorld(screenX, screenY) {
        return {
            x: (screenX - this.offsetX) / this.scale,
            y: (screenY - this.offsetY) / this.scale
        };
    }
    
    // Transform world coordinates to screen coordinates
    worldToScreen(worldX, worldY) {
        return {
            x: worldX * this.scale + this.offsetX,
            y: worldY * this.scale + this.offsetY
        };
    }
    
    // Render the entire canvas
    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Save context state
        this.ctx.save();
        
        // Apply transformations
        this.ctx.translate(this.offsetX, this.offsetY);
        this.ctx.scale(this.scale, this.scale);
        
        // Draw grid background
        this.drawGrid();
        
        // Draw all paths
        this.paths.forEach(path => {
            this.drawPath(path);
        });
        
        // Restore context state
        this.ctx.restore();
    }
    
    // Draw grid background
    drawGrid() {
        const gridSize = 50;
        const startX = Math.floor(-this.offsetX / this.scale / gridSize) * gridSize;
        const startY = Math.floor(-this.offsetY / this.scale / gridSize) * gridSize;
        const endX = startX + (this.canvas.width / this.scale) + gridSize;
        const endY = startY + (this.canvas.height / this.scale) + gridSize;
        
        this.ctx.strokeStyle = 'rgba(0, 212, 255, 0.1)';
        this.ctx.lineWidth = 1 / this.scale;
        
        // Vertical lines
        for (let x = startX; x < endX; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, startY);
            this.ctx.lineTo(x, endY);
            this.ctx.stroke();
        }
        
        // Horizontal lines
        for (let y = startY; y < endY; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(startX, y);
            this.ctx.lineTo(endX, y);
            this.ctx.stroke();
        }
    }
    
    // Draw a single path
    drawPath(path) {
        if (path.points.length < 2) return;
        
        this.ctx.beginPath();
        this.ctx.strokeStyle = path.color;
        this.ctx.lineWidth = path.thickness;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        
        if (path.tool === 'eraser') {
            this.ctx.globalCompositeOperation = 'destination-out';
            this.ctx.lineWidth = path.thickness * 3;
        } else {
            this.ctx.globalCompositeOperation = 'source-over';
        }
        
        this.ctx.moveTo(path.points[0].x, path.points[0].y);
        for (let i = 1; i < path.points.length; i++) {
            this.ctx.lineTo(path.points[i].x, path.points[i].y);
        }
        this.ctx.stroke();
        
        this.ctx.globalCompositeOperation = 'source-over';
    }
    
    selectTool(tool) {
        this.currentTool = tool;
        
        // Update active button
        this.toolBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === tool);
        });
        
        // Update cursor
        if (tool === 'eraser') {
            this.canvas.classList.add('eraser-cursor');
        } else {
            this.canvas.classList.remove('eraser-cursor');
        }
        
        console.log('🖌️ Tool selected:', tool);
    }
    
    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;
        
        // Middle mouse button or spacebar + left click = pan
        if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
            e.preventDefault();
            this.isPanning = true;
            this.panStartX = screenX;
            this.panStartY = screenY;
            this.lastOffsetX = this.offsetX;
            this.lastOffsetY = this.offsetY;
            this.canvas.style.cursor = 'grabbing';
            return;
        }
        
        // Left click = draw
        if (e.button === 0 && !this.isPanning) {
            this.isDrawing = true;
            const worldPos = this.screenToWorld(screenX, screenY);
            this.currentPath = {
                tool: this.currentTool,
                color: this.currentColor,
                thickness: this.currentThickness,
                points: [worldPos]
            };
        }
    }
    
    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;
        
        // Handle panning
        if (this.isPanning) {
            this.offsetX = this.lastOffsetX + (screenX - this.panStartX);
            this.offsetY = this.lastOffsetY + (screenY - this.panStartY);
            this.render();
            return;
        }
        
        // Handle drawing - OPTIMIZED: draw on overlay without full render
        if (this.isDrawing) {
            const worldPos = this.screenToWorld(screenX, screenY);
            this.currentPath.points.push(worldPos);
            
            // Draw current stroke on overlay canvas (fast)
            this.drawCurrentStroke();
        }
    }
    
    // Draw only the current stroke on overlay (performance optimization)
    drawCurrentStroke() {
        // Clear overlay
        this.overlayCtx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);
        
        if (this.currentPath.points.length < 2) return;
        
        // Save and apply transformations
        this.overlayCtx.save();
        this.overlayCtx.translate(this.offsetX, this.offsetY);
        this.overlayCtx.scale(this.scale, this.scale);
        
        // Draw current path
        this.overlayCtx.beginPath();
        this.overlayCtx.strokeStyle = this.currentPath.color;
        this.overlayCtx.lineWidth = this.currentPath.thickness;
        this.overlayCtx.lineCap = 'round';
        this.overlayCtx.lineJoin = 'round';
        
        if (this.currentPath.tool === 'eraser') {
            this.overlayCtx.globalCompositeOperation = 'destination-out';
            this.overlayCtx.lineWidth = this.currentPath.thickness * 3;
        } else {
            this.overlayCtx.globalCompositeOperation = 'source-over';
        }
        
        const points = this.currentPath.points;
        this.overlayCtx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            this.overlayCtx.lineTo(points[i].x, points[i].y);
        }
        this.overlayCtx.stroke();
        
        this.overlayCtx.restore();
        
        // Composite overlay onto main canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.save();
        this.ctx.translate(this.offsetX, this.offsetY);
        this.ctx.scale(this.scale, this.scale);
        this.drawGrid();
        this.paths.forEach(path => this.drawPath(path));
        this.ctx.restore();
        this.ctx.drawImage(this.overlayCanvas, 0, 0);
    }
    
    handleMouseUp() {
        if (this.isPanning) {
            this.isPanning = false;
            this.canvas.style.cursor = this.currentTool === 'eraser' ? 'crosshair' : 'crosshair';
        }
        
        if (this.isDrawing) {
            this.isDrawing = false;
            if (this.currentPath.points.length > 0) {
                this.paths.push(this.currentPath);
                this.saveState();
            }
            this.currentPath = [];
            
            // Clear overlay and do final render
            this.overlayCtx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);
            this.render();
        }
    }
    
    handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const screenX = touch.clientX - rect.left;
        const screenY = touch.clientY - rect.top;
        
        // Two finger touch = pan
        if (e.touches.length === 2) {
            this.isPanning = true;
            this.panStartX = screenX;
            this.panStartY = screenY;
            this.lastOffsetX = this.offsetX;
            this.lastOffsetY = this.offsetY;
            return;
        }
        
        // Single touch = draw
        this.isDrawing = true;
        const worldPos = this.screenToWorld(screenX, screenY);
        this.currentPath = {
            tool: this.currentTool,
            color: this.currentColor,
            thickness: this.currentThickness,
            points: [worldPos]
        };
    }
    
    handleTouchMove(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const screenX = touch.clientX - rect.left;
        const screenY = touch.clientY - rect.top;
        
        if (this.isPanning && e.touches.length === 2) {
            this.offsetX = this.lastOffsetX + (screenX - this.panStartX);
            this.offsetY = this.lastOffsetY + (screenY - this.panStartY);
            this.render();
            return;
        }
        
        if (this.isDrawing && e.touches.length === 1) {
            const worldPos = this.screenToWorld(screenX, screenY);
            this.currentPath.points.push(worldPos);
            this.drawCurrentStroke();
        }
    }
    
    handleWheel(e) {
        e.preventDefault();
        
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Get world position before zoom
        const worldBefore = this.screenToWorld(mouseX, mouseY);
        
        // Update scale
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        this.scale *= zoomFactor;
        this.scale = Math.max(this.minScale, Math.min(this.maxScale, this.scale));
        
        // Get world position after zoom
        const worldAfter = this.screenToWorld(mouseX, mouseY);
        
        // Adjust offset to keep mouse position stable
        this.offsetX += (worldAfter.x - worldBefore.x) * this.scale;
        this.offsetY += (worldAfter.y - worldBefore.y) * this.scale;
        
        this.render();
    }
    
    saveState() {
        // Remove any states after current step
        this.history = this.history.slice(0, this.historyStep + 1);
        
        // Save current paths (deep copy)
        this.history.push(JSON.parse(JSON.stringify(this.paths)));
        this.historyStep++;
        
        // Limit history to 50 states
        if (this.history.length > 50) {
            this.history.shift();
            this.historyStep--;
        }
    }
    
    undo() {
        if (this.historyStep > 0) {
            this.historyStep--;
            this.paths = JSON.parse(JSON.stringify(this.history[this.historyStep]));
            this.render();
            console.log('↩️ Undo');
        }
    }
    
    redo() {
        if (this.historyStep < this.history.length - 1) {
            this.historyStep++;
            this.paths = JSON.parse(JSON.stringify(this.history[this.historyStep]));
            this.render();
            console.log('↪️ Redo');
        }
    }
    
    clearCanvas() {
        if (confirm('Are you sure you want to clear the canvas?')) {
            this.paths = [];
            this.offsetX = 0;
            this.offsetY = 0;
            this.scale = 1;
            this.render();
            this.saveState();
            console.log('🗑️ Canvas cleared');
        }
    }
    
    exportCanvas() {
        // Create a temporary canvas for export
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        // Calculate bounds of all paths
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        this.paths.forEach(path => {
            path.points.forEach(point => {
                minX = Math.min(minX, point.x);
                minY = Math.min(minY, point.y);
                maxX = Math.max(maxX, point.x);
                maxY = Math.max(maxY, point.y);
            });
        });
        
        // Add padding
        const padding = 50;
        minX -= padding;
        minY -= padding;
        maxX += padding;
        maxY += padding;
        
        // Set temp canvas size
        tempCanvas.width = maxX - minX || this.canvas.width;
        tempCanvas.height = maxY - minY || this.canvas.height;
        
        // Fill white background
        tempCtx.fillStyle = 'white';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        // Translate to account for bounds
        tempCtx.translate(-minX, -minY);
        
        // Draw all paths
        this.paths.forEach(path => {
            if (path.points.length < 2) return;
            
            tempCtx.beginPath();
            tempCtx.strokeStyle = path.color;
            tempCtx.lineWidth = path.thickness;
            tempCtx.lineCap = 'round';
            tempCtx.lineJoin = 'round';
            
            tempCtx.moveTo(path.points[0].x, path.points[0].y);
            for (let i = 1; i < path.points.length; i++) {
                tempCtx.lineTo(path.points[i].x, path.points[i].y);
            }
            tempCtx.stroke();
        });
        
        // Export
        const link = document.createElement('a');
        link.download = `vaathiyar-canvas-${Date.now()}.png`;
        link.href = tempCanvas.toDataURL();
        link.click();
        console.log('💾 Canvas exported');
    }
    
    makeToolbarDraggable() {
        const handle = this.floatingToolbar.querySelector('.toolbar-handle');
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        
        handle.addEventListener('mousedown', (e) => {
            isDragging = true;
            initialX = e.clientX - this.floatingToolbar.offsetLeft;
            initialY = e.clientY - this.floatingToolbar.offsetTop;
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            
            this.floatingToolbar.style.left = `${currentX}px`;
            this.floatingToolbar.style.top = `${currentY}px`;
            this.floatingToolbar.style.transform = 'none';
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
        });
    }
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 Initializing Canvas Whiteboard...');
    
    // Initialize canvas whiteboard
    const canvasWhiteboard = new CanvasWhiteboard();
    
    // Save initial empty state
    canvasWhiteboard.saveState();
    
    console.log('✨ Infinite Canvas Whiteboard ready');
    console.log('💡 Controls: Shift+Drag or Middle Mouse to Pan | Scroll to Zoom');
});
