/* Pastebin Session Management */

class PastebinSession {
    constructor() {
        this.storageKey = 'pastebin_session';
        this.sessionExpireDays = 30;
    }

    // Save session data to localStorage
    saveSession(username, rememberMe = true) {
        if (rememberMe && username) {
            const sessionData = {
                username: username,
                loginTime: new Date().toISOString(),
                rememberMe: rememberMe
            };
            localStorage.setItem(this.storageKey, JSON.stringify(sessionData));
        } else {
            this.clearSession();
        }
    }

    // Get session data from localStorage
    getSession() {
        try {
            const savedSession = localStorage.getItem(this.storageKey);
            if (savedSession) {
                return JSON.parse(savedSession);
            }
        } catch (e) {
            this.clearSession();
        }
        return null;
    }

    // Check if session is still valid
    isSessionValid() {
        const session = this.getSession();
        if (!session || !session.loginTime) {
            return false;
        }

        const loginTime = new Date(session.loginTime);
        const now = new Date();
        const daysSinceLogin = (now - loginTime) / (1000 * 60 * 60 * 24);
        
        return daysSinceLogin < this.sessionExpireDays;
    }

    // Clear session data
    clearSession() {
        localStorage.removeItem(this.storageKey);
    }

    // Auto-redirect if already logged in
    autoRedirectIfLoggedIn() {
        const currentPath = window.location.pathname;
        const authPages = ['/login', '/signup'];
        
        if (authPages.includes(currentPath)) {
            if (this.isSessionValid()) {
                window.location.href = '/dashboard';
                return true;
            }
        }
        return false;
    }

    // Pre-fill login form if session exists
    prefillLoginForm() {
        const session = this.getSession();
        const usernameField = document.getElementById('username');
        
        if (session && session.username && usernameField) {
            usernameField.value = session.username;
            
            // Show welcome back message
            const loginTime = new Date(session.loginTime);
            const sessionInfo = document.createElement('div');
            sessionInfo.className = 'session-info';
            sessionInfo.innerHTML = `
                <strong>Welcome back, ${session.username}!</strong><br>
                Last login: ${loginTime.toLocaleDateString()}
            `;
            
            const authForm = document.querySelector('.auth-form');
            if (authForm) {
                authForm.appendChild(sessionInfo);
            }
        }
    }

    // Initialize session management
    init() {
        // Check for expired sessions and clean them up
        if (!this.isSessionValid()) {
            this.clearSession();
        }

        // Auto-redirect on auth pages
        this.autoRedirectIfLoggedIn();

        // Handle logout forms
        const logoutForms = document.querySelectorAll('#logoutForm');
        logoutForms.forEach(form => {
            form.addEventListener('submit', () => {
                this.clearSession();
            });
        });

        // Handle login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            // Pre-fill username if available
            this.prefillLoginForm();
            
            // Save session on login
            loginForm.addEventListener('submit', (e) => {
                const rememberMe = document.getElementById('rememberMe')?.checked !== false;
                const username = document.getElementById('username')?.value;
                this.saveSession(username, rememberMe);
            });
        }

        // Handle signup form
        const signupForm = document.getElementById('signupForm');
        if (signupForm) {
            signupForm.addEventListener('submit', (e) => {
                const rememberMe = document.getElementById('rememberMe')?.checked !== false;
                const username = document.getElementById('username')?.value;
                this.saveSession(username, rememberMe);
            });
        }
    }

    // Get current session status via API
    async getServerSessionStatus() {
        try {
            const response = await fetch('/session-status');
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.log('Could not check server session status');
        }
        return { authenticated: false };
    }
}

// Initialize session management when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const sessionManager = new PastebinSession();
    sessionManager.init();
    
    // Make it globally available
    window.PastebinSession = sessionManager;
});
