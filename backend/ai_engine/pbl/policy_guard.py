"""
PBL policy guardrails for response safety and Socratic compliance.

This module enforces lightweight post-generation checks so mentor output
remains guidance-oriented even when model generations drift.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


_DIRECT_ANSWER_PATTERNS = [
    re.compile(r"\bhere is (the|your) (full|complete) (answer|solution)\b", re.IGNORECASE),
    re.compile(r"\bcopy(?: and)? paste\b", re.IGNORECASE),
    re.compile(r"\bfinal answer\b", re.IGNORECASE),
    re.compile(r"```(?:python|py)?[\s\S]{20,}```", re.IGNORECASE),
]


@dataclass
class PolicyResult:
    text: str
    blocked: bool
    reason: Optional[str] = None


def apply_socratic_policy(text: str, *, struggle_type: Optional[str] = None) -> PolicyResult:
    """
    Apply post-generation policy checks.

    If the response looks like a direct solution handoff, replace it with a
    concise Socratic redirection that still keeps the learner progressing.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return PolicyResult(text="What have you tried so far?", blocked=True, reason="empty_response")

    for pattern in _DIRECT_ANSWER_PATTERNS:
        if pattern.search(cleaned):
            return PolicyResult(
                text=_fallback_guidance(struggle_type),
                blocked=True,
                reason="direct_answer_pattern",
            )

    # Keep responses concise for conversational pacing.
    if len(cleaned) > 1200:
        cleaned = cleaned[:1200].rsplit(" ", 1)[0] + " ..."

    return PolicyResult(text=cleaned, blocked=False, reason=None)


def _fallback_guidance(struggle_type: Optional[str]) -> str:
    if struggle_type == "syntax_confusion":
        return "Let us debug one line together. Which line looks syntactically incomplete to you?"
    if struggle_type == "misconception":
        return "Before we finalize anything, what rule do you think applies here, and why?"
    if struggle_type == "stuck":
        return "You are close. What is the smallest next step you can try in your current code?"
    return "I will guide you step by step. What is your next small move toward solving this?"
