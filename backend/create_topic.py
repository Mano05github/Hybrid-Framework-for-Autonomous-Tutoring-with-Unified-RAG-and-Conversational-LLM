import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Subject, Topic

def create_sample_topic():
    subject, _ = Subject.objects.get_or_create(name="Computer Science")
    topic, created = Topic.objects.get_or_create(
        title="Python Basics",
        defaults={'subject': subject, 'order': 1}
    )
    if created:
        print(f"Created Topic: {topic.title}")
    else:
        print(f"Topic exists: {topic.title}")
    return topic.id

if __name__ == "__main__":
    create_sample_topic()
