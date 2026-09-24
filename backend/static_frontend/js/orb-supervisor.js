// ===================================
// ORB SUPERVISOR - MAIN CONTROLLER
// Integrates 3D Orb with Django Backend
// ===================================

const CONFIG = {
    SESSION_TIMEOUT: 30 * 60 * 1000,  // 30 minutes
    TRANSCRIPT_FADE_DELAY: 5000,      // 5 seconds
    WEBSOCKET_RECONNECT_DELAY: 3000,  // 3 seconds
    MAX_RETRY_ATTEMPTS: 3,
    
    ROUTES: {
        'canvas': 'canvas.html',
        'editor': 'editor.html',
        'assessment': 'assessment.html',
        'dashboard': 'dashboard.html',
        'voice': 'voice.html'
    }
};

class OrbSupervisor {
    constructor() {
        this.sessionId = null;
        this.authenticated = false;
        this.orb = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioContext = null;
        this.audioChunks = [];
        this.transcriptTimeout = null;
        this.sessionTimeout = null;
        
        this.messageInput = null;
        this.sendBtn = null;
        this.micBtn = null;
        this.transcriptText = null;
    }
    
    async init() {
        try {
            console.log('🚀 Initializing Orb Supervisor...');
            
            // 1. Check Authentication
            this.authenticated = await this.checkAuthWithTimeout();
            if (!this.authenticated) {
                window.location.href = '/login.html';
                return;
            }
            
            // 2. Get or Create Session
            this.sessionId = await this.getSessionWithRetry();
            console.log('✅ Session ID:', this.sessionId);
            
            // 3. Initialize UI Elements
            this.initUIElements();
            
            // 4. Initialize 3D Orb
            this.orb = new OrbVisualizer('orb-canvas-container');
            
            // 5. Connect WebSocket
            this.connectWebSocket();
            
            // 6. Setup Session Timeout
            this.setupSessionTimeout();
            
            console.log('✅ Orb Supervisor Ready');
            
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            this.handleInitError(error);
        }
    }
    
    async checkAuthWithTimeout() {
        const authPromise = AuthGuard.checkAuth();
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Auth timeout')), 5000)
        );
        
        return await Promise.race([authPromise, timeoutPromise]);
    }
    
    async getSessionWithRetry() {
        for (let i = 0; i < CONFIG.MAX_RETRY_ATTEMPTS; i++) {
            try {
                const session = await window.sessionManager.getOrCreateSession();
                return session.id || session.session_id;
            } catch (error) {
                if (i === CONFIG.MAX_RETRY_ATTEMPTS - 1) throw error;
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
            }
        }
    }
    
    initUIElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.micBtn = document.getElementById('mic-btn');
        this.transcriptText = document.getElementById('transcript-text');
        
        // Event listeners
        this.sendBtn.addEventListener('click', () => this.sendTextMessage());
        this.micBtn.addEventListener('click', () => this.toggleVoiceInput());
        
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });
        
        // Activity tracking for session timeout
        ['keypress', 'click', 'mousemove', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => this.resetSessionTimeout(), { passive: true });
        });
    }
    
    connectWebSocket() {
        window.wsClient.connect(this.sessionId);
        
        window.wsClient.onConnect(() => {
            console.log('✅ WebSocket connected');
            if (this.orb) {
                this.orb.setState('NEUTRAL');
            }
            // Don't show initial text - keep transcript empty
        });
        
        window.wsClient.onMessage((data) => {
            this.handleBackendMessage(data);
        });
        
        window.wsClient.onBinaryMessage((audioData) => {
            this.handleAudioResponse(audioData);
        });
        
        window.wsClient.onDisconnect(() => {
            console.log('⚠️ WebSocket disconnected');
            if (this.orb) {
                this.orb.setState('ALERT');
            }
            this.updateTranscript('Disconnected - Reconnecting...', false);
        });
        
        window.wsClient.onError((error) => {
            console.error('❌ WebSocket error:', error);
        });
    }
    
    handleBackendMessage(data) {
        console.log('📨 Backend Message:', data);
        
        switch(data.type) {
            case 'audio_ack':
                // Voice input acknowledged
                if (data.emotion) {
                    this.orb?.updateEmotion(data.emotion);
                }
                break;
            
            case 'thinking':
                // AI is processing — show live feedback
                if (this.orb) this.orb.setState('THINKING');
                if (data.user_text) {
                    this.updateTranscript(`You said: "${data.user_text}" — thinking...`, false);
                } else {
                    this.updateTranscript(data.message || '🤔 Thinking...', false);
                }
                break;
                
            case 'ai_response':
            case 'teacher_response':
                // AI responding
                if (this.orb) {
                    this.orb.setState('HAPPY');
                }
                this.updateTranscript(data.message || data.text);
                
                // Return to neutral after 3 seconds
                setTimeout(() => {
                    if (this.orb) this.orb.setState('NEUTRAL');
                }, 3000);
                break;
                
            case 'route_to_view':
                // Routing to another page
                this.handlePageRouting(data);
                break;
                
            case 'telemetry_update':
                // Gap 5 telemetry alerts
                if (data.alerts && data.alerts.length > 0) {
                    const alert = data.alerts[0];
                    if (alert.severity === 'high') {
                        if (this.orb) {
                            this.orb.setState('ALERT');
                        }
                        this.updateTranscript(`⚠️ ${alert.message}`);
                    }
                }
                break;
                
            case 'canvas_command':
                // Visual learning mode
                if (this.orb) {
                    this.orb.setState('THINKING');
                }
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    handlePageRouting(data) {
        const targetPage = CONFIG.ROUTES[data.view];
        if (targetPage) {
            if (this.orb) {
                this.orb.setState('THINKING');
            }
            this.updateTranscript(`Opening ${data.view}...`, false);
            
            setTimeout(() => {
                window.location.href = `${targetPage}?session_id=${this.sessionId}`;
            }, 1500);
        }
    }
    
    async handleAudioResponse(audioData) {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // Start speaking animation
        if (this.orb) {
            this.orb.setState('HAPPY');
            this.orb.startSpeakingAnimation();
        }
        
        this.audioContext.decodeAudioData(audioData, (buffer) => {
            const source = this.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(this.audioContext.destination);
            source.start(0);
            
            source.onended = () => {
                // Stop speaking animation
                if (this.orb) {
                    this.orb.stopSpeakingAnimation();
                    setTimeout(() => {
                        this.orb.setState('NEUTRAL');
                    }, 500);
                }
            };
        }, (error) => {
            console.error('Audio decode error:', error);
            if (this.orb) {
                this.orb.stopSpeakingAnimation();
            }
        });
    }
    
    async sendTextMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        console.log('📤 Sending text:', message);
        
        // Update UI
        this.messageInput.value = '';
        this.messageInput.disabled = true;
        this.sendBtn.disabled = true;
        
        if (this.orb) {
            this.orb.setState('THINKING');
        }
        this.updateTranscript(`You: ${message}`, false);
        
        // Send to backend
        try {
            window.wsClient.sendMessage({
                type: 'context_update',
                event_type: 'chat_message',
                message: message,
                context: {
                    canvas_mode: false,
                    tool: 'text'
                }
            });
        } catch (error) {
            console.error('Failed to send message:', error);
            this.updateTranscript('Error sending message');
            if (this.orb) {
                this.orb.setState('ALERT');
            }
        } finally {
            this.messageInput.disabled = false;
            this.sendBtn.disabled = false;
            this.messageInput.focus();
        }
    }
    
    async toggleVoiceInput() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }
    
    async startRecording() {
        try {
            console.log('🎤 Starting voice input...');
            
            // Request microphone
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                console.log('🎤 Recording stopped, processing...');
                
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                const arrayBuffer = await audioBlob.arrayBuffer();
                
                // Send to backend
                try {
                    window.wsClient.sendBinary(arrayBuffer);
                    
                    if (this.orb) {
                        this.orb.setState('THINKING');
                    }
                    this.updateTranscript('Processing speech...', false);
                    
                } catch (error) {
                    console.error('Failed to send audio:', error);
                    this.updateTranscript('Error processing speech');
                    if (this.orb) {
                        this.orb.setState('ALERT');
                    }
                }
            };
            
            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.micBtn.classList.add('recording');
            this.messageInput.disabled = true;
            this.sendBtn.disabled = true;
            
            if (this.orb) {
                this.orb.setState('ALERT'); // Listening
            }
            this.updateTranscript('🎤 Listening... (click mic to stop)', false);
            
        } catch (error) {
            console.error('❌ Microphone error:', error);
            this.updateTranscript('Microphone access denied');
            if (this.orb) {
                this.orb.setState('ALERT');
            }
            
            // Show user-friendly error
            if (error.name === 'NotAllowedError') {
                alert('Microphone access denied. Please allow microphone access in your browser settings.');
            } else if (error.name === 'NotFoundError') {
                alert('No microphone found. Please connect a microphone and try again.');
            }
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            console.log('🛑 Stopping recording...');
            this.mediaRecorder.stop();
            
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
            }
            
            this.isRecording = false;
            
            // Update UI
            this.micBtn.classList.remove('recording');
            this.messageInput.disabled = false;
            this.sendBtn.disabled = false;
        }
    }
    
    updateTranscript(text, autoFade = true) {
        if (!this.transcriptText) return;
        
        // Clear existing timeout
        if (this.transcriptTimeout) {
            clearTimeout(this.transcriptTimeout);
        }
        
        // Update text
        this.transcriptText.textContent = text;
        this.transcriptText.classList.remove('fade-out');
        this.transcriptText.classList.add('active');
        
        // Auto-fade after delay
        if (autoFade) {
            this.transcriptTimeout = setTimeout(() => {
                this.transcriptText.classList.remove('active');
                this.transcriptText.classList.add('fade-out');
            }, CONFIG.TRANSCRIPT_FADE_DELAY);
        }
    }
    
    setupSessionTimeout() {
        this.resetSessionTimeout();
    }
    
    resetSessionTimeout() {
        if (this.sessionTimeout) {
            clearTimeout(this.sessionTimeout);
        }
        
        this.sessionTimeout = setTimeout(() => {
            this.handleSessionTimeout();
        }, CONFIG.SESSION_TIMEOUT);
    }
    
    async handleSessionTimeout() {
        console.log('⏱️ Session timeout');
        
        if (this.orb) {
            this.orb.setState('ALERT');
        }
        this.updateTranscript('Session expired due to inactivity', false);
        
        await this.endSession();
    }
    
    async endSession() {
        if (this.orb) {
            this.orb.setState('THINKING');
            this.orb.fadeOut();
        }
        this.updateTranscript('Ending session...', false);
        
        try {
            await window.apiClient.endSession(this.sessionId);
            console.log('✅ Session ended');
            
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 2000);
            
        } catch (error) {
            console.error('Failed to end session:', error);
            if (this.orb) {
                this.orb.setState('ALERT');
            }
            this.updateTranscript('Error ending session');
        }
    }
    
    handleInitError(error) {
        document.body.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100vh; color: #fff; background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);">
                <div style="text-align: center; padding: 40px;">
                    <h1 style="color: #ff0033; margin-bottom: 20px;">⚠️ Initialization Failed</h1>
                    <p style="color: #fff; margin-bottom: 10px;">${error.message}</p>
                    <p style="color: rgba(255,255,255,0.6); margin-bottom: 30px;">Please check your connection and try again</p>
                    <button onclick="location.reload()" style="
                        padding: 15px 30px;
                        background: #00eaff;
                        border: none;
                        border-radius: 8px;
                        color: #000;
                        font-weight: 600;
                        cursor: pointer;
                        font-size: 1rem;
                    ">Retry</button>
                </div>
            </div>
        `;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.orbSupervisor = new OrbSupervisor();
        window.orbSupervisor.init();
    });
} else {
    window.orbSupervisor = new OrbSupervisor();
    window.orbSupervisor.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.orbSupervisor) {
        if (window.orbSupervisor.isRecording) {
            window.orbSupervisor.stopRecording();
        }
        if (window.wsClient) {
            window.wsClient.disconnect();
        }
    }
});
