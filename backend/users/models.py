import random
import string
import datetime
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for the Personal Tutoring Website.
    """
    is_student = models.BooleanField(default=True)
    is_tutor = models.BooleanField(default=False)
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text="Unique Student ID (e.g., SID-2024-X9A2)")
    
    def save(self, *args, **kwargs):
        if not self.student_id and self.is_student:
            self.student_id = self.generate_student_id()
        super().save(*args, **kwargs)

    def generate_student_id(self):
        year = datetime.datetime.now().year
        while True:
            # Generate 4 random alphanumeric characters
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            new_id = f"SID-{year}-{random_chars}"
            # Ensure uniqueness
            if not User.objects.filter(student_id=new_id).exists():
                return new_id

    def __str__(self):
        return f"{self.username} ({self.student_id})" if self.student_id else self.username

