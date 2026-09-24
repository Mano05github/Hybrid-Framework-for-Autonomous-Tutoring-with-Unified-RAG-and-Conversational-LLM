# DOCX-Ready Outline
## Vaathiyar Adaptive AI Tutor - New Architecture Report

Date: March 14, 2026

Use this outline as the direct structure for Word/Docs formatting.

---

## Front Matter

1. Title Page
- Project title
- Student details
- Department/Institution
- Guide details
- Submission date

2. Declaration and Certificate (if required by institution)

3. Acknowledgement

4. Abstract
- Problem summary
- Architecture summary
- Key implemented capabilities
- Outcome summary

5. Table of Contents

6. List of Figures
- Figure 1 to Figure 27

7. List of Tables

---

## Chapter 1: Introduction

1.1 Project background  
1.2 Problem statement  
1.3 Project objectives  
1.4 Scope of implementation  
1.5 Report organization

---

## Chapter 2: System Overview

2.1 Executive architecture summary  
2.2 Technology stack  
2.3 Functional modules overview

Insert:
- Figure 1. System Context Diagram
- Figure 2. Layered Architecture View
- Figure 3. Runtime Component Architecture

---

## Chapter 3: Agentic Architecture Design

3.1 Supervisor routing strategy  
3.2 Specialist agents and responsibilities  
3.3 Agent graph topology  
3.4 Shared state contract

Insert:
- Figure 4. Supervisor Routing Decision Flow
- Figure 5. Agent Graph Topology
- Figure 16. AgentState Contract Diagram

---

## Chapter 4: Session and Interaction Architecture

4.1 Session lifecycle model  
4.2 Realtime WebSocket interaction  
4.3 Voice processing architecture  
4.4 Socratic adaptation cycle

Insert:
- Figure 6. Session Phase State Machine
- Figure 10. WebSocket Learning Session Sequence
- Figure 11. Voice Input/Output Sequence
- Figure 8. Use Case Realization Map

---

## Chapter 5: Functional Use Cases

5.1 Primary actors and use cases  
5.2 Student journey use cases  
5.3 Tutor/reviewer interaction use cases

Insert:
- Figure 7. Use Case Diagram (Primary)

---

## Chapter 6: Sequence-Level Behavioral Analysis

6.1 HTTP chat execution sequence  
6.2 Coding submission sequence  
6.3 Emotion adaptation sequence  
6.4 Telemetry and forecasting sequence

Insert:
- Figure 9. HTTP Chat Request Sequence
- Figure 12. Coding Submission Sequence
- Figure 13. Emotion Adaptation Sequence
- Figure 14. Telemetry and Visionary Monitoring Sequence

---

## Chapter 7: Data and Domain Model Design

7.1 Core curriculum and mastery entities  
7.2 Coding subsystem entities  
7.3 Emotion subsystem entities  
7.4 PBL subsystem entities  
7.5 Database relationship summary

Insert:
- Figure 15. Core Learning Domain Class Diagram
- Figure 17. Coding Domain Class Diagram
- Figure 18. Emotion Domain Class Diagram
- Figure 19. PBL Domain Class Diagram
- Figure 20. ER-Style Data Relationship Diagram

---

## Chapter 8: Data Flow and Processing Design

8.1 DFD Level 0  
8.2 DFD Level 1 (learning session)  
8.3 DFD Level 1 (coding tutor)

Insert:
- Figure 21. DFD Level 0 (Whole Platform)
- Figure 22. DFD Level 1 (Learning Session)
- Figure 23. DFD Level 1 (Coding Tutor)

---

## Chapter 9: Performance and Optimization Architecture

9.1 Multi-level cache architecture  
9.2 RAG-grounded response path  
9.3 Render mode decision logic  
9.4 Logical deployment layout

Insert:
- Figure 24. Multi-Level Cache Strategy
- Figure 25. RAG-Enhanced Teaching Pipeline
- Figure 26. Render Mode Selection Logic
- Figure 27. Deployment View (Logical)

---

## Chapter 10: Techniques and Strategies Implemented

10.1 Intent routing strategy  
10.2 Phase-aware tutoring strategy  
10.3 Mastery and revision strategy  
10.4 Coding hint progression strategy  
10.5 Emotion adaptation strategy  
10.6 Telemetry-driven monitoring strategy

Insert table:
- Implemented Techniques and Strategies

---

## Chapter 11: API and Interface Specification

11.1 Top-level API groups  
11.2 AI endpoints  
11.3 Session endpoints  
11.4 Realtime endpoint  
11.5 Input/Output payload highlights

---

## Chapter 12: Implementation Constraints and Reality Notes

12.1 Current routing/wiring constraints  
12.2 State consistency constraints  
12.3 Scale-out constraints

---

## Chapter 13: Evaluation Perspective

13.1 Architectural strengths  
13.2 Technical risks and mitigations  
13.3 Reviewer-facing observations

---

## Chapter 14: Conclusion and Future Hardening Scope

14.1 Conclusion  
14.2 Practical next hardening steps (implementation-consistent)

---

## References

Include code and docs references used for analysis.

Recommended list:
- backend/config/urls.py
- backend/ai_engine/urls.py
- backend/learning_session/urls.py
- backend/learning_session/routing.py
- backend/ai_engine/views.py
- backend/learning_session/views.py
- backend/learning_session/consumers.py
- backend/learning_session/orchestrator.py
- backend/ai_engine/graph.py
- backend/ai_engine/agents.py
- backend/ai_engine/state.py
- backend/core/models.py
- backend/learning_session/models.py
- backend/ai_engine/pbl/models.py

---

## Appendices

A. Mermaid figure source blocks  
B. Endpoint payload examples  
C. Sample runtime logs/screenshots  
D. Testing notes (if included)

