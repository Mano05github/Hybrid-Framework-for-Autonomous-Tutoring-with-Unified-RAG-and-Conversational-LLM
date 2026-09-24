"""
ContentTypeClassifier — v3 Intelligent Mode Switching

Classifies teacher output to determine the frontend render mode:
  "tree"    → Tree Visualization Mode  (concepts, definitions, relationships)
  "canvas"  → Full Canvas / Whiteboard Mode  (formulas, problems, derivations)
  "default" → Fallback (narrative text, general explanation)

Also extracts a structured tree_data dict when mode == "tree", used by the
frontend Tree Mode component to render the live-growing concept tree.

Called from teacher_agent() after LLM response is generated.
"""
import re
import json
import logging
from typing import Tuple, Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# ── Signal patterns ────────────────────────────────────────────────────────────

# Canvas mode triggers (formula / problem / derivation signals)
_CANVAS_SIGNALS = [
    # LaTeX fragments
    r'\$[^$]+\$',               # inline $...$
    r'\$\$[^$]+\$\$',           # block $$...$$
    r'\\frac\{',                # LaTeX fraction
    r'\\int\b', r'\\sum\b', r'\\prod\b',
    r'\\sqrt\{',
    r'\\begin\{',               # LaTeX environment
    # Explicit math notation
    r'=\s*[0-9a-zA-Z\+\-\*/\^\(\)]+',   # assignment/equation
    r'\d+\s*[\+\-\×\÷\*\/]\s*\d+',      # arithmetic expression
    # Problem/derivation keywords
    r'\bderive[ds]?\b', r'\bderivation\b',
    r'\bprove\b', r'\bproof\b',
    r'\bnumerical(ly)?\b',
    r'\bstep[\s-]by[\s-]step\b',
    r'\bsolve\b', r'\bsolution\b',
    r'\bcalculat(e|ion)\b',
    r'\bdiagram\b', r'\bgraph\b', r'\bplot\b',
]

# Tree mode triggers (concept / structure / definition signals)
_TREE_SIGNALS = [
    r'\bdefinition\b', r'\bdefin(e|es|ing)\b',
    r'\bconcept\b', r'\btheory\b', r'\btheoretical\b',
    r'\bcomponent[s]?\b', r'\bpart[s]?\b',
    r'\btype[s]?\b', r'\bcategor(y|ies)\b',
    r'\bstructure\b', r'\borganiz(e|ation)\b',
    r'\brelationship\b', r'\bhierarch(y|ical)\b',
    r'\bclassif(y|ication)\b',
    r'\bprinciple[s]?\b', r'\bcharacteristic[s]?\b',
]

_CANVAS_RE = re.compile('|'.join(_CANVAS_SIGNALS), re.IGNORECASE)
_TREE_RE   = re.compile('|'.join(_TREE_SIGNALS),   re.IGNORECASE)

# Marker for LLM-generated tree structure
_TREE_START = "TREE_STRUCTURE_START"
_TREE_END   = "TREE_STRUCTURE_END"


def classify_content(text: str) -> Tuple[str, float]:
    """
    Classify a text block as "tree", "canvas", or "default".
    Returns (mode, confidence 0–1).
    """
    if not text:
        return "default", 0.5

    # Highest priority: check for CANVAS_SCRIPT_START marker already present
    if "CANVAS_SCRIPT_START" in text:
        return "canvas", 0.99

    # Check for embedded tree structure block
    if _TREE_START in text:
        return "tree", 0.99

    canvas_hits = len(_CANVAS_RE.findall(text))
    tree_hits   = len(_TREE_RE.findall(text))

    total = canvas_hits + tree_hits
    if total == 0:
        return "default", 0.5

    canvas_ratio = canvas_hits / total
    tree_ratio   = tree_hits   / total

    if canvas_ratio >= 0.5:
        confidence = min(0.95, 0.6 + canvas_ratio * 0.35)
        return "canvas", round(confidence, 2)
    elif tree_ratio >= 0.5:
        confidence = min(0.95, 0.6 + tree_ratio * 0.35)
        return "tree", round(confidence, 2)
    else:
        return "default", 0.5


def extract_tree_structure(llm_text: str, primary_concept: str = "") -> Optional[Dict[str, Any]]:
    """
    Extract a TREE_STRUCTURE_START...END JSON block from the LLM response.
    Falls back to a simple flat list of headings if no structured block found.

    Expected LLM JSON format:
    {
      "root": "Concept Name",
      "children": [
        {"label": "Sub-concept 1", "children": [...]},
        {"label": "Sub-concept 2", "children": []}
      ]
    }
    """
    start_idx = llm_text.find(_TREE_START)
    end_idx   = llm_text.find(_TREE_END)

    if start_idx != -1 and end_idx != -1:
        json_str = llm_text[start_idx + len(_TREE_START):end_idx].strip()
        try:
            tree = json.loads(json_str)
            if "root" in tree and "children" in tree:
                return tree
        except json.JSONDecodeError:
            logger.warning("[ContentClassifier] Failed to parse TREE_STRUCTURE JSON block")

    # Fallback: extract bold/header lines as flat children
    headers = re.findall(r'(?:^|\n)\s*(?:#{1,3}|\*\*|__)\s*(.+?)(?:\*\*|__|\n|$)', llm_text)
    if headers and primary_concept:
        return {
            "root":     primary_concept,
            "children": [{"label": h.strip(), "children": []} for h in headers[:8]],
        }

    return None


def build_tree_prompt_addon(primary_concept: str) -> str:
    """
    Returns the addendum to append to the teacher's system prompt when tree
    mode should be generated. Asks the LLM to include a structured JSON tree.
    """
    return (
        f"\n\n*** TREE STRUCTURE OUTPUT (REQUIRED when explaining concepts/theory) ***\n"
        f"After your explanation, if the content is conceptual/definitional, you MUST also output "
        f"a JSON concept tree in this EXACT format:\n"
        f"{_TREE_START}\n"
        f'{{"root": "{primary_concept}", "children": [\n'
        f'  {{"label": "Sub-concept A", "children": [{{"label": "Detail 1", "children": []}}]}},\n'
        f'  {{"label": "Sub-concept B", "children": []}}\n'
        f"]}}\n"
        f"{_TREE_END}\n\n"
        f"Use this ONLY for theory/concept explanations. "
        f"Do NOT use it when explaining formulas, steps, or worked examples."
    )


class ContentTypeClassifier:
    """
    Convenience class wrapping the module-level functions.
    Used by teacher_agent to set render_mode and extract tree_data.
    """

    def classify_and_extract(
        self, response: str, primary_concept: str = ""
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Returns (render_mode, tree_data).
        tree_data is non-None only when render_mode == "tree".
        """
        mode, confidence = classify_content(response)
        logger.debug(f"[ContentClassifier] mode={mode} confidence={confidence}")

        tree_data = None
        if mode == "tree":
            tree_data = extract_tree_structure(response, primary_concept)
            if not tree_data:
                # If we can't extract a tree, fall back to default
                mode = "default"

        return mode, tree_data
