"""
Dialogue State Tracker - Context-aware routing with conversation history
Target: Resolve references, maintain context, improve routing accuracy
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

import spacy
from spacy.tokens import Doc


@dataclass
class DialogueTurn:
    """Single conversation turn."""
    turn_id: int
    query: str
    intent: str
    response: str
    timestamp: datetime
    entities: Dict[str, List[str]] = field(default_factory=dict)
    topic: Optional[str] = None


@dataclass
class DialogueState:
    """Current dialogue state with context."""
    user_id: str
    session_id: str
    turns: List[DialogueTurn]
    current_topic: Optional[str] = None
    last_intent: Optional[str] = None
    mentioned_entities: Dict[str, str] = field(default_factory=dict)  # entity_type -> entity_value
    context_window: int = 5  # Last N turns to consider
    
    def get_recent_turns(self, n: Optional[int] = None) -> List[DialogueTurn]:
        """Get N most recent turns."""
        n = n or self.context_window
        return list(self.turns[-n:]) if self.turns else []
    
    def to_dict(self) -> Dict:
        """Serialize state."""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'turn_count': len(self.turns),
            'current_topic': self.current_topic,
            'last_intent': self.last_intent,
            'entities': self.mentioned_entities
        }


class DialogueStateTracker:
    """
    Tracks conversation context to improve routing decisions.
    
    Features:
    1. Coreference Resolution: "it", "that", "this" -> actual concept
    2. Topic Tracking: Maintain conversation topic across turns
    3. Intent Continuation: Detect follow-up questions
    4. Entity Memory: Remember CS concepts, algorithms mentioned
    
    Example:
        User: "Explain binary search"
        Agent: [teacher explains...]
        User: "Give me practice problems on it"  <- "it" = binary search
        Agent: Should route to examiner with context!
    """
    
    # Reference pronouns
    PRONOUNS = {'it', 'that', 'this', 'them', 'these', 'those'}
    
    # Follow-up indicators
    FOLLOWUP_PHRASES = [
        'explain more', 'tell me more', 'continue', 'go on',
        'what about', 'how about', 'also', 'additionally',
        'on that', 'on this', 'about it', 'about that'
    ]
    
    # Topic indicators (CS concepts)
    TOPICS = {
        'data_structures': ['array', 'list', 'stack', 'queue', 'tree', 'graph', 'heap'],
        'algorithms': ['sort', 'search', 'traversal', 'recursion', 'dynamic programming'],
        'complexity': ['big o', 'time complexity', 'space complexity', 'optimization'],
        'coding': ['debug', 'code', 'implementation', 'function', 'program']
    }
    
    def __init__(self, max_history: int = 50, session_timeout_minutes: int = 30):
        """
        Initialize dialogue tracker.
        
        Args:
            max_history: Maximum turns to keep per session
            session_timeout_minutes: Session expiry time
        """
        self.max_history = max_history
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # Active sessions
        self.sessions: Dict[str, DialogueState] = {}  # session_id -> state
        
        # Load spaCy for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
    
    def track_turn(
        self,
        user_id: str,
        session_id: str,
        query: str,
        intent: str,
        response: str = ""
    ) -> DialogueState:
        """
        Add new turn to dialogue state.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query: User query
            intent: Predicted intent
            response: Agent response
        
        Returns:
            Updated dialogue state
        """
        # Get or create session
        if session_id not in self.sessions:
            self.sessions[session_id] = DialogueState(
                user_id=user_id,
                session_id=session_id,
                turns=[]
            )
        
        state = self.sessions[session_id]
        
        # Parse query with NLP
        doc = self.nlp(query.lower())
        
        # Extract entities
        entities = self._extract_entities(doc)
        
        # Detect topic
        topic = self._detect_topic(doc)
        if topic:
            state.current_topic = topic
        
        # Update entity memory
        for ent_type, ent_values in entities.items():
            for value in ent_values:
                state.mentioned_entities[value] = ent_type
        
        # Create turn
        turn = DialogueTurn(
            turn_id=len(state.turns) + 1,
            query=query,
            intent=intent,
            response=response,
            timestamp=datetime.now(),
            entities=entities,
            topic=topic
        )
        
        # Add turn
        state.turns.append(turn)
        state.last_intent = intent
        
        # Prune old turns
        if len(state.turns) > self.max_history:
            state.turns = state.turns[-self.max_history:]
        
        return state
    
    def resolve_context(
        self,
        query: str,
        session_id: str
    ) -> Tuple[str, Dict]:
        """
        Resolve references and add context to query.
        
        Args:
            query: Raw user query
            session_id: Session identifier
        
        Returns:
            (resolved_query, context_dict)
        
        Example:
            Input: "give me practice problems on it"
            Previous: "Explain binary search"
            Output: "give me practice problems on binary search"
        """
        # Get session state
        if session_id not in self.sessions:
            return query, {}
        
        state = self.sessions[session_id]
        
        # Parse query
        doc = self.nlp(query.lower())
        
        # Check for pronouns
        has_pronoun = any(token.text in self.PRONOUNS for token in doc)
        
        resolved_query = query
        context = {
            'has_context': False,
            'previous_topic': state.current_topic,
            'previous_intent': state.last_intent,
            'recent_entities': list(state.mentioned_entities.keys())[-3:]
        }
        
        if has_pronoun and state.current_topic:
            # Replace pronoun with topic
            resolved_query = self._replace_pronouns(query, state.current_topic)
            context['has_context'] = True
            context['resolved_reference'] = state.current_topic
        
        # Check for follow-up indicators
        is_followup = any(phrase in query.lower() for phrase in self.FOLLOWUP_PHRASES)
        if is_followup:
            context['is_followup'] = True
            if state.current_topic:
                context['followup_topic'] = state.current_topic
        
        return resolved_query, context
    
    def get_state(self, session_id: str) -> Optional[DialogueState]:
        """Retrieve session state."""
        return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str):
        """Clear session history."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def prune_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now()
        expired = []
        
        for session_id, state in self.sessions.items():
            if state.turns:
                last_turn_time = state.turns[-1].timestamp
                if now - last_turn_time > self.session_timeout:
                    expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
        
        if expired:
            print(f"[Dialogue] Pruned {len(expired)} expired sessions")
    
    def _extract_entities(self, doc: Doc) -> Dict[str, List[str]]:
        """
        Extract CS-related entities from query.
        
        Returns:
            Dict mapping entity_type -> [entity_values]
        """
        entities = {}
        
        # Extract noun chunks (algorithms, data structures)
        for chunk in doc.noun_chunks:
            text = chunk.text.lower()
            
            # Classify entity type
            if any(term in text for term in ['sort', 'search', 'algorithm', 'traversal']):
                entities.setdefault('algorithm', []).append(text)
            elif any(term in text for term in ['tree', 'list', 'array', 'stack', 'queue', 'graph']):
                entities.setdefault('data_structure', []).append(text)
        
        return entities
    
    def _detect_topic(self, doc: Doc) -> Optional[str]:
        """
        Detect conversation topic from query.
        
        Returns:
            Topic string or None
        """
        query_text = doc.text
        
        # Check each topic category
        for topic_category, keywords in self.TOPICS.items():
            for keyword in keywords:
                if keyword in query_text:
                    return keyword
        
        # Extract first technical noun phrase
        for chunk in doc.noun_chunks:
            text = chunk.text.lower()
            if any(term in text for term in [
                'sort', 'search', 'tree', 'list', 'array', 'graph',
                'algorithm', 'structure', 'complexity'
            ]):
                return text
        
        return None
    
    def _replace_pronouns(self, query: str, reference: str) -> str:
        """Replace pronouns with actual reference."""
        words = query.split()
        resolved = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower in self.PRONOUNS:
                resolved.append(reference)
            else:
                resolved.append(word)
        
        return ' '.join(resolved)


def test_dialogue_tracker():
    """Test dialogue state tracking with conversation."""
    tracker = DialogueStateTracker()
    
    session_id = "test_session_001"
    user_id = "test_user"
    
    print("=" * 80)
    print("Dialogue State Tracker - Test Conversation")
    print("=" * 80)
    
    # Conversation scenario
    conversation = [
        ("Explain binary search algorithm", "teacher"),
        ("Give me practice problems on it", "examiner"),
        ("Now explain merge sort", "teacher"),
        ("Compare that to quicksort", "teacher"),
        ("Debug my implementation of it", "coder"),
    ]
    
    for i, (query, intent) in enumerate(conversation, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {query}")
        
        # Resolve context
        resolved_query, context = tracker.resolve_context(query, session_id)
        
        if context.get('has_context'):
            print(f"Resolved: {resolved_query}")
            print(f"Reference: {context.get('resolved_reference')}")
        
        if context.get('is_followup'):
            print(f"Follow-up on: {context.get('followup_topic')}")
        
        print(f"Intent: {intent}")
        
        # Track turn
        state = tracker.track_turn(
            user_id=user_id,
            session_id=session_id,
            query=query,
            intent=intent,
            response=f"Response to {intent} query"
        )
        
        print(f"Current Topic: {state.current_topic}")
        print(f"Recent Entities: {context.get('recent_entities', [])}")
    
    # Final state
    print("\n" + "=" * 80)
    print("Final Dialogue State")
    print("=" * 80)
    
    state = tracker.get_state(session_id)
    if state:
        print(f"Total Turns: {len(state.turns)}")
        print(f"Current Topic: {state.current_topic}")
        print(f"Last Intent: {state.last_intent}")
        print(f"Entity Memory: {state.mentioned_entities}")


if __name__ == "__main__":
    test_dialogue_tracker()
