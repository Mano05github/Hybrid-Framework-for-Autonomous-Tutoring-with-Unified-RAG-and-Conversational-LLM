/**
 * Workspace Transition Engine
 * ============================
 * Manages smooth transitions between supervisor and workspace modes
 */

class WorkspaceTransitionEngine {
    constructor() {
        this.currentMode = 'supervisor'; // supervisor | teaching | coding | assessment
        this.isTransitioning = false;
        this.transitionDuration = 500; // ms
        
        this.elements = {
            supervisorPanel: null,
            workspaceContainer: null,
            orbContainer: null,
            neuralOrb: null
        };
        
        this.callbacks = {
            onModeChange: null,
            onTransitionStart: null,
            onTransitionEnd: null
        };
    }
    
    /**
     * Initialize the transition engine
     */
    init(elements) {
        this.elements = { ...this.elements, ...elements };
        console.log('✨ Workspace Transition Engine initialized');
    }
    
    /**
     * Open a workspace (teaching/coding/assessment)
     */
    async openWorkspace(mode, options = {}) {
        if (this.isTransitioning) {
            console.warn('Transition already in progress');
            return false;
        }
        
        if (this.currentMode !== 'supervisor') {
            console.warn('Already in a workspace mode');
            return false;
        }
        
        console.log(`🚀 Opening ${mode} workspace`);
        
        this.isTransitioning = true;
        
        // Callback: transition start
        if (this.callbacks.onTransitionStart) {
            this.callbacks.onTransitionStart(mode);
        }
        
        try {
            // Step 1: Show confirmation (100ms)
            await this._showConfirmation(mode, options.message);
            
            // Step 2: Parallel animations (500ms)
            await Promise.all([
                this._slideInWorkspace(mode),
                this._shrinkSupervisor()
            ]);
            
            // Step 3: Final layout lock (100ms)
            await this._lockLayout(mode);
            
            this.currentMode = mode;
            
            // Callback: mode change
            if (this.callbacks.onModeChange) {
                this.callbacks.onModeChange(mode);
            }
            
            console.log(`✅ ${mode} workspace opened`);
            return true;
            
        } catch (error) {
            console.error('Workspace transition failed:', error);
            return false;
        } finally {
            this.isTransitioning = false;
            
            // Callback: transition end
            if (this.callbacks.onTransitionEnd) {
                this.callbacks.onTransitionEnd(mode);
            }
        }
    }
    
    /**
     * Close current workspace and return to supervisor
     */
    async closeWorkspace() {
        if (this.isTransitioning) {
            console.warn('Transition already in progress');
            return false;
        }
        
        if (this.currentMode === 'supervisor') {
            console.warn('Already in supervisor mode');
            return false;
        }
        
        const previousMode = this.currentMode;
        console.log(`🔙 Closing ${previousMode} workspace`);
        
        this.isTransitioning = true;
        
        // Callback: transition start
        if (this.callbacks.onTransitionStart) {
            this.callbacks.onTransitionStart('supervisor');
        }
        
        try {
            // Reverse animations (400ms)
            await Promise.all([
                this._slideOutWorkspace(),
                this._expandSupervisor()
            ]);
            
            this.currentMode = 'supervisor';
            
            // Callback: mode change
            if (this.callbacks.onModeChange) {
                this.callbacks.onModeChange('supervisor');
            }
            
            console.log('✅ Returned to supervisor mode');
            return true;
            
        } catch (error) {
            console.error('Workspace close failed:', error);
            return false;
        } finally {
            this.isTransitioning = false;
            
            // Callback: transition end
            if (this.callbacks.onTransitionEnd) {
                this.callbacks.onTransitionEnd('supervisor');
            }
        }
    }
    
    /**
     * Switch between workspaces
     */
    async switchWorkspace(newMode) {
        if (this.currentMode === 'supervisor') {
            return this.openWorkspace(newMode);
        } else {
            await this.closeWorkspace();
            await this._delay(100);
            return this.openWorkspace(newMode);
        }
    }
    
    /**
     * Get current mode
     */
    getCurrentMode() {
        return this.currentMode;
    }
    
    /**
     * Check if transitioning
     */
    isInTransition() {
        return this.isTransitioning;
    }
    
    /**
     * Register callbacks
     */
    on(event, callback) {
        if (event === 'modeChange') {
            this.callbacks.onModeChange = callback;
        } else if (event === 'transitionStart') {
            this.callbacks.onTransitionStart = callback;
        } else if (event === 'transitionEnd') {
            this.callbacks.onTransitionEnd = callback;
        }
    }
    
    // ========================================
    // Private Methods
    // ========================================
    
    /**
     * Show confirmation message
     */
    async _showConfirmation(mode, message) {
        const confirmationText = message || `Opening ${mode} workspace...`;
        
        // Update transcript or show toast
        if (this.elements.transcriptElement) {
            const originalText = this.elements.transcriptElement.textContent;
            this.elements.transcriptElement.textContent = confirmationText;
            
            await this._delay(100);
            
            // Restore original text after transition
            setTimeout(() => {
                this.elements.transcriptElement.textContent = originalText;
            }, this.transitionDuration);
        }
    }
    
    /**
     * Slide in workspace from right
     */
    async _slideInWorkspace(mode) {
        const { workspaceContainer } = this.elements;
        if (!workspaceContainer) return;
        
        // Set workspace mode
        workspaceContainer.dataset.mode = mode;
        
        // Add active class to trigger CSS transition
        workspaceContainer.classList.add('active');
        workspaceContainer.classList.add('slide-in-right');
        
        await this._delay(this.transitionDuration);
        
        workspaceContainer.classList.remove('slide-in-right');
    }
    
    /**
     * Slide out workspace to right
     */
    async _slideOutWorkspace() {
        const { workspaceContainer } = this.elements;
        if (!workspaceContainer) return;
        
        workspaceContainer.classList.add('slide-out-right');
        
        await this._delay(this.transitionDuration);
        
        workspaceContainer.classList.remove('active');
        workspaceContainer.classList.remove('slide-out-right');
        delete workspaceContainer.dataset.mode;
    }
    
    /**
     * Shrink supervisor panel to left column
     */
    async _shrinkSupervisor() {
        const { supervisorPanel, orbContainer, neuralOrb } = this.elements;
        if (!supervisorPanel) return;
        
        supervisorPanel.classList.add('shrink-supervisor');
        supervisorPanel.classList.remove('full-mode');
        supervisorPanel.classList.add('workspace-mode');
        
        // Shrink orb visualizers
        if (orbContainer && orbContainer.setState) {
            orbContainer.setState('THINKING');
        }
        
        if (neuralOrb && neuralOrb.updateState) {
            neuralOrb.updateState('THINKING');
        }
        
        await this._delay(this.transitionDuration);
        
        supervisorPanel.classList.remove('shrink-supervisor');
    }
    
    /**
     * Expand supervisor panel to full width
     */
    async _expandSupervisor() {
        const { supervisorPanel, orbContainer, neuralOrb } = this.elements;
        if (!supervisorPanel) return;
        
        supervisorPanel.classList.add('expand-supervisor');
        supervisorPanel.classList.remove('workspace-mode');
        supervisorPanel.classList.add('full-mode');
        
        // Restore orb visualizers
        if (orbContainer && orbContainer.setState) {
            orbContainer.setState('NEUTRAL');
        }
        
        if (neuralOrb && neuralOrb.updateState) {
            neuralOrb.updateState('NEUTRAL');
        }
        
        await this._delay(this.transitionDuration);
        
        supervisorPanel.classList.remove('expand-supervisor');
    }
    
    /**
     * Lock layout after transition
     */
    async _lockLayout(mode) {
        // Ensure final state is stable
        await this._delay(100);
        
        // Could add additional layout adjustments here
        console.log(`🔒 Layout locked in ${mode} mode`);
    }
    
    /**
     * Delay helper
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Expose to global window object
window.WorkspaceTransitionEngine = WorkspaceTransitionEngine;

// Create singleton instance
window.workspaceTransitions = new WorkspaceTransitionEngine();
