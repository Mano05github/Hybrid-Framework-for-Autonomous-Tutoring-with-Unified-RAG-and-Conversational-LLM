/**
 * Assessment Workspace - Quiz Interface
 * ======================================
 * Interactive quiz and assessment UI
 */

class AssessmentWorkspace {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Assessment workspace container not found');
            return;
        }
        
        this.currentQuestion = 0;
        this.score = 0;
        this.answers = [];
        this.questions = [];
        
        this.init();
    }
    
    async init() {
        await this.loadQuestions();
        this.createLayout();
        this.displayQuestion();
        console.log('📝 Assessment Workspace initialized');
    }
    
    async loadQuestions() {
        // Mock questions - in production, fetch from backend
        this.questions = [
            {
                id: 1,
                question: "What is the output of print(2 ** 3)?",
                options: ["6", "8", "9", "Error"],
                correct: 1
            },
            {
                id: 2,
                question: "Which data type is mutable in Python?",
                options: ["tuple", "string", "list", "int"],
                correct: 2
            },
            {
                id: 3,
                question: "What does the len() function do?",
                options: [
                    "Returns the length of an object",
                    "Creates a new list",
                    "Converts to integer",
                    "None of the above"
                ],
                correct: 0
            }
        ];
    }
    
    createLayout() {
        this.container.innerHTML = `
            <div class="assessment-layout">
                <div class="assessment-header">
                    <div class="progress-info">
                        <span class="question-counter">
                            Question <span id="current-q">1</span> of <span id="total-q">${this.questions.length}</span>
                        </span>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="score-display">
                        Score: <span id="score-value">0</span>/${this.questions.length}
                    </div>
                </div>
                
                <div class="question-container" id="question-container">
                    <!-- Question will be rendered here -->
                </div>
                
                <div class="assessment-footer">
                    <button class="nav-btn" id="prev-btn" disabled>
                        <i data-lucide="chevron-left"></i>
                        Previous
                    </button>
                    <button class="nav-btn primary" id="next-btn">
                        Next
                        <i data-lucide="chevron-right"></i>
                    </button>
                    <button class="nav-btn success" id="submit-btn" style="display: none;">
                        <i data-lucide="check-circle"></i>
                        Submit Assessment
                    </button>
                </div>
            </div>
        `;
        
        // Initialize lucide icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
        // Setup event listeners
        document.getElementById('prev-btn').addEventListener('click', () => this.previousQuestion());
        document.getElementById('next-btn').addEventListener('click', () => this.nextQuestion());
        document.getElementById('submit-btn').addEventListener('click', () => this.submitAssessment());
    }
    
    displayQuestion() {
        const question = this.questions[this.currentQuestion];
        const container = document.getElementById('question-container');
        
        container.innerHTML = `
            <div class="question-card">
                <h3 class="question-text">${question.question}</h3>
                <div class="options-list">
                    ${question.options.map((option, index) => `
                        <button class="option-btn ${this.answers[this.currentQuestion] === index ? 'selected' : ''}" 
                                data-index="${index}">
                            <span class="option-letter">${String.fromCharCode(65 + index)}</span>
                            <span class="option-text">${option}</span>
                            ${this.answers[this.currentQuestion] === index ? '<i data-lucide="check"></i>' : ''}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Re-initialize lucide icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
        // Add click listeners to options
        const optionBtns = container.querySelectorAll('.option-btn');
        optionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const index = parseInt(btn.dataset.index);
                this.selectAnswer(index);
            });
        });
        
        // Update UI
        this.updateUI();
    }
    
    selectAnswer(index) {
        this.answers[this.currentQuestion] = index;
        this.displayQuestion();
    }
    
    previousQuestion() {
        if (this.currentQuestion > 0) {
            this.currentQuestion--;
            this.displayQuestion();
        }
    }
    
    nextQuestion() {
        if (this.currentQuestion < this.questions.length - 1) {
            this.currentQuestion++;
            this.displayQuestion();
        }
    }
    
    updateUI() {
        // Update question counter
        document.getElementById('current-q').textContent = this.currentQuestion + 1;
        
        // Update progress bar
        const progress = ((this.currentQuestion + 1) / this.questions.length) * 100;
        document.getElementById('progress-fill').style.width = `${progress}%`;
        
        // Update navigation buttons
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const submitBtn = document.getElementById('submit-btn');
        
        prevBtn.disabled = this.currentQuestion === 0;
        
        if (this.currentQuestion === this.questions.length - 1) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'flex';
        } else {
            nextBtn.style.display = 'flex';
            submitBtn.style.display = 'none';
        }
    }
    
    submitAssessment() {
        // Calculate score
        this.score = 0;
        this.answers.forEach((answer, index) => {
            if (answer === this.questions[index].correct) {
                this.score++;
            }
        });
        
        // Show results
        this.showResults();
    }
    
    showResults() {
        const percentage = Math.round((this.score / this.questions.length) * 100);
        const container = document.getElementById('question-container');
        
        container.innerHTML = `
            <div class="results-card">
                <div class="results-icon">
                    <i data-lucide="${percentage >= 70 ? 'trophy' : 'target'}"></i>
                </div>
                <h2 class="results-title">Assessment Complete!</h2>
                <div class="results-score">
                    <div class="score-circle">
                        <span class="score-percentage">${percentage}%</span>
                    </div>
                    <p class="score-text">You scored ${this.score} out of ${this.questions.length}</p>
                </div>
                <div class="results-message">
                    ${percentage >= 90 ? '🎉 Excellent work!' : 
                      percentage >= 70 ? '👍 Good job!' : 
                      percentage >= 50 ? '📚 Keep practicing!' : 
                      '💪 Don\'t give up!'}
                </div>
                <button class="retry-btn" id="retry-btn">
                    <i data-lucide="rotate-ccw"></i>
                    Try Again
                </button>
            </div>
        `;
        
        // Re-initialize lucide icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
        // Update score display
        document.getElementById('score-value').textContent = this.score;
        
        // Hide footer buttons
        document.querySelector('.assessment-footer').style.display = 'none';
        
        // Retry button
        document.getElementById('retry-btn').addEventListener('click', () => {
            this.reset();
        });
    }
    
    reset() {
        this.currentQuestion = 0;
        this.score = 0;
        this.answers = [];
        document.querySelector('.assessment-footer').style.display = 'flex';
        this.displayQuestion();
    }
    
    destroy() {
        this.container.innerHTML = '';
    }
}

// Expose to global window object
window.AssessmentWorkspace = AssessmentWorkspace;
