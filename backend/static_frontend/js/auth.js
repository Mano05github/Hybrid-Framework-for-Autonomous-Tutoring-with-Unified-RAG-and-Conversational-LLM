// ===================================
// PARTICLES BACKGROUND ANIMATION
// ===================================

class ParticlesBackground {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 80;
        
        this.init();
    }
    
    init() {
        // Set canvas size
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        // Programming symbols array
        const programmingSymbols = ['{', '}', '(', ')', '[', ']', '<', '>', '/', '\\', ';', ':', '=', '+', '-', '*', '&', '|', '!', '?', '#', '$', '%', '@'];
        
        // Create particles
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.3 + 0.1,
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
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Wrap around edges
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            // Draw particle
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity})`;
            this.ctx.font = `${particle.size * 8}px monospace`;
            this.ctx.fillText(particle.symbol, particle.x, particle.y);
            
            // Draw glow
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size * 2, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity * 0.2})`;
            this.ctx.fill();
        });
    }
    
    animate() {
        this.drawParticles();
        requestAnimationFrame(() => this.animate());
    }
}

// ===================================
// PASSWORD TOGGLE FUNCTIONALITY
// ===================================

class PasswordToggle {
    constructor() {
        this.toggleButtons = document.querySelectorAll('.password-toggle');
        this.init();
    }
    
    init() {
        this.toggleButtons.forEach(button => {
            button.addEventListener('click', () => {
                const input = button.previousElementSibling.previousElementSibling;
                const eyeIcon = button.querySelector('.eye-icon');
                const eyeOffIcon = button.querySelector('.eye-off-icon');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    eyeIcon.classList.add('hidden');
                    eyeOffIcon.classList.remove('hidden');
                } else {
                    input.type = 'password';
                    eyeIcon.classList.remove('hidden');
                    eyeOffIcon.classList.add('hidden');
                }
            });
        });
    }
}

// ===================================
// PASSWORD STRENGTH CHECKER
// ===================================

class PasswordStrengthChecker {
    constructor() {
        this.passwordInput = document.getElementById('password');
        this.strengthIndicator = document.getElementById('passwordStrength');
        this.strengthFill = document.getElementById('strengthFill');
        this.strengthText = document.getElementById('strengthText');
        
        if (this.passwordInput && this.strengthIndicator) {
            this.init();
        }
    }
    
    init() {
        this.passwordInput.addEventListener('input', () => {
            const password = this.passwordInput.value;
            
            if (password.length === 0) {
                this.strengthIndicator.classList.add('hidden');
                return;
            }
            
            this.strengthIndicator.classList.remove('hidden');
            const strength = this.calculateStrength(password);
            this.updateIndicator(strength);
        });
    }
    
    calculateStrength(password) {
        let score = 0;
        
        // Length check
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;
        
        // Character variety checks
        if (/[a-z]/.test(password)) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^a-zA-Z0-9]/.test(password)) score++;
        
        // Determine strength level
        if (score <= 2) return 'weak';
        if (score <= 4) return 'medium';
        return 'strong';
    }
    
    updateIndicator(strength) {
        // Remove all classes
        this.strengthFill.classList.remove('weak', 'medium', 'strong');
        
        // Add appropriate class
        this.strengthFill.classList.add(strength);
        
        // Update text
        const strengthLabels = {
            weak: 'Weak',
            medium: 'Medium',
            strong: 'Strong'
        };
        this.strengthText.textContent = strengthLabels[strength];
    }
}

// ===================================
// FORM VALIDATION
// ===================================

class FormValidator {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.errorMessage = document.getElementById('errorMessage');
        this.errorText = document.getElementById('errorText');
        
        if (this.form) {
            this.init();
        }
    }
    
    init() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.validateForm();
        });
    }
    
    showError(message) {
        this.errorText.textContent = message;
        this.errorMessage.classList.remove('hidden');
    }
    
    hideError() {
        this.errorMessage.classList.add('hidden');
    }
    
    validateForm() {
        this.hideError();
        
        const formData = new FormData(this.form);
        const data = Object.fromEntries(formData);
        
        // Check if it's login or register form
        if (this.form.id === 'loginForm') {
            this.handleLogin(data);
        } else if (this.form.id === 'registerForm') {
            this.handleRegister(data);
        }
    }
    
    async handleLogin(data) {
        const { username, password } = data;
        
        // Basic validation
        if (!username || !password) {
            this.showError('Please fill in all fields');
            return;
        }
        
        // Show loading state
        this.setLoadingState(true);
        
        try {
            // Call real backend API
            const response = await window.apiClient.login(username, password);
            
            // Store user data in localStorage
            localStorage.setItem('user', JSON.stringify(response.user));
            
            // Redirect to dashboard
            window.location.href = 'dashboard.html';
        } catch (error) {
            this.setLoadingState(false);
            this.showError(error.message || 'Login failed. Please check your credentials.');
            console.error('Login error:', error);
        }
    }
    
    async handleRegister(data) {
        const { username, email, password, confirmPassword } = data;
        
        // Validation checks
        if (!username || !email || !password || !confirmPassword) {
            this.showError('Please fill in all fields');
            return;
        }
        
        if (username.length < 3) {
            this.showError('Username must be at least 3 characters');
            return;
        }
        
        if (!this.isValidEmail(email)) {
            this.showError('Please enter a valid email address');
            return;
        }
        
        if (password.length < 8) {
            this.showError('Password must be at least 8 characters');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showError('Passwords do not match');
            return;
        }
        
        // Show loading state
        this.setLoadingState(true);
        
        try {
            // Call real backend API with confirm_password
            await window.apiClient.register(username, email, password, confirmPassword);
            
            // Show success message
            this.showSuccess('Account created successfully! Redirecting to login...');
            
            // Redirect to login after 2 seconds
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
            
        } catch (error) {
            // Show backend error message
            let errorMessage = 'Registration failed. Please try again.';
            
            if (error.response && error.response.data) {
                // Extract error messages from backend
                const backendErrors = error.response.data;
                
                if (typeof backendErrors === 'string') {
                    errorMessage = backendErrors;
                } else if (backendErrors.username) {
                    errorMessage = Array.isArray(backendErrors.username) 
                        ? backendErrors.username[0] 
                        : backendErrors.username;
                } else if (backendErrors.password) {
                    errorMessage = Array.isArray(backendErrors.password) 
                        ? backendErrors.password[0] 
                        : backendErrors.password;
                } else if (backendErrors.email) {
                    errorMessage = Array.isArray(backendErrors.email) 
                        ? backendErrors.email[0] 
                        : backendErrors.email;
                } else if (backendErrors.error) {
                    errorMessage = backendErrors.error;
                } else if (backendErrors.detail) {
                    errorMessage = backendErrors.detail;
                }
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            this.showError(errorMessage);
            console.error('Registration error:', error);
        } finally {
            this.setLoadingState(false);
        }
    }
    
    showSuccess(message) {
        const errorMessage = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        
        if (errorMessage && errorText) {
            errorText.textContent = message;
            errorMessage.classList.remove('hidden');
            errorMessage.style.background = 'rgba(16, 185, 129, 0.1)';
            errorMessage.style.borderColor = 'rgba(16, 185, 129, 0.3)';
            errorMessage.style.color = '#10b981';
        }
    }
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    setLoadingState(isLoading) {
        const button = this.form.querySelector('.auth-button');
        const buttonText = button.querySelector('.button-text');
        const buttonLoader = button.querySelector('.button-loader');
        
        if (isLoading) {
            button.disabled = true;
            buttonText.classList.add('hidden');
            buttonLoader.classList.remove('hidden');
        } else {
            button.disabled = false;
            buttonText.classList.remove('hidden');
            buttonLoader.classList.add('hidden');
        }
    }
}

// ===================================
// INPUT ANIMATIONS
// ===================================

class InputAnimations {
    constructor() {
        this.inputs = document.querySelectorAll('.auth-input');
        this.init();
    }
    
    init() {
        this.inputs.forEach(input => {
            // Add ripple effect on focus
            input.addEventListener('focus', (e) => {
                this.createRipple(e);
            });
        });
    }
    
    createRipple(e) {
        const inputGroup = e.target.closest('.input-group');
        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            width: 10px;
            height: 10px;
            background: rgba(0, 212, 255, 0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%) scale(0);
            animation: rippleEffect 0.6s ease-out;
            pointer-events: none;
            z-index: 0;
        `;
        
        inputGroup.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }
}

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes rippleEffect {
        to {
            transform: translate(-50%, -50%) scale(40);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔐 Initializing Authentication Page...');
    
    // Initialize particles background
    const particles = new ParticlesBackground('particles-bg');
    
    // Initialize password toggle
    const passwordToggle = new PasswordToggle();
    
    // Initialize password strength checker (only on register page)
    const passwordStrength = new PasswordStrengthChecker();
    
    // Initialize form validation
    const loginValidator = new FormValidator('loginForm');
    const registerValidator = new FormValidator('registerForm');
    
    // Initialize input animations
    const inputAnimations = new InputAnimations();
    
    console.log('✨ Authentication page ready');
});
