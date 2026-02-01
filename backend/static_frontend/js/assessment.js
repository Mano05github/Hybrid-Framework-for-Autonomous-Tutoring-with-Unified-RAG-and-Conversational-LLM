// ===================================
// ASSESSMENT PAGE FUNCTIONALITY
// ===================================

class AssessmentController {
    constructor() {
        this.currentQuestionIndex = 0;
        this.totalQuestions = 0;
        this.selectedAnswers = [];
        this.reasonings = [];
        this.questions = [];
        this.sessionId = null;
        this.quizId = null;
        this.startTime = null;
        this.questionStartTimes = [];
        
        // DOM elements
        this.mcqContent = document.getElementById('mcqContent');
        this.codeContent = document.getElementById('codeContent');
        this.modeBtns = document.querySelectorAll('.mode-btn');
        this.optionCards = document.querySelectorAll('.option-card');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.submitBtn = document.getElementById('submitBtn');
        this.reasoningTextarea = document.getElementById('reasoning');
        
        // Progress elements
        this.currentQuestionSpan = document.getElementById('currentQuestion');
        this.totalQuestionsSpan = document.getElementById('totalQuestions');
        this.progressPercentSpan = document.getElementById('progressPercent');
        this.progressFill = document.getElementById('progressFill');
        
        this.init();
    }
    
    async init() {
        // Start session
        await this.initSession();
        
        // Load questions from backend
        await this.loadQuestions();
        
        // Mode switcher
        this.modeBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchMode(btn.dataset.mode));
        });
        
        // Option selection
        this.optionCards.forEach(card => {
            card.addEventListener('click', () => this.selectOption(card));
        });
        
        // Navigation buttons
        this.prevBtn.addEventListener('click', () => this.previousQuestion());
        this.nextBtn.addEventListener('click', () => this.nextQuestion());
        this.submitBtn.addEventListener('click', () => this.submitAssessment());
        
        // Reasoning textarea
        this.reasoningTextarea.addEventListener('input', (e) => {
            this.reasonings[this.currentQuestionIndex] = e.target.value;
        });
        
        // Initialize display
        this.startTime = Date.now();
        this.questionStartTimes[this.currentQuestionIndex] = Date.now();
        this.updateDisplay();
    }
    
    async initSession() {
        try {
            const session = await window.apiClient.startSession();
            this.sessionId = session.id || session.session_id;
            console.log('✅ Assessment session started:', this.sessionId);
            
            // Connect WebSocket for quiz results
            window.wsClient.connect(this.sessionId);
            window.wsClient.onConnect(() => {
                console.log('✅ WebSocket connected for assessment');
            });
        } catch (error) {
            console.error('❌ Failed to start session:', error);
        }
    }
    
    async loadQuestions() {
        try {
            // Get topic from URL params or use default
            const urlParams = new URLSearchParams(window.location.search);
            const topicId = urlParams.get('topic') || '1';
            
            // Try to load quiz from backend
            const response = await window.apiClient.request(`/api/core/quizzes/?topic_id=${topicId}`);
            
            if (response && response.length > 0) {
                const quiz = response[0];
                this.quizId = quiz.id;
                this.questions = quiz.questions || [];
                this.totalQuestions = this.questions.length;
                
                console.log(`✅ Loaded ${this.totalQuestions} questions from backend`);
            } else {
                // Fallback to generated questions if API returns empty
                console.warn('⚠️ No questions from API, generating fallback questions');
                await this.generateQuestionsFromExaminer();
            }
            
            // Initialize arrays
            this.selectedAnswers = new Array(this.totalQuestions).fill(null);
            this.reasonings = new Array(this.totalQuestions).fill('');
            this.questionStartTimes = new Array(this.totalQuestions).fill(null);
            
        } catch (error) {
            console.error('❌ Failed to load questions:', error);
            // Fallback to sample questions
            this.questions = this.generateSampleQuestions();
            this.totalQuestions = this.questions.length;
            this.selectedAnswers = new Array(this.totalQuestions).fill(null);
            this.reasonings = new Array(this.totalQuestions).fill('');
            this.questionStartTimes = new Array(this.totalQuestions).fill(null);
        }
    }
    
    async generateQuestionsFromExaminer() {
        try {
            // Call Examiner Agent to generate quiz
            const response = await window.apiClient.request('/api/gaps/generate-quiz/', {
                method: 'POST',
                body: JSON.stringify({
                    topic: 'General Programming',
                    difficulty: 'medium',
                    count: 10
                })
            });
            
            if (response && response.questions) {
                this.questions = response.questions;
                this.totalQuestions = this.questions.length;
                console.log('✅ Generated questions from Examiner Agent');
            } else {
                throw new Error('Examiner Agent returned no questions');
            }
        } catch (error) {
            console.error('❌ Examiner Agent failed, using sample questions:', error);
            this.questions = this.generateSampleQuestions();
            this.totalQuestions = this.questions.length;
        }
    }
    
    switchMode(mode) {
        // Update active button
        this.modeBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        
        // Show/hide content
        if (mode === 'mcq') {
            this.mcqContent.classList.remove('hidden');
            this.codeContent.classList.add('hidden');
        } else {
            this.mcqContent.classList.add('hidden');
            this.codeContent.classList.remove('hidden');
        }
    }
    
    selectOption(selectedCard) {
        // Remove previous selection
        this.optionCards.forEach(card => card.classList.remove('selected'));
        
        // Add selection to clicked card
        selectedCard.classList.add('selected');
        
        // Store answer
        this.selectedAnswers[this.currentQuestionIndex] = selectedCard.dataset.option;
        
        console.log('Selected:', selectedCard.dataset.option);
    }
    
    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.questionStartTimes[this.currentQuestionIndex] = Date.now();
            this.updateDisplay();
        }
    }
    
    nextQuestion() {
        if (this.currentQuestionIndex < this.totalQuestions - 1) {
            this.currentQuestionIndex++;
            this.questionStartTimes[this.currentQuestionIndex] = Date.now();
            this.updateDisplay();
        }
    }
    
    updateDisplay() {
        const question = this.questions[this.currentQuestionIndex];
        
        // Update question text
        document.querySelector('.question-number').textContent = `Q${this.currentQuestionIndex + 1}`;
        document.getElementById('questionText').textContent = question.text;
        
        // Update options
        this.optionCards.forEach((card, index) => {
            const optionKey = String.fromCharCode(65 + index); // A, B, C, D
            card.querySelector('.option-text').textContent = question.options[optionKey];
            
            // Restore selection if exists
            if (this.selectedAnswers[this.currentQuestionIndex] === optionKey) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });
        
        // Update reasoning
        this.reasoningTextarea.value = this.reasonings[this.currentQuestionIndex];
        
        // Update progress
        this.currentQuestionSpan.textContent = this.currentQuestionIndex + 1;
        this.totalQuestionsSpan.textContent = this.totalQuestions;
        
        const progressPercent = Math.round(((this.currentQuestionIndex + 1) / this.totalQuestions) * 100);
        this.progressPercentSpan.textContent = progressPercent;
        this.progressFill.style.width = `${progressPercent}%`;
        
        // Update button states
        this.prevBtn.disabled = this.currentQuestionIndex === 0;
        this.nextBtn.disabled = this.currentQuestionIndex === this.totalQuestions - 1;
        
        // Show submit button on last question
        if (this.currentQuestionIndex === this.totalQuestions - 1) {
            this.submitBtn.style.display = 'flex';
        } else {
            this.submitBtn.style.display = 'none';
        }
    }
    
    async submitAssessment() {
        // Count answered questions
        const answeredCount = this.selectedAnswers.filter(answer => answer !== null).length;
        
        if (answeredCount < this.totalQuestions) {
            const unanswered = this.totalQuestions - answeredCount;
            if (!confirm(`You have ${unanswered} unanswered question(s). Do you want to submit anyway?`)) {
                return;
            }
        }
        
        // Calculate score
        let score = 0;
        const results = [];
        
        this.selectedAnswers.forEach((answer, index) => {
            const question = this.questions[index];
            const isCorrect = answer === question.correct;
            if (isCorrect) score++;
            
            results.push({
                question_id: question.id || index,
                selected_answer: answer,
                correct_answer: question.correct,
                is_correct: isCorrect,
                reasoning: this.reasonings[index]
            });
        });
        
        const totalTime = Math.round((Date.now() - this.startTime) / 1000); // seconds
        const percentage = Math.round((score / this.totalQuestions) * 100);
        
        // Submit to backend and send via WebSocket
        try {
            // Submit results via API (if endpoint exists)
            /*
            await window.apiClient.request('/api/core/quiz-results/', {
                method: 'POST',
                body: JSON.stringify({
                    quiz_id: this.quizId,
                    session_id: this.sessionId,
                    score: score,
                    total: this.totalQuestions,
                    time_taken: totalTime,
                    results: results
                })
            });
            */
            
            // Send quiz result via WebSocket for AI analysis
            if (window.wsClient.isConnected()) {
                window.wsClient.sendMessage({
                    type: 'quiz_result',
                    correct_count: score,
                    total: this.totalQuestions,
                    time_taken: totalTime,
                    results: results
                });
                console.log('✅ Quiz results sent to AI for analysis');
            }
            
        } catch (error) {
            console.error('❌ Failed to submit quiz results:', error);
        }
        
        // Show results
        alert(`Assessment submitted!\n\nScore: ${score}/${this.totalQuestions} (${percentage}%)\nTime: ${Math.floor(totalTime / 60)}m ${totalTime % 60}s\n\nYou will be redirected to the dashboard.`);
        
        console.log('Quiz Results:', {
            score,
            total: this.totalQuestions,
            percentage,
            time: totalTime,
            results
        });
        
        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 2000);
    }
    
    generateSampleQuestions() {
        return [
            {
                text: "What is the capital of France?",
                options: { A: "Berlin", B: "Madrid", C: "Paris", D: "Rome" },
                correct: "C"
            },
            {
                text: "What is the time complexity of binary search?",
                options: { A: "O(n)", B: "O(log n)", C: "O(n²)", D: "O(1)" },
                correct: "B"
            },
            {
                text: "Which data structure uses LIFO (Last In First Out)?",
                options: { A: "Queue", B: "Stack", C: "Array", D: "Tree" },
                correct: "B"
            },
            {
                text: "What does HTML stand for?",
                options: { A: "Hyper Text Markup Language", B: "High Tech Modern Language", C: "Home Tool Markup Language", D: "Hyperlinks and Text Markup Language" },
                correct: "A"
            },
            {
                text: "Which sorting algorithm has the best average-case time complexity?",
                options: { A: "Bubble Sort", B: "Selection Sort", C: "Merge Sort", D: "Insertion Sort" },
                correct: "C"
            },
            {
                text: "What is the result of 2 + 2 * 2?",
                options: { A: "6", B: "8", C: "4", D: "10" },
                correct: "A"
            },
            {
                text: "Which programming language is known as the 'mother of all languages'?",
                options: { A: "Python", B: "Java", C: "C", D: "Assembly" },
                correct: "C"
            },
            {
                text: "What does CSS stand for?",
                options: { A: "Computer Style Sheets", B: "Cascading Style Sheets", C: "Creative Style Sheets", D: "Colorful Style Sheets" },
                correct: "B"
            },
            {
                text: "Which of these is NOT a JavaScript framework?",
                options: { A: "React", B: "Angular", C: "Vue", D: "Django" },
                correct: "D"
            },
            {
                text: "What is the maximum depth of a balanced binary tree with 15 nodes?",
                options: { A: "3", B: "4", C: "5", D: "6" },
                correct: "B"
            }
        ];
    }
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('📝 Initializing Assessment...');
    
    // Initialize assessment controller
    const assessmentController = new AssessmentController();
    
    console.log('✨ Assessment ready');
});
