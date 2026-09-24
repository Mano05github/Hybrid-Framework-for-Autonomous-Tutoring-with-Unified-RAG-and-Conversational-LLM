// ===================================
// SCROLL PROGRESS TRACKER
// ===================================

class ScrollProgressTracker {
    constructor() {
        this.progressBar = document.querySelector('.progress-bar');
        this.init();
    }
    
    init() {
        window.addEventListener('scroll', () => this.updateProgress());
        this.updateProgress();
    }
    
    updateProgress() {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.scrollY;
        const scrollPercent = (scrollTop / (documentHeight - windowHeight)) * 100;
        
        this.progressBar.style.width = `${Math.min(scrollPercent, 100)}%`;
    }
}

// ===================================
// SCENE MANAGER - Scroll-Driven Animations
// ===================================

class SceneManager {
    constructor() {
        this.scenes = document.querySelectorAll('.scene');
        this.currentScene = 1;
        this.sceneHandlers = {
            1: this.handleScene1.bind(this),
            2: this.handleScene2.bind(this),
            3: this.handleScene3.bind(this),
            4: this.handleScene4.bind(this),
            5: this.handleScene5.bind(this),
            6: this.handleScene6.bind(this),
            7: this.handleScene7.bind(this),
            8: this.handleScene8.bind(this)
        };
        this.init();
    }
    
    init() {
        // Set up Intersection Observer for scenes
        const observerOptions = {
            threshold: [0.2, 0.5, 0.8],
            rootMargin: '-10% 0px -10% 0px'
        };
        
        this.observer = new IntersectionObserver(
            this.handleIntersection.bind(this),
            observerOptions
        );
        
        this.scenes.forEach(scene => this.observer.observe(scene));
        
        // Scroll listener for continuous animations
        window.addEventListener('scroll', () => this.updateScenes());
    }
    
    handleIntersection(entries) {
        entries.forEach(entry => {
            const sceneNum = parseInt(entry.target.dataset.scene);
            
            if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
                this.currentScene = sceneNum;
                this.activateScene(sceneNum);
            }
        });
    }
    
    activateScene(sceneNum) {
        if (this.sceneHandlers[sceneNum]) {
            this.sceneHandlers[sceneNum]();
        }
    }
    
    updateScenes() {
        // Update scroll-based animations for all visible scenes
        this.scenes.forEach(scene => {
            const rect = scene.getBoundingClientRect();
            const sceneNum = parseInt(scene.dataset.scene);
            
            if (rect.top < window.innerHeight && rect.bottom > 0) {
                const progress = 1 - (rect.top / window.innerHeight);
                this.updateSceneProgress(sceneNum, Math.max(0, Math.min(1, progress)));
            }
        });
    }
    
    updateSceneProgress(sceneNum, progress) {
        // Scene-specific scroll progress updates
        const scene = document.querySelector(`#scene-${sceneNum}`);
        if (!scene) return;
        
        const text = scene.querySelector('.scene-text');
        if (text && progress > 0.3) {
            text.classList.add('visible');
        }
    }
    
    handleScene1() {
        console.log('Scene 1: The System Listens');
        // Waveform animation is handled by WaveformAnimator
    }
    
    handleScene2() {
        console.log('Scene 2: Knowledge Exists');
        // Particles animation is handled by ParticleSystem
    }
    
    handleScene3() {
        console.log('Scene 3: Retrieval & Grounding');
        this.animateDataStreams();
    }
    
    handleScene4() {
        console.log('Scene 4: Conversational Reasoning');
        this.animateReasoningPaths();
    }
    
    handleScene5() {
        console.log('Scene 5: Hybrid Unification');
        this.animateUnification();
    }
    
    handleScene6() {
        console.log('Scene 6: The Learner Appears');
        this.animateLearner();
    }
    
    handleScene7() {
        console.log('Scene 7: Autonomous Tutoring in Action');
        // AI waveform animation is handled by AIWaveformAnimator
    }
    
    handleScene8() {
        console.log('Scene 8: Scale & Impact');
        this.animateGlobalConnections();
    }
    
    animateDataStreams() {
        const svg = document.querySelector('#scene-3 .data-streams .stream-group');
        if (!svg || svg.hasChildNodes()) return;
        
        const centerX = 500;
        const centerY = 500;
        const streams = 8;
        
        for (let i = 0; i < streams; i++) {
            const angle = (i / streams) * Math.PI * 2;
            const startX = centerX + Math.cos(angle) * 400;
            const startY = centerY + Math.sin(angle) * 400;
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('class', 'stream-line');
            path.setAttribute('d', `M ${startX} ${startY} Q ${centerX + Math.cos(angle) * 200} ${centerY + Math.sin(angle) * 200} ${centerX} ${centerY}`);
            path.style.animationDelay = `${i * 0.2}s`;
            
            svg.appendChild(path);
        }
    }
    
    animateReasoningPaths() {
        const svg = document.querySelector('#scene-4 .reasoning-paths .paths-group');
        if (!svg || svg.hasChildNodes()) return;
        
        const paths = [
            'M 100 300 Q 300 100 500 300 T 900 300',
            'M 100 400 Q 400 200 500 400 T 900 400',
            'M 100 500 Q 350 350 500 500 T 900 500',
            'M 200 250 Q 500 150 800 250',
            'M 200 550 Q 500 450 800 550'
        ];
        
        paths.forEach((d, i) => {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('class', 'reasoning-path');
            path.setAttribute('d', d);
            path.style.animationDelay = `${i * 0.3}s`;
            svg.appendChild(path);
        });
    }
    
    animateUnification() {
        const flows = document.querySelectorAll('#scene-5 .flow');
        const core = document.querySelector('#scene-5 .unified-core');
        
        flows.forEach(flow => flow.classList.add('visible'));
        
        setTimeout(() => {
            if (core) core.classList.add('visible');
        }, 1000);
    }
    
    animateLearner() {
        const student = document.querySelector('#scene-6 .student-character');
        const book = document.querySelector('#scene-6 .orbiting-book');
        
        if (student) student.classList.add('visible');
        setTimeout(() => {
            if (book) book.classList.add('visible');
        }, 500);
    }
    
    animateGlobalConnections() {
        const svg = document.querySelector('#scene-8 .global-connections .connections-group');
        const nodes = document.querySelectorAll('#scene-8 .node');
        
        if (svg && !svg.hasChildNodes()) {
            const connections = [
                [240, 240, 960, 200],
                [240, 240, 600, 480],
                [960, 200, 600, 480],
                [600, 480, 360, 560],
                [600, 480, 840, 600],
                [360, 560, 840, 600]
            ];
            
            connections.forEach(([x1, y1, x2, y2], i) => {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('class', 'connection-line');
                line.setAttribute('x1', x1);
                line.setAttribute('y1', y1);
                line.setAttribute('x2', x2);
                line.setAttribute('y2', y2);
                line.style.animationDelay = `${i * 0.5}s`;
                svg.appendChild(line);
            });
        }
        
        nodes.forEach((node, i) => {
            setTimeout(() => node.classList.add('visible'), i * 200);
        });
    }
}

// ===================================
// WAVEFORM ANIMATOR - Scene 1
// ===================================

class WaveformAnimator {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width = 600;
        this.height = this.canvas.height = 400;
        this.time = 0;
        this.breathing = true;
        
        this.init();
    }
    
    init() {
        this.animate();
    }
    
    drawWaveform() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        const centerY = this.height / 2;
        const amplitude = 60 + Math.sin(this.time * 0.5) * 20; // Breathing effect
        const frequency = 0.02;
        const points = 200;
        
        // Create gradient
        const gradient = this.ctx.createLinearGradient(0, 0, this.width, 0);
        gradient.addColorStop(0, '#00d4ff');
        gradient.addColorStop(0.5, '#a855f7');
        gradient.addColorStop(1, '#00d4ff');
        
        this.ctx.strokeStyle = gradient;
        this.ctx.lineWidth = 3;
        this.ctx.lineCap = 'round';
        this.ctx.shadowBlur = 20;
        this.ctx.shadowColor = '#00d4ff';
        
        this.ctx.beginPath();
        
        for (let i = 0; i < points; i++) {
            const x = (i / points) * this.width;
            const wave1 = Math.sin(i * frequency + this.time) * amplitude;
            const wave2 = Math.sin(i * frequency * 2 - this.time * 0.5) * (amplitude * 0.5);
            const y = centerY + wave1 + wave2;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.stroke();
    }
    
    animate() {
        this.drawWaveform();
        this.time += 0.03;
        requestAnimationFrame(() => this.animate());
    }
}

// ===================================
// PARTICLE SYSTEM - Scene 2
// ===================================

class ParticleSystem {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.width = 0;
        this.height = 0;
        this.particles = [];
        this.particleCount = 220;
        this.dpr = Math.max(1, window.devicePixelRatio || 1);
        
        this.init();
    }
    
    init() {
        this.resize();

        // Programming symbols array
        const programmingSymbols = ['{', '}', '(', ')', '[', ']', '<', '>', '/', '\\', ';', ':', '=', '+', '-', '*', '&', '|', '!', '?', '#', '$', '%', '@'];
        
        // Create particles
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                vx: (Math.random() - 0.5) * 1.1,
                vy: (Math.random() - 0.5) * 1.1,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.6 + 0.35,
                symbol: programmingSymbols[Math.floor(Math.random() * programmingSymbols.length)]
            });
        }
        
        this.animate();
    }

    resize() {
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.canvas.width = Math.floor(this.width * this.dpr);
        this.canvas.height = Math.floor(this.height * this.dpr);
        this.canvas.style.width = `${this.width}px`;
        this.canvas.style.height = `${this.height}px`;
        this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    }
    
    drawParticles() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        this.particles.forEach(particle => {
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Wrap around edges
            if (particle.x < 0) particle.x = this.width;
            if (particle.x > this.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.height;
            if (particle.y > this.height) particle.y = 0;
            
            // Draw particle
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity})`;
            this.ctx.font = `${particle.size * 7}px "Space Grotesk", "Inter", sans-serif`;
            this.ctx.fillText(particle.symbol, particle.x, particle.y);
            
            // Draw glow
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size * 1.2, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity * 0.3})`;
            this.ctx.fill();
        });
    }
    
    animate() {
        this.drawParticles();
        requestAnimationFrame(() => this.animate());
    }
}

// ===================================
// AI WAVEFORM ANIMATOR - Scene 7
// ===================================

class AIWaveformAnimator {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width = 800;
        this.height = this.canvas.height = 600;
        this.time = 0;
        
        this.init();
    }
    
    init() {
        this.animate();
    }
    
    drawAIPresence() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        
        // Draw multiple concentric waveforms
        for (let ring = 0; ring < 5; ring++) {
            const radius = 100 + ring * 60;
            const points = 100;
            
            const gradient = this.ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
            gradient.addColorStop(0, 'rgba(168, 85, 247, 0.6)');
            gradient.addColorStop(1, 'rgba(168, 85, 247, 0.1)');
            
            this.ctx.strokeStyle = gradient;
            this.ctx.lineWidth = 2;
            this.ctx.shadowBlur = 15;
            this.ctx.shadowColor = '#a855f7';
            
            this.ctx.beginPath();
            
            for (let i = 0; i <= points; i++) {
                const angle = (i / points) * Math.PI * 2;
                const wave = Math.sin(i * 0.2 + this.time + ring) * 20;
                const r = radius + wave;
                const x = centerX + Math.cos(angle) * r;
                const y = centerY + Math.sin(angle) * r;
                
                if (i === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            }
            
            this.ctx.closePath();
            this.ctx.stroke();
        }
    }
    
    animate() {
        this.drawAIPresence();
        this.time += 0.02;
        requestAnimationFrame(() => this.animate());
    }
}

// ===================================
// SMOOTH SCROLL HANDLER
// ===================================

class SmoothScrollHandler {
    constructor() {
        this.init();
    }
    
    init() {
        // Add smooth scrolling to CTA buttons
        document.querySelectorAll('.cta-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const text = button.textContent;
                console.log(`CTA clicked: ${text}`);
                // Add your navigation logic here
            });
        });
    }
}

// ===================================
// PARALLAX EFFECT
// ===================================

class ParallaxEffect {
    constructor() {
        this.layers = document.querySelectorAll('.visual-container, .ambient-glow');
        this.init();
    }
    
    init() {
        window.addEventListener('scroll', () => this.updateParallax());
        this.updateParallax();
    }
    
    updateParallax() {
        const scrollY = window.scrollY;
        
        this.layers.forEach((layer, index) => {
            const speed = (index + 1) * 0.05;
            const offset = scrollY * speed;
            layer.style.transform = `translateY(${offset}px)`;
        });
    }
}

// ===================================
// PERFORMANCE OPTIMIZER
// ===================================

class PerformanceOptimizer {
    constructor() {
        this.init();
    }
    
    init() {
        // Reduce motion for users who prefer it
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduced-motion');
            console.log('Reduced motion mode enabled');
        }
        
        // Pause animations when tab is not visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('Page hidden - pausing animations');
            } else {
                console.log('Page visible - resuming animations');
            }
        });
    }
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Scrollytelling Experience...');
    
    // Initialize scroll progress tracker
    const scrollProgress = new ScrollProgressTracker();
    
    // Initialize scene manager
    const sceneManager = new SceneManager();
    
    // Initialize canvas animations
    const waveformAnimator = new WaveformAnimator('waveform-canvas');
    const particleSystem = new ParticleSystem('particles-bg');
    const aiWaveform = new AIWaveformAnimator('ai-waveform');
    
    // Initialize smooth scroll handler
    const smoothScroll = new SmoothScrollHandler();
    
    // Initialize parallax effect
    const parallax = new ParallaxEffect();
    
    // Initialize performance optimizations
    const performanceOptimizer = new PerformanceOptimizer();
    
    console.log('✨ All systems initialized - Begin your journey');
});

// ===================================
// RESIZE HANDLER
// ===================================

let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        console.log('Window resized - recalculating layouts');
        
        // Reinitialize canvas elements if needed
        if (particleSystem) {
            particleSystem.resize();
        }
    }, 250);
});
