"""
Gap 4: Adaptive Empath Engine
Threshold-based emotion detection and teaching strategy adaptation
Enhanced with transformer-based sentiment analysis and multi-signal fusion
"""
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from asgiref.sync import sync_to_async
import threading
from functools import lru_cache

from learning_session.models import (
    EmotionEvent, TeachingStrategy, LearningPattern, EmotionLog
)
from core.models import Topic
from llm_engine.factory import LLMFactory

# Lazy import for transformers to avoid slow startup
_sentiment_pipeline = None
_sentiment_lock = threading.Lock()


@dataclass
class EmotionAssessment:
    """Result of emotion assessment"""
    valence: float  # -1.0 to +1.0
    intensity: str  # 'mild' | 'moderate' | 'strong'
    trigger_type: str
    pause_duration: float
    sentiment_score: float
    error_rate: float
    confidence: float


@dataclass
class InterventionDecision:
    """Teaching strategy intervention decision"""
    should_intervene: bool
    intervention_type: str  # 'pacing' | 'visualization' | 'branching' | 'encouragement'
    delivery_style: str  # 'subtle' | 'brief' | 'explicit'
    action_details: Dict
    reason: str


class EmpathEngine:
    """
    Adaptive Empath Agent Engine with threshold-based emotion detection
    Maps emotions to teaching strategy changes
    """
    
    # Thresholds for emotion intensity
    PAUSE_MILD_THRESHOLD = 3.0  # seconds
    PAUSE_MODERATE_THRESHOLD = 5.0
    PAUSE_STRONG_THRESHOLD = 8.0
    
    SENTIMENT_MILD_THRESHOLD = -0.3  # valence
    SENTIMENT_MODERATE_THRESHOLD = -0.6
    SENTIMENT_STRONG_THRESHOLD = -0.8
    
    ERROR_MILD_THRESHOLD = 2  # errors in last 5 minutes
    ERROR_MODERATE_THRESHOLD = 4
    ERROR_STRONG_THRESHOLD = 6
    
    # Multi-signal fusion weights
    WEIGHT_PAUSE = 0.25
    WEIGHT_SENTIMENT = 0.40
    WEIGHT_ERROR = 0.35
    
    # Intervention cooldown (seconds)
    INTERVENTION_COOLDOWN = 180  # 3 minutes
    
    def __init__(self):
        self.llm_factory = LLMFactory()
        self._last_intervention_time = {}
        self._load_sentiment_model()
    
    async def assess_emotion(
        self,
        user_id: int,
        session_id: str,
        pause_duration: float = 0.0,
        transcript: str = "",
        recent_errors: int = 0,
        activity_type: str = "learning"
    ) -> Dict:
        """
        Main entry point: Assess student emotion and decide intervention
        
        Returns:
            {
                "emotion": EmotionAssessment,
                "intervention": InterventionDecision,
                "encouragement": str
            }
        """
        # 1. Detect emotion intensity
        emotion = await self._detect_emotion_intensity(
            pause_duration=pause_duration,
            transcript=transcript,
            recent_errors=recent_errors
        )
        
        # 2. Decide if intervention needed
        intervention = await self._decide_intervention(
            user_id=user_id,
            emotion=emotion,
            activity_type=activity_type
        )
        
        # 3. Log emotion event
        await self._log_emotion_event(
            user_id=user_id,
            session_id=session_id,
            emotion=emotion,
            intervention=intervention,
            activity_type=activity_type
        )
        
        # 4. Generate contextual encouragement
        encouragement = self._generate_encouragement(emotion, intervention)
        
        return {
            "emotion": asdict(emotion),
            "intervention": asdict(intervention),
            "encouragement": encouragement
        }
    
    # ===== EMOTION DETECTION =====
    
    async def _detect_emotion_intensity(
        self,
        pause_duration: float,
        transcript: str,
        recent_errors: int
    ) -> EmotionAssessment:
        """
        Threshold-based emotion detection using three signals:
        1. Pause duration (physiological)
        2. Sentiment from transcript (linguistic)
        3. Error rate (behavioral)
        """
        # Calculate sentiment score from transcript
        sentiment_score = await self._analyze_sentiment(transcript) if transcript else 0.0
        
        # Normalize error rate (errors per 5 minutes)
        error_rate = min(recent_errors / 6, 1.0)
        
        # Determine intensity for each signal
        pause_intensity = self._classify_pause_intensity(pause_duration)
        sentiment_intensity = self._classify_sentiment_intensity(sentiment_score)
        error_intensity = self._classify_error_intensity(recent_errors)
        
        # Take the maximum intensity (most concerning signal)
        intensities = {'mild': 1, 'moderate': 2, 'strong': 3}
        max_intensity = max(
            intensities.get(pause_intensity, 0),
            intensities.get(sentiment_intensity, 0),
            intensities.get(error_intensity, 0)
        )
        
        intensity_map = {0: 'mild', 1: 'mild', 2: 'moderate', 3: 'strong'}
        final_intensity = intensity_map[max_intensity]
        
        # Determine trigger type
        if max_intensity == intensities.get(pause_intensity, 0):
            trigger_type = 'pause'
        elif max_intensity == intensities.get(sentiment_intensity, 0):
            trigger_type = 'sentiment'
        elif max_intensity == intensities.get(error_intensity, 0):
            trigger_type = 'error_spike'
        else:
            trigger_type = 'combined'
        
        # Calculate overall valence (weighted average)
        valence = (
            sentiment_score * 0.5 +  # Sentiment is strongest signal
            (-pause_duration / 10) * 0.3 +  # Longer pause = more negative
            (-error_rate) * 0.2  # More errors = more negative
        )
        valence = max(min(valence, 1.0), -1.0)  # Clamp to [-1, 1]
        
        # Calculate confidence
        signals_present = sum([
            pause_duration > 0,
            transcript != "",
            recent_errors > 0
        ])
        confidence = signals_present / 3.0
        
        return EmotionAssessment(
            valence=valence,
            intensity=final_intensity,
            trigger_type=trigger_type,
            pause_duration=pause_duration,
            sentiment_score=sentiment_score,
            error_rate=error_rate,
            confidence=confidence
        )
    
    def _classify_pause_intensity(self, pause_duration: float) -> str:
        """Classify pause duration into intensity level"""
        if pause_duration >= self.PAUSE_STRONG_THRESHOLD:
            return 'strong'
        elif pause_duration >= self.PAUSE_MODERATE_THRESHOLD:
            return 'moderate'
        elif pause_duration >= self.PAUSE_MILD_THRESHOLD:
            return 'mild'
        else:
            return 'none'
    
    def _classify_sentiment_intensity(self, sentiment_score: float) -> str:
        """Classify sentiment score into intensity level"""
        if sentiment_score <= self.SENTIMENT_STRONG_THRESHOLD:
            return 'strong'
        elif sentiment_score <= self.SENTIMENT_MODERATE_THRESHOLD:
            return 'moderate'
        elif sentiment_score <= self.SENTIMENT_MILD_THRESHOLD:
            return 'mild'
        else:
            return 'none'
    
    def _classify_error_intensity(self, recent_errors: int) -> str:
        """Classify error count into intensity level"""
        if recent_errors >= self.ERROR_STRONG_THRESHOLD:
            return 'strong'
        elif recent_errors >= self.ERROR_MODERATE_THRESHOLD:
            return 'moderate'
        elif recent_errors >= self.ERROR_MILD_THRESHOLD:
            return 'mild'
        else:
            return 'none'
    
    def _load_sentiment_model(self):
        """Lazy load sentiment analysis model"""
        global _sentiment_pipeline
        if _sentiment_pipeline is None:
            with _sentiment_lock:
                if _sentiment_pipeline is None:
                    try:
                        from transformers import pipeline
                        _sentiment_pipeline = pipeline(
                            "text-classification",
                            model="bhadresh-savani/distilbert-base-uncased-emotion",
                            return_all_scores=True,
                            device=-1
                        )
                    except Exception as e:
                        print(f"Failed to load sentiment model: {e}")
                        _sentiment_pipeline = False
    
    async def _analyze_sentiment(self, transcript: str) -> float:
        """
        Analyze sentiment using transformer-based emotion classification.
        Maps emotions to valence score: -1.0 (negative) to +1.0 (positive)
        """
        global _sentiment_pipeline
        
        if not transcript or len(transcript.strip()) < 3:
            return 0.0
        
        # Use transformer model if available
        if _sentiment_pipeline and _sentiment_pipeline is not False:
            try:
                results = _sentiment_pipeline(transcript[:512])[0]
                
                emotion_valence = {
                    'sadness': -0.8,
                    'anger': -0.9,
                    'fear': -0.7,
                    'surprise': 0.1,
                    'joy': 0.9,
                    'love': 0.8
                }
                
                valence_score = sum(
                    emotion_valence.get(r['label'], 0.0) * r['score']
                    for r in results
                )
                
                return np.clip(valence_score, -1.0, 1.0)
                
            except Exception as e:
                print(f"Sentiment analysis error: {e}")
        
        # Fallback: Enhanced keyword-based sentiment
        transcript_lower = transcript.lower()
        
        strong_negative = ['hate', 'terrible', 'awful', 'frustrated', 'confused', 'lost']
        moderate_negative = ['difficult', 'stuck', 'hard', 'struggling', 'don\'t understand', 'help', 'wrong']
        mild_negative = ['unsure', 'maybe', 'not sure', 'hmm']
        
        strong_positive = ['love', 'excellent', 'perfect', 'amazing', 'brilliant', 'got it']
        moderate_positive = ['good', 'understand', 'clear', 'thanks', 'yes', 'correct', 'right']
        mild_positive = ['ok', 'fine', 'sure', 'yeah']
        
        score = 0.0
        total_weight = 0.0
        
        for word in strong_negative:
            if word in transcript_lower:
                score -= 0.9
                total_weight += 1.0
        for word in moderate_negative:
            if word in transcript_lower:
                score -= 0.6
                total_weight += 1.0
        for word in mild_negative:
            if word in transcript_lower:
                score -= 0.3
                total_weight += 1.0
        for word in strong_positive:
            if word in transcript_lower:
                score += 0.9
                total_weight += 1.0
        for word in moderate_positive:
            if word in transcript_lower:
                score += 0.6
                total_weight += 1.0
        for word in mild_positive:
            if word in transcript_lower:
                score += 0.3
                total_weight += 1.0
        
        if total_weight == 0:
            return 0.0
        
        return np.clip(score / total_weight, -1.0, 1.0)
    
    # ===== INTERVENTION DECISION =====
    
    async def _decide_intervention(
        self,
        user_id: int,
        emotion: EmotionAssessment,
        activity_type: str
    ) -> InterventionDecision:
        """
        Decide teaching strategy intervention based on emotion intensity
        
        Strategy Matrix:
        - Mild: Subtle pacing adjustment
        - Moderate: Visualization switch or modality change
        - Strong: Branching to prerequisite or explicit encouragement
        """
        # No intervention for positive/neutral emotions
        if emotion.intensity == 'mild' and emotion.valence > -0.3:
            return InterventionDecision(
                should_intervene=False,
                intervention_type='none',
                delivery_style='subtle',
                action_details={},
                reason="Emotion within normal range"
            )
        
        # Get user's teaching strategy preferences
        try:
            strategy = await sync_to_async(TeachingStrategy.objects.get)(user_id=user_id)
        except TeachingStrategy.DoesNotExist:
            # Create default strategy
            strategy = await sync_to_async(TeachingStrategy.objects.create)(
                user_id=user_id,
                preferred_modality='mixed'
            )
        
        # Select intervention based on intensity
        if emotion.intensity == 'mild':
            return self._plan_pacing_adjustment(emotion, strategy)
        elif emotion.intensity == 'moderate':
            return await self._plan_visualization_switch(emotion, strategy, activity_type)
        else:  # strong
            return await self._plan_branching_intervention(user_id, emotion, strategy)
    
    def _plan_pacing_adjustment(
        self,
        emotion: EmotionAssessment,
        strategy: TeachingStrategy
    ) -> InterventionDecision:
        """Plan subtle pacing adjustment for mild frustration"""
        # Slow down speech, add pauses, reduce information density
        speech_rate = 0.95  # Slightly slower
        chunk_size_reduction = 0.9  # 10% less content per chunk
        
        return InterventionDecision(
            should_intervene=True,
            intervention_type='pacing',
            delivery_style='subtle',
            action_details={
                'speech_rate': speech_rate,
                'chunk_size_multiplier': chunk_size_reduction,
                'add_pauses': True,
                'simplify_language': True
            },
            reason=f"Mild frustration detected ({emotion.trigger_type}), adjusting pacing"
        )
    
    async def _plan_visualization_switch(
        self,
        emotion: EmotionAssessment,
        strategy: TeachingStrategy,
        activity_type: str
    ) -> InterventionDecision:
        """Plan modality switch for moderate frustration"""
        # Switch to visual representation if currently text-heavy
        current_modality = strategy.preferred_modality
        
        # Determine best target modality
        if current_modality == 'text':
            target_modality = 'visual'
            action = 'switch_to_canvas'
        elif current_modality == 'visual':
            target_modality = 'mixed'
            action = 'add_explanation'
        else:
            target_modality = 'visual'
            action = 'emphasize_diagram'
        
        return InterventionDecision(
            should_intervene=True,
            intervention_type='visualization',
            delivery_style='brief',
            action_details={
                'target_modality': target_modality,
                'action': action,
                'use_whiteboard': True,
                'add_examples': True
            },
            reason=f"Moderate frustration, switching to {target_modality} learning"
        )
    
    async def _plan_branching_intervention(
        self,
        user_id: int,
        emotion: EmotionAssessment,
        strategy: TeachingStrategy
    ) -> InterventionDecision:
        """Plan branching to prerequisite for strong frustration"""
        # Suggest taking a break or switching to easier prerequisite topic
        
        # Check if user needs explicit encouragement
        try:
            patterns = await sync_to_async(LearningPattern.objects.get)(user_id=user_id)
            needs_encouragement = patterns.requires_explicit_encouragement
        except LearningPattern.DoesNotExist:
            needs_encouragement = True
        
        return InterventionDecision(
            should_intervene=True,
            intervention_type='branching',
            delivery_style='explicit',
            action_details={
                'pause_current_task': True,
                'suggest_break': True,
                'offer_prerequisite': True,
                'provide_encouragement': needs_encouragement
            },
            reason="Strong frustration detected, suggesting break or prerequisite review"
        )
    
    async def _evaluate_branching(self, current_topic_id: int) -> Optional[Dict]:
        """
        Find prerequisite or related topics for branching using topic order and subject
        """
        try:
            topic = await sync_to_async(Topic.objects.select_related('subject').get)(id=current_topic_id)
            
            suggestions = []
            
            # Priority 1: Previous topic in same subject (likely prerequisite)
            prev_topic = await sync_to_async(
                lambda: Topic.objects.filter(
                    subject=topic.subject,
                    order__lt=topic.order
                ).order_by('-order').first()
            )()
            
            if prev_topic:
                suggestions.append({
                    'topic_id': prev_topic.id,
                    'title': prev_topic.title,
                    'relationship': 'prerequisite',
                    'reason': f"Review {prev_topic.title} which comes before {topic.title}"
                })
            
            # Priority 2: Other topics in same subject (alternative approaches)
            siblings = await sync_to_async(
                lambda: list(Topic.objects.filter(
                    subject=topic.subject
                ).exclude(id=topic.id).order_by('order')[:2])
            )()
            
            for sibling in siblings:
                if sibling.id != (prev_topic.id if prev_topic else None):
                    suggestions.append({
                        'topic_id': sibling.id,
                        'title': sibling.title,
                        'relationship': 'alternative',
                        'reason': f"Try {sibling.title} for a different perspective"
                    })
            
            # Priority 3: Next topic (simpler breakdown if struggling with current)
            next_topic = await sync_to_async(
                lambda: Topic.objects.filter(
                    subject=topic.subject,
                    order__gt=topic.order
                ).order_by('order').first()
            )()
            
            if next_topic:
                suggestions.append({
                    'topic_id': next_topic.id,
                    'title': next_topic.title,
                    'relationship': 'next',
                    'reason': f"Move to {next_topic.title} for progressive learning"
                })
            
            if suggestions:
                return {
                    'current_topic': topic.title,
                    'suggestions': suggestions[:3]
                }
            
            return None
            
        except Topic.DoesNotExist:
            return None
        except Exception as e:
            print(f"Topic branching error: {e}")
            return None
    
    # ===== DATABASE LOGGING =====
    
    async def _log_emotion_event(
        self,
        user_id: int,
        session_id: str,
        emotion: EmotionAssessment,
        intervention: InterventionDecision,
        activity_type: str
    ):
        """Log emotion event to database for pattern analysis"""
        # Create EmotionEvent
        await sync_to_async(EmotionEvent.objects.create)(
            user_id=user_id,
            session_id=session_id,
            emotion_valence=emotion.valence,
            emotion_intensity=emotion.intensity,
            pause_duration=emotion.pause_duration,
            sentiment_score=emotion.sentiment_score,
            error_rate=emotion.error_rate,
            trigger_type=emotion.trigger_type,
            context_data={
                'confidence': emotion.confidence,
                'intervention_type': intervention.intervention_type
            }
        )
        
        # Create EmotionLog for aggregation
        emotion_level = 'positive' if emotion.valence > 0.3 else ('negative' if emotion.valence < -0.3 else 'neutral')
        
        await sync_to_async(EmotionLog.objects.create)(
            user_id=user_id,
            session_id=session_id,
            emotion_level=emotion_level,
            valence=emotion.valence,
            pause_duration=emotion.pause_duration,
            activity_type=activity_type,
            intervention_taken=intervention.should_intervene,
            intervention_type=intervention.intervention_type if intervention.should_intervene else '',
        )
        
        # Update teaching strategy stats
        if intervention.should_intervene:
            try:
                strategy = await sync_to_async(TeachingStrategy.objects.get)(user_id=user_id)
                strategy.total_interventions += 1
                await sync_to_async(strategy.save)()
            except TeachingStrategy.DoesNotExist:
                pass
    
    # ===== ENCOURAGEMENT =====
    
    def _generate_encouragement(
        self,
        emotion: EmotionAssessment,
        intervention: InterventionDecision
    ) -> str:
        """Generate contextual encouragement based on emotion and intervention"""
        
        if emotion.intensity == 'mild':
            return "You're doing well. Let's keep going. 💪"
        
        elif emotion.intensity == 'moderate':
            if intervention.intervention_type == 'visualization':
                return "Let me show you this visually - it might help clarify things. 📊"
            else:
                return "I can see this is challenging. Let's try a different approach. 🔄"
        
        else:  # strong
            if intervention.delivery_style == 'explicit':
                return "I notice you're struggling with this. That's completely normal! 💙 Would you like to take a short break or review some prerequisite concepts?"
            else:
                return "You're working hard on this. Remember, every challenge is an opportunity to learn. 🌟"
    
    def _get_delivery_style(self, intensity: str) -> str:
        """Get appropriate delivery style for acknowledgment"""
        if intensity == 'mild':
            return 'subtle'
        elif intensity == 'moderate':
            return 'brief'
        else:
            return 'explicit'
