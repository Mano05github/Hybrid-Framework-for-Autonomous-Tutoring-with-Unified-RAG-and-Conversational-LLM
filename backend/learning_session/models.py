from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class CodingProblem(models.Model):
    """Coding problems/exercises for Gap 3 Socratic Coder Agent"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(
        max_length=20,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )
    expected_algorithm = models.CharField(max_length=100)  # e.g., "binary_search"
    test_cases = models.JSONField(default=list)  # [{"input": [...], "expected_output": ...}]
    starter_code = models.TextField(blank=True)
    complexity = models.IntegerField(default=50)  # 0-100 complexity score
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'coding_problems'
        ordering = ['difficulty', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class CodeSubmission(models.Model):
    """Student code submission history for Gap 3"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_submissions')
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    language = models.CharField(max_length=20, default='python')
    
    # Error analysis results
    error_type = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Error'),
            ('syntax', 'Syntax Error'),
            ('logic', 'Logic Error'),
            ('approach', 'Approach Error')
        ],
        default='none'
    )
    error_details = models.TextField(blank=True)
    
    # Hint delivered
    hint_level = models.IntegerField(null=True, blank=True)  # 1-5
    hint_text = models.TextField(blank=True)
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    time_spent_seconds = models.IntegerField(default=0)  # Time since problem start
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'code_submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', 'problem', '-submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.problem.title} ({self.submitted_at})"


class HintHistory(models.Model):
    """Track hint effectiveness for adaptive learning (Gap 3)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hint_history')
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE)
    hint_level = models.IntegerField()  # 1-5
    hint_text = models.TextField()
    
    # Effectiveness metrics
    was_effective = models.BooleanField(null=True, blank=True)  # Did student solve after hint?
    time_to_resolution_seconds = models.IntegerField(null=True, blank=True)
    follow_up_errors = models.IntegerField(default=0)  # Errors after hint
    
    delivered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'hint_history'
        ordering = ['-delivered_at']
    
    def mark_effective(self, resolution_time_seconds):
        """Mark hint as effective when problem is solved"""
        self.was_effective = True
        self.time_to_resolution_seconds = resolution_time_seconds
        self.resolved_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Hint L{self.hint_level} - {self.user.username} ({self.delivered_at})"


class StudentCodingProfile(models.Model):
    """Aggregate coding profile for hint personalization (Gap 3)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coding_profile')
    
    # Skill assessment
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='beginner'
    )
    
    # Performance metrics (stored as JSON for flexibility)
    problems_solved = models.JSONField(default=dict)  # {"easy": 5, "medium": 2, "hard": 0}
    avg_solve_time = models.JSONField(default=dict)   # {"easy": 420.5, "medium": 850.2}
    avg_hint_level = models.FloatField(default=3.0)   # Average hint level needed (1.0-5.0)
    hint_effectiveness = models.JSONField(default=dict)  # {"1": 0.6, "2": 0.75, ...}
    
    # Learning preferences
    preferred_hint_style = models.CharField(
        max_length=20,
        choices=[
            ('minimal', 'Minimal'),
            ('detailed', 'Detailed'),
            ('visual', 'Visual')
        ],
        default='detailed'
    )
    
    # Struggle patterns
    common_error_types = models.JSONField(default=list)  # ["off_by_one", "infinite_loop"]
    quick_learner = models.BooleanField(default=False)   # Adapt faster if true
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_coding_profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.skill_level} (Avg hint: {self.avg_hint_level:.1f})"


# ==================== GAP 4: ADAPTIVE EMPATH AGENT ====================

class EmotionEvent(models.Model):
    """Real-time emotion events for Gap 4 Adaptive Empath Agent"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emotion_events')
    session_id = models.CharField(max_length=100)  # Learning session identifier
    
    # Emotion metrics
    emotion_valence = models.FloatField()  # -1.0 (negative) to +1.0 (positive)
    emotion_intensity = models.CharField(
        max_length=20,
        choices=[
            ('mild', 'Mild'),
            ('moderate', 'Moderate'),
            ('strong', 'Strong')
        ]
    )
    
    # Detection sources
    pause_duration = models.FloatField(default=0.0)  # Seconds of pause
    sentiment_score = models.FloatField(default=0.0)  # From STT transcript sentiment
    error_rate = models.FloatField(default=0.0)  # Errors per minute
    
    # Trigger information
    trigger_type = models.CharField(
        max_length=50,
        choices=[
            ('pause', 'Long Pause'),
            ('sentiment', 'Negative Sentiment'),
            ('error_spike', 'Error Spike'),
            ('combined', 'Combined Factors')
        ]
    )
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    context_data = models.JSONField(default=dict)  # Additional context
    
    class Meta:
        db_table = 'emotion_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'session_id', '-timestamp']),
            models.Index(fields=['emotion_intensity', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.emotion_intensity} ({self.emotion_valence:.2f}) @ {self.timestamp}"


class TeachingStrategy(models.Model):
    """Teaching strategy preferences and effectiveness for Gap 4"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teaching_strategy')
    
    # Modality preferences
    preferred_modality = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('visual', 'Visual'),
            ('audio', 'Audio'),
            ('mixed', 'Mixed')
        ],
        default='mixed'
    )
    
    # Intervention effectiveness (JSON: {intervention_type: effectiveness_score})
    effective_interventions = models.JSONField(default=dict)
    # Example: {"pacing_adjustment": 0.85, "visualization": 0.72, "branching": 0.90}
    
    # Response to interventions
    avg_recovery_time = models.FloatField(default=0.0)  # Seconds to positive emotion
    intervention_acceptance_rate = models.FloatField(default=0.0)  # 0.0-1.0
    
    # Learning context preferences
    prefers_breaks = models.BooleanField(default=False)
    prefers_encouragement = models.BooleanField(default=True)
    sensitive_to_failure = models.BooleanField(default=False)
    
    # Tracking
    total_interventions = models.IntegerField(default=0)
    successful_interventions = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teaching_strategies'
    
    def __str__(self):
        success_rate = (self.successful_interventions / self.total_interventions * 100) if self.total_interventions > 0 else 0
        return f"{self.user.username} - {self.preferred_modality} ({success_rate:.1f}% success)"


class LearningPattern(models.Model):
    """Long-term learning patterns and struggle areas for Gap 4"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_patterns')
    
    # Frustration triggers (topics that cause negative emotions)
    topics_causing_frustration = models.JSONField(default=list)
    # Example: ["Binary Search", "Dynamic Programming", "Graph Algorithms"]
    
    # Peak performance times
    peak_focus_times = models.JSONField(default=dict)
    # Example: {"morning": 0.85, "afternoon": 0.65, "evening": 0.45}
    
    # Session duration patterns
    avg_session_duration = models.IntegerField(default=0)  # Minutes
    optimal_session_length = models.IntegerField(default=45)  # Minutes
    
    # Emotional patterns
    emotion_volatility = models.FloatField(default=0.0)  # 0.0-1.0 (how quickly emotions change)
    baseline_emotion = models.FloatField(default=0.0)  # Average emotional valence
    
    # Recovery patterns
    requires_explicit_encouragement = models.BooleanField(default=False)
    benefits_from_breaks = models.BooleanField(default=True)
    
    # Aggregated metrics
    total_negative_events = models.IntegerField(default=0)
    total_positive_events = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_patterns'
    
    def __str__(self):
        return f"{self.user.username} - Baseline: {self.baseline_emotion:.2f}, Volatility: {self.emotion_volatility:.2f}"


class EmotionLog(models.Model):
    """Aggregated emotion logs for pattern analysis (Gap 4)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emotion_logs')
    session_id = models.CharField(max_length=100)
    topic_id = models.IntegerField(null=True, blank=True)  # Reference to Topic if available
    
    # Emotion data
    emotion_level = models.CharField(
        max_length=20,
        choices=[
            ('positive', 'Positive'),
            ('neutral', 'Neutral'),
            ('negative', 'Negative')
        ]
    )
    valence = models.FloatField()  # -1.0 to +1.0
    
    # Context
    pause_duration = models.FloatField(default=0.0)
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('coding', 'Coding'),
            ('learning', 'Learning'),
            ('quiz', 'Quiz'),
            ('discussion', 'Discussion')
        ],
        default='learning'
    )
    
    # Intervention
    intervention_taken = models.BooleanField(default=False)
    intervention_type = models.CharField(max_length=50, blank=True)
    intervention_effective = models.BooleanField(null=True, blank=True)
    
    # Metadata
    logged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'emotion_logs'
        ordering = ['-logged_at']
        indexes = [
            models.Index(fields=['user', 'session_id', '-logged_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.emotion_level} ({self.valence:.2f}) @ {self.logged_at}"


# ==================== GAP 5: ALWAYS-ON VISIONARY AGENT ====================

class VisionaryMetric(models.Model):
    """Lightweight telemetry snapshots for Gap 5 real-time monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visionary_metrics')
    session_id = models.CharField(max_length=100)
    
    # Telemetry data (every 10 seconds)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Activity metrics
    mouse_events = models.IntegerField(default=0)  # Mouse movements/clicks in interval
    keypress_count = models.IntegerField(default=0)  # Keypresses in interval
    idle_time = models.FloatField(default=0.0)  # Seconds of inactivity
    
    # Performance metrics
    error_count = models.IntegerField(default=0)  # Errors in interval
    completion_time = models.FloatField(null=True, blank=True)  # Problem completion time (if applicable)
    velocity_score = models.FloatField(default=1.0)  # Relative velocity (1.0 = baseline)
    
    # Context
    current_topic = models.CharField(max_length=200, blank=True)
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('coding', 'Coding'),
            ('learning', 'Learning'),
            ('quiz', 'Quiz'),
            ('drawing', 'Canvas Drawing'),
            ('idle', 'Idle')
        ],
        default='learning'
    )
    
    # Metadata
    metadata = models.JSONField(default=dict)  # Additional context
    
    class Meta:
        db_table = 'visionary_metrics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'session_id', '-timestamp']),
            models.Index(fields=['timestamp']),  # For time-series queries
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} @ {self.timestamp}"


class VisionaryForecast(models.Model):
    """Mastery timeline predictions for Gap 5 strategic planning"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visionary_forecasts')
    topic = models.CharField(max_length=200)  # Topic being forecasted
    
    # Forecast data
    created_at = models.DateTimeField(auto_now_add=True)
    forecast_date = models.DateField(auto_now_add=True)  # When prediction was made
    
    # Current state
    current_mastery = models.FloatField()  # 0.0-1.0 (percentage/100)
    
    # Predictions
    predicted_mastery_date = models.DateField(null=True, blank=True)  # When student will reach 85% mastery
    days_remaining = models.IntegerField(null=True, blank=True)  # Days until mastery
    confidence = models.FloatField(default=0.0)  # Model confidence (0.0-1.0)
    
    # Trajectory
    velocity_trend = models.CharField(
        max_length=20,
        choices=[
            ('improving', 'Improving'),
            ('stable', 'Stable'),
            ('declining', 'Declining')
        ],
        default='stable'
    )
    
    # Metadata
    model_type = models.CharField(max_length=50, default='linear_regression')  # Forecasting model used
    data_points = models.IntegerField(default=0)  # Number of historical data points used
    
    class Meta:
        db_table = 'visionary_forecasts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'topic', '-forecast_date']),
        ]
        # Prevent duplicate forecasts for same user+topic+date
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'topic', 'forecast_date'],
                name='unique_forecast_per_user_topic_date'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.topic}: {self.current_mastery:.0%} → {self.predicted_mastery_date or 'TBD'}"


class PerformanceAlert(models.Model):
    """Anomaly detection alerts for Gap 5 immediate intervention"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_alerts')
    session_id = models.CharField(max_length=100)
    
    # Alert metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    alert_type = models.CharField(
        max_length=50,
        choices=[
            ('idle_spike', 'Idle Spike'),
            ('error_cascade', 'Error Cascade'),
            ('velocity_drop', 'Velocity Drop'),
            ('streak_break', 'Streak Break'),
            ('pattern_detected', 'Recurring Pattern'),
            ('canvas_error', 'Canvas Validation Error')
        ]
    )
    
    # Severity
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High')
        ],
        default='moderate'
    )
    
    # Alert details
    message = models.TextField()  # Human-readable alert message
    metric_value = models.FloatField(null=True, blank=True)  # Triggering metric value
    threshold = models.FloatField(null=True, blank=True)  # Threshold that was exceeded
    
    # Context
    current_topic = models.CharField(max_length=200, blank=True)
    activity_type = models.CharField(max_length=50, blank=True)
    
    # Action tracking
    intervention_taken = models.BooleanField(default=False)
    intervention_type = models.CharField(max_length=50, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)  # Additional context (pattern details, etc.)
    
    class Meta:
        db_table = 'performance_alerts'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'session_id', '-timestamp']),
            models.Index(fields=['alert_type', 'severity', '-timestamp']),
            models.Index(fields=['resolved', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.alert_type} ({self.severity}) @ {self.timestamp}"
