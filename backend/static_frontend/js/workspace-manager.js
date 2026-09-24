/**
 * Workspace Manager — Teaching Only
 * Manages the teaching workspace. Coding and assessment workspaces have been removed.
 */

class WorkspaceManager {
    constructor() {
        this.currentWorkspace = null;
        this.workspaceInstances = {};
        this.container = null;
        this.commandQueue = {};
    }

    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Workspace content container not found');
            return;
        }
        console.log('🎯 Workspace Manager initialized');
    }

    async loadWorkspace(mode) {
        console.log(`📦 Loading ${mode} workspace...`);

        if (this.currentWorkspace) {
            this.unloadWorkspace();
        }

        const loading = this.container && this.container.querySelector('.workspace-loading');
        if (loading) loading.style.display = 'none';

        try {
            // Only teaching mode supported — any other mode falls back gracefully
            await this.loadTeachingWorkspace();

            this.currentWorkspace = mode;
            this.processCommandQueue(mode);
            console.log(`✅ ${mode} workspace loaded`);
            return true;

        } catch (error) {
            console.error(`Failed to load ${mode} workspace:`, error);
            this.showError(error.message);
            return false;
        }
    }

    async loadTeachingWorkspace() {
        if (!window.TeachingWorkspace) {
            throw new Error('TeachingWorkspace class not found');
        }
        this.workspaceInstances.teaching = new window.TeachingWorkspace('workspace-content');
    }

    unloadWorkspace() {
        if (!this.currentWorkspace) return;

        const instance = this.workspaceInstances[this.currentWorkspace];
        if (instance && instance.destroy) {
            instance.destroy();
        }

        delete this.workspaceInstances[this.currentWorkspace];
        this.currentWorkspace = null;

        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    showError(message) {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="workspace-error">
                <div class="error-icon"><i data-lucide="alert-circle"></i></div>
                <h3 class="error-title">Failed to Load Workspace</h3>
                <p class="error-message">${message}</p>
                <button class="error-btn" onclick="window.workspaceTransitions.closeWorkspace()">
                    <i data-lucide="arrow-left"></i> Return to Supervisor
                </button>
            </div>
        `;

        if (window.lucide) window.lucide.createIcons();
    }

    queueCommand(mode, command) {
        if (!this.workspaceInstances[mode]) {
            if (!this.commandQueue[mode]) this.commandQueue[mode] = [];
            this.commandQueue[mode].push(command);
            console.log(`📦 Queued command for ${mode} workspace`);
        } else {
            if (this.workspaceInstances[mode].handleCommand) {
                this.workspaceInstances[mode].handleCommand(command);
            }
        }
    }

    processCommandQueue(mode) {
        if (this.commandQueue[mode] && this.commandQueue[mode].length > 0) {
            console.log(`🚀 Processing ${this.commandQueue[mode].length} queued commands for ${mode}`);
            const instance = this.workspaceInstances[mode];
            if (instance && instance.handleCommand) {
                while (this.commandQueue[mode].length > 0) {
                    const cmd = this.commandQueue[mode].shift();
                    instance.handleCommand(cmd);
                }
            }
        }
    }
}

window.WorkspaceManager = WorkspaceManager;
window.workspaceManager = new WorkspaceManager();
