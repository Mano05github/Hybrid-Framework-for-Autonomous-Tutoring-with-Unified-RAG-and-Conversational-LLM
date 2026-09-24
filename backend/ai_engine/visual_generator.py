"""
Visual Explanation Generator
Converts educational concepts into natural, human-like canvas drawing commands
synchronized with voice narration.

Research-backed timing parameters:
- Text: 50-60ms per character
- Equations: 120ms per symbol  
- Diagrams: 250ms per element
- Natural pauses: 500ms (after visual), 1000ms (between concepts)
"""

import random
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CanvasCommand:
    """Single drawing command for canvas rendering"""
    action: str  # 'write_text', 'write_equation', 'draw_diagram', 'highlight', 'draw_array', 'draw_tree'
    content: str  # Text content or diagram specification
    position: Dict[str, float]  # {'x': float, 'y': float}
    style: str = 'handwriting'  # 'handwriting', 'emphasis', 'code'
    animate: str = 'pen_trail'  # 'pen_trail', 'fade_in', 'stroke'
    duration: int = 0  # Milliseconds (auto-calculated if 0)
    font: str = 'Caveat'  # 'Caveat', 'Indie Flower', 'Permanent Marker', 'monospace'
    color: str = '#ffffff'  # Default white
    size: int = 24  # Font size in pixels
    pause_after: int = 500  # Pause after this element (ms)
    visual_stage: Optional[str] = None
    concept_tag: Optional[str] = None
    misconception_target: Optional[str] = None
    attention_anchor: Optional[str] = None
    emotion: Optional[str] = None
    focus_region: Optional[str] = None
    points: Optional[List[List[float]]] = None  # [[x,y], [x,y]] for vector paths
    speech_sync_offset: Optional[int] = None
    highlight_priority: Optional[str] = None  # 'high' | 'medium' | 'low'


class VisualExplanationGenerator:
    """
    Generates natural canvas drawing commands for educational concepts.
    
    Implements research-backed timing and naturalness strategies:
    - Speed variation (±10% per stroke)
    - Micro-pauses (8% probability, 80ms duration)
    - Natural hesitations before complex symbols
    """
    
    # Timing parameters (milliseconds)
    TEXT_SPEED = 55  # ms per character (base)
    EQUATION_SPEED = 120  # ms per symbol
    DIAGRAM_ELEMENT_SPEED = 250  # ms per element
    
    # Pause durations
    PAUSE_AFTER_SENTENCE = 500
    PAUSE_BETWEEN_CONCEPTS = 1000
    PAUSE_BETWEEN_SECTIONS = 2500
    
    # Natural variation ranges
    SPEED_VARIATION = 0.10  # ±10%
    MICRO_PAUSE_PROBABILITY = 0.08  # 8% chance
    MICRO_PAUSE_DURATION = 80  # ms
    
    def __init__(self):
        self.y_position = 50  # Starting Y position
        self.x_position = 50  # Starting X position
        self.line_height = 40  # Space between lines
        
    def _generate_hand_drawn_line(self, x1, y1, x2, y2, segments=10) -> List[List[float]]:
        """Generate a slightly wiggly line to simulate hand-drawing"""
        points = []
        for i in range(segments + 1):
            t = i / segments
            # Linear interpolation
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            
            # Add noise (except start/end)
            if 0 < i < segments:
                x += random.uniform(-2, 2)
                y += random.uniform(-2, 2)
                
            points.append([int(x), int(y)])
        return points

    def _generate_hand_drawn_rect(self, x, y, width, height) -> List[List[float]]:
        """Generate path for a rectangle"""
        points = []
        # Top
        points.extend(self._generate_hand_drawn_line(x, y, x + width, y))
        # Right
        points.extend(self._generate_hand_drawn_line(x + width, y, x + width, y + height))
        # Bottom
        points.extend(self._generate_hand_drawn_line(x + width, y + height, x, y + height))
        # Left
        points.extend(self._generate_hand_drawn_line(x, y + height, x, y))
        return points

    def _generate_hand_drawn_arrow(self, x1, y1, x2, y2) -> List[List[float]]:
        """Generate path for an arrow"""
        points = self._generate_hand_drawn_line(x1, y1, x2, y2)
        
        # Arrowhead
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        head_len = 15
        
        # Left wing
        points.extend(self._generate_hand_drawn_line(
            x2, y2,
            x2 - head_len * math.cos(angle - math.pi/6),
            y2 - head_len * math.sin(angle - math.pi/6),
            segments=3
        ))
        
        # Back to tip
        points.append([x2, y2])
        
        # Right wing
        points.extend(self._generate_hand_drawn_line(
            x2, y2,
            x2 - head_len * math.cos(angle + math.pi/6),
            y2 - head_len * math.sin(angle + math.pi/6),
            segments=3
        ))
        
        return points
        
    def generate_for_concept(self, concept: str, query: str, context: str = "") -> List[CanvasCommand]:
        """
        Generate canvas commands for explaining a concept visually.
        
        Args:
            concept: The main concept being taught (e.g., "binary search", "recursion")
            query: Student's original question
            context: Additional context from RAG retrieval
            
        Returns:
            List of CanvasCommand objects for sequential rendering
        """
        # Validate and refine concept if needed
        validated_concept = self._validate_and_refine_concept(concept, context)
        
        if validated_concept != concept:
            logger.info(f"Refined concept: '{concept}' -> '{validated_concept}'")
            concept = validated_concept
        
        concept_lower = concept.lower()
        
        # Route to specialized generators using improved pattern matching
        
        # Binary Search and Search Algorithms
        if self._matches_pattern(concept_lower, [
            'binary search', 'bsearch', 'bin search', 'bisect',
            'search algorithm', 'searching'
        ]):
            return self._generate_binary_search_visual(query)
        
        # Recursion
        if self._matches_pattern(concept_lower, [
            'recursion', 'recursive', 'recurs', 'call stack',
            'base case', 'recursive call'
        ]):
            return self._generate_recursion_visual(query)
        
        # Sorting Algorithms
        if self._matches_pattern(concept_lower, [
            'sort', 'bubble', 'quick', 'merge', 'insertion',
            'selection', 'heap sort', 'sorting algorithm'
        ]):
            return self._generate_sorting_visual(concept_lower, query)
        
        # Arrays and Lists
        if self._matches_pattern(concept_lower, [
            'array', 'list', 'vector', 'arraylist',
            'index', 'element', 'subarray'
        ]):
            return self._generate_array_visual(query)
        
        # Trees and Graphs
        if self._matches_pattern(concept_lower, [
            'tree', 'graph', 'node', 'bst', 'binary tree',
            'avl', 'red-black', 'trie', 'traversal',
            'vertex', 'edge', 'path'
        ]):
            return self._generate_tree_visual(concept_lower, query)
        
        # Linear Data Structures
        if self._matches_pattern(concept_lower, [
            'stack', 'queue', 'linked list', 'deque',
            'push', 'pop', 'enqueue', 'dequeue', 'fifo', 'lifo'
        ]):
            return self._generate_linear_structure_visual(concept_lower, query)
        
        # Generic fallback
        return self._generate_generic_visual(concept, query)
    
    def _matches_pattern(self, text: str, patterns: list) -> bool:
        """
        Check if text matches any of the given patterns.
        Uses word boundaries and flexible matching.
        
        Args:
            text: Text to search in (lowercased)
            patterns: List of pattern strings to match
            
        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            # Check exact substring match
            if pattern in text:
                return True
            
            # Check word boundary match (for whole words)
            if re.search(r'\b' + re.escape(pattern) + r'\b', text):
                return True
            
            # Check if all words in pattern appear in text (for multi-word patterns)
            pattern_words = pattern.split()
            if len(pattern_words) > 1:
                if all(word in text for word in pattern_words):
                    return True
        
        return False
    
    def _validate_and_refine_concept(self, concept: str, context: str) -> str:
        """
        Validate concept and refine from context if too generic.
        
        Args:
            concept: Initial concept string
            context: LLM response context
            
        Returns:
            Refined concept string
        """
        if not concept or len(concept.strip()) == 0:
            return self._extract_concept_from_context(context) or "Concept"
        
        # Check if concept is too generic
        generic_indicators = [
            'explain', 'show', 'tell', 'what', 'how', 'why',
            'confused', 'understand', 'help', 'please'
        ]
        
        concept_lower = concept.lower()
        if any(indicator in concept_lower for indicator in generic_indicators):
            # Try to extract from context
            extracted = self._extract_concept_from_context(context)
            if extracted:
                return extracted
        
        return concept
    
    def _extract_concept_from_context(self, context: str) -> Optional[str]:
        """
        Extract concept from LLM response context.
        
        Args:
            context: LLM teaching response
            
        Returns:
            Extracted concept or None
        """
        if not context:
            return None
        
        # Known algorithm/DS concepts to look for
        known_concepts = [
            'binary search', 'linear search', 'depth-first search', 'breadth-first search',
            'merge sort', 'quick sort', 'bubble sort', 'insertion sort', 'heap sort',
            'binary tree', 'binary search tree', 'balanced tree', 'avl tree',
            'linked list', 'doubly linked list', 'stack', 'queue', 'priority queue',
            'hash table', 'hash map', 'graph', 'directed graph',
            'dynamic programming', 'greedy algorithm', 'recursion', 'backtracking'
        ]
        
        # Sort by length (prefer longer matches)
        known_concepts.sort(key=len, reverse=True)
        
        # Pattern 1: Extract from "Definition:" section
        definition_match = re.search(
            r'Definition[:\-]?\s*([^\n]{10,100})',
            context,
            re.IGNORECASE
        )
        
        if definition_match:
            definition = definition_match.group(1).lower()
            for concept in known_concepts:
                if concept in definition:
                    return self._capitalize_concept(concept)
        
        # Pattern 2: Look in first few sentences
        sentences = context.split('\n')[:5]
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for concept in known_concepts:
                if concept in sentence_lower:
                    return self._capitalize_concept(concept)
        
        return None
    
    def _capitalize_concept(self, concept: str) -> str:
        """Properly capitalize concept names"""
        special_cases = {
            'avl tree': 'AVL Tree',
            'dfs': 'Depth-First Search',
            'bfs': 'Breadth-First Search',
            'bst': 'Binary Search Tree'
        }
        
        if concept.lower() in special_cases:
            return special_cases[concept.lower()]
        
        return ' '.join(word.capitalize() for word in concept.split())
    
    def _generate_binary_search_visual(self, query: str) -> List[CanvasCommand]:
        """Generate visual for binary search explanation"""
        commands = []
        
        # Title
        commands.append(self._create_text_command(
            "Binary Search Algorithm",
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS,
            visual_stage='intro'
        ))
        
        self._advance_line(1.5)
        
        # Draw sorted array
        array_values = [2, 5, 8, 12, 16, 23, 38, 45, 56, 67, 78]
        commands.extend(self._draw_array(array_values, label="Sorted Array", visual_stage='example'))
        
        self._advance_line(2)
        
        # Explain with pointers
        commands.append(self._create_text_command(
            "Target: 23",
            color='#ffaa00',
            pause_after=self.PAUSE_AFTER_SENTENCE,
            visual_stage='example'
        ))
        
        self._advance_line()
        
        # Draw pointers
        commands.extend([
            self._create_diagram_command('arrow', 
                {'start': (50, self.y_position), 'end': (100, self.y_position)},
                label='low',
                color='#00ff88',
                visual_stage='example'
            ),
            self._create_diagram_command('arrow',
                {'start': (550, self.y_position), 'end': (500, self.y_position)},
                label='high',
                color='#ff4444',
                visual_stage='example'
            ),
            self._create_diagram_command('arrow',
                {'start': (300, self.y_position - 30), 'end': (300, self.y_position - 10)},
                label='mid',
                color='#ffaa00',
                pause_after=self.PAUSE_BETWEEN_CONCEPTS,
                visual_stage='example'
            )
        ])
        
        self._advance_line(2)
        
        # Key insight
        commands.append(self._create_text_command(
            "💡 Divides search space in half each step",
            font='Indie Flower',
            color='#00ff88',
            pause_after=self.PAUSE_BETWEEN_SECTIONS,
            visual_stage='definition'
        ))
        
        return commands
    
    def _generate_recursion_visual(self, query: str) -> List[CanvasCommand]:
        """Generate visual for recursion explanation"""
        commands = []
        
        # Title
        commands.append(self._create_text_command(
            "Recursion: Function Calls Itself",
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS,
            visual_stage='intro'
        ))
        
        self._advance_line(1.5)
        
        # Draw recursion tree (factorial example)
        commands.extend(self._draw_recursion_tree(
            "factorial(4)",
            depth=4,
            pause_after=self.PAUSE_BETWEEN_SECTIONS,
            visual_stage='example'
        ))
        
        self._advance_line(3)
        
        # Base case highlight
        commands.append(self._create_text_command(
            "⚠️ Always need a BASE CASE to stop!",
            font='Permanent Marker',
            color='#ff4444',
            font_size=28,
            pause_after=self.PAUSE_BETWEEN_SECTIONS,
            visual_stage='pitfalls'
        ))
        
        return commands
    
    def _generate_sorting_visual(self, concept: str, query: str) -> List[CanvasCommand]:
        """Generate visual for sorting algorithms"""
        commands = []
        
        # Detect which sorting algorithm
        if 'bubble' in concept:
            title = "Bubble Sort"
            steps = [[5, 2, 8, 1, 9], [2, 5, 1, 8, 9], [2, 1, 5, 8, 9], [1, 2, 5, 8, 9]]
        elif 'quick' in concept:
            title = "Quick Sort"
            steps = [[5, 2, 8, 1, 9], [2, 1, 5, 8, 9], [1, 2, 5, 8, 9]]
        elif 'merge' in concept:
            title = "Merge Sort"
            steps = [[5, 2, 8, 1], [2, 5, 1, 8], [1, 2, 5, 8]]
        else:
            title = "Sorting Algorithm"
            steps = [[5, 2, 8, 1, 9], [2, 5, 1, 8, 9], [1, 2, 5, 8, 9]]
        
        # Title
        commands.append(self._create_text_command(
            title,
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS,
            visual_stage='intro'
        ))
        
        self._advance_line(1.5)
        
        # Draw sorting steps
        for idx, step in enumerate(steps):
            commands.append(self._create_text_command(
                f"Step {idx + 1}:",
                font_size=20,
                color='#ffaa00',
                visual_stage='example'
            ))
            self._advance_line(0.5)
            commands.extend(self._draw_array(step, highlight_sorted=idx == len(steps) - 1, visual_stage='example'))
            self._advance_line(1.5)
        
        return commands
    
    def _generate_array_visual(self, query: str) -> List[CanvasCommand]:
        """Generate visual for array/list concepts"""
        commands = []
        
        commands.append(self._create_text_command(
            "Array: Contiguous Memory",
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS,
            visual_stage='intro'
        ))
        
        self._advance_line(1.5)
        
        # Draw array with indices
        commands.extend(self._draw_array([10, 20, 30, 40, 50], show_indices=True, visual_stage='example'))
        
        self._advance_line(2)
        
        # Key properties
        commands.extend([
            self._create_text_command("✓ O(1) access by index", color='#00ff88', visual_stage='definition'),
            self._create_text_command("✗ O(n) insertion/deletion", color='#ff4444', 
                                     pause_after=self.PAUSE_BETWEEN_SECTIONS,
                                     visual_stage='pitfalls')
        ])
        
        return commands
    
    def _generate_tree_visual(self, concept: str, query: str) -> List[CanvasCommand]:
        """Generate visual for tree/graph concepts"""
        commands = []
        
        if 'binary' in concept:
            title = "Binary Tree"
        elif 'bst' in concept or 'search' in concept:
            title = "Binary Search Tree"
        else:
            title = "Tree Structure"
        
        commands.append(self._create_text_command(
            title,
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS,
            visual_stage='intro'
        ))
        
        self._advance_line(1.5)
        
        # Draw simple binary tree
        commands.extend(self._draw_binary_tree_simple(
            pause_after=self.PAUSE_BETWEEN_SECTIONS,
            visual_stage='example'
        ))
        
        return commands
    
    def _generate_linear_structure_visual(self, concept: str, query: str) -> List[CanvasCommand]:
        """Generate visual for stack/queue/linked list"""
        commands = []
        
        if 'stack' in concept:
            title = "Stack (LIFO)"
            commands.append(self._create_text_command(title, font_size=32, color='#00d4ff', visual_stage='intro'))
            self._advance_line(1.5)
            commands.extend(self._draw_stack(visual_stage='example'))
        
        elif 'queue' in concept:
            title = "Queue (FIFO)"
            commands.append(self._create_text_command(title, font_size=32, color='#00d4ff', visual_stage='intro'))
            self._advance_line(1.5)
            commands.extend(self._draw_queue(visual_stage='example'))
        
        elif 'linked' in concept:
            title = "Linked List"
            commands.append(self._create_text_command(title, font_size=32, color='#00d4ff', visual_stage='intro'))
            self._advance_line(1.5)
            commands.extend(self._draw_linked_list(visual_stage='example'))
        
        return commands
    
    def _generate_generic_visual(self, concept: str, query: str) -> List[CanvasCommand]:
        """Generate generic text-based visual explanation"""
        commands = []
        
        commands.append(self._create_text_command(
            concept.title(),
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS,
            visual_stage='intro'
        ))
        
        self._advance_line(2)
        
        commands.append(self._create_text_command(
            "Let me explain this concept...",
            font='Indie Flower',
            color='#ffaa00',
            pause_after=self.PAUSE_BETWEEN_SECTIONS,
            visual_stage='definition'
        ))
        
        return commands
    
    # ==================== Drawing Primitives ====================
    
    def _draw_array(self, values: List, label: str = "", show_indices: bool = False, 
                    highlight_sorted: bool = False, visual_stage: str = 'example') -> List[CanvasCommand]:
        """Draw an array with boxes and values"""
        commands = []
        box_width = 50
        box_height = 40
        start_x = self.x_position
        
        if label:
            commands.append(self._create_text_command(
                label,
                font_size=18,
                color='#ffaa00',
                visual_stage=visual_stage
            ))
            self._advance_line(0.5)
        
        # Draw boxes and values
        for idx, value in enumerate(values):
            x = start_x + (idx * box_width)
            y = self.y_position
            
            # Box
            commands.append(self._create_diagram_command(
                'rectangle',
                {'x': x, 'y': y, 'width': box_width, 'height': box_height},
                color='#00d4ff' if highlight_sorted else '#ffffff',
                visual_stage=visual_stage
            ))
            
            # NEW: Vector Path Command
            commands.append(CanvasCommand(
                action='draw_path',
                content='box_outline',
                position={'x': x, 'y': y},
                points=self._generate_hand_drawn_rect(x, y, box_width, box_height),
                color='#00d4ff' if highlight_sorted else '#ffffff',
                duration=300,
                visual_stage=visual_stage
            ))
            
            # Value inside box
            commands.append(CanvasCommand(
                action='write_text',
                content=str(value),
                position={'x': x + box_width // 2, 'y': y + box_height // 2},
                style='code',
                font='monospace',
                size=20,
                color='#ffffff',
                duration=self._calculate_natural_duration(str(value), self.TEXT_SPEED),
                visual_stage=visual_stage
            ))
            
            # Index below box
            if show_indices:
                commands.append(CanvasCommand(
                    action='write_text',
                    content=f"[{idx}]",
                    position={'x': x + box_width // 2, 'y': y + box_height + 20},
                    font='monospace',
                    size=14,
                    color='#888888',
                    duration=self._calculate_natural_duration(f"[{idx}]", self.TEXT_SPEED),
                    visual_stage=visual_stage
                ))
        
        return commands
    
    def _draw_recursion_tree(self, root_label: str, depth: int, pause_after: int = 1000, 
                             visual_stage: str = 'example') -> List[CanvasCommand]:
        """Draw a recursion tree"""
        commands = []
        
        # Simplified tree visualization
        levels = [
            [root_label],
            ["factorial(3)", "return"],
            ["factorial(2)", "return"],
            ["factorial(1)", "return"],
            ["BASE CASE: return 1"]
        ]
        
        indent = 0
        for level_idx, level in enumerate(levels[:depth + 1]):
            for item in level:
                commands.append(self._create_text_command(
                    "  " * indent + item,
                    font='monospace',
                    color='#00ff88' if 'BASE' in item else '#ffffff',
                    font_size=18,
                    visual_stage=visual_stage
                ))
                self._advance_line(0.8)
            indent += 2
        
        if commands:
            commands[-1].pause_after = pause_after
        
        return commands
    
    def _draw_binary_tree_simple(self, pause_after: int = 1000, visual_stage: str = 'example') -> List[CanvasCommand]:
        """Draw a simple binary tree structure"""
        commands = []
        
        # ASCII-style tree
        tree_lines = [
            "       10",
            "      /  \\",
            "     5    15",
            "    / \\   / \\",
            "   3   7 12  20"
        ]
        
        for line in tree_lines:
            commands.append(self._create_text_command(
                line,
                font='monospace',
                color='#00ff88',
                font_size=20,
                visual_stage=visual_stage
            ))
            self._advance_line(0.6)
        
        if commands:
            commands[-1].pause_after = pause_after
        
        return commands
    
    def _draw_stack(self, visual_stage: str = 'example') -> List[CanvasCommand]:
        """Draw a stack visualization"""
        commands = []
        
        stack_items = ["30", "20", "10"]
        box_width = 100
        box_height = 40
        x = self.x_position + 150
        
        for idx, item in enumerate(stack_items):
            y = self.y_position + (idx * box_height)
            
            commands.append(self._create_diagram_command(
                'rectangle',
                {'x': x, 'y': y, 'width': box_width, 'height': box_height},
                color='#00d4ff',
                visual_stage=visual_stage
            ))
            
            commands.append(CanvasCommand(
                action='write_text',
                content=item,
                position={'x': x + box_width // 2, 'y': y + box_height // 2},
                font='monospace',
                size=20,
                duration=self._calculate_natural_duration(item, self.TEXT_SPEED),
                visual_stage=visual_stage
            ))
        
        # Top pointer
        commands.append(self._create_text_command(
            "← TOP",
            color='#ffaa00',
            pause_after=self.PAUSE_BETWEEN_SECTIONS,
            visual_stage=visual_stage
        ))
        
        return commands
    
    def _draw_queue(self, visual_stage: str = 'example') -> List[CanvasCommand]:
        """Draw a queue visualization"""
        commands = []
        
        queue_items = ["10", "20", "30", "40"]
        box_width = 60
        box_height = 50
        start_x = self.x_position
        
        for idx, item in enumerate(queue_items):
            x = start_x + (idx * box_width)
            
            commands.append(self._create_diagram_command(
                'rectangle',
                {'x': x, 'y': self.y_position, 'width': box_width, 'height': box_height},
                color='#00d4ff',
                visual_stage=visual_stage
            ))
            
            commands.append(CanvasCommand(
                action='write_text',
                content=item,
                position={'x': x + box_width // 2, 'y': self.y_position + box_height // 2},
                font='monospace',
                size=20,
                duration=self._calculate_natural_duration(item, self.TEXT_SPEED),
                visual_stage=visual_stage
            ))
        
        self._advance_line(2)
        
        commands.append(self._create_text_command(
            "FRONT → ... → REAR",
            color='#ffaa00',
            pause_after=self.PAUSE_BETWEEN_SECTIONS,
            visual_stage=visual_stage
        ))
        
        return commands
    
    def _draw_linked_list(self, visual_stage: str = 'example') -> List[CanvasCommand]:
        """Draw a linked list visualization"""
        commands = []
        
        nodes = ["10", "20", "30", "NULL"]
        node_width = 60
        arrow_width = 40
        start_x = self.x_position
        
        for idx, value in enumerate(nodes):
            x = start_x + (idx * (node_width + arrow_width))
            
            # Node box
            commands.append(self._create_diagram_command(
                'rectangle',
                {'x': x, 'y': self.y_position, 'width': node_width, 'height': 40},
                color='#00d4ff',
                visual_stage=visual_stage
            ))
            
            # Value
            commands.append(CanvasCommand(
                action='write_text',
                content=value,
                position={'x': x + node_width // 2, 'y': self.y_position + 20},
                font='monospace',
                size=18,
                duration=self._calculate_natural_duration(value, self.TEXT_SPEED),
                visual_stage=visual_stage
            ))
            
            # Arrow to next (except last)
            if idx < len(nodes) - 1:
                commands.append(self._create_diagram_command(
                    'arrow',
                    {
                        'start': (x + node_width, self.y_position + 20),
                        'end': (x + node_width + arrow_width, self.y_position + 20)
                    },
                    color='#ffaa00',
                    visual_stage=visual_stage
                ))
        
        return commands
    
    # ==================== Helper Methods ====================
    
    def _create_text_command(self, text: str, font_size: int = 24, color: str = '#ffffff',
                            font: str = 'Caveat', pause_after: Optional[int] = None,
                            visual_stage: Optional[str] = None) -> CanvasCommand:
        """Create a text rendering command with natural timing"""
        duration = self._calculate_natural_duration(text, self.TEXT_SPEED)
        
        cmd = CanvasCommand(
            action='write_text',
            content=text,
            position={'x': self.x_position, 'y': self.y_position},
            style='handwriting',
            animate='pen_trail',
            duration=duration,
            font=font,
            color=color,
            size=font_size,
            pause_after=pause_after if pause_after is not None else self.PAUSE_AFTER_SENTENCE,
            visual_stage=visual_stage
        )
        
        self._advance_line()
        return cmd
    
    def _create_diagram_command(self, diagram_type: str, coordinates: Dict, 
                               label: str = "", color: str = '#ffffff',
                               pause_after: Optional[int] = None,
                               visual_stage: Optional[str] = None) -> CanvasCommand:
        """Create a diagram element command"""
        duration = self._calculate_natural_duration("", self.DIAGRAM_ELEMENT_SPEED)
        
        # Add vector path if available
        points = None
        if diagram_type == 'rectangle':
            points = self._generate_hand_drawn_rect(
                coordinates['x'], coordinates['y'], 
                coordinates['width'], coordinates['height']
            )
        elif diagram_type == 'arrow':
            points = self._generate_hand_drawn_arrow(
                coordinates['start'][0], coordinates['start'][1],
                coordinates['end'][0], coordinates['end'][1]
            )
            
        return CanvasCommand(
            action='draw_path' if points else 'draw_diagram',
            content=f"{diagram_type}:{label}",
            position=coordinates,
            points=points,
            style='diagram',
            animate='pen_trail',
            duration=duration,
            color=color,
            pause_after=pause_after if pause_after is not None else self.PAUSE_AFTER_SENTENCE,
            visual_stage=visual_stage
        )
    
    def _calculate_natural_duration(self, text: str, base_speed: int) -> int:
        """
        Calculate natural duration with human-like variations.
        
        Implements:
        - ±10% speed variation
        - 8% probability of micro-pauses (80ms)
        - Complex symbol slowdown
        """
        # Base duration
        char_count = len(text) if text else 1
        base_duration = char_count * base_speed
        
        # Apply speed variation (±10%)
        variation_factor = 1.0 + random.uniform(-self.SPEED_VARIATION, self.SPEED_VARIATION)
        duration = int(base_duration * variation_factor)
        
        # Add micro-pauses randomly
        if random.random() < self.MICRO_PAUSE_PROBABILITY:
            duration += self.MICRO_PAUSE_DURATION
        
        # Slowdown for complex symbols
        complex_symbols = sum(1 for c in text if c in '()[]{}=+-*/\\<>≤≥∑∏∫√')
        if complex_symbols > 0:
            duration += complex_symbols * 100  # 100ms per complex symbol
        
        return max(duration, 50)  # Minimum 50ms
    
    def _advance_line(self, multiplier: float = 1.0):
        """Move to next line position"""
        self.y_position += int(self.line_height * multiplier)
    
    def reset_position(self):
        """Reset drawing position to top-left"""
        self.y_position = 50
        self.x_position = 50


def generate_from_llm_script(beats: list, generator: 'VisualExplanationGenerator' = None) -> list:
    """
    Convert LLM-generated beats (from parse_canvas_script_from_llm) into
    VisualExplanationGenerator-compatible CanvasCommand dicts.

    Each beat already carries draw/color/label/position_hint fields.
    This function maps them to the action/content/position/color dict format
    that the frontend executeDrawCommand() understands.

    These commands are sent as canvas_commands for the legacy fallback path.
    However, with the new KA beat system, they are redundant — the frontend
    reads draw fields directly from teaching_script phase objects.
    This function is kept for compatibility and is a no-op passthrough.
    """
    commands = []
    for idx, beat in enumerate(beats or []):
        draw_type = beat.get('draw', 'none')
        if draw_type == 'none':
            continue
        # Passthrough the beat as-is so the legacy stageMap still works
        commands.append({
            'action': draw_type,
            'content': beat.get('label', beat.get('title', '')),
            'color': beat.get('color', '#00d4ff'),
            'visual_stage': beat.get('visual_stage', f'beat_{idx}'),
            'position': {'x': 600, 'y': 100 + idx * 80},
            'size': beat.get('size', 24),
            'duration': 900,
            'pause_after': beat.get('pause_after_ms', 600),
        })
    return commands


def should_generate_visual(query: str, response: str, llm_beats: list = None) -> bool:
    """
    Determine if a visual explanation would enhance learning.

    Always True when the LLM has generated beats (Khan Academy style).
    Otherwise, returns True for algorithm/data-structure queries.
    """
    # If the LLM produced canvas beats, always show the canvas
    if llm_beats and len(llm_beats) > 0:
        return True

    visual_keywords = [
        'algorithm', 'search', 'sort', 'tree', 'graph', 'array', 'list',
        'stack', 'queue', 'recursion', 'iteration', 'loop', 'pointer',
        'linked', 'node', 'binary', 'traverse', 'insert', 'delete',
        'complexity', 'step', 'process', 'visualiz', 'diagram', 'example',
        'cell', 'organ', 'anatomy', 'photosynthesis', 'dna', 'molecule',
        'formula', 'equation', 'integral', 'derivative', 'proof',
    ]

    query_lower = query.lower()
    response_lower = response.lower()

    has_visual_intent = any(keyword in query_lower or keyword in response_lower
                            for keyword in visual_keywords)

    greeting_keywords = ['hello', 'hi', 'hey', 'thanks', 'thank you', 'bye']
    is_greeting = any(keyword in query_lower for keyword in greeting_keywords)

    return has_visual_intent and not is_greeting and len(query) > 10
