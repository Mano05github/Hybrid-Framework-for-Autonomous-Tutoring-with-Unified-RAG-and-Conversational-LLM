// ===================================
// 3D ORB VISUALIZER
// Extracted from index.html with performance optimizations
// ===================================

// Performance Configuration
const PERFORMANCE_CONFIG = {
    DESKTOP_HIGH: {
        particles: 6000,
        bloomStrength: 2.5,
        bloomRadius: 0.8,
        targetFPS: 60
    },
    DESKTOP_MEDIUM: {
        particles: 4000,
        bloomStrength: 2.0,
        bloomRadius: 0.6,
        targetFPS: 60
    },
    MOBILE: {
        particles: 2000,
        bloomStrength: 1.5,
        bloomRadius: 0.4,
        targetFPS: 30
    },
    TABLET: {
        particles: 3000,
        bloomStrength: 1.8,
        bloomRadius: 0.5,
        targetFPS: 45
    }
};

// Emotion to State Mapping (Phase 4)
const EMOTION_MAPPING = {
    // Neutral Group
    'neutral': 'NEUTRAL',
    'calm': 'NEUTRAL',
    
    // Positive Group
    'happy': 'HAPPY',
    'surprised': 'HAPPY',
    'excited': 'HAPPY',
    'joyful': 'HAPPY',
    'satisfied': 'HAPPY',
    
    // Negative/Alert Group
    'angry': 'ALERT',
    'fearful': 'ALERT',
    'disgust': 'ALERT',
    'frustrated': 'ALERT',
    'stressed': 'ALERT',
    'overwhelmed': 'ALERT',
    'confused': 'ALERT',
    
    // Processing Group
    'sad': 'THINKING',
    'thinking': 'THINKING',
    'processing': 'THINKING',
    'contemplating': 'THINKING',
    'uncertain': 'THINKING',
    'bored': 'THINKING',
    'tired': 'THINKING',
    
    // Telemetry States (Gap 5)
    'distracted': 'ALERT',
    'cognitive_overload': 'ALERT',
    'idle': 'NEUTRAL',
    'engaged': 'HAPPY',
    
    // Default
    'unknown': 'NEUTRAL'
};

// State Configuration
const STATE_CONFIG = {
    NEUTRAL: {
        color: new THREE.Color(0x00d4ff),  // Match particles color
        bloomStrength: 2.0,
        bloomRadius: 0.5,
        amplitude: 1.0,
        rotationSpeed: 0.002,
        description: 'Ready to assist',
        alertOpacity: 0,
        thinkOpacity: 0
    },
    HAPPY: {
        color: new THREE.Color(0xffaa00),
        bloomStrength: 2.5,
        bloomRadius: 1.0,
        amplitude: 2.5,
        rotationSpeed: 0.02,
        description: 'Positive & Engaged',
        alertOpacity: 0,
        thinkOpacity: 0
    },
    ALERT: {
        color: new THREE.Color(0xff0033),
        bloomStrength: 3.0,
        bloomRadius: 0.4,
        amplitude: 0.8,
        jitter: true,
        description: 'Attention Needed',
        alertOpacity: 0.8,
        thinkOpacity: 0
    },
    THINKING: {
        color: new THREE.Color(0xaa00ff),
        bloomStrength: 3.0,
        bloomRadius: 0.7,
        amplitude: 1.5,
        rotationSpeed: 0.005,
        description: 'Processing...',
        alertOpacity: 0,
        thinkOpacity: 0.8
    }
};

class OrbVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Orb container not found:', containerId);
            return;
        }
        
        this.currentState = 'NEUTRAL';
        this.lastFrameTime = 0;
        this.isSpeaking = false;
        this.isPaused = false;
        
        // Auto-detect performance profile
        this.performanceProfile = this.detectPerformance();
        this.config = PERFORMANCE_CONFIG[this.performanceProfile];
        
        console.log(`🎮 Orb Performance: ${this.performanceProfile} (${this.config.particles} particles)`);
        
        // Check WebGL support
        if (!this.checkWebGLSupport()) {
            this.showFallback();
            return;
        }
        
        this.init();
    }
    
    checkWebGLSupport() {
        try {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
        } catch (e) {
            return false;
        }
    }
    
    showFallback() {
        console.warn('WebGL not supported, showing fallback');
        this.container.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #00eaff;">
                <div style="text-align: center;">
                    <h2>⚠️ WebGL Not Supported</h2>
                    <p>Your browser doesn't support 3D visualization</p>
                    <p style="margin-top: 20px; opacity: 0.7;">Voice assistant is still functional</p>
                </div>
            </div>
        `;
    }
    
    detectPerformance() {
        // Mobile detection
        const isMobile = /Android|iPhone|iPad/i.test(navigator.userAgent);
        const isTablet = /iPad|Android.*Tablet/i.test(navigator.userAgent);
        
        if (isMobile && !isTablet) return 'MOBILE';
        if (isTablet) return 'TABLET';
        
        // GPU detection
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (!gl) return 'MOBILE';
        
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            
            if (/NVIDIA|AMD Radeon|Apple M1|Apple M2/i.test(renderer)) {
                return 'DESKTOP_HIGH';
            }
            
            if (/Intel|Integrated/i.test(renderer)) {
                return 'DESKTOP_MEDIUM';
            }
        }
        
        return 'DESKTOP_MEDIUM';
    }
    
    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        // No fog - transparent background
        
        // Camera
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.container.clientWidth / this.container.clientHeight,
            1,
            1000
        );
        this.camera.position.z = 60;
        
        // Renderer with transparent background
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true,
            premultipliedAlpha: false
        });
        this.renderer.setClearColor(0x000000, 0); // Transparent clear color
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.toneMapping = THREE.ReinhardToneMapping;
        this.container.appendChild(this.renderer.domElement);
        
        // Post-processing
        this.setupPostProcessing();
        
        // Objects
        this.mainGroup = new THREE.Group();
        this.scene.add(this.mainGroup);
        
        this.createParticles();
        this.createAlertGeometry();
        this.createThinkingRings();
        
        // Clock
        this.clock = new THREE.Clock();
        
        // Resize handler
        window.addEventListener('resize', () => this.onResize());
        
        // Start animation
        this.animate();
    }
    
    setupPostProcessing() {
        const renderScene = new THREE.RenderPass(this.scene, this.camera);
        
        this.bloomPass = new THREE.UnrealBloomPass(
            new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
            this.config.bloomStrength,
            this.config.bloomRadius,
            0.85
        );
        this.bloomPass.threshold = 0;
        
        const renderTarget = new THREE.WebGLRenderTarget(
            this.container.clientWidth,
            this.container.clientHeight,
            {
                format: THREE.RGBAFormat
            }
        );
        this.composer = new THREE.EffectComposer(this.renderer, renderTarget);
        this.composer.addPass(renderScene);
        this.composer.addPass(this.bloomPass);
    }
    
    createParticles() {
        const geometry = new THREE.BufferGeometry();
        const positions = [];
        const shifts = [];
        
        const sphereRadius = 18;
        const particleCount = this.config.particles;
        
        for (let i = 0; i < particleCount; i++) {
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);
            
            const x = sphereRadius * Math.sin(phi) * Math.cos(theta);
            const y = sphereRadius * Math.sin(phi) * Math.sin(theta);
            const z = sphereRadius * Math.cos(phi);
            
            positions.push(x, y, z);
            shifts.push(Math.random() * 10);
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geometry.setAttribute('shift', new THREE.Float32BufferAttribute(shifts, 1));
        
        const sprite = new THREE.TextureLoader().load('https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/sprites/spark1.png');
        
        this.shaderMaterial = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                size: { value: 1.2 },
                color: { value: STATE_CONFIG.NEUTRAL.color },
                amplitude: { value: 1.0 },
                pointTexture: { value: sprite }
            },
            vertexShader: document.getElementById('vertexshader').textContent,
            fragmentShader: document.getElementById('fragmentshader').textContent,
            blending: THREE.AdditiveBlending,
            depthTest: false,
            transparent: true
        });
        
        this.particleSphere = new THREE.Points(geometry, this.shaderMaterial);
        this.mainGroup.add(this.particleSphere);
    }
    
    createAlertGeometry() {
        const geometry = new THREE.IcosahedronGeometry(15, 1);
        const material = new THREE.MeshBasicMaterial({
            color: STATE_CONFIG.ALERT.color,
            wireframe: true,
            transparent: true,
            opacity: 0,
            blending: THREE.AdditiveBlending
        });
        this.alertMesh = new THREE.Mesh(geometry, material);
        this.mainGroup.add(this.alertMesh);
    }
    
    createThinkingRings() {
        const geometry = new THREE.TorusGeometry(12, 1, 16, 100);
        const material = new THREE.PointsMaterial({
            color: STATE_CONFIG.THINKING.color,
            size: 0.5,
            transparent: true,
            opacity: 0,
            blending: THREE.AdditiveBlending
        });
        this.thinkMesh = new THREE.Points(geometry, material);
        this.thinkMesh.rotation.x = Math.PI / 2;
        this.mainGroup.add(this.thinkMesh);
    }
    
    updateEmotion(emotionLabel) {
        const normalized = emotionLabel.toLowerCase().trim();
        const targetState = EMOTION_MAPPING[normalized] || 'NEUTRAL';
        
        console.log(`🎭 Emotion: "${emotionLabel}" → ${targetState}`);
        this.setState(targetState);
    }
    
    setState(newState) {
        if (this.currentState === newState) return;
        
        const config = STATE_CONFIG[newState];
        if (!config) return;
        
        this.currentState = newState;
        console.log(`🌐 Orb State: ${newState} (${config.description})`);
        
        // Color transition
        new TWEEN.Tween(this.shaderMaterial.uniforms.color.value)
            .to({ r: config.color.r, g: config.color.g, b: config.color.b }, 800)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();
        
        // Bloom settings
        this.bloomPass.strength = config.bloomStrength;
        this.bloomPass.radius = config.bloomRadius;
        
        // Amplitude
        new TWEEN.Tween(this.shaderMaterial.uniforms)
            .to({ amplitude: { value: config.amplitude } }, 500)
            .start();
        
        // Alert geometry
        new TWEEN.Tween(this.alertMesh.material)
            .to({ opacity: config.alertOpacity }, 500)
            .start();
        
        // Thinking rings
        new TWEEN.Tween(this.thinkMesh.material)
            .to({ opacity: config.thinkOpacity }, 1000)
            .start();
        
        // Screen reader announcement
        const announcement = document.getElementById('sr-announcement');
        if (announcement) {
            announcement.textContent = `AI is now ${config.description}`;
        }
    }
    
    startSpeakingAnimation() {
        this.isSpeaking = true;
        const originalScale = this.mainGroup.scale.x;
        
        this.speakTween = new TWEEN.Tween(this.mainGroup.scale)
            .to({ x: originalScale * 1.1, y: originalScale * 1.1, z: originalScale * 1.1 }, 200)
            .yoyo(true)
            .repeat(Infinity)
            .start();
    }
    
    stopSpeakingAnimation() {
        this.isSpeaking = false;
        if (this.speakTween) {
            this.speakTween.stop();
        }
        this.mainGroup.scale.set(1, 1, 1);
    }
    
    updateStateAnimation() {
        const config = STATE_CONFIG[this.currentState];
        const time = this.clock.getElapsedTime();
        
        if (this.currentState === 'NEUTRAL') {
            this.mainGroup.rotation.y += config.rotationSpeed;
            this.mainGroup.rotation.z += config.rotationSpeed * 0.5;
        }
        else if (this.currentState === 'HAPPY') {
            this.mainGroup.rotation.y += config.rotationSpeed;
            this.mainGroup.rotation.z -= config.rotationSpeed * 0.5;
        }
        else if (this.currentState === 'ALERT') {
            // Jitter effect
            this.mainGroup.position.x = (Math.random() - 0.5) * 0.5;
            this.mainGroup.position.y = (Math.random() - 0.5) * 0.5;
            this.alertMesh.rotation.x += 0.05;
            this.alertMesh.rotation.y += 0.05;
        }
        else if (this.currentState === 'THINKING') {
            this.mainGroup.rotation.y += config.rotationSpeed;
            this.thinkMesh.rotation.z -= 0.02;
            this.thinkMesh.scale.setScalar(1 + Math.sin(time * 2) * 0.1);
        }
        else {
            this.mainGroup.position.set(0, 0, 0);
        }
    }
    
    animate() {
        if (this.isPaused) return;
        
        requestAnimationFrame(() => this.animate());
        
        // FPS throttling for low-end devices
        const now = performance.now();
        const targetFrameTime = 1000 / this.config.targetFPS;
        
        if (now - this.lastFrameTime < targetFrameTime) {
            return;
        }
        
        this.lastFrameTime = now;
        
        // Update
        TWEEN.update();
        this.shaderMaterial.uniforms.time.value = this.clock.getElapsedTime();
        this.updateStateAnimation();
        
        // Render
        this.composer.render();
    }
    
    pause() {
        this.isPaused = true;
    }
    
    resume() {
        this.isPaused = false;
        this.animate();
    }
    
    fadeOut() {
        new TWEEN.Tween(this.mainGroup.scale)
            .to({ x: 0.1, y: 0.1, z: 0.1 }, 1000)
            .easing(TWEEN.Easing.Cubic.In)
            .start();
    }
    
    onResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
        this.composer.setSize(width, height);
    }
}

// Expose to global window object for React access
window.OrbVisualizer = OrbVisualizer;
