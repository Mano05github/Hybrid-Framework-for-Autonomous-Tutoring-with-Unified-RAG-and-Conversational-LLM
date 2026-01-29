from django.db import models
from django.conf import settings

class Subject(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.subject.name} - {self.title}"

class Lesson(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Markdown content for the lesson")
    order = models.PositiveIntegerField(default=0)
    # Fields for AI/RAG integration
    embedding_id = models.CharField(max_length=100, blank=True, null=True, help_text="Reference to vector DB ID")
    
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
    options = models.JSONField(default=list, blank=True, help_text="For MCQ: list of options")
    correct_answer = models.TextField(help_text="For MCQ: correct option text. For Code: expected output or solution pattern")
    explanation = models.TextField(blank=True)
    
    def __str__(self):
        return self.text[:50]

class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title if self.lesson else 'Unknown'}"
