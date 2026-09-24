"""
Gap 5: Heuristic Anomaly Detection Engine
Fast rule-based warning system for immediate intervention (<10ms latency)
"""
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class AnomalyAlert:
    """Detected anomaly with context"""
    alert_type: str
    severity: str  # 'low', 'moderate', 'high'
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    recommended_action: str
    metadata: Dict


class ImmediateHeuristicEngine:
    """
    Fast heuristic-based anomaly detection for Gap 5
    
    Uses simple thresholds for <10ms decision time.
    Detects: idle spikes, error cascades, velocity drops, streak breaks.
    """
    
    # Thresholds — raised to avoid false alerts during normal reading/thinking
    IDLE_THRESHOLD_LOW = 180.0       # 3 minutes idle  (was 1 min)
    IDLE_THRESHOLD_MODERATE = 480.0  # 8 minutes idle  (was 2 min)
    IDLE_THRESHOLD_HIGH = 900.0      # 15 minutes idle (was 5 min)
    
    ERROR_CASCADE_WINDOW = 30.0     # 30 seconds
    ERROR_CASCADE_COUNT = 3         # 3+ errors in window
    
    VELOCITY_DROP_THRESHOLD = 0.5   # 50% slower than baseline
    VELOCITY_DROP_SEVERE = 0.3      # 70% slower
    
    STREAK_THRESHOLD = 3            # Track streaks of 3+
    
    def __init__(self):
        self.error_history: List[Dict] = []  # Sliding window of recent errors
        self.last_success_time: Optional[datetime] = None
        self.current_streak = 0
        self.previous_streak = 0  # Track previous streak for break detection
        self.baseline_velocity = 1.0
    
    def record_error(self, error_data: Dict):
        """Record an error for cascade detection"""
        self.error_history.append(error_data)
        
    def analyze_telemetry(self, telemetry: Dict) -> List[AnomalyAlert]:
        """
        Analyze telemetry snapshot and detect anomalies
        
        Args:
            telemetry: Dict with keys: idle_time, error_count, velocity_score, etc.
            
        Returns:
            List of AnomalyAlert objects
        """
        alerts = []
        now = datetime.now()
        
        # 1. Check idle time
        idle_alert = self._check_idle_spike(
            idle_time=telemetry.get('idle_time', 0.0),
            timestamp=now
        )
        if idle_alert:
            alerts.append(idle_alert)
        
        # 2. Check error cascade
        error_count = telemetry.get('error_count', 0)
        if error_count > 0:
            for _ in range(error_count):
                self.error_history.append(now)
            
            cascade_alert = self._check_error_cascade(timestamp=now)
            if cascade_alert:
                alerts.append(cascade_alert)
        
        # 3. Check velocity drop
        velocity = telemetry.get('velocity_score', 1.0)
        velocity_alert = self._check_velocity_drop(
            velocity=velocity,
            timestamp=now
        )
        if velocity_alert:
            alerts.append(velocity_alert)
        
        # 4. Check streak break
        success = telemetry.get('success', False)
        streak_alert = self._check_streak_break(
            success=success,
            timestamp=now
        )
        if streak_alert:
            alerts.append(streak_alert)
        
        return alerts
    
    def _check_idle_spike(self, idle_time: float, timestamp: datetime) -> Optional[AnomalyAlert]:
        """Detect prolonged idle periods"""
        if idle_time < self.IDLE_THRESHOLD_LOW:
            return None
        
        # Determine severity
        if idle_time >= self.IDLE_THRESHOLD_HIGH:
            severity = 'high'
            message = f"Student idle for {idle_time/60:.1f} minutes. May have left or is stuck."
            action = "Send check-in message: 'Still there? Need help?'"
        elif idle_time >= self.IDLE_THRESHOLD_MODERATE:
            severity = 'moderate'
            message = f"Student idle for {idle_time/60:.1f} minutes. Possible confusion or distraction."
            action = "Send gentle prompt: 'Take your time. Ask if you need a hint.'"
        else:
            severity = 'low'
            message = f"Student idle for {idle_time:.0f} seconds. Normal thinking pause."
            action = "Monitor only, no intervention yet."
        
        return AnomalyAlert(
            alert_type='idle_spike',
            severity=severity,
            message=message,
            metric_value=idle_time,
            threshold=self.IDLE_THRESHOLD_MODERATE,
            timestamp=timestamp,
            recommended_action=action,
            metadata={'idle_minutes': idle_time / 60}
        )
    
    def _check_error_cascade(self, timestamp: datetime) -> Optional[AnomalyAlert]:
        """Detect rapid succession of errors"""
        # Remove errors outside window
        window_start = timestamp - timedelta(seconds=self.ERROR_CASCADE_WINDOW)
        
        # Handle both dict entries (new format) and datetime entries (old format)
        filtered_errors = []
        for e in self.error_history:
            if isinstance(e, dict):
                if e.get('timestamp', datetime.min) >= window_start:
                    filtered_errors.append(e)
            elif isinstance(e, datetime) and e >= window_start:
                # Legacy format - convert to dict
                filtered_errors.append({'timestamp': e, 'type': 'unknown'})
        
        self.error_history = filtered_errors
        error_count = len(self.error_history)
        
        if error_count < self.ERROR_CASCADE_COUNT:
            return None
        
        # Determine severity based on count
        if error_count >= 6:
            severity = 'high'
            message = f"{error_count} errors in {self.ERROR_CASCADE_WINDOW}s. Student is significantly struggling."
            action = "Escalate to Empath Agent for intervention. Consider prerequisite review."
        elif error_count >= 4:
            severity = 'moderate'
            message = f"{error_count} errors in {self.ERROR_CASCADE_WINDOW}s. Approach may be wrong."
            action = "Trigger Coder Agent with Level 4 hint (directional guidance)."
        else:
            severity = 'low'
            message = f"{error_count} errors in {self.ERROR_CASCADE_WINDOW}s. Normal struggle."
            action = "Monitor pattern. Offer hint if continues."
        
        return AnomalyAlert(
            alert_type='error_cascade',
            severity=severity,
            message=message,
            metric_value=error_count,
            threshold=self.ERROR_CASCADE_COUNT,
            timestamp=timestamp,
            recommended_action=action,
            metadata={
                'error_count': error_count,
                'window_seconds': self.ERROR_CASCADE_WINDOW
            }
        )
    
    def _check_velocity_drop(self, velocity: float, timestamp: datetime) -> Optional[AnomalyAlert]:
        """Detect significant slowdown in problem-solving speed"""
        if velocity >= self.VELOCITY_DROP_THRESHOLD:
            return None  # Normal or faster pace
        
        # Calculate percentage drop
        drop_percentage = (1.0 - velocity) * 100
        
        if velocity <= self.VELOCITY_DROP_SEVERE:
            severity = 'high'
            message = f"Problem-solving speed dropped {drop_percentage:.0f}%. Significant slowdown detected."
            action = "Check for conceptual gaps. May need prerequisite review."
        elif velocity <= self.VELOCITY_DROP_THRESHOLD:
            severity = 'moderate'
            message = f"Problem-solving speed dropped {drop_percentage:.0f}%. Student slowing down."
            action = "Monitor complexity. May need difficulty adjustment."
        else:
            severity = 'low'
            message = f"Slight velocity drop ({drop_percentage:.0f}%). Within normal range."
            action = "Continue monitoring."
        
        return AnomalyAlert(
            alert_type='velocity_drop',
            severity=severity,
            message=message,
            metric_value=velocity,
            threshold=self.VELOCITY_DROP_THRESHOLD,
            timestamp=timestamp,
            recommended_action=action,
            metadata={
                'velocity_score': velocity,
                'drop_percentage': drop_percentage
            }
        )
    
    def _check_streak_break(self, success: bool, timestamp: datetime) -> Optional[AnomalyAlert]:
        """Detect break in success streak"""
        if success:
            self.current_streak += 1
            self.last_success_time = timestamp
            return None
        
        # Failure detected
        previous_streak = self.current_streak
        self.current_streak = 0
        
        # Only alert if had significant streak
        if previous_streak < self.STREAK_THRESHOLD:
            return None
        
        # Calculate time since last success
        time_since_success = 0
        if self.last_success_time:
            time_since_success = (timestamp - self.last_success_time).total_seconds()
        
        severity = 'moderate'
        message = f"Success streak of {previous_streak} broken. Student may need encouragement."
        action = "Trigger Empath Agent for supportive message. Analyze if difficulty increased."
        
        return AnomalyAlert(
            alert_type='streak_break',
            severity=severity,
            message=message,
            metric_value=previous_streak,
            threshold=self.STREAK_THRESHOLD,
            timestamp=timestamp,
            recommended_action=action,
            metadata={
                'previous_streak': previous_streak,
                'time_since_last_success': time_since_success
            }
        )
    
    def update_baseline_velocity(self, velocity: float):
        """Update baseline velocity for velocity drop detection"""
        if velocity > 0:
            # Exponential moving average
            alpha = 0.3
            self.baseline_velocity = alpha * velocity + (1 - alpha) * self.baseline_velocity
    
    def reset_session(self):
        """Reset engine state for new session"""
        self.error_history = []
        self.last_success_time = None
        self.current_streak = 0
        self.baseline_velocity = 1.0


class PatternRecognizer:
    """Detect recurring patterns across sessions"""
    
    def __init__(self, pattern_threshold: int = 3):
        self.pattern_threshold = pattern_threshold
        self.pattern_history: Dict[str, List[datetime]] = {}
    
    def record_pattern(self, pattern_key: str, timestamp: datetime = None):
        """Record occurrence of a pattern"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if pattern_key not in self.pattern_history:
            self.pattern_history[pattern_key] = []
        
        self.pattern_history[pattern_key].append(timestamp)
    
    def check_pattern(self, pattern_key: str) -> Optional[Dict]:
        """
        Check if pattern has reached threshold
        
        Returns:
            Dict with pattern info if threshold reached, None otherwise
        """
        if pattern_key not in self.pattern_history:
            return None
        
        occurrences = self.pattern_history[pattern_key]
        
        if len(occurrences) < self.pattern_threshold:
            return None
        
        # Pattern detected
        first_occurrence = occurrences[0]
        latest_occurrence = occurrences[-1]
        time_span = (latest_occurrence - first_occurrence).total_seconds() / 3600  # hours
        
        return {
            'pattern_key': pattern_key,
            'occurrences': len(occurrences),
            'threshold': self.pattern_threshold,
            'time_span_hours': time_span,
            'first_seen': first_occurrence,
            'latest_seen': latest_occurrence,
            'message': f"Pattern '{pattern_key}' detected {len(occurrences)} times in {time_span:.1f} hours"
        }
    
    def get_top_patterns(self, limit: int = 5) -> List[Dict]:
        """Get most frequent patterns"""
        patterns = []
        
        for pattern_key, occurrences in self.pattern_history.items():
            if len(occurrences) >= self.pattern_threshold:
                patterns.append({
                    'pattern': pattern_key,
                    'count': len(occurrences),
                    'latest': occurrences[-1]
                })
        
        # Sort by count, descending
        patterns.sort(key=lambda x: x['count'], reverse=True)
        
        return patterns[:limit]
    
    def clear_old_patterns(self, days: int = 7):
        """Remove patterns older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for pattern_key in list(self.pattern_history.keys()):
            self.pattern_history[pattern_key] = [
                t for t in self.pattern_history[pattern_key] if t >= cutoff
            ]
            
            # Remove pattern if no recent occurrences
            if not self.pattern_history[pattern_key]:
                del self.pattern_history[pattern_key]



