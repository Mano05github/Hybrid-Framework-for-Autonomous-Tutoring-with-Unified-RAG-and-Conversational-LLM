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
        
        // WebSocket and session
        this.sessionId = null;
        this.wsConnected = false;
        this.lastActivity = Date.now();
        
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
        
        // Chat elements
        this.messageInput = document.getElementById('canvasMessageInput');
        this.sendBtn = document.getElementById('canvasSendBtn');
        this.voiceBtn = document.getElementById('canvasVoiceBtn');
        this.connectionStatus = document.getElementById('connectionStatus');
        
        // AI Drawing state
        this.aiDrawingActive = false;
        this.aiDrawingQueue = [];
        this.currentAICommand = null;
        this.penCursor = null;  // Pen trail cursor element
        this.aiLayer = null;    // Separate layer for AI drawings
        
        this.init();
    }
    
    init() {
        // Initialize session and WebSocket
        this.initSession();
        
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
        
        // Chat functionality
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
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
        
        // Initialize AI drawing system
        this.initAIDrawingSystem();
        
        // Initial render
        this.render();
        
        console.log('✨ Canvas Whiteboard initialized (Infinite Canvas Mode + AI Drawing)');
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
                
                // Track activity for pause detection
                this.lastActivity = Date.now();
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
    
    // ===================================
    // SESSION & WEBSOCKET INTEGRATION
    // ===================================
    
    async initSession() {
        try {
            // Ensure API client and WebSocket client are available
            if (!window.apiClient) {
                console.error('❌ API Client not found');
                return;
            }
            
            if (!window.wsClient) {
                console.error('❌ WebSocket Client not found');
                return;
            }
            
            // Start or get active session
            const session = await window.apiClient.startSession();
            this.sessionId = session.id || session.session_id;
            console.log('✅ Canvas session started:', this.sessionId);
            
            // Set up WebSocket callbacks BEFORE connecting
            window.wsClient.onConnect(() => {
                this.wsConnected = true;
                this.updateConnectionStatus('connected');
                console.log('✅ Canvas WebSocket connected');
            });
            
            window.wsClient.onMessage((data) => {
                this.handleAIFeedback(data);
                
                // Listen for pause detection from Gap 5
                if (data.type === 'pause_detected') {
                    console.log('⏸️ Pause detected - suggesting canvas validation');
                    this.autoValidateCanvas();
                }
            });
            
            window.wsClient.onDisconnect(() => {
                this.wsConnected = false;
                this.updateConnectionStatus('disconnected');
                console.log('⚠️ Canvas WebSocket disconnected');
            });
            
            window.wsClient.onError((error) => {
                console.error('❌ WebSocket error:', error);
                this.wsConnected = false;
                this.updateConnectionStatus('error');
            });
            
            // Connect to WebSocket
            window.wsClient.connect(this.sessionId);
            
            // Add validate button to toolbar
            this.addValidateButton();
            
        } catch (error) {
            console.error('❌ Failed to initialize canvas session:', error);
            this.showValidationFeedback('Failed to connect to AI. Please refresh the page.', 'error');
        }
    }
    
    addValidateButton() {
        // Add Validate button to floating toolbar
        const validateBtn = document.createElement('button');
        validateBtn.className = 'tool-btn';
        validateBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 12l2 2 4-4"></path>
                <circle cx="12" cy="12" r="10"></circle>
            </svg>
            <span>Validate</span>
        `;
        validateBtn.title = 'Validate Drawing with AI';
        validateBtn.addEventListener('click', () => this.validateCanvas());
        
        this.floatingToolbar.appendChild(validateBtn);
    }
    
    validateCanvas() {
        if (!this.wsConnected) {
            alert('WebSocket not connected. Please refresh the page.');
            return;
        }
        
        // Capture canvas as base64 image
        const imageData = this.canvas.toDataURL('image/png');
        
        // Send vision request to backend
        window.wsClient.sendMessage({
            type: 'vision_request',
            event_type: 'vision_request_manual',
            image: imageData
        });
        
        console.log('🖼️ Canvas validation requested');
        this.showValidationFeedback('Analyzing your drawing...');
    }
    
    autoValidateCanvas() {
        // Auto-validation triggered by Gap 5 pause detection
        const timeSinceLastActivity = Date.now() - this.lastActivity;
        
        // Only auto-validate if there's been at least 3 seconds of inactivity
        // and there's something drawn on canvas
        if (timeSinceLastActivity > 3000 && this.paths.length > 0) {
            console.log('🤖 Auto-validating canvas due to pause detection');
            this.validateCanvas();
        }
    }
    
    handleAIFeedback(data) {
        if (data.type === 'ai_response' && data.message) {
            this.showValidationFeedback(data.message, 'success');
        }
        
        // Handle AI drawing commands
        if (data.type === 'ai_drawing' && data.canvas_commands && data.canvas_commands.length > 0) {
            console.log('🎨 Received AI drawing commands:', data.canvas_commands.length);
            this.startAIDrawing(data.canvas_commands);
        }
        
        // Handle teacher response with canvas commands
        if (data.type === 'teacher_response' && data.canvas_commands && data.canvas_commands.length > 0) {
            console.log('🎨 Teacher response includes canvas commands:', data.canvas_commands.length);
            this.startAIDrawing(data.canvas_commands);
        }
    }
    
    updateConnectionStatus(status) {
        if (!this.connectionStatus) return;
        
        const dot = this.connectionStatus.querySelector('.status-dot');
        const text = this.connectionStatus.querySelector('.status-text-small');
        
        switch(status) {
            case 'connected':
                dot.style.background = '#00ff88';
                text.textContent = 'Connected';
                this.connectionStatus.style.borderColor = 'rgba(0, 255, 136, 0.3)';
                break;
            case 'disconnected':
                dot.style.background = '#ff4444';
                text.textContent = 'Disconnected';
                this.connectionStatus.style.borderColor = 'rgba(255, 68, 68, 0.3)';
                break;
            case 'error':
                dot.style.background = '#ff9944';
                text.textContent = 'Error';
                this.connectionStatus.style.borderColor = 'rgba(255, 153, 68, 0.3)';
                break;
            default:
                dot.style.background = '#ffaa00';
                text.textContent = 'Connecting...';
                this.connectionStatus.style.borderColor = 'rgba(255, 170, 0, 0.3)';
        }
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Check WebSocket connection
        if (!window.wsClient) {
            this.showValidationFeedback('❌ WebSocket client not initialized. Please refresh the page.', 'error');
            return;
        }
        
        if (!this.wsConnected || !window.wsClient.ws || window.wsClient.ws.readyState !== WebSocket.OPEN) {
            this.showValidationFeedback('❌ Not connected to AI. Reconnecting...', 'error');
            
            // Try to reconnect
            if (this.sessionId) {
                window.wsClient.connect(this.sessionId);
            } else {
                this.showValidationFeedback('❌ No session available. Please refresh the page.', 'error');
            }
            return;
        }
        
        // Show sending status
        this.messageInput.disabled = true;
        this.sendBtn.disabled = true;
        
        try {
            // Send message via WebSocket
            window.wsClient.sendMessage({
                type: 'context_update',
                event_type: 'chat_message',
                message: message,
                context: {
                    canvas_mode: true,
                    tool: this.currentTool
                }
            });
            
            // Clear input
            this.messageInput.value = '';
            
            // Show sent message feedback
            this.showValidationFeedback(`📤 Sent: ${message}`, 'info');
            
            console.log('✅ Message sent:', message);
        } catch (error) {
            console.error('❌ Failed to send message:', error);
            this.showValidationFeedback('❌ Failed to send message. Please try again.', 'error');
        }
        
        // Re-enable input
        setTimeout(() => {
            this.messageInput.disabled = false;
            this.sendBtn.disabled = false;
            this.messageInput.focus();
        }, 500);
    }
    
    // ==================== AI DRAWING SYSTEM ====================
    
    initAIDrawingSystem() {
        // Create pen cursor element
        this.penCursor = document.createElement('div');
        this.penCursor.className = 'ai-pen-cursor';
        this.penCursor.style.display = 'none';
        this.canvas.parentElement.appendChild(this.penCursor);
        
        // Add CSS for pen cursor
        if (!document.getElementById('ai-drawing-styles')) {
            const style = document.createElement('style');
            style.id = 'ai-drawing-styles';
            style.textContent = `
                .ai-pen-cursor {
                    position: absolute;
                    width: 12px;
                    height: 12px;
                    background: radial-gradient(circle, rgba(0,212,255,1) 0%, rgba(0,212,255,0) 70%);
                    border-radius: 50%;
                    pointer-events: none;
                    z-index: 1000;
                    transform: translate(-50%, -50%);
                    box-shadow: 0 0 10px rgba(0,212,255,0.8);
                    transition: all 0.05s linear;
                }
                
                .ai-handwriting {
                    font-family: 'Caveat', cursive;
                }
                
                .ai-handwriting-indie {
                    font-family: 'Indie Flower', cursive;
                }
                
                .ai-handwriting-marker {
                    font-family: 'Permanent Marker', cursive;
                }
            `;
            document.head.appendChild(style);
        }
        
        console.log('✨ AI Drawing System initialized');
    }
    
    async startAIDrawing(commands) {
        if (this.aiDrawingActive) {
            console.log('⏳ AI Drawing already in progress, queueing commands');
            this.aiDrawingQueue.push(...commands);
            return;
        }
        
        this.aiDrawingActive = true;
        console.log('🎨 Starting AI Drawing sequence:', commands.length, 'commands');
        
        for (const cmd of commands) {
            await this.executeDrawCommand(cmd);
        }
        
        // Process queued commands
        if (this.aiDrawingQueue.length > 0) {
            const queued = this.aiDrawingQueue.splice(0);
            await this.startAIDrawing(queued);
        } else {
            this.aiDrawingActive = false;
            this.hidePenCursor();
            console.log('✅ AI Drawing sequence complete');
        }
    }
    
    async executeDrawCommand(cmd) {
        this.currentAICommand = cmd;
        console.log('  Executing:', cmd.action, '-', cmd.content?.substring(0, 30));
        
        switch(cmd.action) {
            case 'write_text':
                await this.aiWriteText(cmd);
                break;
            case 'write_equation':
                await this.aiWriteEquation(cmd);
                break;
            case 'draw_diagram':
                await this.aiDrawDiagram(cmd);
                break;
            case 'draw_array':
                await this.aiDrawArray(cmd);
                break;
            case 'draw_tree':
                await this.aiDrawTree(cmd);
                break;
            case 'highlight':
                await this.aiHighlight(cmd);
                break;
            default:
                console.warn('Unknown AI command:', cmd.action);
        }
        
        // Pause after command
        if (cmd.pause_after) {
            await this.delay(cmd.pause_after);
        }
        
        this.currentAICommand = null;
    }
    
    async aiWriteText(cmd) {
        const { content, position, style, font, color, size, duration } = cmd;
        
        // Convert world coordinates to screen
        const screenPos = this.worldToScreen(position.x, position.y);
        
        // Measure text width
        this.ctx.save();
        this.ctx.font = `${size}px ${font}, cursive`;
        const metrics = this.ctx.measureText(content);
        const textWidth = metrics.width;
        this.ctx.restore();
        
        // Calculate pen trail path (start to end of text)
        const pathLength = textWidth;
        const numSteps = Math.max(20, Math.floor(duration / 16));  // 60 FPS target
        const stepDelay = duration / numSteps;
        
        // Show pen cursor
        this.showPenCursor(screenPos.x, screenPos.y);
        
        // Animate pen cursor moving across text path
        for (let i = 0; i <= numSteps; i++) {
            const progress = i / numSteps;
            const currentX = screenPos.x + (textWidth * progress);
            
            // Natural jitter (±1-2px)
            const jitterX = (Math.random() - 0.5) * 2;
            const jitterY = (Math.random() - 0.5) * 2;
            
            this.movePenCursor(currentX + jitterX, screenPos.y + jitterY);
            
            // Progressively reveal text
            this.ctx.save();
            this.ctx.translate(this.offsetX, this.offsetY);
            this.ctx.scale(this.scale, this.scale);
            
            // Clip to reveal only up to cursor position
            this.ctx.beginPath();
            this.ctx.rect(0, 0, position.x + (metrics.width * progress / this.scale), 10000);
            this.ctx.clip();
            
            // Draw text
            this.ctx.font = `${size}px ${font}, cursive`;
            this.ctx.fillStyle = color;
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(content, position.x, position.y);
            
            this.ctx.restore();
            
            await this.delay(stepDelay);
        }
        
        // Add to permanent paths
        this.paths.push({
            type: 'ai_text',
            content,
            position,
            font,
            color,
            size,
            style
        });
        
        this.saveState();
    }
    
    async aiWriteEquation(cmd) {
        // Similar to text but with slower pace for symbols
        await this.aiWriteText({
            ...cmd,
            duration: cmd.duration * 1.5,  // Slower for equations
            font: 'monospace'
        });
    }
    
    async aiDrawDiagram(cmd) {
        const { content, position, color, duration } = cmd;
        
        // Parse diagram type from content (format: "type:label")
        const [diagramType, label] = content.split(':');
        
        switch(diagramType) {
            case 'rectangle':
                await this.aiDrawRectangle(position, color, duration);
                break;
            case 'arrow':
                await this.aiDrawArrow(position, color, duration);
                break;
            case 'circle':
                await this.aiDrawCircle(position, color, duration);
                break;
        }
        
        // Add label if present
        if (label) {
            await this.aiWriteText({
                content: label,
                position: { x: position.x || position.start?.[0], y: (position.y || position.start?.[1]) - 20 },
                font: 'Indie Flower',
                color: color,
                size: 16,
                duration: label.length * 50
            });
        }
    }
    
    async aiDrawRectangle(pos, color, duration) {
        const { x, y, width, height } = pos;
        const screenStart = this.worldToScreen(x, y);
        
        // Animate drawing rectangle stroke by stroke
        const corners = [
            [[x, y], [x + width, y]],           // Top
            [[x + width, y], [x + width, y + height]],  // Right
            [[x + width, y + height], [x, y + height]], // Bottom
            [[x, y + height], [x, y]]           // Left
        ];
        
        for (const [start, end] of corners) {
            await this.aiDrawLine(start, end, color, duration / 4);
        }
        
        this.paths.push({
            type: 'ai_rectangle',
            x, y, width, height, color
        });
    }
    
    async aiDrawArrow(pos, color, duration) {
        const { start, end } = pos;
        
        // Draw line
        await this.aiDrawLine(start, end, color, duration * 0.8);
        
        // Draw arrowhead
        const angle = Math.atan2(end[1] - start[1], end[0] - start[0]);
        const arrowSize = 10;
        
        const head1 = [
            end[0] - arrowSize * Math.cos(angle - Math.PI / 6),
            end[1] - arrowSize * Math.sin(angle - Math.PI / 6)
        ];
        const head2 = [
            end[0] - arrowSize * Math.cos(angle + Math.PI / 6),
            end[1] - arrowSize * Math.sin(angle + Math.PI / 6)
        ];
        
        await this.aiDrawLine(end, head1, color, duration * 0.1);
        await this.aiDrawLine(end, head2, color, duration * 0.1);
        
        this.paths.push({
            type: 'ai_arrow',
            start, end, color
        });
    }
    
    async aiDrawCircle(pos, color, duration) {
        const { x, y, radius } = pos;
        const numSteps = Math.max(30, Math.floor(duration / 16));
        const stepDelay = duration / numSteps;
        
        for (let i = 0; i <= numSteps; i++) {
            const progress = i / numSteps;
            const angle = progress * Math.PI * 2;
            
            const currentX = x + radius * Math.cos(angle);
            const currentY = y + radius * Math.sin(angle);
            
            const screenPos = this.worldToScreen(currentX, currentY);
            this.movePenCursor(screenPos.x, screenPos.y);
            
            // Draw arc
            this.ctx.save();
            this.ctx.translate(this.offsetX, this.offsetY);
            this.ctx.scale(this.scale, this.scale);
            
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius, 0, angle);
            this.ctx.stroke();
            
            this.ctx.restore();
            
            await this.delay(stepDelay);
        }
        
        this.paths.push({
            type: 'ai_circle',
            x, y, radius, color
        });
    }
    
    async aiDrawLine(start, end, color, duration) {
        const distance = Math.sqrt(
            Math.pow(end[0] - start[0], 2) + Math.pow(end[1] - start[1], 2)
        );
        
        const numSteps = Math.max(10, Math.floor(duration / 16));
        const stepDelay = duration / numSteps;
        
        for (let i = 0; i <= numSteps; i++) {
            const progress = i / numSteps;
            const currentX = start[0] + (end[0] - start[0]) * progress;
            const currentY = start[1] + (end[1] - start[1]) * progress;
            
            const screenPos = this.worldToScreen(currentX, currentY);
            this.movePenCursor(screenPos.x, screenPos.y);
            
            // Draw line segment
            this.ctx.save();
            this.ctx.translate(this.offsetX, this.offsetY);
            this.ctx.scale(this.scale, this.scale);
            
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.moveTo(start[0], start[1]);
            this.ctx.lineTo(currentX, currentY);
            this.ctx.stroke();
            
            this.ctx.restore();
            
            await this.delay(stepDelay);
        }
    }
    
    async aiDrawArray(cmd) {
        // Array drawing is handled by multiple rectangle + text commands
        // This is a placeholder for complex array visualizations
        console.log('Drawing array:', cmd);
    }
    
    async aiDrawTree(cmd) {
        // Tree drawing is handled by multiple line + circle commands
        // This is a placeholder for complex tree visualizations
        console.log('Drawing tree:', cmd);
    }
    
    async aiHighlight(cmd) {
        const { position, color, duration } = cmd;
        const { x, y, width, height } = position;
        
        // Fade in highlight
        const steps = 20;
        for (let i = 0; i <= steps; i++) {
            const alpha = (i / steps) * 0.3;  // Max 30% opacity
            
            this.ctx.save();
            this.ctx.translate(this.offsetX, this.offsetY);
            this.ctx.scale(this.scale, this.scale);
            
            this.ctx.fillStyle = color.replace(')', `, ${alpha})`);
            this.ctx.fillRect(x, y, width, height);
            
            this.ctx.restore();
            
            await this.delay(duration / steps);
        }
        
        this.paths.push({
            type: 'ai_highlight',
            x, y, width, height, color
        });
    }
    
    showPenCursor(x, y) {
        this.penCursor.style.display = 'block';
        this.penCursor.style.left = `${x}px`;
        this.penCursor.style.top = `${y}px`;
    }
    
    movePenCursor(x, y) {
        this.penCursor.style.left = `${x}px`;
        this.penCursor.style.top = `${y}px`;
    }
    
    hidePenCursor() {
        this.penCursor.style.display = 'none';
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // ==================== END AI DRAWING SYSTEM ====================
    
    showValidationFeedback(message, type = 'info') {
        // Create feedback modal/toast
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = `validation-feedback ${type}`;
        feedbackDiv.innerHTML = `
            <div class="feedback-content">
                <div class="feedback-icon">
                    ${type === 'success' ? '✓' : 'ℹ'}
                </div>
                <div class="feedback-message">${message}</div>
                <button class="feedback-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add styles if not already present
        if (!document.getElementById('canvas-feedback-styles')) {
            const style = document.createElement('style');
            style.id = 'canvas-feedback-styles';
            style.textContent = `
                .validation-feedback {
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    max-width: 400px;
                    z-index: 1000;
                    animation: slideIn 0.3s ease;
                }
                .feedback-content {
                    background: rgba(0, 0, 0, 0.9);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(0, 212, 255, 0.3);
                    border-radius: 12px;
                    padding: 20px;
                    display: flex;
                    align-items: flex-start;
                    gap: 15px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                }
                .feedback-icon {
                    font-size: 24px;
                    color: #00d4ff;
                }
                .feedback-message {
                    flex: 1;
                    color: white;
                    line-height: 1.6;
                }
                .feedback-close {
                    background: none;
                    border: none;
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 24px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                }
                .feedback-close:hover {
                    color: white;
                }
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(feedbackDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (feedbackDiv.parentElement) {
                feedbackDiv.remove();
            }
        }, 10000);
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
