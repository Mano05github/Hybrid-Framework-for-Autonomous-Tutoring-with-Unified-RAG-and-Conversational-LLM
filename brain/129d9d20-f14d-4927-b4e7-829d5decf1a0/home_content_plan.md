# Home Page Content Refinement Plan

The goal is to adapt the "WebUni" visual framework to the "Vaathiyar AI" product concept, removing generic template content.

## Core Concept
**Vaathiyar AI** is a personal tutoring platform focused on coding, logic, and interactive learning via Voice and Whiteboard.

## Proposed Content Mapping

### 1. Hero Section
-   **Headline**: Change from "Get The Best Free Online Courses" to:
    -   *Option A*: "Master Logic & Coding with Your AI Tutor"
    -   *Option B*: "Your Personal Guide to Computer Science Mastery"
-   **Sub-headline**: "Interactive Voice Tutoring, Real-time Code Analysis, and Smart Whiteboard Sessions."
-   **Search Box**:
    -   Label: "What do you want to learn today?"
    -   Inputs: "Topic" (e.g., Recursion, Arrays) rather than "Course".

### 2. Categories Section (The 6 Grid Items)
*Current (Generic): IT Dev, Web Design, Illustration, Social Media, Photoshop, Crypto.*
*Proposed (Project Relevant - Computer Science Focus):*
1.  **Algorithms**: Core logic and problem-solving patterns.
2.  **Data Structures**: Arrays, Trees, Graphs, Linked Lists.
3.  **Python Programming**: Syntax, libraries, and best practices.
4.  **System Design**: Architecture, scalability, and database design.
5.  **AI & Machine Learning**: Basics of neural networks and models.
6.  **Web Engineering**: Modern full-stack development concepts.

### 3. Featured Courses Section
*Rename to: "Popular Learning Modules" or "Curated Paths"*
*Items (Examples):*
-   **Introduction to Algorithms**: "Master the basics of sorting and searching." (Level: Beginner)
-   **Advanced Data Structures**: "Deep dive into Graphs and Trees." (Level: Advanced)
-   **Python for Data Science**: "Learn pandas, numpy, and visualization."
-   **Full Stack Roadmap**: "From React to Django/Node."

### 4. CTA Section
-   **Headline**: "Ready to code smarter?"
-   **Text**: "Join your personal AI learning session. No scheduling required, always available."
-   **Button**: "Start Session Now"

## Implementation Actions
-   [ ] Update `frontend/app/page.tsx` with specific text and lucide-icons matching the new categories.
-   [ ] Update `frontend/components/CourseCard.tsx` (if needed) or just the data passed to it to reflect "Modules" instead of generic courses.
-   [ ] Ensure `Sidebar` and `Header` navigation remains consistent.
