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
// COUNT-UP ANIMATION
// ===================================

class CountUpAnimation {
    constructor() {
        this.counters = document.querySelectorAll('[data-target]');
        this.init();
    }
    
    init() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
                    this.animateCounter(entry.target);
                    entry.target.classList.add('counted');
                }
            });
        }, { threshold: 0.5 });
        
        this.counters.forEach(counter => observer.observe(counter));
    }
    
    animateCounter(element) {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 1500;
        const start = 0;
        const startTime = performance.now();
        
        const updateCount = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.floor(easeOutQuart * (target - start) + start);
            
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(updateCount);
            } else {
                element.textContent = target;
            }
        };
        
        requestAnimationFrame(updateCount);
    }
}

// ===================================
// MASTERY CHART
// ===================================

class MasteryChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.data = [0, 0, 0, 0, 0, 0, 0]; // Weekly mastery percentages - all zeros for new user
        this.labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        this.animationProgress = 0;
        
        this.init();
    }
    
    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        // Start animation when chart is visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animate();
                    observer.disconnect();
                }
            });
        }, { threshold: 0.3 });
        
        observer.observe(this.canvas);
    }
    
    updateData(trendData) {
        // Update chart data from API
        this.data = trendData.map(item => item.mastery);
        this.labels = trendData.map(item => item.day);
        this.animationProgress = 0;
        this.animate();
    }
    
    resize() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.offsetWidth;
        this.canvas.height = container.offsetHeight;
    }
    
    drawChart() {
        const padding = 40;
        const width = this.canvas.width - padding * 2;
        const height = this.canvas.height - padding * 2;
        const pointCount = this.data.length;
        const segmentWidth = width / (pointCount - 1);
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw grid lines
        this.ctx.strokeStyle = 'rgba(148, 163, 184, 0.1)';
        this.ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding + (height / 4) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(padding, y);
            this.ctx.lineTo(this.canvas.width - padding, y);
            this.ctx.stroke();
        }
        
        // Calculate points
        const points = this.data.map((value, index) => ({
            x: padding + segmentWidth * index,
            y: padding + height - (value / 100) * height * this.animationProgress
        }));
        
        // Draw gradient fill
        if (this.animationProgress > 0) {
            const gradient = this.ctx.createLinearGradient(0, padding, 0, this.canvas.height - padding);
            gradient.addColorStop(0, 'rgba(0, 212, 255, 0.3)');
            gradient.addColorStop(0.5, 'rgba(168, 85, 247, 0.2)');
            gradient.addColorStop(1, 'rgba(168, 85, 247, 0.05)');
            
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.moveTo(points[0].x, this.canvas.height - padding);
            
            points.forEach(point => {
                this.ctx.lineTo(point.x, point.y);
            });
            
            this.ctx.lineTo(points[points.length - 1].x, this.canvas.height - padding);
            this.ctx.closePath();
            this.ctx.fill();
        }
        
        // Draw line
        this.ctx.strokeStyle = '#00d4ff';
        this.ctx.lineWidth = 3;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        
        this.ctx.beginPath();
        points.forEach((point, index) => {
            if (index === 0) {
                this.ctx.moveTo(point.x, point.y);
            } else {
                this.ctx.lineTo(point.x, point.y);
            }
        });
        this.ctx.stroke();
        
        // Draw points
        points.forEach((point, index) => {
            this.ctx.beginPath();
            this.ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
            this.ctx.fillStyle = '#00d4ff';
            this.ctx.fill();
            
            // Glow effect
            this.ctx.beginPath();
            this.ctx.arc(point.x, point.y, 8, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(0, 212, 255, 0.3)';
            this.ctx.fill();
        });
        
        // Draw labels
        this.ctx.fillStyle = '#94a3b8';
        this.ctx.font = '12px Inter';
        this.ctx.textAlign = 'center';
        
        this.labels.forEach((label, index) => {
            const x = padding + segmentWidth * index;
            this.ctx.fillText(label, x, this.canvas.height - padding + 20);
        });
    }
    
    animate() {
        const duration = 1500;
        const startTime = performance.now();
        
        const animateFrame = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            this.animationProgress = this.easeOutCubic(progress);
            this.drawChart();
            
            if (progress < 1) {
                requestAnimationFrame(animateFrame);
            }
        };
        
        requestAnimationFrame(animateFrame);
    }
    
    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }
}

// ===================================
// VOICE WIDGET INTERACTION
// ===================================

class VoiceWidget {
    constructor() {
        this.widget = document.getElementById('voiceWidget');
        this.activateBtn = document.getElementById('voiceActivateBtn');
        
        if (this.widget) {
            this.init();
        }
    }
    
    init() {
        // Click to activate
        this.widget.addEventListener('click', () => {
            this.activateVoice();
        });
        
        if (this.activateBtn) {
            this.activateBtn.addEventListener('click', () => {
                this.activateVoice();
            });
        }
    }
    
    async activateVoice() {
        // Prevent double-clicks
        if (this.activating) {
            console.log('⏳ Voice activation in progress...');
            return;
        }
        
        this.activating = true;
        
        try {
            // Get or create session using session manager
            const session = await window.sessionManager.getOrCreateSession();
            console.log('✅ Session ready for voice:', session.id);
            
            // Visual feedback
            this.widget.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.widget.style.transform = 'scale(1)';
            }, 150);
            
            // Show listening state briefly
            this.showListeningState();
            
            // Navigate to voice page with session ID
            setTimeout(() => {
                window.location.href = `voice.html?session_id=${session.id}`;
            }, 1000);
            
        } catch (error) {
            console.error('❌ Failed to activate voice:', error);
            alert('Failed to start voice session. Please try again.');
        } finally {
            this.activating = false;
        }
    }
    
    showListeningState() {
        const status = this.widget.querySelector('.widget-status');
        const originalText = status.textContent;
        
        status.textContent = 'LISTENING...';
        status.style.color = '#00d4ff';
        
        setTimeout(() => {
            status.textContent = originalText;
            status.style.color = '#10b981';
        }, 3000);
    }
}

// ===================================
// SESSION CARDS INTERACTION
// ===================================

class SessionCards {
    constructor() {
        this.cards = document.querySelectorAll('.session-card');
        this.init();
    }
    
    init() {
        this.cards.forEach(card => {
            card.addEventListener('click', (e) => {
                const sessionName = card.querySelector('.session-name').textContent;
                console.log(`📚 Opening session: ${sessionName}`);
                // In production, navigate to session details
            });
        });
    }
}

// ===================================
// DASHBOARD DATA LOADING
// ===================================

async function loadDashboardData() {
    try {
        // Display user info first
        const user = AuthGuard.getUser();
        if (user) {
            const usernameEl = document.querySelector('.user-name');
            const emailEl = document.querySelector('.user-email');
            const avatarEl = document.querySelector('.avatar-initial');
            
            if (usernameEl) usernameEl.textContent = user.username || 'User';
            if (emailEl) emailEl.textContent = user.email || '';
            if (avatarEl) {
                const initial = (user.username || 'U').charAt(0).toUpperCase();
                avatarEl.textContent = initial;
            }
        }
        
        // Load today's stats
        const todayStats = await window.apiClient.getTodayStats();
        
        // Update stat cards
        const problemsSolvedEl = document.querySelector('[data-target]');
        const timeSpentEl = document.querySelectorAll('[data-target]')[1];
        const masteryGainedEl = document.querySelectorAll('[data-target]')[2];
        const topicsStudiedEl = document.querySelectorAll('[data-target]')[3];
        
        if (problemsSolvedEl) problemsSolvedEl.setAttribute('data-target', todayStats.problemsSolved);
        if (timeSpentEl) timeSpentEl.setAttribute('data-target', todayStats.timeSpent);
        if (masteryGainedEl) masteryGainedEl.setAttribute('data-target', todayStats.masteryGained);
        if (topicsStudiedEl) topicsStudiedEl.setAttribute('data-target', todayStats.topicsStudied);
        
        // Load weekly trend
        const weeklyStats = await window.apiClient.getWeeklyStats();
        
        // Update mastery chart
        if (window.masteryChart && weeklyStats.trend) {
            window.masteryChart.updateData(weeklyStats.trend);
        }
        
        // Load recent sessions
        const recentSessions = await window.apiClient.getRecentSessions(10);
        
        // Update recent sessions list
        const sessionsContainer = document.querySelector('.sessions-list');
        if (sessionsContainer && recentSessions.sessions) {
            sessionsContainer.innerHTML = recentSessions.sessions.map(session => `
                <div class="session-card">
                    <div class="session-header">
                        <h4 class="session-name">${session.topic}</h4>
                        <span class="session-time">${session.timestamp}</span>
                    </div>
                    <div class="session-stats">
                        <span class="session-duration">${session.duration}</span>
                        <span class="session-problems">${session.problemsSolved} problems</span>
                    </div>
                </div>
            `).join('');
        }
        
        console.log('✅ Dashboard data loaded successfully');
    } catch (error) {
        console.error('❌ Failed to load dashboard data:', error);
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: rgba(239, 68, 68, 0.9); color: white; padding: 16px 24px; border-radius: 12px; z-index: 1000;';
        errorDiv.textContent = 'Failed to load dashboard data. Please refresh the page.';
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// ===================================
// SIDEBAR NAVIGATION
// ===================================

class SidebarNavigation {
    constructor() {
        this.navItems = document.querySelectorAll('.nav-item');
        this.logoutBtn = document.getElementById('logoutBtn');
        this.init();
    }
    
    init() {
        // Highlight current page
        const currentPath = window.location.pathname;
        this.navItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href && (href === currentPath || currentPath.endsWith(href))) {
                item.classList.add('active');
            }
        });
        
        // Handle logout
        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => this.handleLogout());
        }
    }
    
    async handleLogout() {
        try {
            console.log('🚪 Logging out...');
            
            // Call logout API
            const response = await fetch('/api/auth/logout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                credentials: 'include'
            });
            
            if (response.ok) {
                console.log('✅ Logout successful');
                // Clear any stored session data
                sessionStorage.clear();
                localStorage.removeItem('auth_token');
                // Redirect to login
                window.location.href = '/login.html';
            } else {
                console.error('❌ Logout failed:', response.statusText);
                // Force redirect anyway
                window.location.href = '/login.html';
            }
        } catch (error) {
            console.error('❌ Logout error:', error);
            // Force redirect on error
            window.location.href = '/login.html';
        }
    }
    
    getCsrfToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name + '=')) {
                return trimmed.substring(name.length + 1);
            }
        }
        return '';
    }
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📊 Initializing Dashboard...');
    
    // Initialize sidebar navigation
    const sidebar = new SidebarNavigation();
    
    // Initialize particles background
    const particles = new ParticlesBackground('particles-bg');
    
    // Initialize count-up animations
    const countUp = new CountUpAnimation();
    
    // Initialize mastery chart
    window.masteryChart = new MasteryChart('mastery-chart');
    
    // Initialize voice widget
    const voiceWidget = new VoiceWidget();
    
    // Initialize session cards
    const sessionCards = new SessionCards();
    
    // Load real dashboard data
    await loadDashboardData();
    
    console.log('✨ Dashboard ready');
});
