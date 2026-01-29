"""
Gap 5: Canvas Validation System
Smart snapshot capture and diagram validation using Gemini Vision API
"""
import base64
import json
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from llm_engine.factory import LLMFactory


@dataclass
class CanvasSnapshot:
    """Canvas image snapshot with metadata"""
    snapshot_id: str
    timestamp: datetime
    image_data: bytes  # PNG/JPEG bytes
    trigger_reason: str  # 'pause', 'milestone', 'explicit_request'
    topic: str
    activity_type: str


@dataclass
class ValidationResult:
    """Diagram validation result from Vision API"""
    is_valid: bool
    has_errors: bool
    error_list: List[str]
    suggestions: List[str]
    confidence: float
    analysis_time_ms: float


class CanvasMonitor:
    """
    Smart canvas snapshot system for Gap 5
    
    Triggers canvas capture on:
    1. Student pauses drawing (5+ seconds)
    2. Logical unit completion (detected via canvas events)
    3. Explicit validation request ("Check my drawing")
    """
    
    def __init__(self, pause_threshold: float = 5.0):
        self.pause_threshold = pause_threshold
        self.last_stroke_time: Optional[datetime] = None
        self.logical_units: List[Dict] = []
        self.analyzed_states: set = set()  # Avoid re-analyzing same state
        
    def on_canvas_event(self, event: Dict) -> Optional[str]:
        """
        Process canvas event and determine if snapshot should be triggered
        
        Args:
            event: Canvas event with type, data, timestamp
            
        Returns:
            Trigger reason if snapshot should be captured, None otherwise
        """
        event_type = event.get('type', '')
        timestamp = event.get('timestamp', datetime.now())  # Use event timestamp if provided
        
        if event_type == 'stroke_start':
            self.last_stroke_time = timestamp
            return None
        
        elif event_type == 'stroke_end':
            # Don't update last_stroke_time here - we need it for pause calculation
            # The pause detection below will compare current timestamp to last_stroke_time
            pass
            
            # Check if this completes a logical unit
            if self._is_logical_unit_complete(event):
                return 'logical_unit_complete'
        
        elif event_type == 'validation_request':
            # Explicit request from student
            return 'explicit_request'
        
        # Check for pause
        if self.last_stroke_time:
            pause_duration = (timestamp - self.last_stroke_time).total_seconds()
            if pause_duration >= self.pause_threshold:
                # Check if we already analyzed this state
                canvas_hash = event.get('canvas_hash', '')
                if canvas_hash:
                    if canvas_hash not in self.analyzed_states:
                        self.analyzed_states.add(canvas_hash)
                        return 'pause_detected'
                else:
                    # No hash provided - allow pause detection anyway (useful for testing)
                    return 'pause_detected'
        
        return None
    
    def _is_logical_unit_complete(self, event: Dict) -> bool:
        """
        Detect if a logical drawing unit is complete
        
        Heuristics:
        - Tree node + all edges drawn
        - Array visualization + indices labeled
        - Graph vertex + all connections made
        """
        canvas_data = event.get('canvas_data', {})
        
        # Simple heuristic: Check if new object has all required connections
        new_object_type = canvas_data.get('new_object_type', '')
        
        if new_object_type == 'tree_node':
            # Tree node should have parent edge (unless root) and child edges (if not leaf)
            has_edges = canvas_data.get('has_edges', False)
            return has_edges
        
        elif new_object_type == 'array_cell':
            # Array cell should have value and index
            has_value = canvas_data.get('has_value', False)
            has_index = canvas_data.get('has_index', False)
            return has_value and has_index
        
        elif new_object_type == 'graph_vertex':
            # Graph vertex complete when edges are drawn
            has_edges = canvas_data.get('has_edges', False)
            return has_edges
        
        return False
    
    def reset_analysis_cache(self):
        """Clear analyzed states cache"""
        self.analyzed_states.clear()


class DiagramValidator:
    """
    Validates canvas diagrams using Gemini Vision API
    
    Checks for:
    - Correct data structure representation
    - Proper connections and relationships
    - Common errors (e.g., wrong BST child placement)
    """
    
    def __init__(self):
        self.llm_factory = LLMFactory()
        
    async def validate_canvas(
        self,
        snapshot: CanvasSnapshot,
        expected_structure: str,
        validation_criteria: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Validate canvas diagram against expected structure
        
        Args:
            snapshot: Canvas snapshot with image data
            expected_structure: Type of structure (e.g., 'binary_search_tree', 'linked_list')
            validation_criteria: Optional specific criteria to check
            
        Returns:
            ValidationResult with errors and suggestions
        """
        import time
        start_time = time.perf_counter()
        
        # Encode image to base64
        image_b64 = base64.b64encode(snapshot.image_data).decode('utf-8')
        
        # Build validation prompt
        prompt = self._build_validation_prompt(
            expected_structure=expected_structure,
            topic=snapshot.topic,
            criteria=validation_criteria
        )
        
        # Call Vision API
        try:
            # Use Gemini Flash for cost efficiency
            llm = self.llm_factory.create_llm(provider='gemini', model='gemini-1.5-flash')
            
            response = await llm.ainvoke([
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{image_b64}"
                }
            ])
            
            # Parse response
            result = self._parse_validation_response(response.content)
            
        except Exception as e:
            print(f"[DiagramValidator] Error: {e}")
            result = {
                'is_valid': False,
                'has_errors': True,
                'error_list': [f"Validation failed: {str(e)}"],
                'suggestions': ['Please try redrawing or ask for help.'],
                'confidence': 0.0
            }
        
        analysis_time = (time.perf_counter() - start_time) * 1000  # ms
        
        return ValidationResult(
            is_valid=result['is_valid'],
            has_errors=result['has_errors'],
            error_list=result['error_list'],
            suggestions=result['suggestions'],
            confidence=result['confidence'],
            analysis_time_ms=analysis_time
        )
    
    def _build_validation_prompt(
        self,
        expected_structure: str,
        topic: str,
        criteria: Optional[Dict]
    ) -> str:
        """Build prompt for vision model"""
        
        base_prompt = f"""You are analyzing a student's hand-drawn diagram of a {expected_structure}.

Current Topic: {topic}

Please validate the diagram and provide:
1. Is the structure correctly drawn? (Yes/No)
2. List any errors you see
3. Provide constructive suggestions for improvement

Expected Structure: {expected_structure}
"""
        
        if criteria:
            base_prompt += f"\\n\\nSpecific criteria to check:\\n"
            for key, value in criteria.items():
                base_prompt += f"- {key}: {value}\\n"
        
        base_prompt += """

Return your analysis in JSON format:
{
    "is_valid": true/false,
    "has_errors": true/false,
    "error_list": ["error1", "error2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence": 0.0-1.0
}
"""
        
        return base_prompt
    
    def _parse_validation_response(self, response_text: str) -> Dict:
        """Parse JSON response from vision model"""
        try:
            # Extract JSON from response (may have markdown code blocks)
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            # Validate structure
            if not all(k in result for k in ['is_valid', 'has_errors', 'error_list', 'suggestions']):
                raise ValueError("Missing required fields in response")
            
            # Ensure confidence is present
            if 'confidence' not in result:
                result['confidence'] = 0.8  # Default high confidence
            
            return result
            
        except Exception as e:
            print(f"[DiagramValidator] Failed to parse response: {e}")
            print(f"Raw response: {response_text[:200]}...")
            
            # Return default error result
            return {
                'is_valid': False,
                'has_errors': True,
                'error_list': ['Failed to analyze diagram. Please ensure drawing is clear.'],
                'suggestions': ['Try redrawing with clearer lines and labels.'],
                'confidence': 0.0
            }


class SnapshotQueue:
    """Queue for managing canvas snapshots"""
    
    def __init__(self, max_size: int = 100):
        self.queue: List[CanvasSnapshot] = []
        self.max_size = max_size
        self.processing = False
        
    def enqueue(self, snapshot: CanvasSnapshot):
        """Add snapshot to queue"""
        self.queue.append(snapshot)
        
        # Limit queue size
        if len(self.queue) > self.max_size:
            self.queue.pop(0)  # Remove oldest
    
    def dequeue(self) -> Optional[CanvasSnapshot]:
        """Get next snapshot for processing"""
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def peek(self) -> Optional[CanvasSnapshot]:
        """Look at next snapshot without removing"""
        if self.queue:
            return self.queue[0]
        return None
    
    def size(self) -> int:
        """Get queue size"""
        return len(self.queue)
    
    def clear(self):
        """Clear all snapshots"""
        self.queue.clear()


