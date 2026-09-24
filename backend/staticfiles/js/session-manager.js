/**
 * Session Manager Utility
 * Handles session lifecycle and prevents duplicate sessions
 */

class SessionManager {
    constructor() {
        this.activeSession = null;
        this.sessionCheckInProgress = false;
    }
    
    /**
     * Get or create active session
     * Checks for existing active session before creating new one
     */
    async getOrCreateSession() {
        // Prevent concurrent session creation
        if (this.sessionCheckInProgress) {
            console.log('⏳ Session check in progress, waiting...');
            await this.waitForSessionCheck();
        }
        
        // Return cached session if valid
        if (this.activeSession && this.isSessionValid(this.activeSession)) {
            console.log('✅ Using cached session:', this.activeSession.id);
            return this.activeSession;
        }
        
        this.sessionCheckInProgress = true;
        
        try {
            // Check for active session on backend
            const activeSession = await window.apiClient.getActiveSession();
            
            if (activeSession && activeSession.id) {
                console.log('✅ Found active session:', activeSession.id);
                this.activeSession = activeSession;
                return activeSession;
            }
            
            // Create new session if none active
            console.log('🆕 Creating new session...');
            const newSession = await window.apiClient.startSession();
            this.activeSession = newSession;
            
            return newSession;
            
        } finally {
            this.sessionCheckInProgress = false;
        }
    }
    
    /**
     * Check if session is still valid
     */
    isSessionValid(session) {
        if (!session || !session.id) return false;
        
        // Check if session has expired (if timestamp exists)
        if (session.created_at) {
            const createdTime = new Date(session.created_at).getTime();
            const now = Date.now();
            const hoursSinceCreation = (now - createdTime) / (1000 * 60 * 60);
            
            // Sessions expire after 24 hours
            if (hoursSinceCreation > 24) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Wait for session check to complete
     */
    async waitForSessionCheck(maxWait = 5000) {
        const startTime = Date.now();
        
        while (this.sessionCheckInProgress && (Date.now() - startTime) < maxWait) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        if (this.sessionCheckInProgress) {
            console.warn('⚠️ Session check timeout');
        }
    }
    
    /**
     * Clear cached session
     */
    clearSession() {
        this.activeSession = null;
        console.log('🗑️ Session cache cleared');
    }
    
    /**
     * End current session
     */
    async endSession() {
        if (!this.activeSession) return;
        
        try {
            await window.apiClient.endSession(this.activeSession.id);
            console.log('✅ Session ended:', this.activeSession.id);
            this.clearSession();
        } catch (error) {
            console.error('❌ Failed to end session:', error);
        }
    }
}

// Create global instance
window.sessionManager = new SessionManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
}
