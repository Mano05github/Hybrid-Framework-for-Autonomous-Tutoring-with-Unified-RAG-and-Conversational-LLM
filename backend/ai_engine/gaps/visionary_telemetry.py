"""
Gap 5: Telemetry Monitoring System
Lightweight 10-second interval tracking for Always-On Visionary Agent
"""
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class TelemetrySnapshot:
    """Single telemetry data point"""
    timestamp: datetime
    mouse_events: int
    keypress_count: int
    idle_time: float
    error_count: int
    velocity_score: float
    activity_type: str
    current_topic: str
    metadata: Dict


class LightweightTelemetryMonitor:
    """
    Real-time telemetry collector for Visionary Agent
    
    Captures student activity metrics every 10 seconds with minimal overhead.
    Designed for <100ms latency and ~50 bytes per snapshot.
    """
    
    def __init__(self, interval_seconds: int = 10):
        self.interval = interval_seconds
        self.current_session: Dict[str, any] = {}
        self.baseline_velocity = 1.0
        self.last_snapshot_time = None
        
    def start_session(self, user_id: int, session_id: str, topic: str = ""):
        """Initialize telemetry tracking for a session"""
        self.current_session = {
            'user_id': user_id,
            'session_id': session_id,
            'current_topic': topic,
            'start_time': datetime.now(),
            'mouse_events': 0,
            'keypress_count': 0,
            'idle_start': None,
            'total_idle_time': 0.0,
            'error_count': 0,
            'last_activity_time': datetime.now(),
            'activity_type': 'learning',
            'problem_start_time': None,
            'problems_completed': 0,
            'total_completion_time': 0.0
        }
        self.last_snapshot_time = datetime.now()
        
    def record_mouse_event(self):
        """Record mouse movement or click"""
        if not self.current_session:
            return
            
        self.current_session['mouse_events'] += 1
        self._update_activity_time()
        
    def record_keypress(self):
        """Record keyboard input"""
        if not self.current_session:
            return
            
        self.current_session['keypress_count'] += 1
        self._update_activity_time()
        
    def record_error(self, error_type: str = 'unknown'):
        """Record an error occurrence"""
        if not self.current_session:
            return
            
        self.current_session['error_count'] += 1
        self._update_activity_time()
        
        # Store error for pattern analysis
        if 'error_history' not in self.current_session:
            self.current_session['error_history'] = []
        self.current_session['error_history'].append({
            'timestamp': datetime.now(),
            'type': error_type
        })
        
    def set_activity_type(self, activity_type: str):
        """Update current activity type"""
        if not self.current_session:
            return
            
        self.current_session['activity_type'] = activity_type
        
        # Start problem timer if coding
        if activity_type == 'coding' and self.current_session['problem_start_time'] is None:
            self.current_session['problem_start_time'] = datetime.now()
    
    def record_problem_completion(self, success: bool = True, time_taken: float = 0.0):
        """Record completion of a problem/task"""
        if not self.current_session or self.current_session['problem_start_time'] is None:
            return
            
        # Use provided time or calculate from start time
        if time_taken > 0:
            completion_time = time_taken
        else:
            completion_time = (datetime.now() - self.current_session['problem_start_time']).total_seconds()
        
        if success:
            self.current_session['problems_completed'] += 1
            self.current_session['total_completion_time'] += completion_time
            
            # Update baseline velocity
            if self.current_session['problems_completed'] > 0:
                self.baseline_velocity = (
                    self.current_session['total_completion_time'] / 
                    self.current_session['problems_completed']
                )
        
        # Reset problem timer
        self.current_session['problem_start_time'] = None
        
    def update_topic(self, topic: str):
        """Update current learning topic"""
        if not self.current_session:
            return
            
        self.current_session['current_topic'] = topic
        
    def _update_activity_time(self):
        """Update last activity timestamp and handle idle time"""
        now = datetime.now()
        
        # If was idle, record idle duration
        if self.current_session.get('idle_start'):
            idle_duration = (now - self.current_session['idle_start']).total_seconds()
            self.current_session['total_idle_time'] += idle_duration
            self.current_session['idle_start'] = None
        
        self.current_session['last_activity_time'] = now
        
    def _calculate_idle_time(self) -> float:
        """Calculate current idle time"""
        if not self.current_session:
            return 0.0
            
        now = datetime.now()
        last_activity = self.current_session['last_activity_time']
        current_idle = (now - last_activity).total_seconds()
        
        # Mark as idle if no activity for >3 seconds
        if current_idle > 3.0 and self.current_session['idle_start'] is None:
            self.current_session['idle_start'] = last_activity
            
        # Return cumulative idle time in this interval
        interval_idle = self.current_session.get('total_idle_time', 0.0)
        
        # Add current idle if applicable
        if self.current_session.get('idle_start'):
            interval_idle += (now - self.current_session['idle_start']).total_seconds()
            
        return interval_idle
        
    def _calculate_velocity_score(self) -> float:
        """Calculate current velocity relative to baseline"""
        if not self.current_session or self.current_session.get('problem_start_time') is None:
            return 1.0
            
        # Current problem time
        current_time = (datetime.now() - self.current_session['problem_start_time']).total_seconds()
        
        if current_time == 0 or self.baseline_velocity == 0:
            return 1.0
            
        # Velocity = baseline / current (>1.0 = faster, <1.0 = slower)
        velocity = self.baseline_velocity / current_time
        
        # Clamp to reasonable range [0.1, 3.0]
        return max(0.1, min(3.0, velocity))
        
    def get_snapshot(self) -> Optional[TelemetrySnapshot]:
        """
        Capture current telemetry snapshot
        
        Returns:
            TelemetrySnapshot or None if not in active session
        """
        if not self.current_session:
            return None
            
        now = datetime.now()
        
        # Calculate metrics for this interval
        idle_time = self._calculate_idle_time()
        velocity_score = self._calculate_velocity_score()
        
        snapshot = TelemetrySnapshot(
            timestamp=now,
            mouse_events=self.current_session['mouse_events'],
            keypress_count=self.current_session['keypress_count'],
            idle_time=idle_time,
            error_count=self.current_session['error_count'],
            velocity_score=velocity_score,
            activity_type=self.current_session['activity_type'],
            current_topic=self.current_session['current_topic'],
            metadata={
                'problems_completed': self.current_session['problems_completed'],
                'baseline_velocity': self.baseline_velocity
            }
        )
        
        # Reset interval counters
        self._reset_interval_counters()
        self.last_snapshot_time = now
        
        return snapshot
        
    def _reset_interval_counters(self):
        """Reset counters for next interval"""
        self.current_session['mouse_events'] = 0
        self.current_session['keypress_count'] = 0
        self.current_session['error_count'] = 0
        self.current_session['total_idle_time'] = 0.0
        
    def should_capture_snapshot(self) -> bool:
        """Check if it's time for next snapshot"""
        if not self.last_snapshot_time:
            return True
            
        elapsed = (datetime.now() - self.last_snapshot_time).total_seconds()
        return elapsed >= self.interval
        
    def end_session(self):
        """Clean up session data"""
        self.current_session = {}
        self.last_snapshot_time = None


class TelemetryAggregator:
    """Aggregate telemetry snapshots for analytics"""
    
    @staticmethod
    def calculate_average_metrics(snapshots: List[TelemetrySnapshot]) -> Dict:
        """Calculate average metrics from multiple snapshots"""
        if not snapshots:
            return {}
            
        total_mouse = sum(s.mouse_events for s in snapshots)
        total_keys = sum(s.keypress_count for s in snapshots)
        total_idle = sum(s.idle_time for s in snapshots)
        total_errors = sum(s.error_count for s in snapshots)
        avg_velocity = sum(s.velocity_score for s in snapshots) / len(snapshots)
        
        return {
            'avg_mouse_events': total_mouse / len(snapshots),
            'avg_keypress_count': total_keys / len(snapshots),
            'total_idle_time': total_idle,
            'avg_idle_per_interval': total_idle / len(snapshots),
            'total_errors': total_errors,
            'avg_velocity': avg_velocity,
            'snapshot_count': len(snapshots)
        }
    
    @staticmethod
    def detect_trend(snapshots: List[TelemetrySnapshot], metric: str) -> str:
        """
        Detect trend in a metric across snapshots
        
        Returns: 'improving', 'stable', or 'declining'
        """
        if len(snapshots) < 3:
            return 'stable'
            
        # Get metric values
        values = []
        for s in snapshots:
            if metric == 'velocity':
                values.append(s.velocity_score)
            elif metric == 'errors':
                values.append(s.error_count)
            elif metric == 'idle':
                values.append(s.idle_time)
            elif metric == 'activity':
                values.append(s.mouse_events + s.keypress_count)
                
        if not values:
            return 'stable'
            
        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
            
        slope = numerator / denominator
        
        # Determine trend based on metric type
        if metric in ['velocity', 'activity']:
            # Higher is better
            if slope > 0.1:
                return 'improving'
            elif slope < -0.1:
                return 'declining'
        else:
            # Lower is better (errors, idle)
            if slope < -0.1:
                return 'improving'
            elif slope > 0.1:
                return 'declining'
                
        return 'stable'


