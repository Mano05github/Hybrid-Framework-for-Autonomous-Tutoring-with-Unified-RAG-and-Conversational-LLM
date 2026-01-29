"""
Gap 5: Strategic Forecasting & Pattern Analysis Engine
Mastery timeline predictions and recurring error pattern detection
"""
import numpy as np
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression


@dataclass
class MasteryForecast:
    """Mastery timeline prediction"""
    topic: str
    current_mastery: float  # 0.0-1.0
    predicted_mastery_date: Optional[datetime]
    days_remaining: Optional[int]
    confidence: float
    velocity_trend: str  # 'improving', 'stable', 'declining'
    data_points: int


@dataclass
class RecurringPattern:
    """Detected recurring error or struggle pattern"""
    pattern_key: str
    pattern_type: str  # 'error_type', 'topic_struggle', 'code_pattern'
    occurrences: int
    first_seen: datetime
    latest_seen: datetime
    time_span_hours: float
    recommended_action: str


class StrategicForecastingEngine:
    """
    Lightweight ML for long-term trajectory prediction
    
    Uses linear regression for mastery timeline forecasting
    with ±2 days target accuracy.
    """
    
    def __init__(self):
        self.mastery_model = LinearRegression()
        self.velocity_model = LinearRegression()
        self.min_data_points = 3
        
    def forecast_mastery_timeline(
        self,
        topic: str,
        history: List[Dict],
        user_id: Optional[int] = None
    ) -> Optional[MasteryForecast]:
        """
        Predict when student will master a topic
        
        Args:
            user_id: Student ID
            topic: Topic name
            history: List of {day: int, mastery_percentage: float}
            
        Returns:
            MasteryForecast or None if insufficient data
        """
        if len(history) < self.min_data_points:
            return None
        
        # Prepare data
        X = np.array([h['day'] for h in history]).reshape(-1, 1)
        y = np.array([h['mastery_percentage'] for h in history])
        
        # Train model
        self.mastery_model.fit(X, y)
        
        # Get model performance
        confidence = self.mastery_model.score(X, y)
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        # Predict when mastery will reach 85%
        target_mastery = 85.0
        current_mastery = y[-1]
        
        predicted_date = None
        days_remaining = None
        
        if current_mastery < target_mastery:
            # Project forward up to 30 days
            future_days = np.arange(len(history), len(history) + 30).reshape(-1, 1)
            predictions = self.mastery_model.predict(future_days)
            
            # Find first day where prediction >= 85%
            for day_idx, pred in zip(future_days.flatten(), predictions):
                if pred >= target_mastery:
                    days_from_now = int(day_idx - len(history) + 1)  # Convert numpy int to Python int
                    predicted_date = datetime.now() + timedelta(days=days_from_now)
                    days_remaining = days_from_now
                    break
        elif current_mastery >= target_mastery:
            # Already mastered
            predicted_date = datetime.now()
            days_remaining = 0
        
        # Determine velocity trend
        velocity_trend = self._analyze_velocity_trend(history)
        
        return MasteryForecast(
            topic=topic,
            current_mastery=current_mastery,  # Already in 0-100 range
            predicted_mastery_date=predicted_date,
            days_remaining=days_remaining,
            confidence=confidence,
            velocity_trend=velocity_trend,
            data_points=len(history)
        )
    
    def _analyze_velocity_trend(self, history: List[Dict]) -> str:
        """
        Analyze if learning velocity is improving, stable, or declining
        """
        if len(history) < 2:
            return 'stable'
        
        # Calculate mastery gains per day
        gains = []
        for i in range(1, len(history)):
            gain = history[i]['mastery_percentage'] - history[i-1]['mastery_percentage']
            gains.append(gain)
        
        if not gains:
            return 'stable'
        
        # Linear regression on gains to detect trend
        X_gain = np.arange(len(gains)).reshape(-1, 1)
        y_gain = np.array(gains)
        
        gain_model = LinearRegression()
        gain_model.fit(X_gain, y_gain)
        
        slope = gain_model.coef_[0]
        
        # Classify trend
        if slope > 0.5:
            return 'improving'
        elif slope < -0.5:
            return 'declining'
        else:
            return 'stable'
    
    def forecast_multiple_topics(
        self,
        user_id: int,
        topics_history: Dict[str, List[Dict]]
    ) -> List[MasteryForecast]:
        """
        Forecast mastery for multiple topics
        
        Args:
            user_id: Student ID
            topics_history: Dict mapping topic name to history list
            
        Returns:
            List of MasteryForecast objects
        """
        forecasts = []
        
        for topic, history in topics_history.items():
            forecast = self.forecast_mastery_timeline(user_id, topic, history)
            if forecast:
                forecasts.append(forecast)
        
        return forecasts
    
    def get_priority_topics(
        self,
        forecasts: List[MasteryForecast],
        limit: int = 3
    ) -> List[str]:
        """
        Get topics that need attention (low mastery or declining trend)
        
        Args:
            forecasts: List of mastery forecasts
            limit: Max number of topics to return
            
        Returns:
            List of topic names prioritized by need
        """
        # Score each topic by urgency
        scored_topics = []
        
        for forecast in forecasts:
            urgency_score = 0.0
            
            # Low mastery = high urgency
            if forecast.current_mastery < 0.5:
                urgency_score += 3.0
            elif forecast.current_mastery < 0.7:
                urgency_score += 2.0
            elif forecast.current_mastery < 0.85:
                urgency_score += 1.0
            
            # Declining trend = high urgency
            if forecast.velocity_trend == 'declining':
                urgency_score += 2.0
            
            # Long timeline = moderate urgency
            if forecast.days_remaining and forecast.days_remaining > 7:
                urgency_score += 1.0
            
            scored_topics.append((forecast.topic, urgency_score))
        
        # Sort by urgency, descending
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        
        return [topic for topic, score in scored_topics[:limit]]


class PatternAnalyzer:
    """
    Detect recurring patterns across sessions
    
    Identifies:
    - Recurring error types (e.g., off-by-one, null pointer)
    - Topics causing repeated struggles
    - Code patterns that fail consistently
    """
    
    def __init__(self, occurrence_threshold: int = 3):
        self.occurrence_threshold = occurrence_threshold
        
    def detect_recurring_errors(
        self,
        error_history: List[Dict]
    ) -> List[RecurringPattern]:
        """
        Detect recurring error patterns
        
        Args:
            error_history: List of {error_type: str, timestamp: datetime, topic: str}
            
        Returns:
            List of RecurringPattern objects
        """
        # Group errors by type
        error_groups: Dict[str, List[datetime]] = {}
        
        for error in error_history:
            error_type = error.get('error_type', 'unknown')
            timestamp = error.get('timestamp', datetime.now())
            
            if error_type not in error_groups:
                error_groups[error_type] = []
            
            error_groups[error_type].append(timestamp)
        
        # Identify patterns
        patterns = []
        
        for error_type, timestamps in error_groups.items():
            if len(timestamps) >= self.occurrence_threshold:
                timestamps.sort()
                
                first_seen = timestamps[0]
                latest_seen = timestamps[-1]
                time_span = (latest_seen - first_seen).total_seconds() / 3600  # hours
                
                # Determine recommended action
                action = self._get_error_pattern_action(error_type, len(timestamps))
                
                pattern = RecurringPattern(
                    pattern_key=f"error_{error_type}",
                    pattern_type='error_type',
                    occurrences=len(timestamps),
                    first_seen=first_seen,
                    latest_seen=latest_seen,
                    time_span_hours=time_span,
                    recommended_action=action
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def detect_topic_struggles(
        self,
        session_history: List[Dict]
    ) -> List[RecurringPattern]:
        """
        Detect topics that consistently cause frustration
        
        Args:
            session_history: List of {topic: str, struggle_score: float, timestamp: datetime}
            
        Returns:
            List of RecurringPattern objects
        """
        # Group by topic
        topic_struggles: Dict[str, List[Tuple[float, datetime]]] = {}
        
        for session in session_history:
            topic = session.get('topic', 'unknown')
            struggle_score = session.get('struggle_score', 0.0)
            timestamp = session.get('timestamp', datetime.now())
            
            # Only count significant struggles (score > 0.6)
            if struggle_score > 0.6:
                if topic not in topic_struggles:
                    topic_struggles[topic] = []
                
                topic_struggles[topic].append((struggle_score, timestamp))
        
        # Identify patterns
        patterns = []
        
        for topic, struggles in topic_struggles.items():
            if len(struggles) >= self.occurrence_threshold:
                timestamps = [t for _, t in struggles]
                timestamps.sort()
                
                avg_struggle = sum(s for s, _ in struggles) / len(struggles)
                
                first_seen = timestamps[0]
                latest_seen = timestamps[-1]
                time_span = (latest_seen - first_seen).total_seconds() / 3600
                
                action = self._get_topic_struggle_action(topic, len(struggles), avg_struggle)
                
                pattern = RecurringPattern(
                    pattern_key=f"topic_struggle_{topic}",
                    pattern_type='topic_struggle',
                    occurrences=len(struggles),
                    first_seen=first_seen,
                    latest_seen=latest_seen,
                    time_span_hours=time_span,
                    recommended_action=action
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def _get_error_pattern_action(self, error_type: str, occurrences: int) -> str:
        """Recommend action for recurring error pattern"""
        if occurrences >= 5:
            return f"Critical: '{error_type}' error repeated {occurrences} times. Review prerequisite concepts before continuing."
        elif occurrences >= 3:
            return f"Pattern detected: '{error_type}' error seen {occurrences} times. Provide targeted practice on this error type."
        else:
            return f"Monitor: '{error_type}' error seen {occurrences} times. Watch for continuation of pattern."
    
    def _get_topic_struggle_action(self, topic: str, occurrences: int, avg_struggle: float) -> str:
        """Recommend action for topic struggle pattern"""
        if avg_struggle > 0.8 and occurrences >= 3:
            return f"High struggle on '{topic}' (avg {avg_struggle:.2f}). Consider branching to prerequisite review."
        elif occurrences >= 5:
            return f"Repeated struggles with '{topic}'. Break down into smaller sub-topics or use different teaching approach."
        else:
            return f"Moderate struggle with '{topic}'. Provide additional examples and practice problems."
    
    def get_top_patterns(
        self,
        all_patterns: List[RecurringPattern],
        limit: int = 5
    ) -> List[RecurringPattern]:
        """
        Get most significant patterns sorted by occurrences
        """
        sorted_patterns = sorted(all_patterns, key=lambda p: p.occurrences, reverse=True)
        return sorted_patterns[:limit]


