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
        
        this.init();
    }
    
    async init() {
        // Start a learning session
        try {
            const session = await window.apiClient.startSession();
            this.sessionId = session.id || session.session_id;
            console.log('✅ Session started:', this.sessionId);
            
            // Connect WebSocket
            window.wsClient.connect(this.sessionId);
            
            // Set up WebSocket callbacks
            window.wsClient.onConnect(() => {
                this.wsConnected = true;
                console.log('✅ WebSocket connected');
            });
            
            window.wsClient.onMessage((data) => {
                this.handleAIMessage(data);
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
                type: 'text',
                text: message,
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
            console.log('🎤 Voice input activated');
            
            // Update waveform
            if (window.waveformVisualizer) {
                window.waveformVisualizer.setListening(true);
            }
        } else {
            this.voiceToggleBtn.classList.remove('active');
            console.log('🎤 Voice input deactivated');
            
            // Update waveform
            if (window.waveformVisualizer) {
                window.waveformVisualizer.setListening(false);
            }
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
