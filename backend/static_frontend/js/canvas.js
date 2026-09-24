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
        this.endSessionBtn = document.getElementById('endSessionBtn');
        
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

        // Teaching script playback
        this.lastTeachingScript = [];
        this.pendingTeachingScript = [];
        this.pendingTeachingCommands = [];
        this.teachingState = {
            status: 'idle',
            phaseIndex: 0,
            paused: false,
            stop: false,
            skip: false,
            drawnAllCommands: false,
            token: 0
        };
        this.teachPlayBtn = document.getElementById('teachPlayBtn');
        this.teachPauseBtn = document.getElementById('teachPauseBtn');
        this.teachSkipBtn = document.getElementById('teachSkipBtn');
        this.teachStatus = document.getElementById('teachStatus');
        this.phaseBadge = document.getElementById('phaseBadge');
        
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

        if (this.endSessionBtn) {
            this.endSessionBtn.addEventListener('click', () => this.endSessionAndReturn());
        }
        
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

        // Initialize teaching controls
        this.initTeachingControls();
        
        // Initial render
        this.render();
        
        console.log('✨ Canvas Whiteboard initialized (Infinite Canvas Mode + AI Drawing)');
    }

    async endSessionAndReturn() {
        if (this.endSessionInProgress) return;

        const confirmed = confirm('End this session and return to the Supervisor?');
        if (!confirmed) return;

        this.endSessionInProgress = true;
        this.endSessionBtn.disabled = true;
        this.endSessionBtn.textContent = 'Ending...';

        try {
            if (!this.sessionId) {
                const activeSession = await window.apiClient.getActiveSession();
                this.sessionId = activeSession.id || activeSession.session_id || null;
            }

            if (this.sessionId) {
                await window.apiClient.endSession(this.sessionId);
            }
        } catch (error) {
            console.error('Failed to end session:', error);
        }

        window.location.href = 'canvas.html';
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
            
            const urlParams    = new URLSearchParams(window.location.search);
            const urlSessionId = urlParams.get('session_id');
            const urlTopicId   = urlParams.get('topic_id');
            if (urlSessionId) {
                this.sessionId = urlSessionId;
                console.log('✅ Canvas session resumed:', this.sessionId);
            } else {
                const activeSession = await window.apiClient.getActiveSession();
                if (activeSession && (activeSession.id || activeSession.session_id)) {
                    this.sessionId = activeSession.id || activeSession.session_id;
                    console.log('✅ Canvas session reused:', this.sessionId);
                } else {
                    const session = await window.apiClient.startSession(urlTopicId);
                    this.sessionId = session.id || session.session_id;
                    console.log('✅ Canvas session started (topic:', urlTopicId, '):', this.sessionId);
                }
            }
            
            // Set up WebSocket callbacks BEFORE connecting
            window.wsClient.onConnect(() => {
                this.wsConnected = true;
                this.updateConnectionStatus('connected');
                console.log('✅ Canvas WebSocket connected');
                window.wsClient.sendMessage({
                    type: 'canvas_ready',
                    event_type: 'canvas_ready',
                    context: { canvas_mode: true }
                });
            });
            
            window.wsClient.onMessage((data) => {
                console.log('📨 Canvas received WebSocket message:', {
                    type: data.type,
                    hasMessage: !!data.message,
                    hasCanvasCommands: !!data.canvas_commands,
                    commandCount: data.canvas_commands ? data.canvas_commands.length : 0,
                    fullData: data
                });
                
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
        console.log('🔍 handleAIFeedback called:', {
            type: data.type,
            hasMessage: !!data.message,
            hasCanvasCommands: !!data.canvas_commands,
            isArray: Array.isArray(data.canvas_commands),
            commandCount: data.canvas_commands ? data.canvas_commands.length : 0
        });

        if (data.teaching_script && Array.isArray(data.teaching_script)) {
            this.lastTeachingScript = data.teaching_script;
            console.log('📘 Teaching script received:', data.teaching_script);
            if (!data.canvas_commands || data.canvas_commands.length === 0) {
                this.queueTeachingPlayback(data.teaching_script, []);
            }
        }
        
        // Mode switching — tree vs canvas
        if (data.type === 'mode_transition') {
            if (data.to === 'tree' && data.tree_data) {
                window.modeManager?.switchToTree(data.tree_data);
            } else {
                window.modeManager?.switchToCanvas();
            }
        }

        if (data.type === 'teacher_response') {
            if (data.render_mode === 'tree' && data.tree_data) {
                window.modeManager?.switchToTree(data.tree_data);
            } else if (data.render_mode === 'canvas' || data.render_mode === 'default') {
                window.modeManager?.switchToCanvas();
            }
        }

        if (data.type === 'ai_response' && data.message) {
            this.showValidationFeedback(data.message, 'success');
        }
        
        // Handle AI drawing commands
        if (data.type === 'ai_drawing' && data.canvas_commands && data.canvas_commands.length > 0) {
            console.log('🎨 Received AI drawing commands:', data.canvas_commands.length);
            console.log('  Commands:', data.canvas_commands);
            if (data.teaching_script && Array.isArray(data.teaching_script)) {
                this.queueTeachingPlayback(data.teaching_script, data.canvas_commands);
            } else {
                this.startAIDrawing(data.canvas_commands);
            }
        }
        
        // Handle teacher response with canvas commands
        if (data.type === 'teacher_response' && data.canvas_commands && data.canvas_commands.length > 0) {
            console.log('🎨 Teacher response includes canvas commands:', data.canvas_commands.length);
            console.log('  Commands:', data.canvas_commands);
            if (data.teaching_script && Array.isArray(data.teaching_script)) {
                this.queueTeachingPlayback(data.teaching_script, data.canvas_commands);
            } else {
                this.startAIDrawing(data.canvas_commands);
            }
        }
        
        // Debug: Log if expected but not found
        if (data.type === 'teacher_response' && (!data.canvas_commands || data.canvas_commands.length === 0)) {
            console.warn('⚠️ Teacher response received but NO canvas commands found');
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

        // Create Khan Academy style narration subtitle bar
        if (!document.getElementById('ka-narration-bar')) {
            this.narrationBar = document.createElement('div');
            this.narrationBar.id = 'ka-narration-bar';
            this.narrationBar.style.cssText = [
                'position:fixed', 'bottom:28px', 'left:50%',
                'transform:translateX(-50%)',
                'max-width:680px', 'width:90%',
                'background:rgba(10,14,26,0.88)',
                'backdrop-filter:blur(12px)',
                'border:1px solid rgba(0,212,255,0.25)',
                'border-radius:14px',
                'padding:14px 22px',
                'font-family:Inter,sans-serif',
                'font-size:15px',
                'line-height:1.55',
                'color:#e8f4ff',
                'letter-spacing:0.01em',
                'z-index:9999',
                'display:none',
                'transition:opacity 0.35s',
                'box-shadow:0 8px 32px rgba(0,0,0,0.55)'
            ].join(';');
            document.body.appendChild(this.narrationBar);
        } else {
            this.narrationBar = document.getElementById('ka-narration-bar');
        }
        this._narrationHideTimer = null;
        
        // Add CSS for pen cursor & narration
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
                .ai-handwriting { font-family: 'Caveat', cursive; }
                .ai-handwriting-indie { font-family: 'Indie Flower', cursive; }
                .ai-handwriting-marker { font-family: 'Permanent Marker', cursive; }
            `;
            document.head.appendChild(style);
        }
        
        console.log('✨ AI Drawing System + KA Narration Bar initialized');
    }

    // ── Narration subtitle helpers ──────────────────────────────────
    showNarration(text) {
        if (!this.narrationBar || !text) return;
        clearTimeout(this._narrationHideTimer);
        this.narrationBar.textContent = '';
        this.narrationBar.style.display = 'block';
        this.narrationBar.style.opacity = '1';
        // Typewriter reveal: 35ms per char, max 2s
        const chars = [...text];
        const delay = Math.min(35, 1800 / (chars.length || 1));
        chars.forEach((ch, i) => {
            setTimeout(() => {
                if (this.narrationBar) this.narrationBar.textContent += ch;
            }, i * delay);
        });
        // Auto-hide 4s after last char
        this._narrationHideTimer = setTimeout(() => this.hideNarration(), text.length * delay + 4000);
    }

    hideNarration() {
        if (!this.narrationBar) return;
        this.narrationBar.style.opacity = '0';
        setTimeout(() => {
            if (this.narrationBar) this.narrationBar.style.display = 'none';
        }, 380);
    }

    // ==================== TEACHING SCRIPT PLAYBACK ====================

    initTeachingControls() {
        if (this.teachPlayBtn) {
            this.teachPlayBtn.addEventListener('click', () => this.startTeachingPlayback());
        }
        if (this.teachPauseBtn) {
            this.teachPauseBtn.addEventListener('click', () => this.pauseTeachingPlayback());
        }
        if (this.teachSkipBtn) {
            this.teachSkipBtn.addEventListener('click', () => this.skipTeachingPhase());
        }
        this.updateTeachingStatus('Teaching: Idle');
        this.setPhaseBadge('Phase: Idle');
    }

    queueTeachingPlayback(script, commands) {
        this.pendingTeachingScript = Array.isArray(script) ? script : [];
        this.pendingTeachingCommands = Array.isArray(commands) ? commands : [];

        this.teachingState.stop = true;
        this.teachingState.paused = false;
        this.teachingState.skip = false;
        this.teachingState.phaseIndex = 0;
        this.teachingState.drawnAllCommands = false;
        this.teachingState.token += 1;

        const phaseCount = this.pendingTeachingScript.length;
        this.updateTeachingStatus(`Teaching: Ready (${phaseCount} phase${phaseCount === 1 ? '' : 's'})`);
        this.setPhaseBadge('Phase: Ready');

        this.startTeachingPlayback();
    }

    async startTeachingPlayback() {
        if (this.teachingState.status === 'playing' && !this.teachingState.paused) {
            return;
        }

        if (this.teachingState.status === 'playing' && this.teachingState.paused) {
            this.teachingState.paused = false;
            this.updateTeachingStatus('Teaching: Playing');
            this.setPhaseBadge('Phase: Playing');
            return;
        }

        const script = this.pendingTeachingScript.length > 0 ? this.pendingTeachingScript : this.lastTeachingScript;
        if (!script || script.length === 0) {
            this.updateTeachingStatus('Teaching: No script');
            this.setPhaseBadge('Phase: --');
            return;
        }

        const commands = this.pendingTeachingCommands.length > 0 ? this.pendingTeachingCommands : [];
        const stageMap = this.groupCommandsByStage(commands);

        this.teachingState.status = 'playing';
        this.teachingState.paused = false;
        this.teachingState.stop = false;
        this.teachingState.skip = false;
        this.teachingState.drawnAllCommands = false;
        this.teachingState.token += 1;
        const token = this.teachingState.token;

        this.updateTeachingStatus('Teaching: Playing');
        this.setPhaseBadge('Phase: Playing');

        for (let i = 0; i < script.length; i += 1) {
            if (this.teachingState.stop || this.teachingState.token !== token) {
                break;
            }

            const phase = script[i] || {};
            const phaseTitle = phase.title || phase.phase || `Phase ${i + 1}`;
            this.teachingState.phaseIndex = i;
            this.updateTeachingStatus(`Teaching: ${phaseTitle} (${i + 1}/${script.length})`);
            this.setPhaseBadge(`Phase: ${phaseTitle}`);

            // ── Khan Academy style: show narration subtitle + draw on canvas ──
            if (phase.narration) {
                this.showNarration(phase.narration);
            }
            if (phase.prompt) {
                // Quick check beat: show as narration + feedback
                this.showNarration(`🤔 ${phase.prompt}`);
                this.showValidationFeedback(`Quick check: ${phase.prompt}`, 'info');
            }

            await this.waitForResume(token);

            // ── Primary path: beat carries its own draw instruction ──
            if (phase.draw && phase.draw !== 'none') {
                await this.executeKABeat(phase);
            } else {
                // ── Legacy path: look up staged canvas_commands ──
                const stageKey = phase.visual_stage || 'all';
                let phaseCommands = stageMap[stageKey] || [];

                if (phaseCommands.length === 0 && !this.teachingState.drawnAllCommands && stageMap.all && stageMap.all.length > 0) {
                    phaseCommands = stageMap.all;
                    this.teachingState.drawnAllCommands = true;
                }

                if (phaseCommands.length > 0) {
                    await this.startAIDrawing(phaseCommands);
                }
            }

            const pauseAfter = Number(phase.pause_after_ms || 600);
            if (pauseAfter > 0) {
                await this.waitWithPause(pauseAfter, token);
            }

            if (this.teachingState.skip) {
                this.teachingState.skip = false;
            }
        }

        if (!this.teachingState.stop && this.teachingState.token === token) {
            this.teachingState.status = 'idle';
            this.updateTeachingStatus('Teaching: Complete');
            this.setPhaseBadge('Phase: Complete');
            setTimeout(() => this.hideNarration(), 1500);
        }
    }

    // ── Khan Academy Beat Executor ──────────────────────────────────────────
    // Converts a single LLM beat (draw type + position_hint + label + color)
    // into an actual canvas drawing action.
    _kaLayout(hint, canvasW, canvasH, beatIndex) {
        // Map position_hint → world coordinates
        // Canvas world coords: 0..canvasW, 0..canvasH
        const w = canvasW || 1200;
        const h = canvasH || 800;
        const map = {
            top_left:      { x: w * 0.15, y: h * 0.12 },
            top_center:    { x: w * 0.50, y: h * 0.10 },
            top_right:     { x: w * 0.80, y: h * 0.12 },
            center_left:   { x: w * 0.25, y: h * 0.45 },
            center:        { x: w * 0.50, y: h * 0.45 },
            center_right:  { x: w * 0.72, y: h * 0.45 },
            bottom_left:   { x: w * 0.20, y: h * 0.78 },
            bottom_center: { x: w * 0.50, y: h * 0.80 },
            bottom_right:  { x: w * 0.78, y: h * 0.78 },
        };
        // Default: cascade down-center for sequential beats
        return map[hint] || { x: w * 0.50, y: h * (0.15 + (beatIndex % 7) * 0.10) };
    }

    async executeKABeat(beat) {
        const cw = this.canvas.width  / (this.scale || 1);
        const ch = this.canvas.height / (this.scale || 1);
        const idx = this.teachingState.phaseIndex || 0;
        const pos = this._kaLayout(beat.position_hint, cw, ch, idx);
        const color = beat.color || '#00d4ff';
        const label = beat.label || beat.title || '';
        const fontSize = Math.min(Number(beat.size) || 24, 48);
        const drawDuration = 900; // ms for animated strokes

        switch (beat.draw) {
            case 'title_text': {
                // Large bold title centred at top
                const titlePos = this._kaLayout('top_center', cw, ch, 0);
                await this.aiWriteText({
                    content: label,
                    position: { x: titlePos.x - (label.length * fontSize * 0.32), y: titlePos.y },
                    font: 'Permanent Marker',
                    color: color,
                    size: Math.max(fontSize, 32),
                    duration: label.length * 55
                });
                break;
            }
            case 'circle': {
                const radius = Math.min(cw, ch) * 0.12;
                await this.aiDrawCircle(
                    { x: pos.x, y: pos.y, radius },
                    color, drawDuration
                );
                if (label) {
                    await this.aiWriteText({
                        content: label,
                        position: { x: pos.x - label.length * 5, y: pos.y + radius + 18 },
                        font: 'Indie Flower', color, size: 16, duration: label.length * 45
                    });
                }
                break;
            }
            case 'ellipse': {
                const rx = Math.min(cw, ch) * 0.18;
                const ry = Math.min(cw, ch) * 0.11;
                await this.aiDrawEllipse(
                    { x: pos.x, y: pos.y, rx, ry },
                    color, drawDuration
                );
                if (label) {
                    await this.aiWriteText({
                        content: label,
                        position: { x: pos.x - label.length * 5, y: pos.y + ry + 18 },
                        font: 'Indie Flower', color, size: 16, duration: label.length * 45
                    });
                }
                break;
            }
            case 'rectangle': {
                const bw = cw * 0.18;
                const bh = ch * 0.10;
                await this.aiDrawRectangle(
                    { x: pos.x - bw / 2, y: pos.y - bh / 2, width: bw, height: bh },
                    color, drawDuration
                );
                if (label) {
                    await this.aiWriteText({
                        content: label,
                        position: { x: pos.x - label.length * 5, y: pos.y },
                        font: 'Indie Flower', color, size: 15, duration: label.length * 45
                    });
                }
                break;
            }
            case 'arrow': {
                // Draw a downward or rightward arrow depending on position_hint
                const dx = cw * 0.08;
                const start = [pos.x, pos.y];
                const end   = [pos.x + dx, pos.y];
                await this.aiDrawArrow({ start, end }, color, drawDuration);
                if (label) {
                    await this.aiWriteText({
                        content: label,
                        position: { x: pos.x, y: pos.y - 22 },
                        font: 'Indie Flower', color, size: 15, duration: label.length * 45
                    });
                }
                break;
            }
            case 'label_text': {
                await this.aiWriteText({
                    content: label,
                    position: { x: pos.x - label.length * (fontSize * 0.3), y: pos.y },
                    font: 'Caveat', color, size: fontSize, duration: label.length * 50
                });
                break;
            }
            case 'underline': {
                const ulLen = (label.length || 12) * fontSize * 0.55;
                const startU = [pos.x - ulLen / 2, pos.y + 6];
                const endU   = [pos.x + ulLen / 2, pos.y + 6];
                await this.aiDrawLine(startU, endU, color, 500);
                break;
            }
            case 'line': {
                const lineEnd = [pos.x + cw * 0.12, pos.y];
                await this.aiDrawLine([pos.x, pos.y], lineEnd, color, drawDuration);
                break;
            }
            case 'highlight': {
                await this.aiHighlight({
                    position: { x: pos.x - 80, y: pos.y - 20, width: 160, height: 40 },
                    color: color,
                    duration: 600
                });
                break;
            }
            default:
                console.warn('[KA Beat] Unknown draw type:', beat.draw);
        }
    }

    // ── Ellipse drawing (biology-style oval membranes) ──
    async aiDrawEllipse(pos, color, duration) {
        const { x, y, rx, ry } = pos;
        const numSteps = Math.max(40, Math.floor(duration / 16));
        const stepDelay = duration / numSteps;

        for (let i = 0; i <= numSteps; i++) {
            const progress = i / numSteps;
            const angle = progress * Math.PI * 2;
            const cx = x + rx * Math.cos(angle);
            const cy = y + ry * Math.sin(angle);
            const screenPos = this.worldToScreen(cx, cy);
            this.movePenCursor(screenPos.x, screenPos.y);

            this.ctx.save();
            this.ctx.translate(this.offsetX, this.offsetY);
            this.ctx.scale(this.scale, this.scale);
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.ellipse(x, y, rx, ry, 0, 0, angle);
            this.ctx.stroke();
            this.ctx.restore();

            await this.delay(stepDelay);
        }

        this.paths.push({ type: 'ai_ellipse', x, y, rx, ry, color });
        this.saveState();
    }

    pauseTeachingPlayback() {
        if (this.teachingState.status !== 'playing') {
            return;
        }
        this.teachingState.paused = true;
        this.updateTeachingStatus('Teaching: Paused');
        this.setPhaseBadge('Phase: Paused');
    }

    skipTeachingPhase() {
        if (this.teachingState.status !== 'playing') {
            return;
        }
        this.teachingState.skip = true;
        this.updateTeachingStatus('Teaching: Skipping');
        this.setPhaseBadge('Phase: Skipping');
    }

    updateTeachingStatus(message) {
        if (this.teachStatus) {
            this.teachStatus.textContent = message;
        }
    }

    setPhaseBadge(message) {
        if (this.phaseBadge) {
            this.phaseBadge.textContent = message;
        }
    }

    async waitForResume(token) {
        while (this.teachingState.paused && !this.teachingState.stop && this.teachingState.token === token) {
            await this.delay(150);
        }
    }

    async waitWithPause(durationMs, token) {
        let remaining = durationMs;
        while (remaining > 0 && !this.teachingState.stop && this.teachingState.token === token) {
            await this.waitForResume(token);
            if (this.teachingState.skip) {
                break;
            }
            const step = Math.min(200, remaining);
            await this.delay(step);
            remaining -= step;
        }
    }

    groupCommandsByStage(commands) {
        const stageMap = {};
        for (const cmd of commands || []) {
            const stageKey = cmd.visual_stage || cmd.stage || cmd.concept_tag || 'all';
            if (!stageMap[stageKey]) {
                stageMap[stageKey] = [];
            }
            stageMap[stageKey].push(cmd);
        }
        return stageMap;
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
        try {
            const treeData = typeof cmd.content === 'string'
                ? JSON.parse(cmd.content)
                : cmd.content;
            if (treeData && window.modeManager) {
                window.modeManager.switchToTree(treeData);
                await this.delay(cmd.duration || 1500);
            }
        } catch (e) {
            console.warn('aiDrawTree: failed to parse tree data', e);
        }
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
    
    // Initialize canvas whiteboard and expose for ModeManager
    const canvasWhiteboard = new CanvasWhiteboard();
    window.canvasWhiteboard = canvasWhiteboard;
    
    // Save initial empty state
    canvasWhiteboard.saveState();
    
    console.log('✨ Infinite Canvas Whiteboard ready');
    console.log('💡 Controls: Shift+Drag or Middle Mouse to Pan | Scroll to Zoom');
});
