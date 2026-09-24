// ===================================
// CODE EDITOR PAGE FUNCTIONALITY
// ===================================

class CodeEditor {
    constructor() {
        this.editor = null;
        this.sessionId = null;
        this.wsConnected = false;
        this.currentProblemId = null;
        this.currentHintLevel = 0;
        this.keystrokeCount = 0;
        this.errorCount = 0;
        this.lastKeystrokeTime = Date.now();
        this.telemetryInterval = null;
        
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
        
        // Initialize session and WebSocket
        await this.initSession();
        
        // Button event listeners
        this.runBtn.addEventListener('click', () => this.runCode());
        this.hintBtn.addEventListener('click', () => this.showHint());
        this.resetBtn.addEventListener('click', () => this.resetCode());
        this.clearOutputBtn.addEventListener('click', () => this.clearOutput());

        if (this.endSessionBtn) {
            this.endSessionBtn.addEventListener('click', () => this.endSessionAndReturn());
        }
        
        // Add Submit for Review button
        this.addSubmitButton();
        
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
    
    async initSession() {
        try {
            // Start session
            const session = await window.apiClient.startSession();
            this.sessionId = session.id || session.session_id;
            console.log('✅ Editor session started:', this.sessionId);
            
            // Connect WebSocket
            window.wsClient.connect(this.sessionId);
            
            window.wsClient.onConnect(() => {
                this.wsConnected = true;
                console.log('✅ Editor WebSocket connected');
                this.startTelemetryTracking();
            });
            
            window.wsClient.onMessage((data) => {
                this.handleTelemetryUpdate(data);
            });
            
            window.wsClient.onDisconnect(() => {
                this.wsConnected = false;
                console.log('⚠️ Editor WebSocket disconnected');
            });
            
        } catch (error) {
            console.warn('⚠️ Failed to start editor session:', error);
        }
    }
    
    startTelemetryTracking() {
        // Send telemetry updates every 5 seconds
        this.telemetryInterval = setInterval(() => {
            if (this.wsConnected && this.keystrokeCount > 0) {
                window.wsClient.sendMessage({
                    type: 'telemetry_event',
                    event_type: 'keypress',
                    data: {
                        keystroke_count: this.keystrokeCount,
                        time_since_last: Date.now() - this.lastKeystrokeTime
                    }
                });
                this.keystrokeCount = 0;
            }
        }, 5000);
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
            
            // Track keystrokes for telemetry
            this.editor.onDidChangeModelContent(() => {
                this.keystrokeCount++;
                this.lastKeystrokeTime = Date.now();
                
                // Send code changes to WebSocket (debounced)
                if (this.wsConnected) {
                    clearTimeout(this.codeChangeTimeout);
                    this.codeChangeTimeout = setTimeout(() => {
                        window.wsClient.sendMessage({
                            type: 'context_update',
                            event_type: 'code_change',
                            message: this.editor.getValue()
                        });
                    }, 2000);
                }
            });
            
            console.log('✨ Monaco Editor initialized with telemetry tracking');
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
                this.errorCount++;
                
                // Send error telemetry
                if (this.wsConnected) {
                    window.wsClient.sendMessage({
                        type: 'telemetry_event',
                        event_type: 'error',
                        data: {
                            error_message: result.error,
                            code_length: code.length
                        }
                    });
                }
            } else {
                this.showOutput('Code executed successfully (no output)', 'success');
                this.updateStatus('success');
            }
        } catch (error) {
            this.showOutput(`Error: ${error.message}`, 'error');
            this.updateStatus('error');
            this.errorCount++;
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
            this.keystrokeCount = 0;
            this.errorCount = 0;
            console.log('🔄 Code reset');
        }
    }
    
    addSubmitButton() {
        // Add Submit for Review button next to existing buttons
        const submitBtn = document.createElement('button');
        submitBtn.className = 'editor-btn';
        submitBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11l3 3L22 4"></path>
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path>
            </svg>
            <span>Submit for Review</span>
        `;
        submitBtn.title = 'Submit code for Gap 3 Socratic analysis';
        submitBtn.addEventListener('click', () => this.submitForReview());
        
        const toolbar = document.querySelector('.editor-toolbar');
        toolbar.appendChild(submitBtn);
    }
    
    async submitForReview() {
        const code = this.editor.getValue();
        
        if (!code.trim()) {
            alert('Please write some code before submitting for review.');
            return;
        }
        
        this.showOutput('Submitting code for Gap 3 Socratic analysis...', 'info');
        
        try {
            // Call Gap 3 code submission endpoint
            const result = await window.apiClient.submitCodeForReview(
                code, 
                this.sessionId,
                this.currentProblemId || 'general_practice'
            );
            
            if (result.feedback) {
                this.showOutput(`Gap 3 Socratic Analysis:\n\n${result.feedback}`, 'success');
            } else {
                this.showOutput('Code submitted successfully. No specific feedback at this time.', 'success');
            }
            
        } catch (error) {
            this.showOutput(`Failed to submit code: ${error.message}`, 'error');
            console.error('Code submission error:', error);
        }
    }
    
    handleTelemetryUpdate(data) {
        if (data.type === 'telemetry_update') {
            // Display telemetry alerts from Gap 5
            const metrics = data.metrics || {};
            const alerts = data.alerts || [];
            
            if (alerts.length > 0) {
                alerts.forEach(alert => {
                    this.showTelemetryAlert(alert);
                });
            }
            
            console.log('📊 Telemetry Update:', metrics);
        } else if (data.type === 'pause_detected') {
            this.showTelemetryAlert({
                type: 'pause',
                severity: 'info',
                message: data.message || 'Pause detected - take your time to think through the problem.',
                recommendation: 'Consider reviewing the problem requirements or requesting a hint.'
            });
        }
    }
    
    showTelemetryAlert(alert) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `telemetry-alert ${alert.severity || 'info'}`;
        alertDiv.innerHTML = `
            <div class="alert-content">
                <div class="alert-icon">
                    ${alert.severity === 'warning' ? '⚠️' : alert.severity === 'error' ? '❌' : 'ℹ️'}
                </div>
                <div class="alert-body">
                    <div class="alert-title">${alert.type || 'Telemetry Alert'}</div>
                    <div class="alert-message">${alert.message}</div>
                    ${alert.recommendation ? `<div class="alert-recommendation">💡 ${alert.recommendation}</div>` : ''}
                </div>
                <button class="alert-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add styles if not present
        if (!document.getElementById('telemetry-alert-styles')) {
            const style = document.createElement('style');
            style.id = 'telemetry-alert-styles';
            style.textContent = `
                .telemetry-alert {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    max-width: 400px;
                    z-index: 1000;
                    animation: slideUp 0.3s ease;
                }
                .alert-content {
                    background: rgba(0, 0, 0, 0.95);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(0, 212, 255, 0.3);
                    border-radius: 12px;
                    padding: 20px;
                    display: flex;
                    gap: 15px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                }
                .telemetry-alert.warning .alert-content {
                    border-color: rgba(255, 165, 0, 0.5);
                }
                .telemetry-alert.error .alert-content {
                    border-color: rgba(255, 0, 0, 0.5);
                }
                .alert-icon {
                    font-size: 24px;
                }
                .alert-body {
                    flex: 1;
                    color: white;
                }
                .alert-title {
                    font-weight: 600;
                    margin-bottom: 5px;
                    text-transform: capitalize;
                    color: #00d4ff;
                }
                .alert-message {
                    font-size: 14px;
                    line-height: 1.5;
                    margin-bottom: 8px;
                }
                .alert-recommendation {
                    font-size: 13px;
                    font-style: italic;
                    color: rgba(255, 255, 255, 0.8);
                }
                .alert-close {
                    background: none;
                    border: none;
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 24px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    align-self: flex-start;
                }
                .alert-close:hover {
                    color: white;
                }
                @keyframes slideUp {
                    from {
                        transform: translateY(100px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 15 seconds
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 15000);
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
