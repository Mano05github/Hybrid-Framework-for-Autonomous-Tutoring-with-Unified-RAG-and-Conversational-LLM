"""
PBL Models

Tables:
    ConceptNode   — node in the subject concept graph (links to core.Topic)
    PBLSession    — one learning session per student attempt
    PBLAttempt    — code submission within a session
    TelemetryEvent— batched client telemetry records
"""

import uuid
from django.db import models
from django.conf import settings
from core.models import Topic, Subject


# ── Concept Graph ─────────────────────────────────────────────────────────────

class ConceptNode(models.Model):
    """
    A concept within a subject's learning graph.
    Wraps a core.Topic to add PBL-specific metadata.
    """
    DIFFICULTY_CHOICES = [(i, str(i)) for i in range(1, 6)]

    topic       = models.OneToOneField(Topic, on_delete=models.CASCADE,
                                        related_name='concept_node')
    slug        = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    difficulty  = models.PositiveSmallIntegerField(default=1, choices=DIFFICULTY_CHOICES,
                                                    help_text="1=easiest, 5=hardest")
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True,
                                            related_name='unlocks')
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.topic.title} (d={self.difficulty})"

    @property
    def subject(self):
        return self.topic.subject


# ── Session ───────────────────────────────────────────────────────────────────

class PBLSession(models.Model):
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                      related_name='pbl_sessions')
    concept       = models.ForeignKey(ConceptNode, on_delete=models.SET_NULL, null=True,
                                       related_name='sessions')
    subject       = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True,
                                       related_name='pbl_sessions')

    # Problem snapshot (generated at session start)
    problem_title     = models.CharField(max_length=300, blank=True)
    problem_statement = models.TextField(blank=True)

    # Adaptive state
    difficulty_level  = models.PositiveSmallIntegerField(default=1)
    mastery_score     = models.FloatField(default=0.0)
    hint_count        = models.PositiveIntegerField(default=0)
    attempt_count     = models.PositiveIntegerField(default=0)

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"PBLSession({self.user}, {self.concept}, {self.status})"


# ── Attempt ───────────────────────────────────────────────────────────────────

class PBLAttempt(models.Model):
    session         = models.ForeignKey(PBLSession, on_delete=models.CASCADE,
                                         related_name='attempts')
    attempt_number  = models.PositiveSmallIntegerField(default=1)
    code_submitted  = models.TextField(blank=True)
    output          = models.TextField(blank=True)
    is_correct      = models.BooleanField(null=True)   # None = not yet evaluated
    ai_feedback     = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['attempt_number']

    def __str__(self):
        return f"Attempt#{self.attempt_number} ({self.session_id}) correct={self.is_correct}"


# ── Telemetry ─────────────────────────────────────────────────────────────────

class TelemetryEvent(models.Model):
    session    = models.ForeignKey(PBLSession, on_delete=models.CASCADE,
                                    related_name='telemetry', null=True, blank=True)
    event_type = models.CharField(max_length=60)
    payload    = models.JSONField(default=dict)
    ts         = models.DateTimeField()           # client-reported timestamp

    class Meta:
        ordering = ['ts']

    def __str__(self):
        return f"[{self.event_type}] @ {self.ts}"
