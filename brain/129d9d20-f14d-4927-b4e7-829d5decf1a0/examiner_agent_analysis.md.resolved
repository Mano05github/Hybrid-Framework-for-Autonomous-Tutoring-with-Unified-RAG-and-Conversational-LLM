# Deep Analysis: Examiner Agent ("The Quiz Master")

## 1. 🏛️ Agent Description
*   **Name**: Examiner Agent.
*   **Role**: The assessment engine. It generates dynamic questions to verify understanding.
*   **Philosophy**: "Assessment for Learning." Quizzes are for feedback, not just grading.

---

## 2. ⚙️ Technical Working Model

### Inputs
1.  **Topic**: "Binary Search Trees".
2.  **Difficulty**: "Hard" (0.8).
3.  **Type**: "MCQ" or "Code Challenge".

### Core Logic (The Algorithms)
#### A. Few-Shot Generation
*   **Prompt**: Uses 3 examples of "Good Questions" in the prompt to ensure JSON format stability.
*   **Validation**: Self-Correction loop. If JSON is broken, it regenerates.

#### B. Adaptive Grading
*   **Logic**:
    *   If User Answer is Wrong -> Explain *why* the specific wrong option is incorrect (Distractor Analysis).
    *   If User Code fails -> Provide a Test Case that breaks it.

### Outputs
*   **Quiz Object**:
    ```json
    {
      "question": "What is the worst-case time complexity...",
      "options": ["O(n)", "O(log n)", "O(n^2)"],
      "correct": "O(n)",
      "explanation": "In a skewed tree, it becomes a linked list."
    }
    ```

---

## 3. 🔄 Workflow Diagram

```mermaid
graph TD
    Request(Supervisor Request) --> Config[Difficulty Setter]
    
    Config --> Generator[LLM (Structured Output)]
    Generator --> Validator{Valid JSON?}
    
    Validator -- No --> Generator
    Validator -- Yes --> Output(Quiz JSON)
    
    UserAns(User Answer) --> Grader[Comparison Logic]
    Grader --> Feedback(Explanation)
```

---

## 4. 🛠️ Implementation Specs

*   **Model**: Llama 3.2 (Excellent at JSON structure).
*   **Format**: `langchain.output_parsers.PydanticOutputParser`.
