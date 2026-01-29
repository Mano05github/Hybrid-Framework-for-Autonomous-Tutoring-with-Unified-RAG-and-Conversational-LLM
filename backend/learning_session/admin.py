from django.contrib import admin
from .models import (
    CodingProblem, CodeSubmission, HintHistory, StudentCodingProfile,
    EmotionEvent, TeachingStrategy, LearningPattern, EmotionLog,
    VisionaryMetric, VisionaryForecast, PerformanceAlert
)


# ==================== Gap 3: Socratic Coder Admin ====================

@admin.register(CodingProblem)
class CodingProblemAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'expected_algorithm', 'complexity', 'created_at']
    list_filter = ['difficulty', 'expected_algorithm']
    search_fields = ['title', 'description']


@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'problem', 'error_type', 'hint_level', 'is_correct', 'submitted_at']
    list_filter = ['error_type', 'is_correct', 'language']
    search_fields = ['user__username', 'problem__title']
    date_hierarchy = 'submitted_at'


@admin.register(HintHistory)
class HintHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'problem', 'hint_level', 'was_effective', 'delivered_at']
    list_filter = ['hint_level', 'was_effective']
    search_fields = ['user__username', 'problem__title']
    date_hierarchy = 'delivered_at'


@admin.register(StudentCodingProfile)
class StudentCodingProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill_level', 'avg_hint_level', 'quick_learner', 'updated_at']
    list_filter = ['skill_level', 'quick_learner', 'preferred_hint_style']
    search_fields = ['user__username']


# ==================== Gap 4: Adaptive Empath Admin ====================

@admin.register(EmotionEvent)
class EmotionEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'emotion_intensity', 'emotion_valence', 'trigger_type', 'timestamp']
    list_filter = ['emotion_intensity', 'trigger_type']
    search_fields = ['user__username', 'session_id']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']


@admin.register(TeachingStrategy)
class TeachingStrategyAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_modality', 'total_interventions', 'successful_interventions', 'updated_at']
    list_filter = ['preferred_modality', 'prefers_breaks', 'sensitive_to_failure']
    search_fields = ['user__username']
    readonly_fields = ['updated_at']


@admin.register(LearningPattern)
class LearningPatternAdmin(admin.ModelAdmin):
    list_display = ['user', 'avg_session_duration', 'optimal_session_length', 'baseline_emotion', 'emotion_volatility', 'updated_at']
    list_filter = ['requires_explicit_encouragement', 'benefits_from_breaks']
    search_fields = ['user__username']
    readonly_fields = ['updated_at']


@admin.register(EmotionLog)
class EmotionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'emotion_level', 'valence', 'intervention_type', 'intervention_effective', 'logged_at']
    list_filter = ['emotion_level', 'intervention_type', 'intervention_effective', 'activity_type']
    search_fields = ['user__username', 'session_id']
    date_hierarchy = 'logged_at'
    readonly_fields = ['logged_at']


# ==================== Gap 5: Always-On Visionary Admin ====================

@admin.register(VisionaryMetric)
class VisionaryMetricAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'activity_type', 'idle_time', 'error_count', 'velocity_score', 'timestamp']
    list_filter = ['activity_type', 'current_topic']
    search_fields = ['user__username', 'session_id', 'current_topic']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']
    
    # Analytics view
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_id', 'timestamp')
        }),
        ('Activity Metrics', {
            'fields': ('activity_type', 'current_topic', 'mouse_events', 'keypress_count')
        }),
        ('Performance Metrics', {
            'fields': ('idle_time', 'error_count', 'velocity_score')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )


@admin.register(VisionaryForecast)
class VisionaryForecastAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'current_mastery', 'predicted_mastery_date', 'days_remaining', 'velocity_trend', 'forecast_date']
    list_filter = ['velocity_trend']
    search_fields = ['user__username', 'topic']
    date_hierarchy = 'forecast_date'
    readonly_fields = ['forecast_date']
    
    # Forecasting view
    fieldsets = (
        ('Student & Topic', {
            'fields': ('user', 'topic', 'forecast_date')
        }),
        ('Current Status', {
            'fields': ('current_mastery', 'data_points')
        }),
        ('Predictions', {
            'fields': ('predicted_mastery_date', 'days_remaining', 'confidence', 'velocity_trend')
        })
    )


@admin.register(PerformanceAlert)
class PerformanceAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'alert_type', 'severity', 'resolved', 'timestamp']
    list_filter = ['alert_type', 'severity', 'resolved']
    search_fields = ['user__username', 'session_id']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']
    
    # Alert management view
    fieldsets = (
        ('Alert Info', {
            'fields': ('user', 'session_id', 'alert_type', 'severity', 'timestamp')
        }),
        ('Details', {
            'fields': ('message', 'metric_value', 'threshold', 'current_topic', 'activity_type')
        }),
        ('Resolution', {
            'fields': ('resolved', 'intervention_taken', 'intervention_type', 'resolved_at')
        }),
        ('Context', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} alert(s) marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'

