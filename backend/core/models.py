from django.db import models
from django.conf import settings
from django.utils import timezone


class Subject(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    grade_level = models.PositiveSmallIntegerField(
        default=0,
        help_text="0 = all grades; 8–12 for grade-specific content"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    prerequisites = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='required_for',
        help_text="Topics that must be sufficiently mastered before this one"
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.subject.name} - {self.title}"


class Lesson(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Markdown content for the lesson")
    order = models.PositiveIntegerField(default=0)
    embedding_id = models.CharField(max_length=100, blank=True, null=True,
                                    help_text="Reference to vector DB ID")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Quiz(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice'),
        ('CODE', 'Code Challenge'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=4, choices=QUESTION_TYPES, default='MCQ')
    options = models.JSONField(default=list, blank=True,
                               help_text="For MCQ: list of options")
    correct_answer = models.TextField(
        help_text="For MCQ: correct option text. For Code: expected output or solution pattern"
    )
    explanation = models.TextField(blank=True)

    def __str__(self):
        return self.text[:50]


class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title if self.lesson else 'Unknown'}"


# ─────────────────────────────────────────────────────────────────────────────
# Student Intelligence Profile (SIP) — v2 spec
# ─────────────────────────────────────────────────────────────────────────────

MASTERY_WEAK       = "weak"
MASTERY_DEVELOPING = "developing"
MASTERY_STRONG     = "strong"
MASTERY_MASTERED   = "mastered"


def _mastery_label(score: float) -> str:
    if score < 40:
        return MASTERY_WEAK
    if score < 70:
        return MASTERY_DEVELOPING
    if score < 85:
        return MASTERY_STRONG
    return MASTERY_MASTERED


class StudentIntelligenceProfile(models.Model):
    """
    Persistent per-student adaptive model (v2 Student Intelligence Profile).

    Fields persist across grades and accumulate over the student's lifetime.
    Never reset — only evolve.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sip'
    )

    # ── Mastery ───────────────────────────────────────────────────────────────
    mastery_map = models.JSONField(
        default=dict,
        help_text="topic_id (str) → Elo mastery score (float 0–2000; 1500 = baseline 70/100)"
    )
    mistake_patterns = models.JSONField(
        default=dict,
        help_text="topic_id → {error_type: count}  e.g. {'42': {'off_by_one': 3}}"
    )

    # ── Learning Style Weights (0.0–1.0 per dimension, sum ≈ 1.0) ────────────
    visual_weight      = models.FloatField(default=0.25)
    analytical_weight  = models.FloatField(default=0.25)
    conceptual_weight  = models.FloatField(default=0.25)
    pattern_weight     = models.FloatField(default=0.25)

    # ── Tolerance & Pace ─────────────────────────────────────────────────────
    difficulty_tolerance = models.FloatField(
        default=0.5,
        help_text="0.0 = needs very easy content; 1.0 = handles hard content comfortably"
    )
    response_time_avg = models.FloatField(
        default=0.0,
        help_text="Average seconds taken to answer questions correctly"
    )

    # ── Confidence ────────────────────────────────────────────────────────────
    confidence_index = models.FloatField(
        default=50.0,
        help_text="0–100; updated after each mini-test based on accuracy trend"
    )

    # ── Streaks ───────────────────────────────────────────────────────────────
    daily_streak         = models.PositiveIntegerField(default=0)
    correct_streak       = models.PositiveIntegerField(default=0)
    last_active_date     = models.DateField(null=True, blank=True)

    # ── Recommendation Queue ─────────────────────────────────────────────────
    revision_priority_queue = models.JSONField(
        default=list,
        help_text="Ordered list of topic_ids to revise; recalculated post-session"
    )

    # ── Session Adaptation ────────────────────────────────────────────────────
    consecutive_wrong_answers = models.PositiveSmallIntegerField(
        default=0,
        help_text="Counter for adaptive difficulty engine — reset on correct answer"
    )
    reinforcement_mode_active = models.BooleanField(
        default=False,
        help_text="True when concept reinforcement loop is triggered"
    )
    reinforcement_failures = models.PositiveSmallIntegerField(
        default=0,
        help_text="Failures during current reinforcement mode session"
    )

    # ── Metadata ─────────────────────────────────────────────────────────────
    grade_level    = models.PositiveSmallIntegerField(default=8)
    total_sessions = models.PositiveIntegerField(default=0)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Intelligence Profile"

    def __str__(self):
        return f"SIP({self.user.username})"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def get_mastery_score(self, topic_id) -> float:
        """Return normalised 0–100 mastery score for a topic."""
        elo = self.mastery_map.get(str(topic_id), 1500.0)
        # Elo 1500 → 70/100 (baseline); scale: 1000 → 0, 2000 → 100
        return max(0.0, min(100.0, (elo - 1000) / 10.0))

    def get_mastery_label(self, topic_id) -> str:
        return _mastery_label(self.get_mastery_score(topic_id))

    def update_mastery(self, topic_id, correct: bool, k_factor: float = 30.0):
        """
        Elo-based mastery update with forgetting-curve decay.
        Call this after every evaluated answer / mini-test question.
        """
        import math
        topic_key = str(topic_id)
        current_elo = self.mastery_map.get(topic_key, 1500.0)

        # Forgetting decay: 0.99 per day since last update
        decay_info = (self.mistake_patterns.get('_last_seen') or {})
        last_seen_str = decay_info.get(topic_key)
        if last_seen_str:
            from datetime import date
            try:
                last_seen = date.fromisoformat(last_seen_str)
                days = (date.today() - last_seen).days
                current_elo = current_elo * (0.99 ** days)
            except Exception:
                pass

        # Elo expected score
        expected = 1 / (1 + math.pow(10, (1500 - current_elo) / 400))
        actual   = 1.0 if correct else 0.0
        new_elo  = current_elo + k_factor * (actual - expected)
        new_elo  = max(800.0, min(2200.0, new_elo))

        self.mastery_map[topic_key] = new_elo

        # Record last-seen date for this topic
        if '_last_seen' not in self.mistake_patterns:
            self.mistake_patterns['_last_seen'] = {}
        self.mistake_patterns['_last_seen'][topic_key] = str(timezone.now().date())

        # Update adaptive difficulty counter
        if correct:
            self.consecutive_wrong_answers = 0
            self.correct_streak += 1
            self.reinforcement_failures    = 0
            if self.reinforcement_mode_active:
                self.reinforcement_mode_active = False
        else:
            self.consecutive_wrong_answers += 1
            self.correct_streak = 0
            if self.reinforcement_mode_active:
                self.reinforcement_failures += 1

    def update_streaks(self):
        """Call at start of each session to update daily streak."""
        today = timezone.now().date()
        if self.last_active_date:
            delta = (today - self.last_active_date).days
            if delta == 1:
                self.daily_streak += 1
            elif delta > 1:
                self.daily_streak = 1
            # delta == 0 → same day, no change
        else:
            self.daily_streak = 1
        self.last_active_date = today
        self.total_sessions  += 1

    def dominant_learning_style(self) -> str:
        weights = {
            'visual':      self.visual_weight,
            'analytical':  self.analytical_weight,
            'conceptual':  self.conceptual_weight,
            'pattern':     self.pattern_weight,
        }
        return max(weights, key=weights.get)

    def recalculate_revision_queue(self, all_topic_ids: list) -> list:
        """
        Recompute revision_priority_queue: weakest high-impact topics first.
        Call after each mini-test. Returns sorted list of topic_id strings.
        """
        scored = []
        for tid in all_topic_ids:
            score = self.get_mastery_score(tid)
            if score < 85:          # Only topics not yet mastered
                scored.append((str(tid), score))
        # Sort ascending by mastery (weakest first)
        scored.sort(key=lambda x: x[1])
        self.revision_priority_queue = [t[0] for t in scored[:10]]
        return self.revision_priority_queue
