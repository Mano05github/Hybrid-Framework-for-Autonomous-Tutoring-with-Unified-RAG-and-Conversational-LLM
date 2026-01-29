/**
 * Authentication Guard
 * Checks if user is logged in and redirects to login if not
 */
class AuthGuard {
    /**
     * Check if user is authenticated
     * @returns {Promise<boolean>} True if authenticated, false otherwise
     */
    static async checkAuth() {
        try {
            // Check if user exists in localStorage
            const user = localStorage.getItem('user');
            
            if (!user) {
                // No user in storage, redirect to login
                window.location.href = '/login.html';
                return false;
            }
            
            // Verify session with backend
            try {
                const response = await window.apiClient.getCurrentUser();
                
                if (response && response.id) {
                    // Update localStorage with fresh data
                    localStorage.setItem('user', JSON.stringify(response));
                    return true;
                }
            } catch (error) {
                // Session expired or invalid
                console.warn('Session validation failed:', error);
                localStorage.removeItem('user');
                window.location.href = '/login.html';
                return false;
            }
        } catch (error) {
            // Unexpected error
            console.error('Auth check failed:', error);
            localStorage.removeItem('user');
            window.location.href = '/login.html';
            return false;
        }
    }
    
    /**
     * Get current user from localStorage
     * @returns {Object|null} User object or null
     */
    static getUser() {
        const userJson = localStorage.getItem('user');
        return userJson ? JSON.parse(userJson) : null;
    }
    
    /**
     * Logout user and redirect to login
     */
    static async logout() {
        try {
            // Call backend logout
            await window.apiClient.logout();
        } catch (error) {
            console.error('Logout API call failed:', error);
        } finally {
            // Always clear local storage and redirect
            localStorage.removeItem('user');
            window.location.href = '/login.html';
        }
    }
}

// Export to window
window.AuthGuard = AuthGuard;
