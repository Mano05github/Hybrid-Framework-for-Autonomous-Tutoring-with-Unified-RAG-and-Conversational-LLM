/**
 * Coding Workspace - Monaco Editor Integration
 * =============================================
 * Code editor with Python execution
 */

class CodingWorkspace {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Coding workspace container not found');
            return;
        }
        
        this.editor = null;
        this.terminal = null;
        
        this.init();
    }
    
    async init() {
        this.createLayout();
        await this.initMonaco();
        this.createTerminal();
        console.log('💻 Coding Workspace initialized');
    }
    
    createLayout() {
        this.container.innerHTML = `
            <div class="coding-workspace-layout">
                <div class="editor-panel">
                    <div class="editor-header">
                        <span class="editor-title">
                            <i data-lucide="file-code"></i>
                            main.py
                        </span>
                        <div class="editor-actions">
                            <button class="editor-btn" id="run-code-btn">
                                <i data-lucide="play"></i>
                                Run Code
                            </button>
                        </div>
                    </div>
                    <div id="monaco-editor" class="monaco-container"></div>
                </div>
                <div class="terminal-panel">
                    <div class="terminal-header">
                        <span class="terminal-title">
                            <i data-lucide="terminal"></i>
                            Output
                        </span>
                        <button class="terminal-btn" id="clear-terminal-btn">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                    <div id="terminal-output" class="terminal-output"></div>
                </div>
            </div>
        `;
        
        // Initialize lucide icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
        // Setup event listeners
        const runBtn = document.getElementById('run-code-btn');
        if (runBtn) {
            runBtn.addEventListener('click', () => this.runCode());
        }
        
        const clearBtn = document.getElementById('clear-terminal-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearTerminal());
        }
    }
    
    async initMonaco() {
        // Check if Monaco is loaded
        if (!window.monaco) {
            console.error('Monaco Editor not loaded');
            return;
        }
        
        const editorContainer = document.getElementById('monaco-editor');
        if (!editorContainer) return;
        
        // Create Monaco editor
        this.editor = monaco.editor.create(editorContainer, {
            value: '# Write your Python code here\n\ndef greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("Student"))\n',
            language: 'python',
            theme: 'vs-dark',
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollbar: {
                vertical: 'auto',
                horizontal: 'auto'
            },
            padding: { top: 10, bottom: 10 }
        });
        
        // Custom dark theme
        monaco.editor.defineTheme('vaathiyar-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [],
            colors: {
                'editor.background': '#0a0a0f',
                'editor.foreground': '#f8fafc',
                'editorLineNumber.foreground': '#4a5568',
                'editor.selectionBackground': '#00d4ff33',
                'editor.lineHighlightBackground': '#ffffff08'
            }
        });
        
        monaco.editor.setTheme('vaathiyar-dark');
    }
    
    createTerminal() {
        this.terminal = document.getElementById('terminal-output');
        if (this.terminal) {
            this.appendToTerminal('Ready to execute code...', 'info');
        }
    }
    
    async runCode() {
        const code = this.editor.getValue();
        
        this.clearTerminal();
        this.appendToTerminal('Running code...', 'info');
        
        try {
            // Send code to backend for execution
            const response = await fetch('/api/execute-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code, language: 'python' })
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (result.output) {
                    this.appendToTerminal(result.output, 'success');
                }
                if (result.error) {
                    this.appendToTerminal(result.error, 'error');
                }
            } else {
                this.appendToTerminal(result.error || 'Execution failed', 'error');
            }
        } catch (error) {
            this.appendToTerminal(`Error: ${error.message}`, 'error');
        }
    }
    
    appendToTerminal(text, type = 'output') {
        if (!this.terminal) return;
        
        const line = document.createElement('div');
        line.className = `terminal-line terminal-${type}`;
        line.textContent = text;
        
        this.terminal.appendChild(line);
        this.terminal.scrollTop = this.terminal.scrollHeight;
    }
    
    clearTerminal() {
        if (this.terminal) {
            this.terminal.innerHTML = '';
        }
    }
    
    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    destroy() {
        if (this.editor) {
            this.editor.dispose();
        }
        this.container.innerHTML = '';
    }
}

// Expose to global window object
window.CodingWorkspace = CodingWorkspace;
