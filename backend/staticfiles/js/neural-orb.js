/**
 * Neural Orb Visualizer - Centered AI Cognition Core
 * ===================================================
 * Manages the centered holographic neural sphere visualization
 * Syncs with voice supervisor states and provides ambient animation
 */

class NeuralOrbVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Neural orb container not found:', containerId);
            return;
        }
        
        this.currentState = 'NEUTRAL';
        this.particleCount = this.isMobile() ? 20 : 40;
        this.mouseX = 0;
        this.mouseY = 0;
        this.parallaxEnabled = !this.isMobile();
        
        this.init();
    }
    
    isMobile() {
        return window.innerWidth <= 768;
    }
    
    init() {
        // Create DOM structure
        this.createStructure();
        
        // Setup mouse parallax (desktop only)
        if (this.parallaxEnabled) {
            this.setupParallax();
        }
        
        // Start ambient animation
        this.animate();
        
        console.log('✨ Neural Orb Visualizer initialized');
    }
    
    createStructure() {
        // Main container
        this.container.className = 'neural-orb-container';
        
        // Volumetric glow (bottom layer)
        const volumetricGlow = document.createElement('div');
        volumetricGlow.className = 'volumetric-glow';
        this.container.appendChild(volumetricGlow);
        
        // Neural waves
        const neuralWaves = document.createElement('div');
        neuralWaves.className = 'neural-waves';
        for (let i = 0; i < 3; i++) {
            const wave = document.createElement('div');
            wave.className = 'neural-wave';
            neuralWaves.appendChild(wave);
        }
        this.container.appendChild(neuralWaves);
        
        // Energy spikes (desktop only)
        if (!this.isMobile()) {
            const energySpikes = document.createElement('div');
            energySpikes.className = 'energy-spikes';
            for (let i = 0; i < 8; i++) {
                const spike = document.createElement('div');
                spike.className = 'energy-spike';
                energySpikes.appendChild(spike);
            }
            this.container.appendChild(energySpikes);
        }
        
        // Particle halo
        const particleHalo = document.createElement('div');
        particleHalo.className = 'particle-halo';
        
        for (let i = 0; i < this.particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random starting position on orbit
            const angle = (360 / this.particleCount) * i;
            particle.style.transform = `rotate(${angle}deg) translateX(150px) rotate(-${angle}deg)`;
            particle.style.animationDelay = `${(i / this.particleCount) * 8}s`;
            
            particleHalo.appendChild(particle);
        }
        this.container.appendChild(particleHalo);
        
        // Core neural sphere (top layer)
        const neuralCore = document.createElement('div');
        neuralCore.className = 'neural-core';
        this.container.appendChild(neuralCore);
        
        // Store references
        this.elements = {
            core: neuralCore,
            waves: neuralWaves,
            particles: particleHalo,
            glow: volumetricGlow
        };
    }
    
    setupParallax() {
        let ticking = false;
        
        const updateMousePosition = (e) => {
            this.mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
            this.mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
            
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    this.applyParallax();
                    ticking = false;
                });
                ticking = true;
            }
        };
        
        window.addEventListener('mousemove', updateMousePosition);
    }
    
    applyParallax() {
        if (!this.parallaxEnabled || !this.container) return;
        
        const offsetX = this.mouseX * 15; // Max 15px movement
        const offsetY = this.mouseY * 15;
        
        this.container.style.transform = `translate(calc(-50% + ${offsetX}px), calc(-50% + ${offsetY}px))`;
    }
    
    updateState(newState) {
        if (this.currentState === newState) return;
        
        console.log(`🔮 Neural Orb state: ${this.currentState} → ${newState}`);
        
        // Remove old state class
        this.container.classList.remove(`state-${this.currentState.toLowerCase()}`);
        
        // Add new state class
        this.currentState = newState;
        this.container.classList.add(`state-${newState.toLowerCase()}`);
        
        // Trigger state-specific effects
        this.triggerStateEffect(newState);
    }
    
    triggerStateEffect(state) {
        switch(state) {
            case 'THINKING':
                this.intensifyWaves();
                break;
            case 'ALERT':
                this.flashSpikes();
                break;
            case 'HAPPY':
                this.burstParticles();
                break;
            default:
                // NEUTRAL - default animations
                break;
        }
    }
    
    intensifyWaves() {
        // Temporarily speed up wave ripples
        const waves = this.elements.waves.querySelectorAll('.neural-wave');
        waves.forEach((wave, i) => {
            wave.style.animation = 'waveRipple 1.5s ease-out infinite';
            wave.style.animationDelay = `${i * 0.5}s`;
        });
        
        // Reset after 3 seconds
        setTimeout(() => {
            waves.forEach((wave, i) => {
                wave.style.animation = 'waveRipple 3s ease-out infinite';
                wave.style.animationDelay = `${i * 1}s`;
            });
        }, 3000);
    }
    
    flashSpikes() {
        // Trigger simultaneous spike flash
        const spikes = this.container.querySelectorAll('.energy-spike');
        spikes.forEach(spike => {
            spike.style.animation = 'none';
            setTimeout(() => {
                spike.style.animation = 'spikeFlash 1s ease-in-out infinite';
            }, 10);
        });
    }
    
    burstParticles() {
        // Temporarily speed up particle orbits
        const particles = this.elements.particles.querySelectorAll('.particle');
        particles.forEach(particle => {
            const currentDuration = parseFloat(getComputedStyle(particle).animationDuration);
            particle.style.animationDuration = `${currentDuration * 0.5}s`;
        });
        
        // Reset after 2 seconds
        setTimeout(() => {
            particles.forEach(particle => {
                particle.style.animationDuration = '';
            });
        }, 2000);
    }
    
    animate() {
        // Continuous ambient animation loop
        // Currently handled by CSS, but can add dynamic effects here
        requestAnimationFrame(() => this.animate());
    }
    
    pause() {
        this.container.style.animationPlayState = 'paused';
        this.container.querySelectorAll('*').forEach(el => {
            el.style.animationPlayState = 'paused';
        });
    }
    
    resume() {
        this.container.style.animationPlayState = 'running';
        this.container.querySelectorAll('*').forEach(el => {
            el.style.animationPlayState = 'running';
        });
    }
    
    fadeOut() {
        this.container.style.transition = 'opacity 1s ease-out';
        this.container.style.opacity = '0';
    }
    
    fadeIn() {
        this.container.style.transition = 'opacity 1s ease-in';
        this.container.style.opacity = '1';
    }
}

// Expose to global window object for React access
window.NeuralOrbVisualizer = NeuralOrbVisualizer;
