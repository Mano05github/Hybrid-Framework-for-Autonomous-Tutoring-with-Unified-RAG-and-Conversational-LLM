// ===================================
// SHARED UTILITIES FOR LEARNING PAGES
// ===================================

// ===================================
// PARTICLES BACKGROUND ANIMATION
// ===================================

class ParticlesBackground {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 60;
        
        this.init();
    }
    
    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        const programmingSymbols = ['{', '}', '(', ')', '[', ']', '<', '>', '/', '\\', ';', ':', '=', '+', '-', '*', '&', '|', '!', '?', '#', '$', '%', '@'];
        
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.2,
                vy: (Math.random() - 0.5) * 0.2,
                size: Math.random() * 2 + 0.5,
                opacity: Math.random() * 0.2 + 0.05,
                symbol: programmingSymbols[Math.floor(Math.random() * programmingSymbols.length)]
            });
        }
        
        this.animate();
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    drawParticles() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity})`;
            this.ctx.font = `${particle.size * 8}px monospace`;
            this.ctx.fillText(particle.symbol, particle.x, particle.y);
        });
    }
    
    animate() {
        this.drawParticles();
        requestAnimationFrame(() => this.animate());
    }
}

// ===================================
// WAVEFORM VISUALIZATION
// ===================================

class WaveformVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.isListening = false;
        this.audioData = null;
        
        this.init();
    }
    
    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.animate();
    }
    
    resize() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.offsetWidth;
        this.canvas.height = container.offsetHeight;
    }
    
    setListening(listening) {
        this.isListening = listening;
    }
    
    setAudioData(data) {
        this.audioData = data;
    }
    
    drawWaveform() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        const centerY = this.canvas.height / 2;
        const waveCount = 5;
        const time = Date.now() * 0.001;
        
        for (let i = 0; i < waveCount; i++) {
            const gradient = this.ctx.createLinearGradient(0, 0, this.canvas.width, 0);
            
            if (i % 2 === 0) {
                gradient.addColorStop(0, 'rgba(0, 212, 255, 0.3)');
                gradient.addColorStop(0.5, 'rgba(168, 85, 247, 0.5)');
                gradient.addColorStop(1, 'rgba(0, 212, 255, 0.3)');
            } else {
                gradient.addColorStop(0, 'rgba(168, 85, 247, 0.3)');
                gradient.addColorStop(0.5, 'rgba(0, 212, 255, 0.5)');
                gradient.addColorStop(1, 'rgba(168, 85, 247, 0.3)');
            }
            
            this.ctx.strokeStyle = gradient;
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            
            for (let x = 0; x < this.canvas.width; x++) {
                const frequency = 0.02 + (i * 0.005);
                const amplitude = this.isListening ? 30 + (i * 10) : 15 + (i * 5);
                const phase = time + (i * 0.5);
                
                const y = centerY + Math.sin(x * frequency + phase) * amplitude;
                
                if (x === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            }
            
            this.ctx.stroke();
        }
    }
    
    animate() {
        this.drawWaveform();
        requestAnimationFrame(() => this.animate());
    }
}

// ===================================
// VOICE PANEL CONTROLLER
// ===================================

class VoicePanelController {
    constructor() {
        this.panel = document.querySelector('.voice-panel');
        this.toggleBtn = document.querySelector('.toggle-panel-btn');
        this.voiceBtn = document.querySelector('.voice-btn');
        this.voiceInput = document.querySelector('.voice-input');
        this.statusText = document.querySelector('.status-text');
        this.isListening = false;
        
        if (this.panel) {
            this.init();
        }
    }
    
    init() {
        // Toggle panel visibility
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => {
                this.panel.classList.toggle('collapsed');
            });
        }
        
        // Voice button click
        if (this.voiceBtn) {
            this.voiceBtn.addEventListener('click', () => {
                this.toggleListening();
            });
        }
        
        // Enter key to send message
        if (this.voiceInput) {
            this.voiceInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }
    }
    
    toggleListening() {
        this.isListening = !this.isListening;
        
        if (this.isListening) {
            this.voiceBtn.classList.add('active');
            this.statusText.textContent = 'Listening...';
            console.log('🎤 Voice activated');
        } else {
            this.voiceBtn.classList.remove('active');
            this.statusText.textContent = 'Click to speak';
            console.log('🎤 Voice deactivated');
        }
        
        // Update waveform if available
        if (window.waveformVisualizer) {
            window.waveformVisualizer.setListening(this.isListening);
        }
    }
    
    sendMessage() {
        const message = this.voiceInput.value.trim();
        if (message) {
            console.log('📤 Sending message:', message);
            this.voiceInput.value = '';
            
            // Trigger custom event for other components to handle
            window.dispatchEvent(new CustomEvent('voiceMessage', {
                detail: { message }
            }));
        }
    }
}

// ===================================
// INITIALIZATION HELPER
// ===================================

function initializeSharedComponents() {
    console.log('🚀 Initializing shared components...');
    
    // Initialize particles background
    if (document.getElementById('particles-bg')) {
        window.particlesBackground = new ParticlesBackground('particles-bg');
    }
    
    // Initialize waveform visualizer
    if (document.getElementById('waveform-canvas')) {
        window.waveformVisualizer = new WaveformVisualizer('waveform-canvas');
    }
    
    // Initialize voice panel controller
    window.voicePanelController = new VoicePanelController();
    
    console.log('✨ Shared components ready');
}

// Auto-initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSharedComponents);
} else {
    initializeSharedComponents();
}
