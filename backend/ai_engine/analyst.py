import logging
from .state import AgentState
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

import json
import os
import time
from datetime import datetime

class AnalystAgent:
    """
    The Analyst Agent ("The Auditor").
    Tracks user mastery using Elo Rating algorithm.
    Features:
    1. Persistence: Saves to 'mastery_db.json'.
    2. Forgetting Curve: Decay by 1% every 24h.
    """
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'mastery_db.json')
        self.k_factor = 30
        self.mastery_db = self._load_db()

    def _load_db(self):
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Analyst: Load Failed {e}")
        return {}

    def _save_db(self):
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.mastery_db, f, indent=2)
        except Exception as e:
            logger.error(f"Analyst: Save Failed {e}")

    def _apply_decay(self, topic):
        """Applies Forgetting Curve: 1% decay per 24h."""
        if topic not in self.mastery_db:
            return

        data = self.mastery_db[topic]
        last_ts = data.get('last_updated', time.time())
        current_ts = time.time()
        
        hours_passed = (current_ts - last_ts) / 3600
        days_passed = hours_passed / 24
        
        if days_passed > 1:
            old_score = data['score']
            decay_factor = 0.99 ** int(days_passed) # 1% drop per day
            new_score = old_score * decay_factor
            
            self.mastery_db[topic]['score'] = round(new_score, 2)
            self.mastery_db[topic]['last_updated'] = current_ts # Reset timer
            logger.info(f"Analyst: Decay applied to {topic}. {old_score} -> {new_score}")

    def invoke(self, state: AgentState) -> dict:
        messages = state['messages']
        if not messages:
            return {}

        topic = state.get('current_topic', 'general')
        
        # Initialize if new
        if topic not in self.mastery_db:
            self.mastery_db[topic] = {'score': 1000, 'last_updated': time.time()}

        # 1. Apply Decay First (Memory Validation)
        self._apply_decay(topic)
        
        current_elo = self.mastery_db[topic]['score']
        
        # 2. Elo Update Logic
        quiz_result = state.get('quiz_result') 
        
        if quiz_result:
            actual_score = 1 if quiz_result == 'correct' else 0
            expected_score = 1 / (1 + 10 ** ((1500 - current_elo) / 400))
            
            new_elo = current_elo + self.k_factor * (actual_score - expected_score)
            
            self.mastery_db[topic]['score'] = round(new_elo, 2)
            self.mastery_db[topic]['last_updated'] = time.time()
            self._save_db() # Persist immediately
            
            logger.info(f"Analyst: Elo Updated for {topic}. {current_elo} -> {new_elo}")
            
            if new_elo < 800:
                logger.warning(f"Analyst: Mastery low on {topic}.")

        # Return simplified dict for other agents
        simple_view = {k: v['score'] for k, v in self.mastery_db.items()}
        return {"user_mastery": simple_view}

        # The Analyst usually returns nothing to the chat, just updates state/DB.
        return {"user_mastery": self.mastery_db}
