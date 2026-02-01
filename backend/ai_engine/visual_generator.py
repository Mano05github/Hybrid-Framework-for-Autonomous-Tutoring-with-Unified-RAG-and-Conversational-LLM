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
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


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
        concept_lower = concept.lower()
        
        # Route to specialized generators
        if any(term in concept_lower for term in ['binary search', 'search algorithm']):
            return self._generate_binary_search_visual(query)
        
        elif any(term in concept_lower for term in ['recursion', 'recursive']):
            return self._generate_recursion_visual(query)
        
        elif any(term in concept_lower for term in ['sort', 'bubble', 'quick', 'merge']):
            return self._generate_sorting_visual(concept_lower, query)
        
        elif any(term in concept_lower for term in ['array', 'list', 'data structure']):
            return self._generate_array_visual(query)
        
        elif any(term in concept_lower for term in ['tree', 'graph', 'node']):
            return self._generate_tree_visual(concept_lower, query)
        
        elif any(term in concept_lower for term in ['stack', 'queue', 'linked list']):
            return self._generate_linear_structure_visual(concept_lower, query)
        
        else:
            # Generic text explanation with diagrams
            return self._generate_generic_visual(concept, query)
    
    def _generate_binary_search_visual(self, query: str) -> List[CanvasCommand]:
        """Generate visual for binary search explanation"""
        commands = []
        
        # Title
        commands.append(self._create_text_command(
            "Binary Search Algorithm",
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS
        ))
        
        self._advance_line(1.5)
        
        # Draw sorted array
        array_values = [2, 5, 8, 12, 16, 23, 38, 45, 56, 67, 78]
        commands.extend(self._draw_array(array_values, label="Sorted Array"))
        
        self._advance_line(2)
        
        # Explain with pointers
        commands.append(self._create_text_command(
            "Target: 23",
            color='#ffaa00',
            pause_after=self.PAUSE_AFTER_SENTENCE
        ))
        
        self._advance_line()
        
        # Draw pointers
        commands.extend([
            self._create_diagram_command('arrow', 
                {'start': (50, self.y_position), 'end': (100, self.y_position)},
                label='low',
                color='#00ff88'
            ),
            self._create_diagram_command('arrow',
                {'start': (550, self.y_position), 'end': (500, self.y_position)},
                label='high',
                color='#ff4444'
            ),
            self._create_diagram_command('arrow',
                {'start': (300, self.y_position - 30), 'end': (300, self.y_position - 10)},
                label='mid',
                color='#ffaa00',
                pause_after=self.PAUSE_BETWEEN_CONCEPTS
            )
        ])
        
        self._advance_line(2)
        
        # Key insight
        commands.append(self._create_text_command(
            "💡 Divides search space in half each step",
            font='Indie Flower',
            color='#00ff88',
            pause_after=self.PAUSE_BETWEEN_SECTIONS
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
            pause_after=self.PAUSE_BETWEEN_CONCEPTS
        ))
        
        self._advance_line(1.5)
        
        # Draw recursion tree (factorial example)
        commands.extend(self._draw_recursion_tree(
            "factorial(4)",
            depth=4,
            pause_after=self.PAUSE_BETWEEN_SECTIONS
        ))
        
        self._advance_line(3)
        
        # Base case highlight
        commands.append(self._create_text_command(
            "⚠️ Always need a BASE CASE to stop!",
            font='Permanent Marker',
            color='#ff4444',
            font_size=28,
            pause_after=self.PAUSE_BETWEEN_SECTIONS
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
            pause_after=self.PAUSE_BETWEEN_CONCEPTS
        ))
        
        self._advance_line(1.5)
        
        # Draw sorting steps
        for idx, step in enumerate(steps):
            commands.append(self._create_text_command(
                f"Step {idx + 1}:",
                font_size=20,
                color='#ffaa00'
            ))
            self._advance_line(0.5)
            commands.extend(self._draw_array(step, highlight_sorted=idx == len(steps) - 1))
            self._advance_line(1.5)
        
        return commands
    
    def _generate_array_visual(self, query: str) -> List[CanvasCommand]:
        """Generate visual for array/list concepts"""
        commands = []
        
        commands.append(self._create_text_command(
            "Array: Contiguous Memory",
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS
        ))
        
        self._advance_line(1.5)
        
        # Draw array with indices
        commands.extend(self._draw_array([10, 20, 30, 40, 50], show_indices=True))
        
        self._advance_line(2)
        
        # Key properties
        commands.extend([
            self._create_text_command("✓ O(1) access by index", color='#00ff88'),
            self._create_text_command("✗ O(n) insertion/deletion", color='#ff4444', 
                                     pause_after=self.PAUSE_BETWEEN_SECTIONS)
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
            pause_after=self.PAUSE_BETWEEN_CONCEPTS
        ))
        
        self._advance_line(1.5)
        
        # Draw simple binary tree
        commands.extend(self._draw_binary_tree_simple(
            pause_after=self.PAUSE_BETWEEN_SECTIONS
        ))
        
        return commands
    
    def _generate_linear_structure_visual(self, concept: str, query: str) -> List[CanvasCommand]:
        """Generate visual for stack/queue/linked list"""
        commands = []
        
        if 'stack' in concept:
            title = "Stack (LIFO)"
            commands.append(self._create_text_command(title, font_size=32, color='#00d4ff'))
            self._advance_line(1.5)
            commands.extend(self._draw_stack())
        
        elif 'queue' in concept:
            title = "Queue (FIFO)"
            commands.append(self._create_text_command(title, font_size=32, color='#00d4ff'))
            self._advance_line(1.5)
            commands.extend(self._draw_queue())
        
        elif 'linked' in concept:
            title = "Linked List"
            commands.append(self._create_text_command(title, font_size=32, color='#00d4ff'))
            self._advance_line(1.5)
            commands.extend(self._draw_linked_list())
        
        return commands
    
    def _generate_generic_visual(self, concept: str, query: str) -> List[CanvasCommand]:
        """Generate generic text-based visual explanation"""
        commands = []
        
        commands.append(self._create_text_command(
            concept.title(),
            font_size=32,
            color='#00d4ff',
            pause_after=self.PAUSE_BETWEEN_CONCEPTS
        ))
        
        self._advance_line(2)
        
        commands.append(self._create_text_command(
            "Let me explain this concept...",
            font='Indie Flower',
            color='#ffaa00',
            pause_after=self.PAUSE_BETWEEN_SECTIONS
        ))
        
        return commands
    
    # ==================== Drawing Primitives ====================
    
    def _draw_array(self, values: List, label: str = "", show_indices: bool = False, 
                    highlight_sorted: bool = False) -> List[CanvasCommand]:
        """Draw an array with boxes and values"""
        commands = []
        box_width = 50
        box_height = 40
        start_x = self.x_position
        
        if label:
            commands.append(self._create_text_command(
                label,
                font_size=18,
                color='#ffaa00'
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
                color='#00d4ff' if highlight_sorted else '#ffffff'
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
                duration=self._calculate_natural_duration(str(value), self.TEXT_SPEED)
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
                    duration=self._calculate_natural_duration(f"[{idx}]", self.TEXT_SPEED)
                ))
        
        return commands
    
    def _draw_recursion_tree(self, root_label: str, depth: int, pause_after: int = 1000) -> List[CanvasCommand]:
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
                    font_size=18
                ))
                self._advance_line(0.8)
            indent += 2
        
        if commands:
            commands[-1].pause_after = pause_after
        
        return commands
    
    def _draw_binary_tree_simple(self, pause_after: int = 1000) -> List[CanvasCommand]:
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
                font_size=20
            ))
            self._advance_line(0.6)
        
        if commands:
            commands[-1].pause_after = pause_after
        
        return commands
    
    def _draw_stack(self) -> List[CanvasCommand]:
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
                color='#00d4ff'
            ))
            
            commands.append(CanvasCommand(
                action='write_text',
                content=item,
                position={'x': x + box_width // 2, 'y': y + box_height // 2},
                font='monospace',
                size=20,
                duration=self._calculate_natural_duration(item, self.TEXT_SPEED)
            ))
        
        # Top pointer
        commands.append(self._create_text_command(
            "← TOP",
            color='#ffaa00',
            pause_after=self.PAUSE_BETWEEN_SECTIONS
        ))
        
        return commands
    
    def _draw_queue(self) -> List[CanvasCommand]:
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
                color='#00d4ff'
            ))
            
            commands.append(CanvasCommand(
                action='write_text',
                content=item,
                position={'x': x + box_width // 2, 'y': self.y_position + box_height // 2},
                font='monospace',
                size=20,
                duration=self._calculate_natural_duration(item, self.TEXT_SPEED)
            ))
        
        self._advance_line(2)
        
        commands.append(self._create_text_command(
            "FRONT → ... → REAR",
            color='#ffaa00',
            pause_after=self.PAUSE_BETWEEN_SECTIONS
        ))
        
        return commands
    
    def _draw_linked_list(self) -> List[CanvasCommand]:
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
                color='#00d4ff'
            ))
            
            # Value
            commands.append(CanvasCommand(
                action='write_text',
                content=value,
                position={'x': x + node_width // 2, 'y': self.y_position + 20},
                font='monospace',
                size=18,
                duration=self._calculate_natural_duration(value, self.TEXT_SPEED)
            ))
            
            # Arrow to next (except last)
            if idx < len(nodes) - 1:
                commands.append(self._create_diagram_command(
                    'arrow',
                    {
                        'start': (x + node_width, self.y_position + 20),
                        'end': (x + node_width + arrow_width, self.y_position + 20)
                    },
                    color='#ffaa00'
                ))
        
        return commands
    
    # ==================== Helper Methods ====================
    
    def _create_text_command(self, text: str, font_size: int = 24, color: str = '#ffffff',
                            font: str = 'Caveat', pause_after: Optional[int] = None) -> CanvasCommand:
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
            pause_after=pause_after if pause_after is not None else self.PAUSE_AFTER_SENTENCE
        )
        
        self._advance_line()
        return cmd
    
    def _create_diagram_command(self, diagram_type: str, coordinates: Dict, 
                               label: str = "", color: str = '#ffffff',
                               pause_after: Optional[int] = None) -> CanvasCommand:
        """Create a diagram element command"""
        duration = self._calculate_natural_duration("", self.DIAGRAM_ELEMENT_SPEED)
        
        return CanvasCommand(
            action='draw_diagram',
            content=f"{diagram_type}:{label}",
            position=coordinates,
            style='diagram',
            animate='pen_trail',
            duration=duration,
            color=color,
            pause_after=pause_after if pause_after is not None else self.PAUSE_AFTER_SENTENCE
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


def should_generate_visual(query: str, response: str) -> bool:
    """
    Determine if a visual explanation would enhance learning.
    
    Returns True for:
    - Algorithm explanations
    - Data structure concepts
    - Step-by-step processes
    - Mathematical concepts
    
    Returns False for:
    - Simple greetings
    - Definitions without visual components
    - Abstract conceptual discussions
    """
    visual_keywords = [
        'algorithm', 'search', 'sort', 'tree', 'graph', 'array', 'list',
        'stack', 'queue', 'recursion', 'iteration', 'loop', 'pointer',
        'linked', 'node', 'binary', 'traverse', 'insert', 'delete',
        'complexity', 'step', 'process', 'visualiz', 'diagram', 'example'
    ]
    
    query_lower = query.lower()
    response_lower = response.lower()
    
    # Check if query or response contains visual keywords
    has_visual_intent = any(keyword in query_lower or keyword in response_lower 
                            for keyword in visual_keywords)
    
    # Exclude simple greetings/social queries
    greeting_keywords = ['hello', 'hi', 'hey', 'thanks', 'thank you', 'bye']
    is_greeting = any(keyword in query_lower for keyword in greeting_keywords)
    
    return has_visual_intent and not is_greeting and len(query) > 10
