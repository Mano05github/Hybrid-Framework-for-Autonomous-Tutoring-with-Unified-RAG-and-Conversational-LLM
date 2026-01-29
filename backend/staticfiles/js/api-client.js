/**
 * API Client for Vaathiyar Backend
 * Handles all HTTP requests to Django REST API with CSRF token support
 */

class APIClient {
    constructor(baseURL = '') {
        // Use window.location.origin for flexibility (works in dev and production)
        this.baseURL = baseURL || window.location.origin;
        this.csrfToken = null;
        this.init();
    }

    /**
     * Initialize the API client by fetching CSRF token
     */
    async init() {
        await this.getCSRFToken();
    }

    /**
     * Get CSRF token from Django
     */
    async getCSRFToken() {
        try {
            const response = await fetch(`${this.baseURL}/api/users/csrf/`, {
                credentials: 'include'
            });
            const data = await response.json();
            this.csrfToken = data.csrfToken || this.getCookie('csrftoken');
        } catch (error) {
            console.error('Failed to get CSRF token:', error);
            // Fallback to cookie
            this.csrfToken = this.getCookie('csrftoken');
        }
    }

    /**
     * Get cookie value by name
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    /**
     * Make HTTP request with CSRF token
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Add CSRF token for non-GET requests
        if (options.method && options.method !== 'GET') {
            headers['X-CSRFToken'] = this.csrfToken || this.getCookie('csrftoken');
        }

        const config = {
            ...options,
            headers,
            credentials: 'include' // Include cookies
        };

        try {
            const response = await fetch(url, config);
            
            // Handle non-JSON responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                
                if (!response.ok) {
                    // Create error object with response data for better error handling
                    const error = new Error(data.error || data.message || `HTTP ${response.status}`);
                    error.response = { data, status: response.status };
                    throw error;
                }
                
                return data;
            } else {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.text();
            }
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // ==================== Authentication Methods ====================

    /**
     * Login user
     */
    async login(loginId, password) {
        return await this.request('/api/users/login/', {
            method: 'POST',
            body: JSON.stringify({ login_id: loginId, password })
        });
    }

    /**
     * Register new user
     */
    async register(username, email, password, confirmPassword = null) {
        return await this.request('/api/users/register/', {
            method: 'POST',
            body: JSON.stringify({ 
                username, 
                email, 
                password,
                confirm_password: confirmPassword || password  // Backend expects confirm_password
            })
        });
    }

    /**
     * Logout user
     */
    async logout() {
        return await this.request('/api/users/logout/', {
            method: 'POST'
        });
    }

    /**
     * Get current user info
     */
    async getCurrentUser() {
        return await this.request('/api/users/me/', {
            method: 'GET'
        });
    }

    // ==================== Session Methods ====================

    /**
     * Start a new learning session
     */
    async startSession(topicId = null) {
        return await this.request('/api/sessions/start/', {
            method: 'POST',
            body: JSON.stringify({ topic_id: topicId })
        });
    }

    /**
     * End current learning session
     */
    async endSession(sessionId) {
        return await this.request(`/api/sessions/${sessionId}/end/`, {
            method: 'POST'
        });
    }

    /**
     * Get today's session statistics
     */
    async getTodayStats() {
        return await this.request('/api/sessions/stats/today/', {
            method: 'GET'
        });
    }

    /**
     * Get weekly session statistics
     */
    async getWeeklyStats() {
        return await this.request('/api/sessions/stats/weekly/', {
            method: 'GET'
        });
    }

    /**
     * Get recent sessions
     */
    async getRecentSessions(limit = 10) {
        return await this.request(`/api/sessions/recent/?limit=${limit}`, {
            method: 'GET'
        });
    }

    // ==================== Coding Methods (Gap 3) ====================

    /**
     * Execute Python code
     */
    async executeCode(code, sessionId = null) {
        return await this.request('/api/gaps/coding/execute/', {
            method: 'POST',
            body: JSON.stringify({ code, session_id: sessionId })
        });
    }

    /**
     * Get coding hint (5-level Socratic hints)
     */
    async getHint(problemId, currentLevel = 0, sessionId = null) {
        return await this.request('/api/gaps/coding/hint/', {
            method: 'POST',
            body: JSON.stringify({ 
                problem_id: problemId, 
                level: currentLevel,
                session_id: sessionId 
            })
        });
    }

    /**
     * Submit code solution
     */
    async submitCode(problemId, code, sessionId = null) {
        return await this.request('/api/gaps/coding/submit/', {
            method: 'POST',
            body: JSON.stringify({ 
                problem_id: problemId, 
                code,
                session_id: sessionId 
            })
        });
    }

    // ==================== Learning Methods ====================

    /**
     * Get available topics
     */
    async getTopics() {
        return await this.request('/api/topics/available/', {
            method: 'GET'
        });
    }

    /**
     * Get questions for a topic
     */
    async getQuestions(topicId) {
        return await this.request(`/api/core/topics/${topicId}/questions/`, {
            method: 'GET'
        });
    }

    /**
     * Submit MCQ answer
     */
    async submitMCQAnswer(questionId, answer, reasoning = '', sessionId = null) {
        return await this.request('/api/core/questions/submit/', {
            method: 'POST',
            body: JSON.stringify({ 
                question_id: questionId, 
                answer,
                reasoning,
                session_id: sessionId 
            })
        });
    }

    /**
     * Browse topics
     */
    async browseTopics(category = null) {
        const endpoint = category 
            ? `/api/core/topics/?category=${category}` 
            : '/api/core/topics/';
        return await this.request(endpoint, {
            method: 'GET'
        });
    }

    // ==================== Telemetry Methods (Gap 5) ====================

    /**
     * Send telemetry snapshot
     */
    async sendTelemetrySnapshot(data) {
        return await this.request('/api/gaps/telemetry/snapshot/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Track user activity (keystroke, idle, etc.)
     */
    async trackActivity(activityType, metadata = {}) {
        return await this.request('/api/gaps/telemetry/activity/', {
            method: 'POST',
            body: JSON.stringify({ 
                activity_type: activityType,
                metadata,
                timestamp: new Date().toISOString()
            })
        });
    }
}

// Create global instance
window.apiClient = new APIClient();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}
