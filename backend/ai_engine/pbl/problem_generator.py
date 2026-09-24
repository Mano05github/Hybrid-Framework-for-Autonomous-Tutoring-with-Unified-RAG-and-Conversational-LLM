"""
problem_generator.py — Generates PBL problems from RAG context

Flow:
    1. Retrieve RAG context chunks for the concept's topic
    2. Build a generation prompt with difficulty constraints
    3. Call LLM → parse structured problem JSON
    4. Return a ProblemSpec dataclass

The output is deterministic enough to be reproduceable given the same
concept + difficulty (via temperature=0), but the RAG context may vary.
"""

import json
import logging
import re
from dataclasses import dataclass, asdict
from typing import Optional

from rag.retriever import retrieve_context
from llm_engine.factory import LLMFactory

logger = logging.getLogger(__name__)

# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ProblemSpec:
    title: str
    statement: str
    concept_name: str
    subject_name: str
    difficulty: int        # 1–5
    expected_output: str   # What a correct solution should produce/output
    hints: list            # Pre-generated Socratic hints, 5 levels
    tags: list             # e.g. ['loops', 'conditionals']


# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are an expert coding tutor who creates exciting Problem-Based Learning
challenges for students. Given a concept and RAG-retrieved content, generate one coding problem.

Return ONLY valid JSON with these keys:
{
  "title": "Short problem title",
  "statement": "Full problem description including examples. Use markdown.",
  "expected_output": "Description of what correct code should produce",
  "hints": [
    "Hint 1 (very vague, e.g. think about the structure)",
    "Hint 2 (slightly more specific)",
    "Hint 3 (point to correct approach)",
    "Hint 4 (near-direct guidance)",
    "Hint 5 (almost give the answer)"
  ],
  "tags": ["tag1", "tag2"]
}"""

_USER_PROMPT_TPL = """Concept: {concept}
Subject: {subject}
Difficulty level: {difficulty}/5 ({difficulty_desc})

RAG Context (study material):
---
{rag_context}
---

Generate a Python coding problem that:
- Tests understanding of "{concept}" at difficulty {difficulty}/5
- Is solvable in 15–30 minutes
- Requires writing actual Python code
- Has a clear, measurable expected output
- Is engaging and relatable for a {grade_hint} student"""

_DIFFICULTY_MAP = {
    1: "beginner — very basic syntax, no complex logic",
    2: "elementary — simple conditionals and loops",
    3: "intermediate — functions, lists, basic algorithms",
    4: "advanced — OOP, recursion, or data structures",
    5: "expert — complex algorithms, optimization",
}

_GRADE_HINTS = {
    1: "middle school",
    2: "high school freshman",
    3: "high school sophomore/junior",
    4: "high school senior or CS introductory college",
    5: "advanced college",
}


# ── Main function ─────────────────────────────────────────────────────────────

def generate_problem(concept_node, difficulty: int = None) -> Optional[ProblemSpec]:
    """
    Generate a PBL problem for the given ConceptNode.

    Args:
        concept_node: ConceptNode instance
        difficulty:   Override difficulty; defaults to concept_node.difficulty

    Returns:
        ProblemSpec or None on failure
    """
    if difficulty is None:
        difficulty = concept_node.difficulty

    difficulty = max(1, min(5, difficulty))

    topic    = concept_node.topic
    subject  = topic.subject

    # 1. Retrieve RAG context
    rag_context = retrieve_context(
        query=f"coding problem about {topic.title}",
        topic_id=topic.pk,
        intent="example",
        difficulty_bias="confident" if difficulty >= 4 else None,
        k=10,
        max_chars=2500,
    )

    if not rag_context:
        rag_context = topic.description or f"Topic: {topic.title}"

    # 2. Build prompt
    user_prompt = _USER_PROMPT_TPL.format(
        concept=topic.title,
        subject=subject.name,
        difficulty=difficulty,
        difficulty_desc=_DIFFICULTY_MAP.get(difficulty, "intermediate"),
        rag_context=rag_context,
        grade_hint=_GRADE_HINTS.get(difficulty, "student"),
    )

    # 3. Call LLM
    llm = LLMFactory.get_provider()
    try:
        raw = llm.generate_response(
            prompt=user_prompt,
            system_instruction=_SYSTEM_PROMPT,
        )
        logger.info('[ProblemGen] LLM responded (%d chars)', len(raw or ''))
    except Exception as exc:
        logger.error('[ProblemGen] LLM call failed: %s', exc)
        return _fallback_problem(concept_node, difficulty)

    # 4. Parse JSON
    spec = _parse_response(raw, concept_node, difficulty)
    if spec is None:
        spec = _fallback_problem(concept_node, difficulty)

    return spec


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_response(raw: str, concept_node, difficulty: int) -> Optional[ProblemSpec]:
    if not raw:
        return None

    # Strip markdown code fences if present
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON block
        m = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                logger.error('[ProblemGen] JSON parse failed after extraction')
                return None
        else:
            logger.error('[ProblemGen] No JSON found in LLM response')
            return None

    topic   = concept_node.topic
    subject = topic.subject

    return ProblemSpec(
        title           = str(data.get('title', topic.title)),
        statement       = str(data.get('statement', '')),
        concept_name    = topic.title,
        subject_name    = subject.name,
        difficulty      = difficulty,
        expected_output = str(data.get('expected_output', '')),
        hints           = list(data.get('hints', [])),
        tags            = list(data.get('tags', [])),
    )


def _fallback_problem(concept_node, difficulty: int) -> ProblemSpec:
    topic   = concept_node.topic
    subject = topic.subject

    statement = (
        f"Write a Python program that demonstrates your understanding of **{topic.title}**.\n\n"
        f"Your program should:\n"
        f"- Use the core concepts of {topic.title}\n"
        f"- Produce clear, readable output\n"
        f"- Handle at least one edge case\n\n"
        f"Start simple and build up as you go. There's no single correct answer — "
        f"show your thinking!"
    )

    return ProblemSpec(
        title=f"{topic.title} Challenge",
        statement=statement,
        concept_name=topic.title,
        subject_name=subject.name,
        difficulty=difficulty,
        expected_output="A working Python program demonstrating the concept.",
        hints=[
            f"Think about what {topic.title} means at its core.",
            f"What is the basic structure needed?",
            f"Consider a simple example first, then extend it.",
            f"Look at the expected output — what operations produce it?",
            f"Try writing just the function signature first, then fill in the body.",
        ],
        tags=[topic.title.lower().replace(' ', '_')],
    )
