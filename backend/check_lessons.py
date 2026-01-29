import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Lesson, Topic

def check_lessons():
    print("Checking database for Lessons...")
    lessons = Lesson.objects.all()
    print(f"Total Lessons: {lessons.count()}")
    
    algo_topic = Topic.objects.filter(title="Algorithms").first()
    if algo_topic:
        algo_lessons = Lesson.objects.filter(topic=algo_topic)
        print(f"Lessons under 'Algorithms' topic: {algo_lessons.count()}")
        for l in algo_lessons:
            print(f" - {l.title} (Order: {l.order})")
    else:
        print("Topic 'Algorithms' NOT FOUND!")

if __name__ == "__main__":
    check_lessons()
