// ===================================
// VOICE ASSISTANT PAGE FUNCTIONALITY
// ===================================

class VoiceAssistant {
    constructor() {
        this.chatHistory = document.getElementById('chatHistory');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.voiceToggleBtn = document.getElementById('voiceToggleBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.quickActionBtns = document.querySelectorAll('.quick-action-btn');
        
        this.isListening = false;
        this.messages = [];
        this.sessionId = null;
        this.wsConnected = false;
        
        // Audio recording properties
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioContext = null;
        this.audioStream = null;
        
        this.init();
    }
    
    async init() {
        // Get session from URL params or create new one
        const urlParams = new URLSearchParams(window.location.search);
        const sessionIdFromUrl = urlParams.get('session_id');
        
        // Start or reuse learning session
        try {
            if (sessionIdFromUrl) {
                this.sessionId = sessionIdFromUrl;
                console.log('✅ Using session from URL:', this.sessionId);
            } else {
                const session = await window.sessionManager.getOrCreateSession();
                this.sessionId = session.id || session.session_id;
                console.log('✅ Session started:', this.sessionId);
            }
            
            // Connect WebSocket
            window.wsClient.connect(this.sessionId);
            
            // Set up WebSocket callbacks
            window.wsClient.onConnect(() => {
                this.wsConnected = true;
                console.log('✅ WebSocket connected');
            });
            
            window.wsClient.onMessage((data) => {
                // Handle routing messages
                if (data.type === 'route_to_view') {
                    this.handlePageRouting(data);
                } else {
                    this.handleAIMessage(data);
                }
            });
            
            window.wsClient.onBinaryMessage((audioData) => {
                this.playAudioResponse(audioData);
            });
            
            window.wsClient.onDisconnect(() => {
                this.wsConnected = false;
                console.log('⚠️ WebSocket disconnected');
            });
            
            window.wsClient.onError((error) => {
                console.error('❌ WebSocket error:', error);
            });
        } catch (error) {
            console.error('❌ Failed to initialize session:', error);
        }
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (this.wsConnected) {
                window.wsClient.disconnect();
            }
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.stopRecording();
            }
        });
        
        // Send button click
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Voice toggle
        this.voiceToggleBtn.addEventListener('click', () => this.toggleVoice());
        
        // Quick actions
        this.quickActionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });
        
        // Update waveform based on voice state
        this.updateWaveform();
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message
        this.addMessage('user', message);
        
        // Clear input
        this.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send via WebSocket if connected
        if (this.wsConnected) {
            window.wsClient.sendMessage({
                type: 'context_update',
                event_type: 'chat_message',
                message: message,
                session_id: this.sessionId
            });
        } else {
            // Fallback to mock response if WebSocket not connected
            setTimeout(() => {
                this.hideTypingIndicator();
                this.addMessage('ai', "I'm having trouble connecting. Please refresh the page.");
            }, 1000);
        }
    }
    
    handleAIMessage(data) {
        // Hide typing indicator
        this.hideTypingIndicator();
        
        // Add AI response to chat
        if (data.text || data.message) {
            this.addMessage('ai', data.text || data.message);
        }
    }
    
    handlePageRouting(data) {
        const { view, intent } = data;
        console.log(`🔀 Routing to ${view} page (intent: ${intent})`);
        
        // Show notification before redirect
        const notification = document.createElement('div');
        notification.className = 'routing-notification';
        notification.textContent = `Switching to ${view} mode...`;
        document.body.appendChild(notification);
        
        // Redirect after brief delay
        setTimeout(() => {
            const routes = {
                'canvas': `/canvas.html?session_id=${this.sessionId}`,
                'editor': `/code-editor.html?session_id=${this.sessionId}`,
                'assessment': `/assessment.html?session_id=${this.sessionId}`,
                'dashboard': `/dashboard.html`,
                'voice': `/voice.html?session_id=${this.sessionId}`
            };
            
            const targetUrl = routes[view];
            if (targetUrl) {
                window.location.href = targetUrl;
            }
        }, 1000);
    }
    
    addMessage(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message fade-in`;
        
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    ${role === 'ai' 
                        ? '<circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path>'
                        : '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>'
                    }
                </svg>
            </div>
            <div class="message-content">
                <p class="message-sender">${role === 'ai' ? 'Vaathiyar' : 'You'}</p>
                <p class="message-text">${text}</p>
                <span class="message-time">${time}</span>
            </div>
        `;
        
        this.chatHistory.appendChild(messageDiv);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
        
        // Store message
        this.messages.push({ role, text, time });
    }
    
    generateAIResponse(userMessage) {
        // Simple response generation (in production, this would call your AI backend)
        const responses = {
            'explain': "I'd be happy to explain! Could you specify which topic you'd like me to explain?",
            'example': "Sure! Let me provide you with a practical example...",
            'quiz': "Great! Let's test your knowledge. I'll prepare some questions for you.",
            'default': "I understand you're asking about: \"" + userMessage + "\". Let me help you with that..."
        };
        
        let response = responses.default;
        
        // Check for keywords
        if (userMessage.toLowerCase().includes('explain')) {
            response = responses.explain;
        } else if (userMessage.toLowerCase().includes('example')) {
            response = responses.example;
        } else if (userMessage.toLowerCase().includes('quiz') || userMessage.toLowerCase().includes('test')) {
            response = responses.quiz;
        }
        
        this.addMessage('ai', response);
    }
    
    handleQuickAction(action) {
        const actionMessages = {
            'explain': 'Can you explain this concept to me?',
            'example': 'Can you give me an example?',
            'quiz': 'I want to take a quiz on this topic'
        };
        
        const message = actionMessages[action];
        if (message) {
            this.messageInput.value = message;
            this.sendMessage();
        }
    }
    
    toggleVoice() {
        this.isListening = !this.isListening;
        
        if (this.isListening) {
            this.voiceToggleBtn.classList.add('active');
            this.startRecording();
            console.log('🎤 Voice input activated');
            
            // Update waveform
            if (window.waveformVisualizer) {
                window.waveformVisualizer.setListening(true);
            }
        } else {
            this.voiceToggleBtn.classList.remove('active');
            this.stopRecording();
            console.log('🎤 Voice input deactivated');
            
            // Update waveform
            if (window.waveformVisualizer) {
                window.waveformVisualizer.setListening(false);
            }
        }
    }
    
    async startRecording() {
        try {
            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                } 
            });
            
            // Initialize audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 16000
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.sendAudioToBackend(audioBlob);
                this.audioChunks = [];
            };
            
            // Start recording
            this.mediaRecorder.start();
            console.log('🔴 Recording started');
            
        } catch (error) {
            console.error('❌ Microphone access denied:', error);
            this.isListening = false;
            this.voiceToggleBtn.classList.remove('active');
            alert('Please allow microphone access to use voice features.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            console.log('⏹️ Recording stopped');
        }
        
        // Stop audio tracks
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
    }
    
    async sendAudioToBackend(audioBlob) {
        try {
            // Convert WebM to ArrayBuffer
            const arrayBuffer = await audioBlob.arrayBuffer();
            
            // Convert to WAV format if needed (WebM → WAV conversion)
            const wavBlob = await this.convertToWAV(arrayBuffer);
            const wavArrayBuffer = await wavBlob.arrayBuffer();
            
            // Send binary audio via WebSocket
            if (this.wsConnected) {
                window.wsClient.sendBinary(wavArrayBuffer);
                this.showTypingIndicator();
            }
        } catch (error) {
            console.error('❌ Error sending audio:', error);
        }
    }
    
    async convertToWAV(webmArrayBuffer) {
        // Decode WebM audio to PCM
        const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const audioBuffer = await audioContext.decodeAudioData(webmArrayBuffer);
        
        // Extract PCM data (mono, 16-bit)
        const channelData = audioBuffer.getChannelData(0); // Get mono channel
        const pcmData = new Int16Array(channelData.length);
        
        // Convert float32 to int16
        for (let i = 0; i < channelData.length; i++) {
            const s = Math.max(-1, Math.min(1, channelData[i]));
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Create WAV file
        const wavBuffer = this.encodeWAV(pcmData, 16000, 1);
        return new Blob([wavBuffer], { type: 'audio/wav' });
    }
    
    encodeWAV(samples, sampleRate, numChannels) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);
        
        // WAV header
        this.writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + samples.length * 2, true);
        this.writeString(view, 8, 'WAVE');
        this.writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true); // Subchunk1Size
        view.setUint16(20, 1, true); // AudioFormat (PCM)
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numChannels * 2, true); // ByteRate
        view.setUint16(32, numChannels * 2, true); // BlockAlign
        view.setUint16(34, 16, true); // BitsPerSample
        this.writeString(view, 36, 'data');
        view.setUint32(40, samples.length * 2, true);
        
        // Write PCM samples
        const offset = 44;
        for (let i = 0; i < samples.length; i++) {
            view.setInt16(offset + i * 2, samples[i], true);
        }
        
        return buffer;
    }
    
    writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }
    
    async playAudioResponse(audioArrayBuffer) {
        try {
            // Create audio context if not exists
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(audioArrayBuffer);
            
            // Create audio source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            
            // Play audio
            source.start(0);
            console.log('🔊 Playing TTS audio response');
            
        } catch (error) {
            console.error('❌ Error playing audio:', error);
        }
    }
    
    showTypingIndicator() {
        this.typingIndicator.classList.remove('hidden');
    }
    
    hideTypingIndicator() {
        this.typingIndicator.classList.add('hidden');
    }
    
    updateWaveform() {
        // Update listening text based on voice state
        const listeningText = document.querySelector('.listening-text');
        if (listeningText) {
            setInterval(() => {
                if (this.isListening) {
                    listeningText.textContent = 'Listening...';
                } else {
                    listeningText.textContent = 'Say "Vanakkam Vaathiyarey" to activate';
                }
            }, 100);
        }
    }
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🎙️ Initializing Voice Assistant...');
    
    // Initialize voice assistant
    const voiceAssistant = new VoiceAssistant();
    
    console.log('✨ Voice Assistant ready');
});
