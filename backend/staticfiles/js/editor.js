// ===================================
// CODE EDITOR PAGE FUNCTIONALITY
// ===================================

class CodeEditor {
    constructor() {
        this.editor = null;
        this.sessionId = null;
        this.currentProblemId = null;
        this.currentHintLevel = 0;
        this.defaultCode = `# Binary Search Tree Implementation
class Node:
    def __init__(self, key):
        self.left = None
        self.right = None
        self.val = key

# Start coding...
root = Node(50)
print("Node created with value:", root.val)
`;
        
        // DOM elements
        this.runBtn = document.getElementById('runBtn');
        this.hintBtn = document.getElementById('hintBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.clearOutputBtn = document.getElementById('clearOutputBtn');
        this.outputContent = document.getElementById('outputContent');
        this.outputStatus = document.getElementById('outputStatus');
        this.endSessionBtn = document.getElementById('endSessionBtn');
        
        this.init();
    }
    
    async init() {
        // Initialize Monaco Editor
        this.initMonaco();
        
        // Initialize session for tracking
        try {
            const session = await window.apiClient.startSession();
            this.sessionId = session.id || session.session_id;
            console.log('✅ Session started:', this.sessionId);
        } catch (error) {
            console.warn('⚠️ Failed to start session:', error);
        }
        
        // Button event listeners
        this.runBtn.addEventListener('click', () => this.runCode());
        this.hintBtn.addEventListener('click', () => this.showHint());
        this.resetBtn.addEventListener('click', () => this.resetCode());
        this.clearOutputBtn.addEventListener('click', () => this.clearOutput());

        if (this.endSessionBtn) {
            this.endSessionBtn.addEventListener('click', () => this.endSessionAndReturn());
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter to run
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.runCode();
            }
            // Ctrl+H for hint
            if (e.ctrlKey && e.key === 'h') {
                e.preventDefault();
                this.showHint();
            }
        });
    }

    async endSessionAndReturn() {
        if (this.endSessionInProgress) return;

        const confirmed = confirm('End this session and return to the Supervisor?');
        if (!confirmed) return;

        this.endSessionInProgress = true;
        this.endSessionBtn.disabled = true;
        this.endSessionBtn.textContent = 'Ending...';

        try {
            if (!this.sessionId) {
                const activeSession = await window.apiClient.getActiveSession();
                this.sessionId = activeSession.id || activeSession.session_id || null;
            }

            if (this.sessionId) {
                await window.apiClient.endSession(this.sessionId);
            }
        } catch (error) {
            console.error('Failed to end session:', error);
        }

        window.location.href = 'voice-supervisor.html';
    }
    
    initMonaco() {
        require.config({ 
            paths: { 
                'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' 
            } 
        });
        
        require(['vs/editor/editor.main'], () => {
            this.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                value: this.defaultCode,
                language: 'python',
                theme: 'vs-dark',
                fontSize: 14,
                minimap: { enabled: false },
                automaticLayout: true,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                padding: { top: 16, bottom: 16 },
                fontFamily: "'Fira Code', 'Cascadia Code', monospace",
                fontLigatures: true,
                cursorBlinking: 'smooth',
                cursorSmoothCaretAnimation: 'on',
                smoothScrolling: true,
                renderLineHighlight: 'all',
                bracketPairColorization: {
                    enabled: true
                }
            });
            
            console.log('✨ Monaco Editor initialized');
        });
    }
    
    async runCode() {
        const code = this.editor.getValue();
        
        if (!code.trim()) {
            this.showOutput('No code to execute', 'error');
            return;
        }
        
        // Update status
        this.updateStatus('running');
        this.showOutput('Executing code...', 'info');
        
        try {
            // Call backend API for code execution
            const result = await window.apiClient.executeCode(code, this.sessionId);
            
            if (result.output) {
                this.showOutput(result.output, 'success');
                this.updateStatus('success');
            } else if (result.error) {
                this.showOutput(`Error: ${result.error}`, 'error');
                this.updateStatus('error');
            } else {
                this.showOutput('Code executed successfully (no output)', 'success');
                this.updateStatus('success');
            }
        } catch (error) {
            this.showOutput(`Error: ${error.message}`, 'error');
            this.updateStatus('error');
            console.error('Code execution error:', error);
        }
    }
    
    simulatePythonExecution(code) {
        // This is a simple simulation for demo purposes
        // In production, code would be sent to backend for safe execution
        
        const lines = code.split('\n');
        let output = [];
        
        // Look for print statements
        lines.forEach((line, index) => {
            if (line.trim().startsWith('print(')) {
                // Extract content between print()
                const match = line.match(/print\((.*)\)/);
                if (match) {
                    const content = match[1].replace(/"/g, '').replace(/'/g, '');
                    output.push(content);
                }
            }
        });
        
        if (output.length > 0) {
            return output.join('\n');
        } else {
            return 'Code executed successfully (no output)';
        }
    }
    
    async showHint() {
        try {
            // Get hint from Socratic Coder (Gap 3)
            const result = await window.apiClient.getHint(
                this.currentProblemId || 1,  // Default problem ID
                this.currentHintLevel || 0,
                this.sessionId
            );
            
            this.showOutput(`💡 ${result.hint_text || result.hint}`, 'info');
            this.currentHintLevel = result.hint_level || (this.currentHintLevel || 0) + 1;
            
            console.log('💡 Hint received from Gap 3');
        } catch (error) {
            // Fallback to generic hint if API fails
            const fallbackHints = [
                "💡 Hint: Consider the base case for your recursive function.",
                "💡 Hint: Think about the loop condition - when should it terminate?",
                "💡 Hint: Remember to handle edge cases like empty inputs.",
                "💡 Hint: Try breaking down the problem into smaller sub-problems.",
                "💡 Hint: Check if you're updating your variables correctly inside the loop."
            ];
            
            const randomHint = fallbackHints[Math.floor(Math.random() * fallbackHints.length)];
            this.showOutput(randomHint, 'info');
            
            console.log('💡 Using fallback hint (API unavailable)');
        }
    }
    
    resetCode() {
        if (confirm('Are you sure you want to reset the code to the default template?')) {
            this.editor.setValue(this.defaultCode);
            this.clearOutput();
            this.updateStatus('ready');
            console.log('🔄 Code reset');
        }
    }
    
    clearOutput() {
        this.outputContent.innerHTML = '<p class="output-placeholder">$ Ready to run your code...</p>';
        this.updateStatus('ready');
    }
    
    showOutput(text, type = 'info') {
        // Clear placeholder if exists
        const placeholder = this.outputContent.querySelector('.output-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        const outputLine = document.createElement('p');
        outputLine.className = `output-line output-${type}`;
        
        // Add appropriate prefix
        let prefix = '';
        if (type === 'success') prefix = '✓ ';
        if (type === 'error') prefix = '✗ ';
        if (type === 'info') prefix = '$ ';
        
        outputLine.textContent = prefix + text;
        this.outputContent.appendChild(outputLine);
        
        // Auto-scroll to bottom
        this.outputContent.scrollTop = this.outputContent.scrollHeight;
    }
    
    updateStatus(status) {
        const statusDot = this.outputStatus.querySelector('.status-dot');
        const statusText = this.outputStatus.querySelector('.status-text');
        
        // Remove all status classes
        statusDot.classList.remove('running', 'error');
        
        switch (status) {
            case 'running':
                statusDot.classList.add('running');
                statusText.textContent = 'Running...';
                break;
            case 'error':
                statusDot.classList.add('error');
                statusText.textContent = 'Error';
                break;
            case 'success':
                statusText.textContent = 'Success';
                break;
            default:
                statusText.textContent = 'Output';
        }
    }
}

// ===================================
// INITIALIZATION
// ===================================

window.addEventListener('load', () => {
    console.log('💻 Initializing Code Editor...');
    
    // Initialize code editor
    const codeEditor = new CodeEditor();
    
    console.log('✨ Code Editor ready');
});
